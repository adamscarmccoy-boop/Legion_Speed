
# ============================================================
# SOVEREIGN CONDUCTOR v4 — True Stereo & Pure Inference
# ============================================================
# Core philosophy:
# 1. Preserve the full stereo image. 
# 2. DO NOT use math loops to force the output. 
# 3. Trust the OmniCondVAE Brain. It figures it all out together.
# ============================================================
import os, sys, ray, torch
import numpy as np, librosa
import onnxruntime as ort
import soundfile as sf
import lancedb
from scipy.spatial.distance import cdist

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


try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

TRACKS = [
    r"C:\Users\adams\Downloads\feed this desire.wav",
    r"C:\Users\adams\Downloads\jumpy jumpy.wav",
    r"C:\Users\adams\Downloads\admit it.mp3",
    r"C:\Users\adams\Downloads\VIZON & Ren Carter - Had To Go [Extended Mix].mp3",
]
ONNX_BRAIN   = r"C:\WEB CASE STUDY\sonic_dna_output\fretflow_omni_v3.onnx"
PT_PATH      = r"C:\WEB CASE STUDY\sonic_dna_output\fretflow_omni_v3.pt"
LANCEDB_PATH = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
EXPORT_DIR   = r"C:\WEB CASE STUDY\mastered_output"
os.makedirs(EXPORT_DIR, exist_ok=True)

# ── 1. Connect Ray ──────────────────────────────────────────
ray.init(namespace="legion", ignore_reinit_error=True)
try:
    genome_actor = ray.get_actor("GenomeBrain", namespace="legion")
    print("Connected: GenomeBrain")
except ValueError:
    genome_actor = None
    print("GenomeBrain not found")

# ── 2. Load ONNX brain + checkpoint stats ──────────────────
brain         = ort.InferenceSession(ONNX_BRAIN)
ckpt          = torch.load(PT_PATH, map_location="cpu")
X_mean_ckpt   = np.array(ckpt["X_mean"], dtype=np.float32)
X_std_ckpt    = np.array(ckpt["X_std"],  dtype=np.float32)
genre2idx_ckpt= ckpt["genre2idx"]
TECH_IDX      = int(genre2idx_ckpt.get("TECH_HOUSE", 4))
print(f"Brain ready | TECH_HOUSE={TECH_IDX} | omni_dim={ckpt['omni_dim']}")

# ── 3. Load LanceDB semantic baseline ────────────────────────
print("Loading omni_semantic_baselines...")
ldb    = lancedb.connect(LANCEDB_PATH)
bl_df  = ldb.open_table("omni_semantic_baselines").to_pandas()

if "rms" in bl_df.columns and "rms_db" not in bl_df.columns:
    bl_df["rms_db_ref"] = bl_df["rms"].apply(
        lambda v: float(20*np.log10(max(float(v), 1e-9))) if v else -60.0)
    ref_col = "rms_db_ref"
else:
    ref_col = "rms_db"

REF_COLS      = [ref_col, "crest_factor", "sub_bass_energy",
                 "bass_energy", "mid_energy", "high_energy"]
for c in REF_COLS:
    if c not in bl_df.columns: bl_df[c] = 0.0

bl_dsp_matrix = bl_df[REF_COLS].fillna(0).values.astype(np.float32)
bl_vectors    = np.array(bl_df["vector"].tolist(), dtype=np.float32)
print(f"Baseline: {len(bl_df)} rows | vec_dim={bl_vectors.shape[1]}")

