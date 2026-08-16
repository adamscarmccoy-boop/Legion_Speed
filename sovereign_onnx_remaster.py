# -*- coding: utf-8 -*-
"""
SOVEREIGN ONNX REMASTER — Real Neural Chain
============================================
Reads every .wav in python_masters, extracts a REAL 64-dim DNA vector
(12 acoustic features + zero-padded to 64), runs sovereign_big_brain_exhaustive.onnx
to predict 12 DSP parameters, then applies them via pedalboard and writes:
  1. A remastered .wav
  2. A .dna.json sidecar with full math
"""
import os, sys, json, time
import numpy as np
import librosa
import soundfile as sf
import onnxruntime as ort
import pandas as pd
import lancedb
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from scipy.interpolate import interp1d
from pedalboard import (
    Pedalboard, Compressor, HighpassFilter, Gain, Limiter,
    HighShelfFilter, LowShelfFilter
)

# Rule 4: Unicode safeguard
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ==============================================================================
# CONFIG
# ==============================================================================
INPUT_DIR   = Path(r"C:\WEB CASE STUDY\python_masters")
OUTPUT_DIR  = Path(r"C:\WEB CASE STUDY\sovereign_onnx_masters")
CURVES_DIR  = Path(r"C:\WEB CASE STUDY\curves_onnx")
MODEL_PATH  = r"C:\WEB CASE STUDY\sovereign_big_brain_exhaustive.onnx"
BASELINE_DB = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CURVES_DIR, exist_ok=True)

# The 12 DSP target columns the model was trained on
TARGET_COLS = [
    "rms", "crest_factor", "sub_bass_energy", "bass_energy", "mid_energy",
    "high_energy", "spectral_centroid", "spectral_bandwidth",
    "spectral_rolloff", "spectral_flatness", "spectral_contrast", "zero_crossing_rate"
]

