# -*- coding: utf-8 -*-
"""
SOVEREIGN ONNX v2 — RAY DISTRIBUTED
Uses Ray remote tasks to parallelize across all available CPUs.
"""
import os, sys, json, time
import numpy as np
import ray
import matplotlib.pyplot as plt

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

# ==============================================================================
# CONFIG
# ==============================================================================
INPUT_DIR   = r"C:\WEB CASE STUDY\python_masters"
OUTPUT_DIR  = r"C:\WEB CASE STUDY\sovereign_onnx_masters_v2"
CURVES_DIR  = r"C:\WEB CASE STUDY\curves_onnx_v2"
MODEL_PATH  = r"C:\WEB CASE STUDY\sovereign_big_brain_exhaustive.onnx"
BASELINE_DB = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
MONO_CROSSOVER_HZ = 150.0

TARGET_COLS = [
    "rms", "crest_factor", "sub_bass_energy", "bass_energy", "mid_energy",
    "high_energy", "spectral_centroid", "spectral_bandwidth",
    "spectral_rolloff", "spectral_flatness", "spectral_contrast", "zero_crossing_rate"
]

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CURVES_DIR, exist_ok=True)

# ==============================================================================
# RAY REMOTE TASK — one per track, uses 1 CPU each
# ==============================================================================
@ray.remote(num_cpus=1)
def process_track(filepath, gold_mean_dict, scaler_mean, scaler_scale):
    import numpy as np
    import librosa
    import soundfile as sf
    import onnxruntime as ort
    import pandas as pd
    import json
    from scipy.signal import butter, sosfilt
    from scipy.interpolate import interp1d
    from pedalboard import (
        Pedalboard, Compressor, Gain, Limiter,
        HighShelfFilter, PeakFilter
    )
    from sklearn.preprocessing import StandardScaler
    from pathlib import Path

    fname = os.path.basename(filepath)
    t_start = time.perf_counter()

    # Rebuild scaler from serialized params
    scaler = StandardScaler()
    scaler.mean_ = np.array(scaler_mean)
    scaler.scale_ = np.array(scaler_scale)
    scaler.var_ = scaler.scale_ ** 2
    scaler.n_features_in_ = len(scaler_mean)

    # Load ONNX
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

    # Load audio
    y, sr = librosa.load(filepath, sr=None, mono=False)
    if y.ndim == 1:
        y = y[np.newaxis, :]
    is_stereo = y.shape[0] >= 2
    y_mono = librosa.to_mono(y) if is_stereo else y[0]

    # Windowed DNA
    duration = len(y_mono) / sr
    points = []
    for start in np.arange(0, max(duration - 2.0, 0.1), 0.5):
        s, e = int(start * sr), int(min((start + 2.0) * sr, len(y_mono)))
        chunk = y_mono[s:e]
        if len(chunk) < 1024:
            continue
        d64, f12 = extract_dna(chunk, sr)
        points.append((start, d64, f12))

    if not points:
        return {"file": fname, "status": "skipped"}

    # Inference
    times_arr = np.array([p[0] for p in points])
    all_params = [predict(p[1]) for p in points]

    # Curves
    curves = {}
    for col in TARGET_COLS:
        vals = np.array([p[col] for p in all_params])
        kind = 'cubic' if len(times_arr) > 3 else 'linear'
        curves[col] = interp1d(times_arr, vals, kind=kind, fill_value="extrapolate")

    # Render
    block_samples = int(0.5 * sr)
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

    # Generate and Save Curve Plots
    try:
        import matplotlib.pyplot as plt
        fig, axs = plt.subplots(3, 1, figsize=(12, 10))
        t_plot = np.linspace(times_arr[0], times_arr[-1], 200)
        
        # RMS & Crest Factor
        axs[0].plot(t_plot, curves["rms"](t_plot), label="Target RMS", color='blue')
        axs[0].plot(t_plot, curves["crest_factor"](t_plot), label="Target Crest", color='orange')
        axs[0].set_title(f"Dynamic Mastering Curves: {fname}")
        axs[0].legend()
        axs[0].grid(True)
        
        # Energy Bands
        axs[1].plot(t_plot, curves["sub_bass_energy"](t_plot), label="Sub Bass", color='purple')
        axs[1].plot(t_plot, curves["bass_energy"](t_plot), label="Bass", color='red')
        axs[1].plot(t_plot, curves["mid_energy"](t_plot), label="Mid", color='green')
        axs[1].plot(t_plot, curves["high_energy"](t_plot), label="High", color='cyan')
        axs[1].legend()
        axs[1].grid(True)
        
        # Spectral properties
        axs[2].plot(t_plot, curves["spectral_centroid"](t_plot), label="Centroid", color='brown')
        axs[2].legend()
        axs[2].grid(True)
        
        plt.tight_layout()
        plot_path = os.path.join(CURVES_DIR, f"{fname}_curves.png")
        plt.savefig(plot_path)
        plt.close(fig)
    except Exception as e:
        print(f"Failed to plot curves for {fname}: {e}")

    # 150Hz Truth
    if is_stereo and mastered.shape[0] >= 2:
        sos_low = butter(4, MONO_CROSSOVER_HZ, btype='low', fs=sr, output='sos')
        sos_high = butter(4, MONO_CROSSOVER_HZ, btype='high', fs=sr, output='sos')
        low_mono = (sosfilt(sos_low, mastered[0]) + sosfilt(sos_low, mastered[1])) * 0.5
        mastered[0] = low_mono + sosfilt(sos_high, mastered[0])
        mastered[1] = low_mono + sosfilt(sos_high, mastered[1])

    mastered = np.clip(mastered, -1.0, 1.0)

    out_path = os.path.join(OUTPUT_DIR, f"ONNX2_{fname}")
    sf.write(out_path, mastered.T, sr)

    # Sidecar
    sidecar = {
        "source": fname, "model": "sovereign_big_brain_exhaustive.onnx",
        "version": "v2_ray_150hz", "stereo": is_stereo,
        "duration_sec": round(y.shape[1] / sr, 2),
        "inference_count": len(points),
    }
    with open(out_path + ".dna.json", "w") as f:
        json.dump(sidecar, f, indent=2)

    elapsed = time.perf_counter() - t_start
    return {"file": fname, "status": "done", "time": round(elapsed, 1), "windows": len(points)}


