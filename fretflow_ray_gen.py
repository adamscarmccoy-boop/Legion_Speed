import ray
import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import lancedb
import soundfile as sf
import os
import datetime
import re
from scipy.spatial.distance import cdist
import warnings

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


warnings.filterwarnings('ignore')

# --- CONFIGURATION ---
WEIGHTS_PATH = r"C:\WEB CASE STUDY\sonic_dna_output\fretflow_omni_v3.pt"
SAMPLES_JSON = r"C:\WEB CASE STUDY\data\enriched_samples_only.json"
LANCEDB_PATH = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\vectors\lancedb_store"
OUTPUT_DIR = r"C:\WEB CASE STUDY\generated_audio_ray"

# Audio Constants
SR = 44100

# ---------------------------------------------------------------------------
# 1. The Model Architecture (FretFlow Engine)
# ---------------------------------------------------------------------------
class FretFlowEngine(nn.Module):
    def __init__(self, in_dim, latent_dim):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(in_dim, 256), nn.LayerNorm(256), nn.GELU(),
            nn.Linear(256, 128), nn.LayerNorm(128), nn.GELU(),
            nn.Linear(128, latent_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 128), nn.GELU(),
            nn.Linear(128, 256), nn.GELU(),
            nn.Linear(256, in_dim)
        )
    def forward(self, x):
        return self.decoder(self.encoder(x))

# ---------------------------------------------------------------------------
# 2. Ray Actor for High-Speed Search & Assembly
# ---------------------------------------------------------------------------
@ray.remote
class GenerationWorker:
    def __init__(self, weights_path, samples_df, ldb_table):
        self.checkpoint = torch.load(weights_path, map_location="cpu")
        self.X_mean = np.array(self.checkpoint['X_mean'], dtype=np.float32)
        self.X_std = np.array(self.checkpoint['X_std'], dtype=np.float32)
        
        self.model = FretFlowEngine(self.checkpoint['in_dim'], self.checkpoint['latent_dim'])
        self.model.load_state_dict(self.checkpoint['model_state_dict'])
        self.model.eval()
        
        self.df = samples_df
        self.ldb_table = ldb_table
        
        # Pre-calculate matrices for fast cosine search
        self.df['omni_vector'] = self.df.apply(self._build_omni_vector, axis=1)
        self.all_vecs = np.vstack(self.df['omni_vector'].values)
        self.all_vecs = np.nan_to_num(self.all_vecs, nan=0.0)

    def _build_omni_vector(self, row):
        sem = np.array(row['vector'], dtype=np.float32)
        bpm = np.array([float(row.get('tempo', 128.0))], dtype=np.float32)
        return np.concatenate([sem, bpm])

    def hallucinate_dna(self, seed_vec_raw, variance=1.2):
        seed_vec_norm = (seed_vec_raw - self.X_mean) / (self.X_std + 1e-8)
        seed_tensor = torch.tensor(seed_vec_norm, dtype=torch.float32).unsqueeze(0)
        
        with torch.no_grad():
            latent = self.model.encoder(seed_tensor)
            latent = latent + torch.randn_like(latent) * variance
            output_tensor_norm = self.model.decoder(latent).numpy()[0]
            
        omni_output_raw = (output_tensor_norm * self.X_std) + self.X_mean
        return omni_output_raw

    def find_best_match(self, target_vec, pool_filter=None):
        # Filter pool if provided (e.g., 'BASS')
        if pool_filter:
            mask = self.df['genre_class'].str.contains(pool_filter, na=False, case=False) | \
                   self.df['filename'].str.contains(pool_filter, na=False, case=False)
            pool_df = self.df[mask]
            if len(pool_df) == 0: pool_df = self.df
            pool_mat = np.vstack(pool_df['omni_vector'].values)
        else:
            pool_df = self.df
            pool_mat = self.all_vecs
            
        pool_mat = np.nan_to_num(pool_mat, nan=0.0)
        dists = cdist([target_vec], pool_mat, metric="cosine")[0]
        
        # Top-K Softmax Sampling
        k = 5
        top_k_indices = np.argsort(dists)[:k]
        logits = -dists[top_k_indices] / 0.5 # temp = 0.5
        probs = np.exp(logits - np.max(logits))
        probs /= np.sum(probs)
        
        selected_idx = np.random.choice(top_k_indices, p=probs)
        return pool_df.iloc[selected_idx]

    def assemble_audio(self, target_bpm, kick_path, bass_path, perc_path, filename):
        # --- PRO ASSEMBLY LOGIC ---
        SR = 44100
        BPM = target_bpm if 60 < target_bpm < 200 else 128.0
        TOTAL_SAMPLES = int(16 * 4 * (60.0 / BPM) * SR)
        mix = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

        def load_and_stretch(path, target_len=None):
            if not path or not os.path.exists(path): return np.zeros((0, 2))
            try:
                y, sr = sf.read(path, always_2d=True)
                # Simple Linear Resampling for Time-Stretch
                if target_len and len(y) != target_len:
                    # Use numpy interp for fast stretching
                    idx = np.linspace(0, len(y)-1, target_len)
                    y = np.stack([np.interp(idx, np.arange(len(y)), y[i]) for i in range(2)], axis=1)
                return y
            except: return np.zeros((0, 2))

        # 1. Process Stems
        y_kick = load_and_stretch(kick_path)
        # Stretch bass/perc to fit exactly 4 bars (16 beats)
        four_bar_len = int(4 * 4 * (60.0 / BPM) * SR)
        y_bass = load_and_stretch(bass_path, target_len=four_bar_len)
        y_perc = load_and_stretch(perc_path, target_len=four_bar_len)

        # 2. Sequencer: Grid-based Triggering
        beat_samples = int((60.0 / BPM) * SR)
        
        # Mix Gain Staging
        G_KICK, G_BASS, G_PERC = 1.0, 0.6, 0.4

        # Place Kicks (Every beat)
        for beat in range(16 * 4):
            pos = beat * beat_samples
            length = min(len(y_kick), TOTAL_SAMPLES - pos)
            if length > 0:
                # Basic Sidechain: Duck the mix slightly when kick hits
                # (We do this during summation)
                mix[pos:pos+length] += y_kick[:length] * G_KICK

        # Loop Bass and Perc
        def tile_loop(loop_arr, total_len):
            out = np.zeros((total_len, 2), dtype=np.float32)
            ll = len(loop_arr)
            if ll == 0: return out
            p = 0
            while p < total_len:
                c = min(ll, total_len - p)
                out[p:p+c] = loop_arr[:c]
                p += ll
            return out

        # Add Bass with Sidechain Ducking
        bass_layer = tile_loop(y_bass, TOTAL_SAMPLES) * G_BASS
        for beat in range(16 * 4):
            pos = beat * beat_samples
            duck_len = int(0.1 * SR) # 100ms duck
            end = min(pos + duck_len, TOTAL_SAMPLES)
            # Linear ramp up from 0.2 to 1.0
            ramp = np.linspace(0.2, 1.0, end - pos)
            bass_layer[pos:end, 0] *= ramp
            bass_layer[pos:end, 1] *= ramp

        mix += bass_layer
        mix += tile_loop(y_perc, TOTAL_SAMPLES) * G_PERC

        # Final Clip and Export
        out_path = os.path.join(OUTPUT_DIR, f"RAY_GEN_{filename}_{datetime.datetime.now().strftime('%H%M%S')}.wav")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        sf.write(out_path, np.clip(mix, -1.0, 1.0), SR)
        return out_path

