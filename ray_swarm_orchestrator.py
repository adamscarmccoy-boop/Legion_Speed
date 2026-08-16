# --------------------------------------------------------------
# ray_swarm_orchestrator.py
# --------------------------------------------------------------
#  • Fixes LanceDB/Lance schema & zero‑copy issues
#  • Starts a local Ray cluster (the “warden/manager”)
#  • Launches Ingestion, Diffusion, and Serving actors
#  • Exposes a simple HTTP API for an external WebGPU front‑end
# --------------------------------------------------------------

import os
import time
import numpy as np
import torch
import ray
from ray import serve

# ==============================================================================
# SOVEREIGN LIFE-CYCLE STABILIZER (AUTO-INJECTED)
# Prevents dangling stdout/stdio pipes and GCS registry locks on Windows exit
# ==============================================================================
import atexit
import signal

def clean_exit_handler(*args, **kwargs):
    import sys
    sys.stderr.write("\n[LMS LIFECYCLE] Exit triggered. Flushing system streams...\n")
    sys.stderr.flush()
    try:
        import ray
        if ray.is_initialized():
            sys.stderr.write("[LMS LIFECYCLE] Active Ray session detected. Disconnecting...\n")
            ray.shutdown()
    except Exception:
        pass
    sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================

from fastapi import FastAPI, File, UploadFile, Response
from fastapi.responses import StreamingResponse
import soundfile as sf
import librosa
import duckdb
import lancedb
import pyarrow as pa
import polars as pl
from pydantic import BaseModel, Field, ValidationError
from typing import Optional, List

# ------------------------------------------------------------------
# 1️⃣  Ray cluster initialization (the “warden/manager”)
# ------------------------------------------------------------------
# If you already have a cluster running, use address='auto'.
# Here we start a local cluster with all available CPUs and one GPU.
ray.init(
    num_cpus=os.cpu_count(),
    num_gpus=1 if torch.cuda.is_available() else 0,
    include_dashboard=True,
    dashboard_host="0.0.0.0",
    dashboard_port=8265,
    namespace="legion",
    _temp_dir=os.path.expanduser("~/ray_tmp"),
)
print("[Ray] Dashboard -> http://127.0.0.1:8265")
print("[Ray] Cluster resources:", ray.available_resources())

# ------------------------------------------------------------------
# 2️⃣  Helper: Fixed LanceDB table creation (zero‑copy safe)
# ------------------------------------------------------------------
def get_or_create_lance_table(db_path: str, table_name: str = "audio_vibe_gpu"):
    """
    Returns a LanceDB table with the exact schema used in the notebook:
        filename: string
        filepath: string
        vector:   fixed‑size list<float32>[384]
    The function safely drops & recreates the table if it already exists
    (to avoid schema‑mismatch crashes that were seen in the original scripts).
    """
    db = lancedb.connect(db_path)
    if table_name in db.table_names():
        db.drop_table(table_name)  # clean slate – prevents stale schema errors
    schema = pa.schema([
        pa.field("filename", pa.string()),
        pa.field("filepath", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), 384)),
    ])
    tbl = db.create_table(table_name, schema=schema)
    return tbl

# ------------------------------------------------------------------
# 3️⃣  Pydantic firewall – the exact 46‑point schema from the notebook
# ------------------------------------------------------------------
class AlignedDSPTrackRecord(BaseModel):
    filepath: str
    filename: str
    asset_type: str
    drum_type: str
    tempo: float
    key: str
    rms_db: float
    crest_factor: float
    sub_bass_energy: float
    bass_energy: float
    mid_energy: float
    high_energy: float
    spectral_centroid: float
    spectral_rolloff: float
    spectral_bandwidth: float
    spectral_contrast: float
    zcr: float
    onset_strength: float
    transient_density: float
    harmonic_ratio: float
    percussive_ratio: float
    # MFCCs 1‑13
    mfcc_1: float; mfcc_2: float; mfcc_3: float; mfcc_4: float; mfcc_5: float
    mfcc_6: float; mfcc_7: float; mfcc_8: float; mfcc_9: float; mfcc_10: float
    mfcc_11: float; mfcc_12: float; mfcc_13: float
    # Chroma C‑B (12 bins)
    chroma_C: float; chroma_Cs: float; chroma_D: float; chroma_Ds: float
    chroma_E: float; chroma_F: float; chroma_Fs: float; chroma_G: float
    chroma_Gs: float; chroma_A: float; chroma_As: float; chroma_B: float

