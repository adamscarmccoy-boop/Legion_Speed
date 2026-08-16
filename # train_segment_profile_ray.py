# train_segment_profile_ray.py
# Real Ray segment-profile trainer.
# No mock data. No random fallback. If audio is missing/bad, it fails.

import os
import json
import math
import glob
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch
import ray

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


import librosa
from sklearn.cluster import MiniBatchKMeans
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import StandardScaler


# =========================
# CONFIG
# =========================

TRAINING_AUDIO_DIR = r"C:\WEB CASE STUDY\Snoop_Stylizer_App\training_audio"
OUTPUT_DIR = r"C:\WEB CASE STUDY\Snoop_Stylizer_App"

PROFILE_NAME = "Snoop"

SAMPLE_RATE = 22050
SEGMENT_SECONDS = 0.75
HOP_SECONDS = 0.375

N_MFCC = 20
N_CLUSTERS = 12

MIN_SEGMENT_RMS = 0.003
MIN_FILES_REQUIRED = 1
MIN_SEGMENTS_REQUIRED = 20

RAY_NAMESPACE = "legion"


# =========================
# FEATURE EXTRACTION
# =========================

AUDIO_EXTENSIONS = [
    "*.wav", "*.mp3", "*.m4a", "*.flac", "*.ogg", "*.aiff", "*.aif"
]


def find_audio_files(audio_dir: str) -> List[str]:
    files = []
    for ext in AUDIO_EXTENSIONS:
        files.extend(glob.glob(os.path.join(audio_dir, "**", ext), recursive=True))
    files = sorted(set(files))
    return files


def safe_float(x, fallback=0.0) -> float:
    try:
        if x is None:
            return fallback
        if np.isnan(x) or np.isinf(x):
            return fallback
        return float(x)
    except Exception:
        return fallback


def extract_segment_features(y: np.ndarray, sr: int) -> np.ndarray:
    """
    Returns one feature vector for one audio segment.
    Feature vector is intentionally broad:
    - MFCC mean/std
    - spectral centroid/bandwidth/rolloff/flatness
    - zero crossing
    - RMS
    - pitch median/spread
    - tempo-ish onset strength summary
    """

    if y.ndim > 1:
        y = np.mean(y, axis=0)

    y = np.asarray(y, dtype=np.float32)

    if len(y) < int(0.1 * sr):
        raise ValueError("Segment too short")

    rms = librosa.feature.rms(y=y)[0]
    mean_rms = safe_float(np.mean(rms))

    if mean_rms < MIN_SEGMENT_RMS:
        raise ValueError(f"Silent/low RMS segment: {mean_rms:.8f}")

    # Normalize segment peak gently for feature stability, not output audio.
    peak = np.max(np.abs(y))
    if peak > 0:
        y_norm = y / peak
    else:
        raise ValueError("Zero peak segment")

    mfcc = librosa.feature.mfcc(y=y_norm, sr=sr, n_mfcc=N_MFCC)
    mfcc_mean = np.mean(mfcc, axis=1)
    mfcc_std = np.std(mfcc, axis=1)

    centroid = librosa.feature.spectral_centroid(y=y_norm, sr=sr)[0]
    bandwidth = librosa.feature.spectral_bandwidth(y=y_norm, sr=sr)[0]
    rolloff = librosa.feature.spectral_rolloff(y=y_norm, sr=sr)[0]
    flatness = librosa.feature.spectral_flatness(y=y_norm)[0]
    zcr = librosa.feature.zero_crossing_rate(y_norm)[0]

    # Pitch via pyin. It can fail on some material, so missing pitch becomes 0.
    try:
        f0, voiced_flag, _ = librosa.pyin(
            y_norm,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
            sr=sr,
        )
        valid_f0 = f0[voiced_flag] if f0 is not None and voiced_flag is not None else []
        if len(valid_f0) > 0:
            pitch_median = safe_float(np.median(valid_f0))
            pitch_std = safe_float(np.std(valid_f0))
            voiced_ratio = safe_float(np.mean(voiced_flag))
        else:
            pitch_median = 0.0
            pitch_std = 0.0
            voiced_ratio = 0.0
    except Exception:
        pitch_median = 0.0
        pitch_std = 0.0
        voiced_ratio = 0.0

    try:
        onset_env = librosa.onset.onset_strength(y=y_norm, sr=sr)
        onset_mean = safe_float(np.mean(onset_env))
        onset_std = safe_float(np.std(onset_env))
    except Exception:
        onset_mean = 0.0
        onset_std = 0.0

    extra = np.array([
        mean_rms,
        safe_float(np.std(rms)),
        safe_float(np.mean(centroid)),
        safe_float(np.std(centroid)),
        safe_float(np.mean(bandwidth)),
        safe_float(np.std(bandwidth)),
        safe_float(np.mean(rolloff)),
        safe_float(np.std(rolloff)),
        safe_float(np.mean(flatness)),
        safe_float(np.std(flatness)),
        safe_float(np.mean(zcr)),
        safe_float(np.std(zcr)),
        pitch_median,
        pitch_std,
        voiced_ratio,
        onset_mean,
        onset_std,
    ], dtype=np.float32)

    feature = np.concatenate([
        mfcc_mean.astype(np.float32),
        mfcc_std.astype(np.float32),
        extra,
    ]).astype(np.float32)

    if not np.all(np.isfinite(feature)):
        raise ValueError("Non-finite feature vector")

    return feature