# ---------------------------------------------------------------------------
# 3. Execution Orchestrator
# ---------------------------------------------------------------------------
def main():
    print("[BOOT] Initializing Ray-Powered FretFlow Generation...")
    ray.init(ignore_reinit_error=True)
    
    # Load Data
    samples_df = pd.read_json(SAMPLES_JSON)
    ldb = lancedb.connect(LANCEDB_PATH)
    ldb_table = ldb.open_table("audio_vibe_gpu")
    
    # Initialize Worker
    worker = GenerationWorker.remote(WEIGHTS_PATH, samples_df, ldb_table)
    
    # Pick Seeds
    seeds = samples_df.sample(3)
    
    for idx, row in seeds.iterrows():
        print(f"\n[GEN] Processing Seed: {row['filename']}")
        
        # 1. Hallucinate DNA (via Ray)
        seed_vec = np.array(row['vector'], dtype=np.float32)
        # Add BPM to seed vector for the model
        seed_vec_omni = np.concatenate([seed_vec, [float(row.get('tempo', 128.0))]])
        
        dna = ray.get(worker.hallucinate_dna.remote(seed_vec_omni))
        
        # 2. Extract DNA Components
        semantic_slice = dna[:384]
        target_bpm = dna[384]
        print(f"  -> Hallucinated BPM: {target_bpm:.2f}")
        
        # 3. Search for best matches (via Ray)
        best_bass = ray.get(worker.find_best_match.remote(semantic_slice, "BASS"))
        best_kick = ray.get(worker.find_best_match.remote(semantic_slice, "KICK"))
        best_perc = ray.get(worker.find_best_match.remote(semantic_slice, "PERC"))
        
        bass_fp = best_bass.get('filepath', '')
        kick_fp = best_kick.get('filepath', '')
        perc_fp = best_perc.get('filepath', '')
        
        print(f"  [MATCH] Kick: {os.path.basename(kick_fp)} | Bass: {os.path.basename(bass_fp)} | Perc: {os.path.basename(perc_fp)}")
        
        # 4. Pro Assembly (via Ray)
        out_file = ray.get(worker.assemble_audio.remote(
            target_bpm, kick_fp, bass_fp, perc_fp, os.path.basename(row['filename'])
        ))
        print(f"  [SUCCESS] Rendered: {out_file}")

    ray.shutdown()

if __name__ == "__main__":
    main()