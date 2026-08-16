import os
import sys
import time
import datetime
import numpy as np
import librosa
import soundfile as sf
import onnxruntime as ort
import lancedb
from sklearn.preprocessing import StandardScaler
from scipy.signal import butter, sosfilt
from scipy.interpolate import PchipInterpolator  # Optimized monotonicity
from pedalboard import Pedalboard, Compressor, Gain, Limiter, HighShelfFilter, PeakFilter
from pathlib import Path
import json

# --- Paths ---
INPUT_TRACK = r"C:\Users\adams\Downloads\SCAR-red strobe.mp3"
MODEL_PATH = r"C:\WEB CASE STUDY\sovereign_big_brain_exhaustive.onnx"
BASELINE_DB = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
OUTPUT_DIR = r"C:\WEB CASE STUDY\sovereign_onnx_masters_v2"
CURVES_DIR = r"C:\WEB CASE STUDY\curves_onnx_v2"
MONO_CROSSOVER_HZ = 150.0

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CURVES_DIR, exist_ok=True)

TARGET_COLS = [
    "rms", "crest_factor", "sub_bass_energy", "bass_energy", "mid_energy",
    "high_energy", "spectral_centroid", "spectral_bandwidth",
    "spectral_rolloff", "spectral_flatness", "spectral_contrast", "zero_crossing_rate"
]

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
fname = os.path.basename(INPUT_TRACK)
base_name, _ = os.path.splitext(fname)
# Force output extension to .wav to prevent sf.write failure
out_audio_path = os.path.join(OUTPUT_DIR, f"ONNX2_{timestamp}_{base_name}.wav")
out_json_path = out_audio_path + ".dna.json"

print(f"[1/5] Loading Gold Baseline from LanceDB...")
db = lancedb.connect(BASELINE_DB)
df_gold = db.open_table("omni_semantic_baselines").to_pandas()
mask = df_gold["track_name"].str.contains("chris lake|somebody", case=False, na=False)
df_gold = df_gold[mask].reset_index(drop=True)

scaler = StandardScaler()
scaler.fit(df_gold[TARGET_COLS].fillna(0.0).values.astype(np.float32))
gold_mean_dict = {col: float(df_gold[col].mean()) for col in TARGET_COLS}

print(f"[2/5] Loading ONNX Session...")
session = ort.InferenceSession(MODEL_PATH)
input_name = session.get_inputs()[0].name

