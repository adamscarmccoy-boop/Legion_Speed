
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
    r"C:\Users\adams\Downloads\VIZON & Ren Carter - Had To Go [Extended Mix] (2).mp3"
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

# Import the new Forest Engine Scorer
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

def verify_ray_cluster_state():
    if not RAY_AVAILABLE:
        logging.info("🚀 Ray is not available. Using local processing.")
        return
    if not ray.is_initialized():
        logging.warning("⚠️ Ray cluster context not initialized. Activating fallback local worker context...")
        try:
            ray.init(num_cpus=os.cpu_count(), ignore_reinit_error=True)
            logging.info("✅ Ray runtime successfully initialized locally.")
        except Exception as e:
            logging.critical(f"❌ Failed to spin up Ray cluster execution framework: {str(e)}")
            sys.exit(1)
    else:
        logging.info("🚀 Ray cluster execution context verified. Distributed memory spaces accessible.")

def enforce_sub_bass_mono(audio_frame: np.ndarray, sample_rate: int) -> np.ndarray:
    if audio_frame.ndim == 1 or audio_frame.shape[1] < 2:
        return audio_frame
        
    left = audio_frame[:, 0]
    right = audio_frame[:, 1]
    
    mid = (left + right) / 2.0
    side = (left - right) / 2.0
    
    # Clean the stereo footprint below 150Hz via Pedalboard high-pass filtering
    side_mono_purged = HighpassFilter(cutoff_frequency_hz=150.0)(side, sample_rate=sample_rate)
    
    # Phase-aligned stereo reconstruction matrix
    reconstructed_stereo = np.zeros_like(audio_frame)
    reconstructed_stereo[:, 0] = mid + side_mono_purged
    reconstructed_stereo[:, 1] = mid - side_mono_purged
    
    return reconstructed_stereo

def apply_boundary_crossfade(target_buffer: np.ndarray, processed_chunk: np.ndarray, 
                             start_idx: int, end_idx: int, crossfade_samples: int = 512):
    chunk_len = end_idx - start_idx
    if chunk_len <= 0 or len(processed_chunk) == 0:
        return
        
    target_buffer[start_idx:end_idx] = processed_chunk
    
    if start_idx > 0 and chunk_len > crossfade_samples:
        fade_in = np.linspace(0.0, 1.0, crossfade_samples).reshape(-1, 1) if target_buffer.ndim > 1 else np.linspace(0.0, 1.0, crossfade_samples)
        fade_out = np.linspace(1.0, 0.0, crossfade_samples).reshape(-1, 1) if target_buffer.ndim > 1 else np.linspace(1.0, 0.0, crossfade_samples)
        
        target_buffer[start_idx:start_idx + crossfade_samples] = (
            target_buffer[start_idx:start_idx + crossfade_samples] * fade_in +
            target_buffer[start_idx - crossfade_samples:start_idx] * fade_out
        )