# ==============================================================================
# DNA EXTRACTOR — Real acoustic features from audio
# ==============================================================================
def extract_dna_vector(y_mono, sr, n_fft=2048, hop=512):
    """
    Extract a 12-dim acoustic feature vector from a mono audio signal,
    then zero-pad to 64 dims to match the ONNX input shape.
    """
    rms_val      = float(np.sqrt(np.mean(y_mono ** 2)))
    peak         = float(np.max(np.abs(y_mono))) + 1e-9
    crest        = peak / (rms_val + 1e-9)

    # Spectral features (mean across time)
    S = np.abs(librosa.stft(y_mono, n_fft=n_fft, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

    centroid  = float(np.mean(librosa.feature.spectral_centroid(S=S, freq=freqs)))
    bandwidth = float(np.mean(librosa.feature.spectral_bandwidth(S=S, freq=freqs)))
    rolloff   = float(np.mean(librosa.feature.spectral_rolloff(S=S, freq=freqs)))
    flatness  = float(np.mean(librosa.feature.spectral_flatness(S=S)))
    contrast  = float(np.mean(librosa.feature.spectral_contrast(S=S, sr=sr)))
    zcr       = float(np.mean(librosa.feature.zero_crossing_rate(y_mono)))

    # Band energies
    def band_energy(S, freqs, lo, hi):
        mask = (freqs >= lo) & (freqs < hi)
        return float(np.mean(S[mask, :] ** 2)) if mask.any() else 0.0

    sub_bass = band_energy(S, freqs, 20, 60)
    bass     = band_energy(S, freqs, 60, 250)
    mid      = band_energy(S, freqs, 250, 4000)
    high     = band_energy(S, freqs, 4000, 20000)

    # 12 real features
    features_12 = np.array([
        rms_val, crest, sub_bass, bass, mid, high,
        centroid, bandwidth, rolloff, flatness, contrast, zcr
    ], dtype=np.float32)

    # Pad to 64 dims
    dna_64 = np.zeros(64, dtype=np.float32)
    dna_64[:12] = features_12
    return dna_64, features_12


def extract_windowed_dna(y_mono, sr, window_sec=2.0, hop_sec=1.0):
    """
    Sliding-window DNA extraction for temporal parameter trajectory.
    Returns list of (time, dna_64, features_12) tuples.
    """
    duration = len(y_mono) / sr
    points = []
    for start in np.arange(0, max(duration - window_sec, 0.1), hop_sec):
        s = int(start * sr)
        e = int(min((start + window_sec) * sr, len(y_mono)))
        chunk = y_mono[s:e]
        if len(chunk) < 1024:
            continue
        dna_64, feat_12 = extract_dna_vector(chunk, sr)
        points.append((start, dna_64, feat_12))
    return points

# ==============================================================================
# SOVEREIGN ENGINE
# ==============================================================================
class SovereignONNXEngine:
    def __init__(self):
        print("🌌 Loading Sovereign Big Brain Exhaustive ONNX...")
        self.session = ort.InferenceSession(MODEL_PATH)
        self.input_name = self.session.get_inputs()[0].name
        print(f"   Input: {self.input_name} shape={self.session.get_inputs()[0].shape}")
        print(f"   Output: dsp_state shape={self.session.get_outputs()[0].shape}")

        # Load gold baseline scaler
        print("   Loading Gold Baseline scaler from LanceDB...")
        db = lancedb.connect(BASELINE_DB)
        df_gold = db.open_table("omni_semantic_baselines").to_pandas()
        mask = df_gold["track_name"].str.contains("chris lake|somebody", case=False, na=False)
        df_gold = df_gold[mask].reset_index(drop=True)

        self.scaler = StandardScaler()
        self.scaler.fit(df_gold[TARGET_COLS].fillna(0.0).values.astype(np.float32))
        self.gold_mean = df_gold[TARGET_COLS].mean().to_dict()
        print(f"   Gold Baseline fitted on {len(df_gold)} rows.")
        print("   ✅ Engine ready.\n")

    def predict_dsp(self, dna_64):
        """Run ONNX inference → inverse-scale → return dict of 12 DSP params."""
        inp = dna_64.reshape(1, 64).astype(np.float32)
        norm_pred = self.session.run(None, {self.input_name: inp})[0][0]
        real_pred = self.scaler.inverse_transform(norm_pred.reshape(1, -1))[0]
        return {col: float(real_pred[i]) for i, col in enumerate(TARGET_COLS)}

    def process_file(self, input_path):
        fname = input_path.name
        print(f"🚀 {fname}")
        t_start = time.perf_counter()

        y, sr = librosa.load(str(input_path), sr=None, mono=False)
        if y.ndim == 1:
            y = y[np.newaxis, :]
        y_mono = y[0]

        # 1. Windowed DNA extraction
        points = extract_windowed_dna(y_mono, sr, window_sec=2.0, hop_sec=0.5)
        if not points:
            print(f"   ⚠️ Skipped (too short)")
            return

        # 2. ONNX inference per window
        times = []
        all_params = []
        all_raw_dna = []
        for (t, dna_64, feat_12) in points:
            params = self.predict_dsp(dna_64)
            times.append(t)
            all_params.append(params)
            all_raw_dna.append(feat_12.tolist())

        # 3. Build temporal curves with cubic interpolation
        times = np.array(times)
        curves = {}
        for col in TARGET_COLS:
            vals = np.array([p[col] for p in all_params])
            if len(times) > 3:
                f = interp1d(times, vals, kind='cubic', fill_value="extrapolate")
            else:
                f = interp1d(times, vals, kind='linear', fill_value="extrapolate")
            curves[col] = f

        # Save curves CSV
        curve_times = np.linspace(times[0], times[-1], 200)
        curve_df = pd.DataFrame({col: curves[col](curve_times) for col in TARGET_COLS})
        curve_df.insert(0, "time", curve_times)
        curve_df.to_csv(CURVES_DIR / f"{fname}_curves.csv", index=False)

        # 4. Physical rendering via Pedalboard
        # Map predicted DSP targets to compressor/EQ settings
        duration = y.shape[1] / sr
        block_samples = int(0.5 * sr)  # 500ms blocks

        gain_node = Gain(gain_db=0.0)
        hp_node   = HighpassFilter(cutoff_frequency_hz=30.0)
        comp_node = Compressor(threshold_db=-20.0, ratio=3.0, attack_ms=10.0, release_ms=100.0)
        lim_node  = Limiter(threshold_db=-0.3, release_ms=100.0)
        board = Pedalboard([hp_node, gain_node, comp_node, lim_node])

        mastered = np.zeros_like(y)
        for start_samp in range(0, y.shape[1] - block_samples, block_samples):
            end_samp = start_samp + block_samples
            t = start_samp / sr

            # Clamp t within curve range
            t_clamped = np.clip(t, times[0], times[-1])
            p = {col: float(curves[col](t_clamped)) for col in TARGET_COLS}

            # DSP param mapping from predicted targets
            target_rms = p["rms"]
            target_crest = p["crest_factor"]
            gold_rms = self.gold_mean.get("rms", -14.0)

            # Gain: push toward gold RMS level
            chunk = y[:, start_samp:end_samp]
            chunk_rms = float(np.sqrt(np.mean(chunk ** 2))) + 1e-9
            chunk_rms_db = 20 * np.log10(chunk_rms + 1e-9)
            target_rms_db = 20 * np.log10(abs(target_rms) + 1e-9) if target_rms > 0 else -20.0
            gain_delta = np.clip(target_rms_db - chunk_rms_db, -12.0, 12.0)
            gain_node.gain_db = float(gain_delta)

            # Compressor: higher crest = more compression needed
            ratio = np.clip(target_crest * 0.8, 1.5, 8.0)
            threshold = np.clip(-6.0 - abs(gain_delta), -30.0, -3.0)
            comp_node.ratio = float(ratio)
            comp_node.threshold_db = float(threshold)

            mastered[:, start_samp:end_samp] = board(chunk, sample_rate=sr, reset=False)

        # Handle tail
        tail_start = (y.shape[1] // block_samples) * block_samples
        if tail_start < y.shape[1]:
            mastered[:, tail_start:] = y[:, tail_start:]

        # 5. Write output
        out_path = OUTPUT_DIR / f"ONNX_{fname}"
        sf.write(str(out_path), mastered.T, sr)

        # 6. Write DNA sidecar
        sidecar = {
            "source": fname,
            "model": "sovereign_big_brain_exhaustive.onnx",
            "sample_rate": sr,
            "duration_sec": round(duration, 2),
            "inference_count": len(points),
            "gold_baseline": self.gold_mean,
            "dsp_trajectory_summary": {
                col: {
                    "mean": float(np.mean([p[col] for p in all_params])),
                    "min": float(np.min([p[col] for p in all_params])),
                    "max": float(np.max([p[col] for p in all_params])),
                }
                for col in TARGET_COLS
            },
            "raw_dna_vectors": all_raw_dna[:5],  # first 5 for reference
        }
        sidecar_path = OUTPUT_DIR / f"ONNX_{fname}.dna.json"
        with open(sidecar_path, "w") as f:
            json.dump(sidecar, f, indent=2)

        elapsed = time.perf_counter() - t_start
        print(f"   ✅ {elapsed:.1f}s | {len(points)} windows | → {out_path.name}")


# ==============================================================================
# MAIN
# ==============================================================================
if __name__ == "__main__":
    engine = SovereignONNXEngine()

    # Get all base SOV tracks (skip already-mastered variants)
    all_wavs = sorted(INPUT_DIR.glob("*.wav"))
    # Filter: only process base SOV_ files, skip _MASTERED, _DYNAMIC, _NEURAL suffixes
    skip_suffixes = ["_MASTERED", "_DYNAMIC_MASTERED", "_SONIC_DNA_MASTERED",
                     "_SONIC_DNA_V4_MASTERED", "_SONIC_DNA_V5_NEURAL",
                     "_DYNAMIC_MASTERED_v2", "_SMART_MASTER"]
    base_wavs = []
    for w in all_wavs:
        stem = w.stem
        if any(stem.endswith(s) for s in skip_suffixes):
            continue
        # Skip mono duplicates
        if "mastered mono" in stem or "mastered." in w.name:
            continue
        base_wavs.append(w)

    print(f"{'=' * 60}")
    print(f"  SOVEREIGN ONNX REMASTER — {len(base_wavs)} tracks")
    print(f"  Model: sovereign_big_brain_exhaustive.onnx (64→12)")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"{'=' * 60}\n")

    for wf in base_wavs:
        try:
            engine.process_file(wf)
        except Exception as e:
            print(f"   ❌ FAILED: {e}")

    print(f"\n{'=' * 60}")
    print(f"  REMASTER COMPLETE — {len(base_wavs)} tracks processed")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"{'=' * 60}")
