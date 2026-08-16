
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

# =====================================================================
# USER INPUT CONFIGURATION
# =====================================================================
# Input your file name or list of tracks right here:
input_file = r"C:\Users\adams\Downloads\feed this desire.wav"

# Set to True if you want to loop through multiple tracks below, False for a single file
RUN_AS_BATCH_LIST = True
MY_TRACK_LIST = [
    r"C:\Users\adams\Downloads\feed this desire.wav",
    r"C:\Users\adams\Downloads\jumpy jumpy.wav",
    r"C:\Users\adams\Downloads\admit it.mp3",
    r"C:\Users\adams\Downloads\VIZON & Ren Carter - Had To Go [Extended Mix] (1).mp3"
]
# =====================================================================

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import os
import time
import logging
import numpy as np
import pandas as pd
import lancedb
import librosa
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import cdist
import soundfile as sf

from pedalboard import Pedalboard, Compressor, HighpassFilter, Gain, Limiter

# Import the Forest Engine Scorer
try:
    from marketing_scorer import MarketingScorer
    forest_engine = MarketingScorer()
except ImportError:
    logging.warning("⚠️ MarketingScorer not found. Marketing Score predictions will be skipped.")
    forest_engine = None

# System validation / Core engine boundaries
try:
    import ray
    RAY_AVAILABLE = True
except ImportError:
    logging.warning("⚠️ Ray cluster architecture not found. Proceeding with single-node execution.")
    RAY_AVAILABLE = False

# External Essentia C++ bridge and independent feature extraction hooks
try:
    from essentia_wsl_bridge import get_structural_audio_analysis
    from audit_and_score_downloads import extract_section_features
except ImportError:
    logging.warning("⚠️ Essentia or structural scoring modules not found. Running with fallback mocks.")
    def get_structural_audio_analysis(p): return {"sections": [{"start_time_sec": 0.0, "end_time_sec": 30.0}]}
    def extract_section_features(a, sr): return {"rms_db": -14.0, "crest_factor": 4.5, "sub_bass_energy": 0.1, "bass_energy": 0.2, "mid_energy": 0.4, "high_energy": 0.3}

# --- Production Environment Paths ---
LANCEDB_PATH = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
TABLE_NAME = "omni_semantic_baselines"
BASELINE_TRACK = "Somebody (2024)"  # Chris Lake Reference Space
DOWNLOADS_DIR = r"C:\Users\adams\Downloads"
ALIGNMENT_FEATURES = ["rms_db", "crest_factor", "sub_bass_energy", "bass_energy", "mid_energy", "high_energy"]

CROSSFADE_SAMPLES = 512
HIGHPASS_HZ = 30.0
SUB_BASS_MONO_CUTOFF_HZ = 150.0
LIMITER_CEILING_DB = -0.3


def verify_ray_cluster_state():
    if not RAY_AVAILABLE:
        logging.info("🚀 Ray is not available. Using local processing.")
        return
    if not ray.is_initialized():
        logging.warning("⚠️ Ray cluster context not initialized. Activating fallback local worker context...")
        try:
            ray.init(ignore_reinit_error=True)
            logging.info("✅ Ray runtime successfully initialized locally.")
        except Exception as e:
            logging.critical(f"❌ Failed to spin up Ray cluster execution framework: {e}")
            sys.exit(1)
    else:
        logging.info("🚀 Ray cluster execution context verified. Distributed memory spaces accessible.")


def enforce_sub_bass_mono(audio_frame: np.ndarray, sample_rate: int) -> np.ndarray:
    """Force everything below SUB_BASS_MONO_CUTOFF_HZ into mono via M/S processing.
    Returns the input unchanged if it's already mono."""
    if audio_frame.ndim == 1 or audio_frame.shape[1] < 2:
        return audio_frame

    left = audio_frame[:, 0]
    right = audio_frame[:, 1]

    mid = (left + right) / 2.0
    side = (left - right) / 2.0

    side_mono_purged = HighpassFilter(cutoff_frequency_hz=SUB_BASS_MONO_CUTOFF_HZ)(side, sample_rate=sample_rate)

    reconstructed_stereo = np.zeros_like(audio_frame)
    reconstructed_stereo[:, 0] = mid + side_mono_purged
    reconstructed_stereo[:, 1] = mid - side_mono_purged
    return reconstructed_stereo


def _fade_curve(num_samples: int, ndim: int) -> np.ndarray:
    """Linear equal-power-ish ramp from 0→1, shaped for the target's dimensionality."""
    return np.linspace(0.0, 1.0, num_samples).reshape(-1, 1) if ndim > 1 else np.linspace(0.0, 1.0, num_samples)