# ------------------------------------------------------------------
# 4️⃣  Ingestion Actor – runs the vetted v11 pipeline
# ------------------------------------------------------------------
@ray.remote(num_cpus=2, num_gpus=0)  # CPU‑heavy, no GPU needed for DSP
class IngestionActor:
    def __init__(self,
                 t_memory_json: str,
                 duckdb_path: str,
                 lancedb_path: str):
        self.t_memory_json = t_memory_json
        self.duckdb_path = duckdb_path
        self.lancedb_path = lancedb_path
        self.duck_conn = duckdb.connect(duckdb_path)
        self.lance_tbl = get_or_create_lance_table(lancedb_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print("[IngestionActor] Ready.")

    def run(self) -> dict:
        """
        Executes the full v11 ingestion once.
        Returns a summary dict with counts.
        """
        start = time.perf_counter()
        # ---- 1️⃣ SIMD JSON → Polars -------------------------------------------------
        with open(self.t_memory_json, "rb") as f:
            raw_catalog = simdjson.load(f)
        df_catalog = pl.DataFrame(raw_catalog)
        print(f"[Ingestion] Loaded {df_catalog.shape[0]} tracks "
              f"in {(time.perf_counter()-start)*1000:.1f} ms")

        duck_payloads: list[dict] = []
        lance_payloads: list[dict] = []

        # ---- 2️⃣ Process each file -------------------------------------------------
        for row in df_catalog.iter_rows(named=True):
            fp = row["filepath"]
            if not os.path.exists(fp):
                continue
            try:
                # ---- C‑backed audio decode (soundfile) ------------------------------
                y, sr = sf.read(fp)
                if y.ndim > 1:
                    y = np.mean(y, axis=1)          # mono
                if sr != 16000:
                    y = librosa.resample(y, orig_sr=sr, target_sr=16000)
                y = y.astype(np.float32)           # [-1,1] float32

                # ---- Layer‑1: 46‑point acoustic physics ----------------------------
                rms = np.sqrt(np.mean(y**2))
                peak = np.max(np.abs(y))
                crest = float(peak / rms if rms > 0 else 0.0)

                y_harm, y_perc = librosa.effects.hpss(y)
                harm = float(np.sum(y_harm**2) / (np.sum(y**2) + 1e-8))
                perc = float(np.sum(y_perc**2) / (np.sum(y**2) + 1e-8))

                onset_env = librosa.onset.onset_strength(y=y, sr=16000)
                trans_den = float(len(librosa.onset.onset_detect(
                                    onset_envelope=onset_env, sr=16000))
                                  / (len(y) / 16000))

                S = np.abs(librosa.stft(y))
                freqs = librosa.fft_frequencies(sr=16000)
                sub_bass = np.where(freqs < 80)[0]
                bass = np.where((freqs >= 80) & (freqs < 300))[0]
                mid = np.where((freqs >= 300) & (freqs < 2000))[0]
                high = np.where(freqs >= 2000)[0]

                sub_bass_e = float(np.mean(S[sub_bass, :])) if sub_bass.size else 0.0
                bass_e     = float(np.mean(S[bass, :]))     if bass.size     else 0.0
                mid_e      = float(np.mean(S[mid, :]))      if mid.size      else 0.0
                high_e     = float(np.mean(S[high, :]))     if high.size     else 0.0

                spec_cent = float(librosa.feature.spectral_centroid(y=y, sr=16000).mean())
                spec_roll = float(librosa.feature.spectral_rolloff(y=y, sr=16000).mean())
                spec_bw   = float(librosa.feature.spectral_bandwidth(y=y, sr=16000).mean())
                spec_contr= float(librosa.feature.spectral_contrast(y=y, sr=16000).mean())
                zcr       = float(librosa.feature.zero_crossing_rate(y).mean())

                mfccs = librosa.feature.mfcc(y=y, sr=16000, n_mfcc=13).mean(axis=1)
                chroma= librosa.feature.chroma_stft(y=y, sr=16000).mean(axis=1)

                record = AlignedDSPTrackRecord(
                    filepath=fp,
                    filename=os.path.basename(fp),
                    asset_type="SAMPLE" if "Loop" in fp else "SONG",
                    drum_type="UNKNOWN",
                    tempo=float(row.get("bpm", 0.0)),
                    key=str(row.get("key_signature", "")),
                    rms_db=float(20 * np.log10(rms + 1e-8)),
                    crest_factor=crest,
                    sub_bass_energy=sub_bass_e,
                    bass_energy=bass_e,
                    mid_energy=mid_e,
                    high_energy=high_e,
                    spectral_centroid=spec_cent,
                    spectral_rolloff=spec_roll,
                    spectral_bandwidth=spec_bw,
                    spectral_contrast=spec_contr,
                    zcr=zcr,
                    onset_strength=float(onset_env.mean()),
                    transient_density=trans_den,
                    harmonic_ratio=harm,
                    percussive_ratio=perc,
                    mfcc_1=float(mfccs[0]), mfcc_2=float(mfccs[1]), mfcc_3=float(mfccs[2]),
                    mfcc_4=float(mfccs[3]), mfcc_5=float(mfccs[4]), mfcc_6=float(mfccs[5]),
                    mfcc_7=float(mfccs[6]), mfcc_8=float(mfccs[7]), mfcc_9=float(mfccs[8]),
                    mfcc_10=float(mfccs[9]), mfcc_11=float(mfccs[10]), mfcc_12=float(mfccs[11]),
                    mfcc_13=float(mfccs[12]),
                    chroma_C=float(chroma[0]), chroma_Cs=float(chroma[1]),
                    chroma_D=float(chroma[2]), chroma_Ds=float(chroma[3]),
                    chroma_E=float(chroma[4]), chroma_F=float(chroma[5]),
                    chroma_Fs=float(chroma[6]), chroma_G=float(chroma[7]),
                    chroma_Gs=float(chroma[8]), chroma_A=float(chroma[9]),
                    chroma_As=float(chroma[10]), chroma_B=float(chroma[11])
                )

                # ---- DuckDB payload (exactly 46 fields) ---------------------------
                duck_payloads.append(record.dict())

                # ---- LanceDB payload: 384‑D AST vector (placeholder) -------------
                # In a real swap you would load your frozen AST model here:
                #   ast_vec = ast_model(torch.from_numpy(y).unsqueeze(0).to(self.device))
                #   ast_vec = ast_vec.squeeze(0).detach().cpu().numpy()
                # For now we use a deterministic pseudo‑random vector derived from the waveform:
                rng = np.random.default_rng(seed=int(np.sum(y * 1000)) & 0xFFFFFFFF)
                ast_vec = rng.standard_normal(384).astype(np.float32)
                # Normalise to unit length (consistent with the notebook’s hypersphere idea)
                ast_vec /= (np.linalg.norm(ast_vec) + 1e-8)

                lance_payloads.append({
                    "filename": os.path.basename(fp),
                    "filepath": fp,
                    "vector": ast_vec.tolist()   # list of 384 float32
                })

            except Exception as exc:
                print(f"[Ingestion] ✗ {fp}: {exc}")

        # ---- 3️⃣ Flush to DuckDB ----------------------------------------------------
        if duck_payloads:
            pa_tbl = pa.Table.from_pylist(duck_payloads)
            self.duck_conn.execute("DROP TABLE IF EXISTS audio_features")
            self.duck_conn.execute("CREATE TABLE audio_features AS SELECT * FROM pa_tbl")
            print(f"[Ingestion] ✅ DuckDB: {len(duck_payloads)} rows written.")

        # ---- 4️⃣ Flush to LanceDB (zero‑copy safe) ---------------------------------
        if lance_payloads:
            # LanceDB expects Arrow record batches; we pass the list of dicts.
            self.lance_tbl.add(lance_payloads)
            print(f"[Ingestion] ✅ LanceDB: {len(lance_payloads)} vectors inserted.")
        else:
            print("[Ingestion] ⚠️ No Lance payloads to write.")

        elapsed = time.perf_counter() - start
        print(f"[Ingestion] Finished in {elapsed:.2f}s")
        return {
            "tracks_processed": df_catalog.shape[0],
            "duck_rows": len(duck_payloads),
            "lance_vectors": len(lance_payloads),
            "elapsed_sec": elapsed
        }

# ------------------------------------------------------------------
# 5️⃣  Diffusion Matrix Actor – a simple (but swappable) diffusion denoiser
# ------------------------------------------------------------------
# NOTE: Replace the dummy UNet with your actual checkpoint (e.g., a
# Stable Diffusion‑Audio UNet, AudioLDM, or any latent diffusion model).
# The actor keeps the model resident on GPU so we avoid reload stalls.
@ray.remote(num_gpus=1 if torch.cuda.is_available() else 0, num_cpus=1)
class DiffusionMatrixActor:
    def __init__(self,
                 checkpoint_path: Optional[str] = None,
                 device: Optional[torch.device] = None):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self._load_model(checkpoint_path)
        self.model.eval()
        self.model.to(self.device)
        print(f"[Diffusion] Model loaded on {self.device}")

    @staticmethod
    def _load_model(ckpt: Optional[str]):
        """
        Placeholder: replace with your actual diffusion UNet.
        For illustration we return a tiny convolutional net that
        mimics a diffusion denoiser on 384‑dim latents.
        """
        if ckpt and os.path.exists(ckpt):
            # Example: torch.load(ckpt, map_location="cpu")
            raise NotImplementedError("Insert your checkpoint loading here.")
        # Dummy network – in practice you would load a trained diffusion model.
        return torch.nn.Sequential(
            torch.nn.Linear(384, 1024),
            torch.nn.SiLU(),
            torch.nn.Linear(1024, 1024),
            torch.nn.SiLU(),
            torch.nn.Linear(1024, 384),
        )

    @torch.no_grad()
    def denoise(self, latent: np.ndarray, steps: int = 25) -> np.ndarray:
        """
        Very simple deterministic diffusion‑like iteration:
          x_t+1 = x_t - ε * ∇_x L(x_t)   (here we just apply the network as a denoiser)
        In a real system you would plug in a proper scheduler.
        Returns a denoised latent (np.ndarray, float32, shape=[384]).
        """
        x = torch.from_numpy(latent).to(self.device).float()
        eps = 0.1  # fixed step size for demo
        for _ in range(steps):
            pred = self.model(x)
            x = x - eps * (x - pred)   # simple gradient step toward model output
        return x.cpu().numpy().astype(np.float32)

# ------------------------------------------------------------------
# 6️⃣  Ray Serve deployment – the HTTP bridge for the front‑end
# ------------------------------------------------------------------
app = FastAPI()

@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 2, "num_gpus": 0})
@serve.ingress(app)
class APIIngress:
    def __init__(self,
                 ingestion_handle: ray.actor.ActorHandle,
                 diffusion_handle: ray.actor.ActorHandle):
        self.ingest = ingestion_handle
        self.diffuse = diffusion_handle

    @app.post("/generate")
    async def generate(self, file: UploadFile = File(...)):
        """
        Expects a raw .wav file (any samplerate, any channels).
        Returns a 16‑bit PCM wav of the denoised audio (for demo: just resynthesize noise).
        In a real pipeline you would:
          1. Run ingestion on the uploaded file to get its 384‑D latent.
          2. Pass that latent through the diffusion denoiser.
          3. Decode the latent to waveform with a vocoder (e.g., HiFi‑GAN).
        Here we skip steps 1 & 3 for brevity and just demonstrate the round‑trip.
        """
        # Save upload to a temp file
        tmp_path = f"/tmp/{file.filename}"
        with open(tmp_path, "wb") as f:
            f.write(await file.read())

        # Step 1: get latent via ingestion actor (runs the v11 pipeline on this single file)
        # We reuse the ingestion actor but ask it to process only this file.
        # For simplicity we call a helper method on the actor (you could expose a dedicated method).
        # Here we call the actor's internal method via ray.get.
        # NOTE: In production you would expose a dedicated `get_latent.remote(filepath)` method.
        latent_ref = self.ingest.get_latent.remote(tmp_path)  # we'll add this method below
        latent = ray.get(latent_ref)   # np.ndarray, shape (384,)

        # Step 2: diffuse/denoise
        denoised_latent = self.diffuse.denoise.remote(latent)
        denoised_latent = ray.get(denoised_latent)

        # Step 3: Dummy synth – convert latent to audio via inverse IDCT (just for demo)
        # Replace with your vocoder decoder in a real system.
        audio = np.fft.irfft(denoised_latent, n=2*len(denoised_latent))  # placeholder
        audio = np.clip(audio, -1.0, 1.0).astype(np.float32)

        # Write to wav bytes
        out_buf = io.BytesIO()
        sf.write(out_buf, audio, samplerate=16000, format='WAV', subtype='PCM_16')
        out_buf.seek(0)

        return StreamingResponse(out_buf,
                                 media_type="audio/wav",
                                 headers={"Content-Disposition": f'attachment; filename="denoised_{file.filename}"'})

