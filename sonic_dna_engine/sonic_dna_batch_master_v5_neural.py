"""
sonic_dna_batch_master_v5_neural.py
===================================
Uses Continuous Parameter Automation (v4 logic)
BUT replaces the LanceDB + DSP Math with the properly trained
Sonic DNA Master Neural Network (v3 weights).
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import os, time, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import soundfile as sf
import torch
import torch.nn as nn
from pedalboard import Pedalboard, Compressor, HighpassFilter, Gain, Limiter

try:
    from marketing_scorer import MarketingScorer
    forest_engine = MarketingScorer()
    print("[OK] Forest Engine loaded")
except ImportError:
    forest_engine = None

# ── Config ─────────────────────────────────────────────────────────────────────
RUN_AS_BATCH_LIST = True
MY_TRACK_LIST = [
    r"C:\Users\adams\Downloads\admit it.mp3",
]
TARGET_LUFS        = -9.0
BLOCK_SIZE         = 1024
GLIDE_MS           = 150.0
HIGHPASS_HZ        = 30.0
SUB_BASS_MONO_HZ   = 150.0
LIMITER_CEILING_DB = -0.3
MODEL_PATH         = os.path.join(os.path.dirname(__file__), "sonic_dna_master_v3.pt")

# ── 1. Neural Network Definition ─────────────────────────────────────────────
class _MasteringNet(nn.Module):
    def __init__(self, in_dim, out_dim):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(in_dim, 128), nn.LayerNorm(128), nn.GELU(),
            nn.Linear(128, 64),    nn.LayerNorm(64),  nn.GELU(),
        )
        self.sonic_dna   = nn.Linear(64, 64)
        self.master_head = nn.Sequential(nn.Linear(64, 32), nn.GELU(), nn.Linear(32, out_dim))
    def forward(self, x):
        h = self.encoder(x)
        return self.master_head(h)

class SonicDNAMaster:
    def __init__(self, model_path):
        ckpt = torch.load(model_path, map_location="cpu", weights_only=False)
        self.dsp_cols = ckpt["dsp_cols"]
        self.X_mean  = torch.tensor(ckpt["X_mean"])
        self.X_std   = torch.tensor(ckpt["X_std"])
        self.Y_mean  = torch.tensor(ckpt["Y_mean"])
        self.Y_std   = torch.tensor(ckpt["Y_std"])
        self.model   = _MasteringNet(ckpt["in_dim"], ckpt["out_dim"])
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.model.eval()
        print(f"[OK] Neural Network Loaded: {model_path}")

    def predict(self, feat_dict: dict):
        vec = torch.tensor([float(feat_dict.get(c, 0.0)) for c in self.dsp_cols], dtype=torch.float32)
        vec_norm = (vec - self.X_mean) / self.X_std
        with torch.no_grad():
            raw = self.model(vec_norm.unsqueeze(0)).squeeze()
        out = raw * self.Y_std + self.Y_mean
        gain_db      = float(np.clip(out[0].item(), -12.0, 12.0))
        comp_ratio   = float(np.clip(out[1].item(), 1.0, 4.5))
        threshold_db = float(np.clip(out[2].item(), -80.0, 0.0))
        return gain_db, comp_ratio, threshold_db


# ── 2. Feature Extraction ────────────────────────────────────────────────────
def extract_dsp_features(y_mono: np.ndarray, sr: int):
    """Extracts DSP features matching the training data."""
    rms_val = float(np.sqrt(np.mean(y_mono**2)))
    rms_db  = float(20 * np.log10(max(rms_val, 1e-9)))
    peak    = float(np.max(np.abs(y_mono)) + 1e-9)
    crest   = float(peak / max(rms_val, 1e-9))

    N   = len(y_mono)
    fft = np.abs(np.fft.rfft(y_mono)) ** 2
    freqs = np.fft.rfftfreq(N, 1.0/sr)
    def band(lo, hi): return float(np.sum(fft[(freqs >= lo) & (freqs < hi)]))

    import librosa
    try:
        sc  = float(np.mean(librosa.feature.spectral_centroid(y=y_mono, sr=sr)))
        sbw = float(np.mean(librosa.feature.spectral_bandwidth(y=y_mono, sr=sr)))
        sr_ = float(np.mean(librosa.feature.spectral_rolloff(y=y_mono, sr=sr)))
        sct = float(np.mean(librosa.feature.spectral_contrast(y=y_mono, sr=sr)))
        zcr = float(np.mean(librosa.feature.zero_crossing_rate(y_mono)))
    except Exception:
        sc = sbw = sr_ = sct = zcr = 0.0

    return {
        "rms_db": rms_db, "crest_factor": crest,
        "sub_bass_energy": band(20, 80), "bass_energy": band(80, 300),
        "mid_energy": band(300, 3000), "high_energy": band(3000, 16000),
        "spectral_centroid": sc, "spectral_bandwidth": sbw,
        "spectral_rolloff": sr_, "spectral_contrast": sct,
        "zero_crossing_rate": zcr,
    }


def enforce_sub_bass_mono(audio_frame: np.ndarray, sr: int) -> np.ndarray:
    if audio_frame.ndim == 1 or audio_frame.shape[1] < 2:
        return audio_frame
    left, right = audio_frame[:, 0], audio_frame[:, 1]
    mid  = (left + right) / 2.0
    side = (left - right) / 2.0
    side = HighpassFilter(cutoff_frequency_hz=SUB_BASS_MONO_HZ)(side, sample_rate=sr)
    out = np.zeros_like(audio_frame)
    out[:, 0] = mid + side
    out[:, 1] = mid - side
    return out


# ── 3. Core Processing ───────────────────────────────────────────────────────
def process_track(input_path: str, model: SonicDNAMaster):
    base     = os.path.splitext(os.path.basename(input_path))[0]
    out_path = os.path.join(os.path.dirname(input_path),
                            base + "_SONIC_DNA_V5_NEURAL%date%.wav")

    if not os.path.exists(input_path):
        print(f"  [SKIP] Not found: {input_path}")
        return None

    print(f"\n[>>] {os.path.basename(input_path)}")

    y_full, sr_full = sf.read(input_path, always_2d=True)
    mastered = np.zeros_like(y_full)

    segment_sec = 6.0
    frames = int(segment_sec * sr_full)
    num_segments = int(np.ceil(y_full.shape[0] / frames))
    
    print(f"     Planning continuous mastering curves via Neural Network ({num_segments} sections)...")
    
    section_targets = []
    for i in range(num_segments):
        s = i * frames
        e = min(s + frames, y_full.shape[0])
        chunk = y_full[s:e]
        if chunk.shape[0] == 0:
            section_targets.append((0.0, 1.0, 0.0))
            continue
            
        mono_chunk = chunk.mean(axis=1) if chunk.ndim > 1 else chunk
        feats = extract_dsp_features(mono_chunk, sr_full)
        
        # Predict directly from Neural Network
        gain_db, ratio, thr = model.predict(feats)
        section_targets.append((gain_db, ratio, thr))
        
        if i < 5 or i == num_segments - 1:
            print(f"     seg{i:03d}  NN Predicts: gain={gain_db:+.1f}dB  ratio={ratio:.2f}:1  thr={thr:.1f}dB")

    # Build continuous arrays
    num_blocks = int(np.ceil(y_full.shape[0] / BLOCK_SIZE))
    param_gain = np.zeros(num_blocks)
    param_ratio = np.ones(num_blocks)
    param_thresh = np.zeros(num_blocks)
    
    for i in range(num_segments):
        b_start = int((i * frames) // BLOCK_SIZE)
        b_end   = int(((i + 1) * frames) // BLOCK_SIZE)
        b_end   = min(b_end, num_blocks)
        if b_end > b_start:
            param_gain[b_start:b_end] = section_targets[i][0]
            param_ratio[b_start:b_end] = section_targets[i][1]
            param_thresh[b_start:b_end] = section_targets[i][2]

    # Smooth the curves (Glide)
    blocks_per_glide = max(1, int((GLIDE_MS / 1000.0 * sr_full) / BLOCK_SIZE))
    window = np.ones(blocks_per_glide) / blocks_per_glide
    param_gain = np.convolve(param_gain, window, mode='same')
    param_ratio = np.clip(np.convolve(param_ratio, window, mode='same'), 1.0, 100.0)
    param_thresh = np.convolve(param_thresh, window, mode='same')

    # Continuous Automation processing
    print(f"     Processing continuous stream ({num_blocks} micro-blocks)...")
    global_board = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=HIGHPASS_HZ),
        Gain(gain_db=0.0),
        Compressor(threshold_db=0.0, ratio=1.0, attack_ms=10.0, release_ms=100.0),
        Limiter(threshold_db=LIMITER_CEILING_DB, release_ms=100.0),
    ])
    
    for b in range(num_blocks):
        s = b * BLOCK_SIZE
        e = min(s + BLOCK_SIZE, y_full.shape[0])
        chunk = y_full[s:e]
        
        global_board[1].gain_db      = float(param_gain[b])
        global_board[2].ratio        = float(param_ratio[b])
        global_board[2].threshold_db = float(param_thresh[b])
        
        chunk = enforce_sub_bass_mono(chunk, sr_full)
        mastered[s:e] = global_board(chunk, sample_rate=sr_full, reset=False)

    # LUFS pass
    try:
        import pyloudnorm as pyln
        meter = pyln.Meter(sr_full)
        lufs  = meter.integrated_loudness(mastered)
        if lufs > -70.0 and not np.isinf(lufs):
            delta  = float(np.clip(TARGET_LUFS - lufs, -6.0, 12.0))
            makeup = 10 ** (delta / 20.0)
            mastered = np.clip(mastered * makeup, -0.98, 0.98)
            print(f"     LUFS: {lufs:.1f} -> {TARGET_LUFS:.1f} LUFS  (makeup {delta:+.1f}dB)")
    except Exception as ex:
        pass

    sf.write(out_path, mastered, sr_full)
    print(f"     [OK] -> {os.path.basename(out_path)}")
    return out_path


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 70)
    print("  SONIC DNA BATCH MASTER v5 (NEURAL)")
    print("  Continuous Parameter Automation via Sonic DNA Master v3 Weights")
    print("=" * 70)

    model = SonicDNAMaster(MODEL_PATH)
    
    t0 = time.time()
    for track_path in MY_TRACK_LIST:
        try:
            process_track(track_path, model)
        except Exception as ex:
            import traceback
            print(f"  [ERR] {os.path.basename(track_path)}: {ex}")
            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"  DONE in {time.time()-t0:.1f}s")
    print("=" * 70)