def extract_dna(y_mono, sr, n_fft=2048, hop=512):
    rms_val = float(np.sqrt(np.mean(y_mono ** 2)))
    peak = float(np.max(np.abs(y_mono))) + 1e-9
    crest = peak / (rms_val + 1e-9)
    S = np.abs(librosa.stft(y_mono, n_fft=n_fft, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    centroid = float(np.mean(librosa.feature.spectral_centroid(S=S, freq=freqs)))
    bandwidth = float(np.mean(librosa.feature.spectral_bandwidth(S=S, freq=freqs)))
    rolloff = float(np.mean(librosa.feature.spectral_rolloff(S=S, freq=freqs)))
    flatness = float(np.mean(librosa.feature.spectral_flatness(S=S)))
    contrast = float(np.mean(librosa.feature.spectral_contrast(S=S, sr=sr)))
    zcr = float(np.mean(librosa.feature.zero_crossing_rate(y_mono)))
    
    def band_e(S, f, lo, hi):
        m = (f >= lo) & (f < hi)
        return float(np.mean(S[m, :] ** 2)) if m.any() else 0.0
        
    sub_bass = band_e(S, freqs, 20, 60)
    bass = band_e(S, freqs, 60, 250)
    mid = band_e(S, freqs, 250, 4000)
    high = band_e(S, freqs, 4000, 20000)
    
    f12 = np.array([rms_val, crest, sub_bass, bass, mid, high,
                    centroid, bandwidth, rolloff, flatness, contrast, zcr], dtype=np.float32)
    d64 = np.zeros(64, dtype=np.float32)
    d64[:12] = f12
    return d64, f12

def predict(dna_64):
    norm = session.run(None, {input_name: dna_64.reshape(1, 64).astype(np.float32)})[0][0]
    real = scaler.inverse_transform(norm.reshape(1, -1))[0]
    return {col: float(real[i]) for i, col in enumerate(TARGET_COLS)}

print(f"[3/5] Loading track: {fname}...")
y, sr = librosa.load(INPUT_TRACK, sr=None, mono=False)
if y.ndim == 1:
    y = y[np.newaxis, :]
is_stereo = y.shape[0] >= 2
y_mono = librosa.to_mono(y) if is_stereo else y[0]

print(f"[4/5] Extracting dynamic trajectories (Window=0.5s, Hop=0.1s)...")
duration = len(y_mono) / sr
points = []
for start in np.arange(0, max(duration - 0.5, 0.05), 0.1):
    s, e = int(start * sr), int(min((start + 0.5) * sr, len(y_mono)))
    chunk = y_mono[s:e]
    if len(chunk) < 512:
        continue
    d64, f12 = extract_dna(chunk, sr)
    points.append((start, d64, f12))

times_arr = np.array([p[0] for p in points])
all_params = [predict(p[1]) for p in points]

curves = {}
for col in TARGET_COLS:
    vals = np.array([p[col] for p in all_params])
    curves[col] = PchipInterpolator(times_arr, vals)

print(f"[5/5] Processing mastering effects stream...")
block_samples = int(0.1 * sr)  # Smaller block processing
mastered = np.copy(y)

for start_samp in range(0, y.shape[1] - block_samples, block_samples):
    end_samp = start_samp + block_samples
    t = np.clip(start_samp / sr, times_arr[0], times_arr[-1])
    p = {col: float(curves[col](t)) for col in TARGET_COLS}
    chunk = y[:, start_samp:end_samp].copy()

    chunk_rms = float(np.sqrt(np.mean(chunk ** 2))) + 1e-9
    target_rms = max(p["rms"], 1e-6)
    blended_rms = target_rms * 0.7 + gold_mean_dict["rms"] * 0.3
    gain_db = np.clip(20 * np.log10(blended_rms + 1e-9) - 20 * np.log10(chunk_rms), -6.0, 6.0)

    ratio = np.clip(p["crest_factor"] * 0.6, 1.2, 4.0)
    threshold = np.clip(-10.0 - abs(gain_db) * 0.5, -24.0, -6.0)

    mid_delta = 0.0
    if gold_mean_dict["mid_energy"] > 0 and p["mid_energy"] > 0:
        mid_delta = np.clip(-3.0 * np.log2(p["mid_energy"] / gold_mean_dict["mid_energy"] + 1e-9), -3.0, 3.0)
    high_delta = 0.0
    if gold_mean_dict["high_energy"] > 0 and p["high_energy"] > 0:
        high_delta = np.clip(-2.0 * np.log2(p["high_energy"] / gold_mean_dict["high_energy"] + 1e-9), -2.0, 3.0)

    board = Pedalboard([
        Gain(gain_db=float(gain_db)),
        PeakFilter(cutoff_frequency_hz=1000.0, gain_db=float(mid_delta), q=0.7),
        HighShelfFilter(cutoff_frequency_hz=8000.0, gain_db=float(high_delta), q=0.7),
        Compressor(threshold_db=float(threshold), ratio=float(ratio), attack_ms=15.0, release_ms=120.0),
        Limiter(threshold_db=-1.0, release_ms=150.0),
    ])
    mastered[:, start_samp:end_samp] = board(chunk, sample_rate=sr)

if is_stereo and mastered.shape[0] >= 2:
    sos_low = butter(4, MONO_CROSSOVER_HZ, btype='low', fs=sr, output='sos')
    sos_high = butter(4, MONO_CROSSOVER_HZ, btype='high', fs=sr, output='sos')
    low_mono = (sosfilt(sos_low, mastered[0]) + sosfilt(sos_low, mastered[1])) * 0.5
    mastered[0] = low_mono + sosfilt(sos_high, mastered[0])
    mastered[1] = low_mono + sosfilt(sos_high, mastered[1])

mastered = np.clip(mastered, -1.0, 1.0)
sf.write(out_audio_path, mastered.T, sr)

sidecar = {
    "source": fname,
    "model": "sovereign_big_brain_exhaustive.onnx",
    "version": "v2_pchip_highres",
    "stereo": is_stereo,
    "duration_sec": round(y.shape[1] / sr, 2),
    "inference_count": len(points),
    "audio_output_path": out_audio_path,
    "timestamp": timestamp
}

with open(out_json_path, "w") as f:
    json.dump(sidecar, f, indent=2)

print(f"\n[SUCCESS] MASTERING COMPLETE!")
print(f"Audio Mastered File: {out_audio_path}")
print(f"DNA Sidecar File: {out_json_path}")