# ── 4. True Stereo Extraction ────────────────────────────────
def extract_dsp_mono(y_stereo: np.ndarray, sr: int) -> dict:
    """Extracts DSP from a mono downmix, keeping original stereo intact."""
    if y_stereo.ndim > 1 and y_stereo.shape[0] > 1:
        y_mono = librosa.to_mono(y_stereo)
    else:
        y_mono = y_stereo.flatten()
        
    rms   = float(librosa.feature.rms(y=y_mono).mean())
    rms_db= float(20*np.log10(rms+1e-12))
    crest = float(np.max(np.abs(y_mono))/(rms+1e-8))
    S     = np.abs(librosa.stft(y_mono, n_fft=2048))**2
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    
    def band(lo, hi): return float(S[(freqs>=lo)&(freqs<hi)].sum())
    sub, bass = band(20,60),  band(60,250)
    mid, high = band(250,4000), band(4000,20000)
    
    return dict(
        rms_db=rms_db, crest_factor=crest,
        sub_bass_energy=sub, bass_energy=bass,
        mid_energy=mid, high_energy=high,
        mid_multiplier=mid/(sub+1e-8),
        spectral_centroid  =float(librosa.feature.spectral_centroid(y=y_mono, sr=sr).mean()),
        spectral_bandwidth =float(librosa.feature.spectral_bandwidth(y=y_mono, sr=sr).mean()),
        spectral_rolloff   =float(librosa.feature.spectral_rolloff(y=y_mono, sr=sr).mean()),
        spectral_contrast  =float(librosa.feature.spectral_contrast(y=y_mono, sr=sr).mean()),
        zero_crossing_rate =float(librosa.feature.zero_crossing_rate(y_mono).mean()),
    )

def get_semantic_embedding(dsp: dict) -> tuple:
    query = np.array([[dsp["rms_db"], dsp["crest_factor"],
                       dsp["sub_bass_energy"], dsp["bass_energy"],
                       dsp["mid_energy"], dsp["high_energy"]]], dtype=np.float32)
    dists = cdist(query, bl_dsp_matrix, metric="euclidean")[0]
    top5  = np.argsort(dists)[:5]
    sem   = bl_vectors[top5].mean(axis=0).astype(np.float32)
    name  = bl_df.iloc[top5[0]].get("track_name", "unknown")
    return sem, name

# ── 5. The Brain (Pure Inference) ───────────────────────────
def run_brain(dsp: dict, sem: np.ndarray) -> dict:
    dsp_vec = np.array([
        dsp["rms_db"], dsp["crest_factor"],
        dsp["sub_bass_energy"], dsp["bass_energy"],
        dsp["mid_energy"], dsp["high_energy"],
        dsp["spectral_centroid"], dsp["spectral_bandwidth"],
        dsp["spectral_rolloff"], dsp["spectral_contrast"],
        dsp["zero_crossing_rate"],
    ], dtype=np.float32)
    
    raw  = np.concatenate([sem, dsp_vec, [128.0]]).astype(np.float32)
    norm = ((raw - X_mean_ckpt) / X_std_ckpt).reshape(1, -1)
    
    g = np.array([TECH_IDX], dtype=np.int64)
    b = norm[0, -1:].reshape(1).astype(np.float32)
    
    out = brain.run(
        [brain.get_outputs()[0].name],
        {"omni_input": norm, "genre_input": g, "bpm_input": b}
    )[0][0]
    
    return dict(
        gain_db     = float(out[0]),
        ratio       = float(np.clip(abs(out[1]), 1.0, 20.0)),
        threshold_db= float(min(out[2], 0.0)),
    ), norm, g, b


def measure_stereo_rms(y_stereo: np.ndarray) -> float:
    # Use downmix for reporting only
    y_mono = librosa.to_mono(y_stereo) if y_stereo.ndim > 1 else y_stereo.flatten()
    rms = float(np.sqrt(np.mean(y_mono**2)))
    return float(20*np.log10(rms+1e-12))

# ── 7. MAIN ──────────────────────────────────────────────────
print("\n" + "="*64)
print("  SOVEREIGN CONDUCTOR v4 (True Stereo + Pure Inference)")
print("  Strategy: The Brain figures it all out together.")
print("  NO Math Loops. NO Forcing. True Stereo Output.")
print("="*64)

session_log = []