# ==============================================================================
# MAIN — Fan out across Ray
# ==============================================================================
if __name__ == "__main__":
    import lancedb
    from sklearn.preprocessing import StandardScaler
    from pathlib import Path

    ray.init(address="auto", namespace="legion")
    print(f"Ray connected: {ray.cluster_resources()}")

    # Load gold baseline on driver
    db = lancedb.connect(BASELINE_DB)
    df_gold = db.open_table("omni_semantic_baselines").to_pandas()
    mask = df_gold["track_name"].str.contains("chris lake|somebody", case=False, na=False)
    df_gold = df_gold[mask].reset_index(drop=True)

    scaler = StandardScaler()
    scaler.fit(df_gold[TARGET_COLS].fillna(0.0).values.astype(np.float32))
    gold_mean = {col: float(df_gold[col].mean()) for col in TARGET_COLS}

    # Serialize scaler for workers
    s_mean = scaler.mean_.tolist()
    s_scale = scaler.scale_.tolist()

    # Collect tracks
    all_wavs = sorted(Path(INPUT_DIR).glob("*.wav"))
    skip = ["_MASTERED", "_DYNAMIC_MASTERED", "_SONIC_DNA_MASTERED",
            "_SONIC_DNA_V4_MASTERED", "_SONIC_DNA_V5_NEURAL",
            "_DYNAMIC_MASTERED_v2", "_SMART_MASTER"]
    base_wavs = [w for w in all_wavs
                 if not any(w.stem.endswith(s) for s in skip)
                 and "mastered mono" not in w.stem and "mastered." not in w.name]

    print(f"\n{'=' * 60}")
    print(f"  SOVEREIGN ONNX v2 — RAY DISTRIBUTED")
    print(f"  Tracks: {len(base_wavs)} | Workers: {int(ray.cluster_resources().get('CPU', 1))}")
    print(f"{'=' * 60}\n")

    t0 = time.perf_counter()

    # Fan out all tracks as parallel Ray tasks
    futures = [process_track.remote(str(w), gold_mean, s_mean, s_scale) for w in base_wavs]
    results = ray.get(futures)

    elapsed = time.perf_counter() - t0

    done = [r for r in results if r["status"] == "done"]
    print(f"\n{'=' * 60}")
    print(f"  COMPLETE: {len(done)}/{len(base_wavs)} tracks in {elapsed:.1f}s")
    print(f"  Avg: {elapsed/max(len(done),1):.1f}s/track (wall clock)")
    for r in done:
        print(f"    ✅ {r['file']} — {r['time']}s, {r['windows']} windows")
    print(f"{'=' * 60}")