# ------------------------------------------------------------------
# 7️⃣  Wire everything up and launch Serve
# ------------------------------------------------------------------
def main():
    # Paths – adjust to your actual layout
    T_MEMORY_JSON = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\abelton-session-intelligence\exported_json\t_core_memory.json"
    DUCKDB_PATH   = r"C:\STUDIES_BACKUP\data\metadata\sonic_core_v2.duckdb"
    LANCEDB_PATH  = r"C:\STUDIES_BACKUP\vectors\lancedb_store"

    # Start the ingestion actor (single instance; it holds DB connections)
    ingest_actor = IngestionActor.remote(T_MEMORY_JSON, DUCKDB_PATH, LANCEDB_PATH)

    # Optional: expose a method to get latent for a single file (used by the API)
    # We'll monkey‑patch the actor class to add this helper; in real code define it in the class.
    @ray.remote
    def _get_latent_helper(actor_ref, filepath):
        # Re‑run the per‑file logic from IngestionActor.run but just for one file
        # For brevity we reuse the same code; in production factor it out.
        y, sr = sf.read(filepath)
        if y.ndim > 1:
            y = np.mean(y, axis=1)
        if sr != 16000:
            y = librosa.resample(y, orig_sr=sr, target_sr=16000)
        y = y.astype(np.float32)

        # --- compute 384‑D AST placeholder (deterministic from waveform) ---
        rng = np.random.default_rng(seed=int(np.sum(y * 1000)) & 0xFFFFFFFF)
        vec = rng.standard_normal(384).astype(np.float32)
        vec /= (np.linalg.norm(vec) + 1e-8)
        return vec

    # Attach helper to the actor via a remote function bound to the actor
    def get_latent(filepath):
        return _get_latent_helper.remote(ingest_actor, filepath)

    # Attach as a method for convenience (not strictly necessary)
    ingest_actor.get_latent = get_latent

    # Start diffusion actor
    diffuse_actor = DiffusionMatrixActor.remote()

    # Start Ray Serve
    serve.start()
    serve.run(APIIngress.bind(ingest_actor, diffuse_actor), route_prefix="/")
    print("\n=== [Serve] Serve is ready ===")
    print("POST a wav file to:  http://127.0.0.1:8000/generate")
    print("Ray Dashboard:       http://<node-ip>:8265")
    print("Press Ctrl+C to stop.\n")

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        serve.shutdown()
        ray.shutdown()

if __name__ == "__main__":
    import io  # needed for the StreamingResponse above
    main()