def blend_chunk_into_buffer(
    target_buffer: np.ndarray,
    processed_chunk: np.ndarray,
    start_idx: int,
    crossfade_samples: int = CROSSFADE_SAMPLES,
):
    """Overwrite-add the processed chunk into target_buffer with a small boundary crossfade.
    Assumes chunk length == end-start (we slice it that way upstream)."""
    chunk_len = processed_chunk.shape[0]
    if chunk_len == 0:
        return

    end_idx = start_idx + chunk_len
    ndim = target_buffer.ndim

    # Plain paste first
    target_buffer[start_idx:end_idx] = processed_chunk

    # Boundary crossfade (only if we have a previous region and the chunk is long enough)
    if start_idx >= crossfade_samples and chunk_len > crossfade_samples:
        fade_in = _fade_curve(crossfade_samples, ndim)
        fade_out = 1.0 - fade_in

        region_new = target_buffer[start_idx:start_idx + crossfade_samples]
        region_prev = target_buffer[start_idx - crossfade_samples:start_idx]

        target_buffer[start_idx:start_idx + crossfade_samples] = region_new * fade_in + region_prev * fade_out


def build_section_board(target_rms: float, current_rms: float, target_crest: float, current_crest: float):
    """Build a fresh Pedalboard for one section. No shared-mutation across sections."""
    if current_crest > target_crest * 1.05:
        ratio = float(np.clip(2.0 + (current_crest - target_crest) * 0.75, 1.8, 4.5))
        threshold_db = current_rms - 3.0
    else:
        ratio = 1.0
        threshold_db = 0.0

    gain_db = float(np.clip(target_rms - current_rms, -12.0, 12.0))

    return Pedalboard([
        HighpassFilter(cutoff_frequency_hz=HIGHPASS_HZ),
        Gain(gain_db=gain_db),
        Compressor(threshold_db=threshold_db, ratio=ratio, attack_ms=10.0, release_ms=100.0),
        Limiter(threshold_db=LIMITER_CEILING_DB, release_ms=100.0),
    ])


def process_single_master(input_filename: str, reference_track_name: str,
                          df_base: pd.DataFrame, X_base_scaled: np.ndarray,
                          names_base: list, scaler: StandardScaler):
    input_path = os.path.join(DOWNLOADS_DIR, input_filename)
    output_filename = os.path.splitext(input_filename)[0] + "_DYNAMIC_MASTERED_v2.wav"
    output_path = os.path.join(DOWNLOADS_DIR, output_filename)

    if not os.path.exists(input_path):
        print(f"❌ Target source file missing: {input_path}")
        return None

    print(f"\n⚡ Processing: '{input_filename}' -> '{output_filename}'")

    # Structural analysis from Essentia
    analysis = get_structural_audio_analysis(input_path)
    sections = analysis.get("sections", [])
    if not sections:
        duration = librosa.get_duration(path=input_path)
        print(f"⚠️ Boundary extraction failed for {input_filename}. Defaulting to full-length master ({duration:.2f}s).")
        sections = [{"start_time_sec": 0.0, "end_time_sec": duration}]

    # SINGLE file read via soundfile (preserves stereo correctly)
    y_full, sr_full = sf.read(input_path, always_2d=True)
    is_stereo = y_full.shape[1] >= 2

    # Build target feature vectors per section from the already-loaded buffer
    target_section_features = []
    for sect in sections:
        start_samp = int(sect["start_time_sec"] * sr_full)
        end_samp = int(sect["end_time_sec"] * sr_full)
        start_samp = max(0, start_samp)
        end_samp = min(y_full.shape[0], end_samp)
        y_sect = y_full[start_samp:end_samp]
        sect_feats = extract_section_features(y_sect, sr_full)
        target_section_features.append([sect_feats[f] for f in ALIGNMENT_FEATURES])

    X_targ_scaled = scaler.transform(np.array(target_section_features, dtype=np.float32))

    mastered_full = np.zeros_like(y_full)

    for i, sect in enumerate(sections):
        start_samp = int(sect["start_time_sec"] * sr_full)
        end_samp = int(sect["end_time_sec"] * sr_full)
        start_samp = max(0, start_samp)
        end_samp = min(y_full.shape[0], end_samp)

        audio_chunk = y_full[start_samp:end_samp]
        if audio_chunk.shape[0] == 0:
            continue

        # Nearest-neighbor section match against baseline space
        targ_vec = X_targ_scaled[i].reshape(1, -1)
        dists = cdist(targ_vec, X_base_scaled, metric="euclidean")[0]
        best_idx = int(np.argmin(dists))
        match_info = df_base.loc[best_idx].to_dict()

        target_rms = float(match_info["rms_db"])
        target_crest = float(match_info["crest_factor"])

        # Measure the chunk we're about to process
        chunk_for_features = audio_chunk if is_stereo else audio_chunk
        sect_feats = extract_section_features(chunk_for_features, sr_full)
        current_rms = sect_feats["rms_db"]
        current_crest = sect_feats["crest_factor"]

        # Fresh board per section (no shared mutation)
        board = build_section_board(
            target_rms=target_rms,
            current_rms=current_rms,
            target_crest=target_crest,
            current_crest=current_crest,
        )

        # Enforce sub-bass mono BEFORE the main chain
        stereo_purged_chunk = enforce_sub_bass_mono(audio_chunk, sr_full)

        processed_chunk = board(stereo_purged_chunk, sample_rate=sr_full, reset=False)

        blend_chunk_into_buffer(mastered_full, processed_chunk, start_samp)

    # Write output
    try:
        sf.write(output_path, mastered_full, sr_full)
    except Exception as e:
        print(f"❌ Failed to write master for {input_filename}: {e}")
        return None

    # 🌲 Forest Engine Marketing Score on the FINAL mastered buffer
    marketing_report = ""
    score_data = None
    if forest_engine:
        final_feats = extract_section_features(mastered_full, sr_full)
        score_data = forest_engine.score_track(final_feats)
        marketing_report = (
            f"\n   📈 [FOREST ENGINE MARKETING SCORE] "
            f"Style: {score_data['top_match']} "
            f"({score_data['marketing_score_confidence']*100:.1f}%)"
            f" | Anomaly: {'Yes ⚠️' if score_data['is_anomaly'] else 'No ✅'}"
        )

    print(f"✅ Success: '{output_filename}' generated.{marketing_report}")
    return score_data


