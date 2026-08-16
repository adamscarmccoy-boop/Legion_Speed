# -*- coding: utf-8 -*-
"""Quick DNA comparison: Original SOV vs ONNX2 remastered"""
import sys, os, json
import numpy as np
import librosa
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

SOV_DIR  = Path(r"C:\WEB CASE STUDY\python_masters")
ONNX_DIR = Path(r"C:\WEB CASE STUDY\sovereign_onnx_masters_v2")

PICKS = [
    "SOV_admit it.wav",
    "SOV_jumpy jumpy.wav",
    "SOV_Sovereign Anchor V3.wav",
    "SOV_come n get it.wav",
    "SOV_La Di Da Dancin 4444.wav",
]

def analyze(path):
    y, sr = librosa.load(str(path), sr=None, mono=False)
    if y.ndim == 1: y = y[np.newaxis, :]
    mono = librosa.to_mono(y) if y.shape[0] >= 2 else y[0]
    
    rms = float(np.sqrt(np.mean(mono ** 2)))
    peak = float(np.max(np.abs(mono)))
    crest = peak / (rms + 1e-9)
    rms_db = 20 * np.log10(rms + 1e-9)
    peak_db = 20 * np.log10(peak + 1e-9)
    
    S = np.abs(librosa.stft(mono, n_fft=2048, hop_length=512))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    
    def band_e(lo, hi):
        m = (freqs >= lo) & (freqs < hi)
        return float(np.mean(S[m, :] ** 2)) if m.any() else 0.0
    
    centroid = float(np.mean(librosa.feature.spectral_centroid(S=S, freq=freqs)))
    
    # Stereo width (correlation between L and R above 150Hz)
    stereo_width = 0.0
    if y.shape[0] >= 2:
        from scipy.signal import butter, sosfilt
        sos = butter(4, 150, btype='high', fs=sr, output='sos')
        hi_L = sosfilt(sos, y[0])
        hi_R = sosfilt(sos, y[1])
        corr = np.corrcoef(hi_L, hi_R)[0, 1]
        stereo_width = 1.0 - corr  # 0=mono, 1=full stereo
    
    return {
        "rms_db": round(rms_db, 2),
        "peak_db": round(peak_db, 2),
        "crest": round(crest, 2),
        "sub_bass": round(band_e(20, 60) * 1e6, 3),
        "bass": round(band_e(60, 250) * 1e6, 3),
        "mid": round(band_e(250, 4000) * 1e6, 3),
        "high": round(band_e(4000, 20000) * 1e6, 3),
        "centroid_hz": round(centroid, 0),
        "stereo_width": round(stereo_width, 4),
    }

print("=" * 90)
print("  SOVEREIGN DNA COMPARISON: Original SOV vs ONNX2 Remaster")
print("=" * 90)

for fname in PICKS:
    sov_path = SOV_DIR / fname
    onnx_path = ONNX_DIR / f"ONNX2_{fname}"
    
    if not sov_path.exists() or not onnx_path.exists():
        print(f"\n⚠️ Missing: {fname}")
        continue
    
    a = analyze(sov_path)
    b = analyze(onnx_path)
    
    print(f"\n🎵 {fname}")
    print(f"  {'Metric':<18} {'Original':>12} {'ONNX2':>12} {'Delta':>10}")
    print(f"  {'-'*52}")
    for key in a:
        av, bv = a[key], b[key]
        d = bv - av
        flag = " ⚠️" if abs(d) > abs(av) * 0.3 and key != "stereo_width" else ""
        print(f"  {key:<18} {av:>12} {bv:>12} {d:>+10.3f}{flag}")

# Also dump one sidecar
sidecar_path = ONNX_DIR / f"ONNX2_{PICKS[0]}.dna.json"
if sidecar_path.exists():
    with open(sidecar_path) as f:
        sc = json.load(f)
    print(f"\n📋 Sidecar for {PICKS[0]}:")
    print(f"   Model: {sc.get('model')}")
    print(f"   Version: {sc.get('version')}")
    print(f"   Inference windows: {sc.get('inference_count')}")
    print(f"   Duration: {sc.get('duration_sec')}s")
    print(f"   Stereo: {sc.get('stereo')}")

print(f"\n{'=' * 90}")