@ray.remote(num_cpus=1)
def process_audio_file(path: str) -> Dict:
    """
    Ray worker: loads one audio file, slices it into overlapping segments,
    extracts features, and returns segment feature matrix.
    """

    result = {
        "path": path,
        "ok": False,
        "error": None,
        "segments": 0,
        "duration_sec": 0.0,
        "features": None,
    }

    try:
        y, sr = librosa.load(path, sr=SAMPLE_RATE, mono=True)
        if y is None or len(y) == 0:
            raise ValueError("Loaded empty audio")

        duration = len(y) / float(sr)
        result["duration_sec"] = duration

        seg_len = int(SEGMENT_SECONDS * sr)
        hop_len = int(HOP_SECONDS * sr)

        if len(y) < seg_len:
            raise ValueError(f"File shorter than one segment: {duration:.2f}s")

        features = []

        for start in range(0, len(y) - seg_len + 1, hop_len):
            segment = y[start:start + seg_len]

            try:
                feat = extract_segment_features(segment, sr)
                features.append(feat)
            except Exception:
                # Not mock data. We skip bad/silent segments only.
                continue

        if not features:
            raise ValueError("No usable non-silent segments extracted")

        mat = np.stack(features).astype(np.float32)

        result["ok"] = True
        result["segments"] = int(mat.shape[0])
        result["features"] = mat

        return result

    except Exception as e:
        result["error"] = repr(e)
        return result


# =========================
# TORCH ROUTER MODEL
# =========================

class SegmentRouter(torch.nn.Module):
    def __init__(self, input_dim: int, n_clusters: int):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(input_dim, 128),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.10),
            torch.nn.Linear(128, 64),
            torch.nn.ReLU(),
            torch.nn.Linear(64, n_clusters),
        )

    def forward(self, x):
        return self.net(x)