for tp in TRACKS:
    if not os.path.exists(tp):
        print(f"\nSkipping: {tp}")
        continue

    name = os.path.basename(tp)
    print(f"\n  TRACK: {name}")

    # Load as stereo: shape becomes (2, N)
    y_stereo, sr = librosa.load(tp, mono=False, sr=None)
    
    # Extract baseline
    dsp = extract_dsp_mono(y_stereo, sr)
    print(f"  Initial: rms={dsp['rms_db']:.2f}dB  crest={dsp['crest_factor']:.3f}  midx={dsp['mid_multiplier']:.2f}")

    # 1. Get embedding
    sem, nn_name = get_semantic_embedding(dsp)
    print(f"  Semantic context: '{nn_name}'")

    # 2. Run Brain (Extract vectors + predictions)
    cmds, norm_in, g_in, b_in = run_brain(dsp, sem)
    print(f"  Brain Output: gain={cmds['gain_db']:.2f}dB  ratio={cmds['ratio']:.2f}  thresh={cmds['threshold_db']:.2f}dB")

    # 3. Just output the suggestions! We DO NOT apply math to the stereo waveform.
    # The parameters will go "around the hole" and be applied downstream.
    
    session_log.append(dict(
        track     = name,
        init_rms  = round(dsp["rms_db"], 2),
        brain_gain= round(cmds["gain_db"], 2),
        brain_ratio= round(cmds["ratio"], 2),
        brain_thresh= round(cmds["threshold_db"], 2),
        norm_in   = norm_in,
        g_in      = g_in,
        b_in      = b_in
    ))
    print("  RESULT: Math bypassed. Target parameters logged.")

print("\n" + "="*64)
print("  SESSION REPORT")
print("="*64)
for e in session_log:
    print(f"  {e['track']:<45} {e['init_rms']:>8.2f}dB -> [AI Suggestion] Gain: {e['brain_gain']:+.2f}dB | Ratio: {e['brain_ratio']:.2f} | Thresh: {e['brain_thresh']:.2f}dB")
print("="*64)

# ── 8. NEW CELL: TRAIN WEIGHTS & EXPORT TO ONNX ──────────────────────────
print("\n" + "="*64)
print("  TRAINING NEW SOVEREIGN WEIGHTS (ONNX EXPORT)")
print("="*64)

import torch
import torch.nn as nn
import torch.optim as optim

class SovereignFinetuneNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(1036, 128)
        self.fc2 = nn.Linear(128, 3)
    def forward(self, omni_input, genre_input, bpm_input):
        # We ignore genre/bpm for this focused overfit to achieve mathematically perfect targets
        x = torch.relu(self.fc1(omni_input))
        return self.fc2(x)

# 1. Prepare Real Training Data
X_omni_list = []
X_genre_list = []
X_bpm_list = []
Y_targets = []

TARGET_RMS = -13.9

for e in session_log:
    # We define the mathematically perfect target commands
    target_gain = TARGET_RMS - e["init_rms"]
    target_ratio = 2.0
    target_thresh = TARGET_RMS
    
    Y_targets.append([target_gain, target_ratio, target_thresh])
    X_omni_list.append(e["norm_in"][0])
    X_genre_list.append(e["g_in"][0])
    X_bpm_list.append(e["b_in"][0])

t_omni = torch.tensor(np.array(X_omni_list), dtype=torch.float32)
t_genre = torch.tensor(np.array(X_genre_list), dtype=torch.long)
t_bpm = torch.tensor(np.array(X_bpm_list), dtype=torch.float32)
t_targets = torch.tensor(np.array(Y_targets), dtype=torch.float32)

# 2. Train the Model
model = SovereignFinetuneNet()
opt = optim.Adam(model.parameters(), lr=0.01)
loss_fn = nn.MSELoss()

model.train()
print("Training on real DSP to hit -13.9dB Sovereign Truth...")
for ep in range(150):
    opt.zero_grad()
    pred = model(t_omni, t_genre, t_bpm)
    loss = loss_fn(pred, t_targets)
    loss.backward()
    opt.step()

print(f"✅ Training Complete. Final MSE Loss: {loss.item():.6f}")

# 3. Export to ONNX
model.eval()
ONNX_OUT = os.path.join(EXPORT_DIR, "sovereign_master_v5.onnx")

dummy_omni = torch.randn(1, 1036)
dummy_genre = torch.tensor([4], dtype=torch.long)
dummy_bpm = torch.tensor([[128.0]], dtype=torch.float32)

torch.onnx.export(
    model,
    (dummy_omni, dummy_genre, dummy_bpm),
    ONNX_OUT,
    input_names=["omni_input", "genre_input", "bpm_input"],
    output_names=["mastering_command_set"],
    dynamic_axes={"omni_input": {0: "batch"}},
    opset_version=14
)

print(f"🚀 ONNX EXPORT SUCCESSFUL: {ONNX_OUT}")
print("Ready for Ableton C++/Rust ORT Callback!")