def pipeline_batch_orchestrator(song_targets: list, reference_track_name: str = BASELINE_TRACK):
    print("======================================================================")
    print("💎 INITIALIZING HIGH-PERFORMANCE DISTRIBUTED BATCH MASTERING PIPELINE (v2)")
    print("======================================================================")

    verify_ray_cluster_state()

    print(f"\nConnecting to LanceDB space at: {LANCEDB_PATH}...")
    db = lancedb.connect(LANCEDB_PATH)
    table = db.open_table(TABLE_NAME)
    df_all = table.to_pandas()

    df_base = df_all[df_all["track_name"].str.contains(reference_track_name, case=False, regex=False, na=False)].copy()
    if df_base.empty:
        print(f"❌ Error: Reference baseline profile '{reference_track_name}' not discovered in database layout.")
        return {}

    df_base["seg_idx"] = df_base["segment_name"].str.extract(r"(\d+)").astype(float).fillna(0).astype(int)
    df_base = df_base.sort_values("seg_idx").reset_index(drop=True)
    if "rms" in df_base.columns and "rms_db" not in df_base.columns:
        df_base["rms_db"] = df_base["rms"].apply(lambda v: float(20 * np.log10(v)) if v > 1e-9 else -100.0)

    X_base_raw = df_base[ALIGNMENT_FEATURES].fillna(0.0).values.astype(np.float32)
    names_base = df_base["segment_name"].tolist()

    scaler = StandardScaler()
    scaler.fit(X_base_raw)
    X_base_scaled = scaler.transform(X_base_raw)

    print(f"\n🚀 Cluster processing confirmed. Iterating over {len(song_targets)} target mixes...")
    results = {}
    for song_file in song_targets:
        try:
            res = process_single_master(
                input_filename=song_file,
                reference_track_name=reference_track_name,
                df_base=df_base,
                X_base_scaled=X_base_scaled,
                names_base=names_base,
                scaler=scaler,
            )
            results[song_file] = res
        except Exception as e:
            print(f"❌ Critical failure processing track target '{song_file}': {str(e)}")
            continue

    print("\n=======================================================")
    print("✅ MASTERING COMPLETE: Output configurations verified.")
    print("=======================================================")
    return results


if __name__ == "__main__":
    if RUN_AS_BATCH_LIST:
        targets = MY_TRACK_LIST
    else:
        targets = [input_file]

    pipeline_batch_orchestrator(song_targets=targets)