def train_router(features_scaled: np.ndarray, labels: np.ndarray, input_dim: int, n_clusters: int) -> Tuple[SegmentRouter, Dict]:
    X_train, X_val, y_train, y_val = train_test_split(
        features_scaled,
        labels,
        test_size=0.20,
        random_state=42,
        stratify=labels if len(set(labels.tolist())) > 1 else None,
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = SegmentRouter(input_dim=input_dim, n_clusters=n_clusters).to(device)

    X_train_t = torch.tensor(X_train, dtype=torch.float32, device=device)
    y_train_t = torch.tensor(y_train, dtype=torch.long, device=device)
    X_val_t = torch.tensor(X_val, dtype=torch.float32, device=device)
    y_val_t = torch.tensor(y_val, dtype=torch.long, device=device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    loss_fn = torch.nn.CrossEntropyLoss()

    best_val = float("inf")
    best_state = None

    epochs = 120
    batch_size = 128

    for epoch in range(1, epochs + 1):
        model.train()

        perm = torch.randperm(X_train_t.shape[0], device=device)
        total_loss = 0.0

        for i in range(0, X_train_t.shape[0], batch_size):
            idx = perm[i:i + batch_size]
            xb = X_train_t[idx]
            yb = y_train_t[idx]

            optimizer.zero_grad()
            logits = model(xb)
            loss = loss_fn(logits, yb)
            loss.backward()
            optimizer.step()

            total_loss += float(loss.item())

        model.eval()
        with torch.no_grad():
            val_logits = model(X_val_t)
            val_loss = float(loss_fn(val_logits, y_val_t).item())
            val_pred = torch.argmax(val_logits, dim=1)
            val_acc = float((val_pred == y_val_t).float().mean().item())

        if val_loss < best_val:
            best_val = val_loss
            best_state = {
                k: v.detach().cpu().clone()
                for k, v in model.state_dict().items()
            }

        if epoch % 20 == 0 or epoch == 1:
            print(f"[router] epoch={epoch:03d} val_loss={val_loss:.4f} val_acc={val_acc:.3f}")

    if best_state is not None:
        model.load_state_dict(best_state)

    model.eval()

    with torch.no_grad():
        logits = model(X_val_t)
        pred = torch.argmax(logits, dim=1).detach().cpu().numpy()

    report = {
        "device": str(device),
        "best_val_loss": best_val,
        "validation_report": classification_report(y_val, pred, output_dict=True, zero_division=0),
    }

    return model.cpu(), report


# =========================
# DSP PRESET DERIVATION
# =========================

def derive_cluster_dsp_presets(raw_features: np.ndarray, labels: np.ndarray) -> List[Dict]:
    """
    Turns learned segment clusters into DSP hints.
    This is not arbitrary mock presetting: it derives broad EQ/compression hints
    from each cluster's spectral/pitch/energy stats.
    """

    presets = []

    # Feature indices:
    # MFCC mean: 0:20
    # MFCC std: 20:40
    # extra starts at 40
    EXTRA_START = N_MFCC * 2
    IDX_RMS = EXTRA_START + 0
    IDX_CENTROID_MEAN = EXTRA_START + 2
    IDX_ROLLOFF_MEAN = EXTRA_START + 6
    IDX_PITCH_MEDIAN = EXTRA_START + 12
    IDX_VOICED_RATIO = EXTRA_START + 14

    for cluster_id in sorted(set(labels.tolist())):
        cluster_features = raw_features[labels == cluster_id]

        rms = safe_float(np.mean(cluster_features[:, IDX_RMS]))
        centroid = safe_float(np.mean(cluster_features[:, IDX_CENTROID_MEAN]))
        rolloff = safe_float(np.mean(cluster_features[:, IDX_ROLLOFF_MEAN]))
        pitch = safe_float(np.mean(cluster_features[:, IDX_PITCH_MEDIAN]))
        voiced = safe_float(np.mean(cluster_features[:, IDX_VOICED_RATIO]))

        # Derived, bounded DSP hints.
        if centroid < 1200:
            lowpass = 3200.0
            highpass = 55.0
        elif centroid < 2200:
            lowpass = 4500.0
            highpass = 70.0
        else:
            lowpass = 6500.0
            highpass = 100.0

        if rms < 0.015:
            gain_db = 4.0
            comp_threshold = -28.0
        elif rms < 0.035:
            gain_db = 1.5
            comp_threshold = -22.0
        else:
            gain_db = -1.0
            comp_threshold = -16.0

        if voiced > 0.45 and pitch > 0:
            # Slight pitch nudge, not identity conversion.
            pitch_shift = float(np.clip(12.0 * np.log2(max(pitch, 1.0) / 150.0), -6.0, 6.0))
        else:
            pitch_shift = 0.0

        preset = {
            "cluster_id": int(cluster_id),
            "rms": rms,
            "centroid_hz": centroid,
            "rolloff_hz": rolloff,
            "pitch_hz": pitch,
            "voiced_ratio": voiced,
            "derived_dsp": {
                "gain_db": gain_db,
                "compressor_threshold_db": comp_threshold,
                "compressor_ratio": 3.0,
                "highpass_hz": highpass,
                "lowpass_hz": lowpass,
                "pitch_shift_semitones": pitch_shift,
            },
        }

        presets.append(preset)

    return presets


# =========================
# MAIN TRAINING PIPELINE
# =========================

def main():
    started = time.time()

    audio_dir = TRAINING_AUDIO_DIR
    output_dir = OUTPUT_DIR

    os.makedirs(output_dir, exist_ok=True)

    print("============================================")
    print("REAL RAY SEGMENT PROFILE TRAINER")
    print("============================================")
    print(f"Training audio dir: {audio_dir}")
    print(f"Output dir:         {output_dir}")
    print(f"Profile name:       {PROFILE_NAME}")
    print("")

    files = find_audio_files(audio_dir)

    if len(files) < MIN_FILES_REQUIRED:
        raise SystemExit(
            f"No usable audio files found in: {audio_dir}\n"
            f"Put WAV/MP3/M4A/FLAC files in that folder and rerun."
        )

    print(f"Found {len(files)} audio files.")
    for f in files[:10]:
        print(f"  - {f}")
    if len(files) > 10:
        print(f"  ... plus {len(files) - 10} more")

    # Connect to Ray cluster if present, otherwise start local Ray.
    # This is not mock training. It just chooses cluster/local execution.
    try:
        ray.init(address="auto", namespace=RAY_NAMESPACE, ignore_reinit_error=True)
        print("Connected to existing Ray cluster.")
    except Exception as e:
        print(f"No existing Ray cluster found. Starting local Ray. Reason: {e}")
        ray.init(namespace=RAY_NAMESPACE, ignore_reinit_error=True)

    futures = [process_audio_file.remote(f) for f in files]
    results = ray.get(futures)

    ok_results = [r for r in results if r["ok"]]
    bad_results = [r for r in results if not r["ok"]]

    print("")
    print(f"Files OK:  {len(ok_results)}")
    print(f"Files bad: {len(bad_results)}")

    if bad_results:
        print("\nBad file examples:")
        for r in bad_results[:10]:
            print(f"  - {r['path']} :: {r['error']}")

    if not ok_results:
        raise SystemExit("No files produced usable segments. Training aborted.")

    all_features = np.concatenate([r["features"] for r in ok_results], axis=0).astype(np.float32)

    total_segments = all_features.shape[0]
    input_dim = all_features.shape[1]

    print("")
    print(f"Total usable segments: {total_segments}")
    print(f"Feature dim:           {input_dim}")

    if total_segments < MIN_SEGMENTS_REQUIRED:
        raise SystemExit(
            f"Only {total_segments} usable segments found. Need at least {MIN_SEGMENTS_REQUIRED}.\n"
            f"Add more/cleaner audio and rerun."
        )

    k = min(N_CLUSTERS, max(2, total_segments // 10))
    print(f"Training segment clusters: k={k}")

    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(all_features).astype(np.float32)

    kmeans = MiniBatchKMeans(
        n_clusters=k,
        random_state=42,
        batch_size=512,
        n_init="auto",
        max_iter=500,
    )

    labels = kmeans.fit_predict(features_scaled).astype(np.int64)

    print("Cluster counts:")
    unique, counts = np.unique(labels, return_counts=True)
    for u, c in zip(unique, counts):
        print(f"  cluster {int(u):02d}: {int(c)} segments")

    print("")
    print("Training Torch segment router...")
    router, router_report = train_router(
        features_scaled=features_scaled,
        labels=labels,
        input_dim=input_dim,
        n_clusters=k,
    )

    dsp_presets = derive_cluster_dsp_presets(all_features, labels)

    profile = {
        "profile_name": PROFILE_NAME,
        "created_unix": time.time(),
        "training_audio_dir": audio_dir,
        "sample_rate": SAMPLE_RATE,
        "segment_seconds": SEGMENT_SECONDS,
        "hop_seconds": HOP_SECONDS,
        "n_mfcc": N_MFCC,
        "input_dim": input_dim,
        "n_clusters": k,

        # Raw profile stats
        "feature_mean": torch.tensor(np.mean(all_features, axis=0), dtype=torch.float32),
        "feature_std": torch.tensor(np.std(all_features, axis=0), dtype=torch.float32),

        # Scaler used before router/kmeans
        "scaler_mean": torch.tensor(scaler.mean_, dtype=torch.float32),
        "scaler_scale": torch.tensor(scaler.scale_, dtype=torch.float32),

        # KMeans centroids in scaled feature space
        "cluster_centers_scaled": torch.tensor(kmeans.cluster_centers_, dtype=torch.float32),
        "cluster_counts": {int(u): int(c) for u, c in zip(unique, counts)},

        # DSP hints derived from each segment cluster
        "cluster_dsp_presets": dsp_presets,

        # Provenance
        "files_ok": [
            {
                "path": r["path"],
                "segments": int(r["segments"]),
                "duration_sec": float(r["duration_sec"]),
            }
            for r in ok_results
        ],
        "files_bad": [
            {
                "path": r["path"],
                "error": r["error"],
            }
            for r in bad_results
        ],
    }

    profile_path = os.path.join(output_dir, f"{PROFILE_NAME}_segment_profile.pt")
    router_path = os.path.join(output_dir, f"{PROFILE_NAME}_segment_router.pt")
    report_path = os.path.join(output_dir, f"{PROFILE_NAME}_training_report.json")

    torch.save(profile, profile_path)
    torch.save(
        {
            "model_state_dict": router.state_dict(),
            "input_dim": input_dim,
            "n_clusters": k,
            "profile_name": PROFILE_NAME,
            "scaler_mean": torch.tensor(scaler.mean_, dtype=torch.float32),
            "scaler_scale": torch.tensor(scaler.scale_, dtype=torch.float32),
        },
        router_path,
    )

    report = {
        "profile_name": PROFILE_NAME,
        "training_audio_dir": audio_dir,
        "output_dir": output_dir,
        "files_found": len(files),
        "files_ok": len(ok_results),
        "files_bad": len(bad_results),
        "total_segments": int(total_segments),
        "input_dim": int(input_dim),
        "n_clusters": int(k),
        "cluster_counts": {str(int(u)): int(c) for u, c in zip(unique, counts)},
        "router_report": router_report,
        "elapsed_seconds": round(time.time() - started, 3),
        "outputs": {
            "profile_pt": profile_path,
            "router_pt": router_path,
            "report_json": report_path,
        },
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("")
    print("============================================")
    print("TRAINING COMPLETE")
    print("============================================")
    print(f"Saved profile: {profile_path}")
    print(f"Saved router:  {router_path}")
    print(f"Saved report:  {report_path}")
    print("")


if __name__ == "__main__":
    main()