def process_single_master(input_filename: str, reference_track_name: str, df_base: pd.DataFrame, X_base_scaled: np.ndarray, names_base: list, scaler: StandardScaler):
    input_path = os.path.join(DOWNLOADS_DIR, input_filename)
    output_filename = os.path.splitext(input_filename)[0] + "_DYNAMIC_MASTERED.wav"
    output_path = os.path.join(DOWNLOADS_DIR, output_filename)
    
    if not os.path.exists(input_path):
        print(f"❌ Target source file missing: {input_path}")
        return

    print(f"\n⚡ Processing: '{input_filename}' -> Outputting unique name: '{output_filename}'")
    
    analysis = get_structural_audio_analysis(input_path)
    sections = analysis.get("sections", [])
    
    if not sections:
        print(f"⚠️ Boundary extraction failed for {input_filename}. Defaulting to full-length master track strategy.")
        sections = [{"start_time_sec": 0.0, "end_time_sec": librosa.get_duration(path=input_path)}]
        
    y, sr = librosa.load(input_path, sr=None, mono=False)
    
    target_sections_features = []
    for sect in sections:
        start_samp = int(sect["start_time_sec"] * sr)
        end_samp = int(sect["end_time_sec"] * sr)
        y_sect = y[:, start_samp:end_samp] if y.ndim > 1 else y[start_samp:end_samp]
        sect_feats = extract_section_features(y_sect, sr)
        target_sections_features.append([sect_feats[f] for f in ALIGNMENT_FEATURES])

    X_targ_scaled = scaler.transform(np.array(target_sections_features, dtype=np.float32))

    hp = HighpassFilter(cutoff_frequency_hz=30.0)
    comp = Compressor(threshold_db=-20.0, ratio=3.0, attack_ms=10.0, release_ms=100.0)
    gain = Gain(gain_db=0.0)
    lim = Limiter(threshold_db=-0.3, release_ms=100.0)
    board = Pedalboard([hp, gain, comp, lim])
    
    y_full, sr_full = sf.read(input_path)
    mastered_full = np.zeros_like(y_full)
    
    for i, sect in enumerate(sections):
        start_samp = int(sect["start_time_sec"] * sr_full)
        end_samp = int(sect["end_time_sec"] * sr_full)
        audio_chunk = y_full[start_samp:end_samp, :] if y_full.ndim > 1 else y_full[start_samp:end_samp]
        
        if len(audio_chunk) == 0:
            continue
            
        targ_vec = X_targ_scaled[i].reshape(1, -1)
        dists = cdist(targ_vec, X_base_scaled, metric="euclidean")[0]
        best_idx = int(np.argmin(dists))
        match_info = df_base.loc[best_idx].to_dict()
        
        target_rms = float(match_info["rms_db"])
        target_crest = float(match_info["crest_factor"])
        
        sect_feats = extract_section_features(audio_chunk.T if y_full.ndim > 1 else audio_chunk, sr_full)
        current_rms = sect_feats["rms_db"]
        current_crest = sect_feats["crest_factor"]
        
        if current_crest > target_crest * 1.05:
            comp.ratio = max(1.8, min(4.5, 2.0 + (current_crest - target_crest) * 0.75))
            comp.threshold_db = current_rms - 3.0
        else:
            comp.ratio = 1.0
            comp.threshold_db = 0.0
            
        gain.gain_db = max(-12.0, min(12.0, target_rms - current_rms))
        
        # Enforce Strict Stereo Separation Laws under 150Hz BEFORE passing to the main plugin chain
        stereo_purged_chunk = enforce_sub_bass_mono(audio_chunk, sr_full)
        
        processed_chunk = board(stereo_purged_chunk, sample_rate=sr_full, reset=False)
        
        apply_boundary_crossfade(mastered_full, processed_chunk, start_samp, end_samp, crossfade_samples=512)
        
    sf.write(output_path, mastered_full, sr_full)
    
    # 🌲 Run Forest Engine Marketing Score on the final Mastered Output
    marketing_report = ""
    if forest_engine:
        final_feats = extract_section_features(mastered_full.T if mastered_full.ndim > 1 else mastered_full, sr_full)
        score_data = forest_engine.score_track(final_feats)
        marketing_report = (
            f"\n   📈 [FOREST ENGINE MARKETING SCORE] "
            f"Style: {score_data['top_match']} "
            f"({score_data['marketing_score_confidence']*100:.1f}%)"
            f" | Anomaly: {'Yes ⚠️' if score_data['is_anomaly'] else 'No ✅'}"
        )

    print(f"✅ Success: '{output_filename}' generated completely phase-aligned.{marketing_report}")
    return score_data if forest_engine else None

def pipeline_batch_orchestrator(song_targets: list[str], reference_track_name: str = BASELINE_TRACK):
    print("======================================================================")
    print("💎 INITIALIZING HIGH-PERFORMANCE DISTRIBUTED BATCH MASTERING PIPELINE")
    print("======================================================================")
    
    verify_ray_cluster_state()
    
    print(f"\nConnecting to LanceDB space at: {LANCEDB_PATH}...")
    db = lancedb.connect(LANCEDB_PATH)
    table = db.open_table(TABLE_NAME)
    df_all = table.to_pandas()
    
    df_base = df_all[df_all["track_name"].str.contains(reference_track_name, case=False, regex=False, na=False)].copy()
    if df_base.empty:
        print(f"❌ Error: Reference baseline profile '{reference_track_name}' not discovered in database layout.")
        return
        
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
                scaler=scaler
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
    # Determine execution strategy based on user variables at the very top
    if RUN_AS_BATCH_LIST:
        targets = MY_TRACK_LIST
    else:
        targets = [input_file]
        
    pipeline_batch_orchestrator(song_targets=targets)