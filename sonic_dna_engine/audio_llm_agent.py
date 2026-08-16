"""
audio_llm_agent.py
==================
The Autonomous AI Arranger Pipeline.
Uses the Audio LLM to hallucinate vectors, DuckDB RAG to fetch loops,
assembles a 128 BPM track, and passes it to the V5 Mastering Engine.
"""
import os, sys
import torch
import torch.nn as nn
import numpy as np
import duckdb
import soundfile as sf
import warnings
warnings.filterwarnings("ignore")

# Import our V5 Mastering Engine
sys.path.append(r"C:\WEB CASE STUDY\sonic_dna_engine")
try:
    from sonic_dna_batch_master_v5_neural import SonicDNAMaster, process_track
except ImportError:
    print("[ERR] Could not import v5 mastering engine.")
    sys.exit(1)

print("=" * 70)
print("  AUDIO LLM: GENERATIVE ARRANGER AGENT")
print("=" * 70)

# ── 1. Load the Audio LLM (Foundation Model) ─────────────────────────────────
LLM_PATH = r"C:\WEB CASE STUDY\sonic_dna_engine\audio_llm_v1.pt"
ckpt = torch.load(LLM_PATH, map_location="cpu", weights_only=False)
DSP_COLS = ckpt["dsp_cols"]
IN_DIM = ckpt["in_dim"]

class AudioLLM(nn.Module):
    def __init__(self, in_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 64), nn.LayerNorm(64), nn.GELU(),
            nn.Linear(64, 64),    nn.LayerNorm(64),  nn.GELU(),
            nn.Linear(64, in_dim)
        )
    def forward(self, x):
        return self.net(x)

audio_llm = AudioLLM(IN_DIM)
audio_llm.load_state_dict(ckpt["model_state_dict"])
audio_llm.eval()
print(f"[OK] Audio LLM Loaded.")

# ── 2. Database RAG (Loop Selection) ─────────────────────────────────────────
print("\n[PHASE 1] Connecting to DuckDB for loop selection...")
conn = duckdb.connect(r"C:\WEB CASE STUDY\web_intel_sonicdb.duckdb", read_only=True)

# Select a random KICK
df_kick = conn.execute("SELECT * FROM audio_features WHERE asset_type='SAMPLE' AND drum_type='KICK' ORDER BY random() LIMIT 1").fetchdf()
if len(df_kick) == 0:
    raise RuntimeError("No kicks found in DB.")
if "zcr" in df_kick.columns and "zero_crossing_rate" not in df_kick.columns:
    df_kick = df_kick.rename(columns={"zcr": "zero_crossing_rate"})

kick_path = df_kick["filepath"].iloc[0]
kick_vec = torch.tensor(df_kick[DSP_COLS].values[0].astype(np.float32)).unsqueeze(0)
print(f"  [AGENT] Selected Kick: {os.path.basename(kick_path)}")

# Hallucinate the perfect Bass
with torch.no_grad():
    hallucinated_bass_vec = audio_llm(kick_vec).numpy()[0]
print(f"  [AGENT] Hallucinated ideal bass vector mathematically.")

# Retrieve the closest actual Bass loop from DuckDB
df_basses = conn.execute("SELECT * FROM audio_features WHERE asset_type='SAMPLE' AND drum_type='BASS'").fetchdf()
if "zcr" in df_basses.columns and "zero_crossing_rate" not in df_basses.columns:
    df_basses = df_basses.rename(columns={"zcr": "zero_crossing_rate"})
bass_matrix = df_basses[DSP_COLS].values.astype(np.float32)

from scipy.spatial.distance import cdist
dists = cdist([hallucinated_bass_vec], bass_matrix, metric="euclidean")[0]
best_bass_idx = np.argmin(dists)
bass_path = df_basses["filepath"].iloc[best_bass_idx]
print(f"  [AGENT] Retrieved Bass: {os.path.basename(bass_path)} (Dist: {dists[best_bass_idx]:.2f})")

# Select a random PERC/LOOP (since model only maps kick->bass in v1 POC)
df_perc = conn.execute("SELECT filepath FROM audio_features WHERE asset_type='SAMPLE' AND drum_type IN ('PERC', 'LOOP', 'HAT') ORDER BY random() LIMIT 1").fetchdf()
perc_path = df_perc["filepath"].iloc[0]
print(f"  [AGENT] Selected Percussion: {os.path.basename(perc_path)}")
conn.close()

# ── 3. Audio Assembly ────────────────────────────────────────────────────────
print("\n[PHASE 2] Assembling the multitrack (128 BPM, 4 Bars)...")
SR = 44100
BPM = 128.0
BARS = 4
BEATS_PER_BAR = 4
TOTAL_BEATS = BARS * BEATS_PER_BAR
SECONDS_PER_BEAT = 60.0 / BPM
TOTAL_SAMPLES = int(TOTAL_BEATS * SECONDS_PER_BEAT * SR)

mix = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

def load_audio(path):
    y, sr = sf.read(path, always_2d=True)
    if sr != SR:
        # Simplistic resample by skipping/duplicating if needed, but assuming 44.1k for splice
        pass 
    return y

try:
    y_kick = load_audio(kick_path)
    y_bass = load_audio(bass_path)
    y_perc = load_audio(perc_path)
except Exception as e:
    print(f"[ERR] Loading audio failed: {e}")
    sys.exit(1)

# Sequence Kick on Quarter Notes
beat_samples = int(SECONDS_PER_BEAT * SR)
for beat in range(TOTAL_BEATS):
    pos = beat * beat_samples
    length = min(len(y_kick), TOTAL_SAMPLES - pos)
    mix[pos:pos+length] += y_kick[:length]

# Tile Bass and Percussion
def tile_loop(loop_arr, total_len):
    out = np.zeros((total_len, 2), dtype=np.float32)
    loop_len = len(loop_arr)
    pos = 0
    while pos < total_len:
        chunk = min(loop_len, total_len - pos)
        out[pos:pos+chunk] = loop_arr[:chunk]
        pos += chunk
    return out

mix += tile_loop(y_bass, TOTAL_SAMPLES)
mix += tile_loop(y_perc, TOTAL_SAMPLES)

# Soft clip to prevent blowing out before mastering
mix = np.clip(mix, -1.0, 1.0)

out_raw = r"C:\WEB CASE STUDY\sonic_dna_engine\generated_track_raw.wav"
sf.write(out_raw, mix, SR)
print(f"  [OK] Raw assembly saved to {out_raw}")

# ── 4. V5 Mastering ──────────────────────────────────────────────────────────
print("\n[PHASE 3] Passing assembled track to Sonic DNA V5 Neural Master...")
MASTER_WEIGHTS = r"C:\WEB CASE STUDY\sonic_dna_engine\sonic_dna_master_v3.pt"
master_model = SonicDNAMaster(MASTER_WEIGHTS)
try:
    process_track(out_raw, master_model)
    print("\n[SUCCESS] Track Arranged and Mastered successfully!")
except Exception as e:
    print(f"[ERR] Mastering failed: {e}")
