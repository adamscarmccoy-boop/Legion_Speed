"""
test_weights_on_mastered.py
===========================
Feeds the V4 MASTERED audio back into the V3 model weights (`sonic_dna_master_v2.pt`).
If the model actually learned what a "mastered" track sounds like, it should
predict 0dB gain and 1.0 ratio because the track is already mastered. Let's see.
"""

import os
import numpy as np
import soundfile as sf
import torch
import torch.nn as nn

# ── Sonic DNA Master Model Definition (from v3) ────────────────────────────────
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
        ckpt = torch.load(model_path, weights_only=False)
        self.in_dim  = ckpt["in_dim"]
        self.out_dim = ckpt["out_dim"]
        self.dsp_cols = ckpt["dsp_cols"]
        self.X_mean  = torch.tensor(ckpt["X_mean"])
        self.X_std   = torch.tensor(ckpt["X_std"])
        self.Y_mean  = torch.tensor(ckpt["Y_mean"])
        self.Y_std   = torch.tensor(ckpt["Y_std"])
        self.model   = _MasteringNet(self.in_dim, self.out_dim)
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.model.eval()

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

# ── Feature Extractor ──────────────────────────────────────────────────────────
def extract_dsp_features(y, sr):
    y_mono = y.mean(axis=1) if y.ndim > 1 else y
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

# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    MODEL_PATH = r"C:\WEB CASE STUDY\sonic_dna_output\sonic_dna_master_v2.pt"
    TRACK_PATH = r"C:\Users\adams\Downloads\jumpy jumpy_SONIC_DNA_V4_MASTERED.wav"
    
    print("=" * 70)
    print("  FEEDING V4 MASTERED AUDIO INTO V3 MODEL WEIGHTS")
    print("=" * 70)
    
    model = SonicDNAMaster(MODEL_PATH)
    
    y, sr = sf.read(TRACK_PATH)
    
    # Let's test the first 3 sections (6 seconds each)
    segment_length = int(6.0 * sr)
    
    print(f"\n[>>] {os.path.basename(TRACK_PATH)}")
    for i in range(3):
        start = i * segment_length
        end   = start + segment_length
        chunk = y[start:end]
        
        feats = extract_dsp_features(chunk, sr)
        gain_db, ratio, threshold_db = model.predict(feats)
        
        print(f"     Section {i+1} [Mastered Audio]:")
        print(f"        Model Predicts: Gain={gain_db:+.1f}dB, Ratio={ratio:.2f}:1, Threshold={threshold_db:.1f}dB")
        
    print("\nIf the model understood mastering, it would predict Gain=0.0dB and Ratio=1.00:1 here.")
    print("=" * 70)
