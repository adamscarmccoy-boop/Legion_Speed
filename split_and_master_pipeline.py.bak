import os
import json
import subprocess
import librosa
import numpy as np
import time
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


# Paths
DOWNLOADS_DIR = r"C:\Users\adams\Downloads"
ASSETS_DIR = r"C:\WEB CASE STUDY\Acoustic-DNA-Audio-Engine\assets"
SEPARATED_DIR = r"C:\STUDIES_BACKUP\separated_stems"
PYTHON_FRESH = r"c:\STUDIES_BACKUP\.venv_fresh\Scripts\python.exe"
CHRIS_LAKE_STEMS_FILE = r"c:\WEB CASE STUDY\data\chrislake_stems_duckdb.json"
OUTPUT_REPORT = os.path.join(ASSETS_DIR, "stem_separation_mastering_report.json")

# Ensure assets folder exists
os.makedirs(ASSETS_DIR, exist_ok=True)

# 1. Ray remote task for parallel feature extraction
@ray.remote
def extract_stem_features_ray(file_path, drum_type, ref_stem_data):
    if not os.path.exists(file_path):
        return {"error": f"File {file_path} not found"}
        
    y, sr = librosa.load(file_path, sr=22050, mono=True)
    
    # Standard RMS
    rms = librosa.feature.rms(y=y)
    avg_rms = np.mean(rms)
    rms_db = 20 * np.log10(avg_rms) if avg_rms > 0 else -100.0
    
    # Peak & Crest
    peak = np.max(np.abs(y))
    crest_factor = peak / avg_rms if avg_rms > 0 else 0.0
    
    # Frequency energy bands
    S = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)
    
    sub_bass = np.sum(S[(freqs >= 20) & (freqs < 60), :])
    bass = np.sum(S[(freqs >= 60) & (freqs < 250), :])
    mids = np.sum(S[(freqs >= 250) & (freqs < 2000), :])
    highs = np.sum(S[freqs >= 2000, :])
    
    centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
    
    # Compute deltas against reference
    rms_delta = float(rms_db) - ref_stem_data["rms_db"]
    crest_delta = float(crest_factor) - ref_stem_data["crest_factor"]
    centroid_delta = centroid - ref_stem_data["spectral_centroid"]
    
    # Calculate corrective recommendation
    recommendation = ""
    if rms_delta > 3.0:
        recommendation += f"Reduce gain by {abs(rms_delta):.1f} dB. "
    elif rms_delta < -3.0:
        recommendation += f"Increase gain by {abs(rms_delta):.1f} dB. "
        
    if crest_delta < -1.5:
        recommendation += "Too squashed. Reduce limiter/compressor ratio. "
    elif crest_delta > 1.5:
        recommendation += "Too dynamic. Add light compression. "
        
    if centroid_delta > 300:
        recommendation += "High frequencies too dominant. Add high shelf cut. "
    elif centroid_delta < -300:
        recommendation += "Dull high end. Brighten with high shelf boost."
        
    if not recommendation:
        recommendation = "Sonic signature matches Chris Lake baseline! Perfect mix."
        
    return {
        "drum_type": drum_type,
        "file": os.path.basename(file_path),
        "rms_db": float(rms_db),
        "crest_factor": float(crest_factor),
        "spectral_centroid": centroid,
        "chris_lake_ref_rms": ref_stem_data["rms_db"],
        "chris_lake_ref_crest": ref_stem_data["crest_factor"],
        "rms_delta": rms_delta,
        "crest_delta": crest_delta,
        "recommendation": recommendation.strip()
    }

def run_pipeline(target_filename):
    track_path = os.path.join(DOWNLOADS_DIR, target_filename)
    if not os.path.exists(track_path):
        print(f"[ERROR] Track not found at: {track_path}")
        return
        
    print(f"\n==========================================")
    print(f"PROCESSING TRACK (RAY ACTIVE): {target_filename}")
    print(f"==========================================")
    
    # Load Chris Lake Stem Baselines
    with open(CHRIS_LAKE_STEMS_FILE, 'r', encoding='utf-8') as f:
        CL_STEMS_RAW = json.load(f)
    CL_STEMS = {s["drum_type"]: s for s in CL_STEMS_RAW}
    
    # Step 1: Initial Full Track Audit
    print("\n[STEP 1] Auditing full track...")
    y_full, sr_full = librosa.load(track_path, sr=22050, mono=True)
    full_rms = float(20 * np.log10(np.mean(librosa.feature.rms(y=y_full))))
    print(f"  - Loudness: {full_rms:.2f} dB RMS")
    
    # Step 2: Split Stems using Demucs from the external venv
    print("\n[STEP 2] Splitting track into stems via Demucs (running in .venv_fresh)...")
    t_start = time.perf_counter()
    
    cmd = [
        PYTHON_FRESH,
        "-m", "demucs.separate",
        "-o", SEPARATED_DIR,
        track_path
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[ERROR] Demucs split failed: {res.stderr}")
        return
        
    split_duration = time.perf_counter() - t_start
    print(f"Demucs split completed in {split_duration:.1f} seconds.")
    
    # Step 3: Locate separated stems
    song_folder_name = os.path.splitext(target_filename)[0]
    stems_folder = os.path.join(SEPARATED_DIR, "htdemucs", song_folder_name)
    
    # Fallback search
    if not os.path.exists(stems_folder):
        htdemucs_dir = os.path.join(SEPARATED_DIR, "htdemucs")
        folders = [d for d in os.listdir(htdemucs_dir) if os.path.isdir(os.path.join(htdemucs_dir, d))]
        for folder in folders:
            if song_folder_name.lower() in folder.lower() or folder.lower() in song_folder_name.lower():
                stems_folder = os.path.join(htdemucs_dir, folder)
                break
                
    if not os.path.exists(stems_folder):
        print(f"[ERROR] Could not find separated stems folder at: {stems_folder}")
        return
        
    print(f"Found stems folder at: {stems_folder}")
    
    # Step 4: Boot Ray cluster and run parallel feature extraction
    print("\n[STEP 4] Initializing local Ray cluster for parallel stem analysis...")
    ray.init(ignore_reinit_error=True, log_to_driver=False)
    
    stem_files = {
        "bass.wav": ("BASS", CL_STEMS["BASS"]),
        "drums.wav": ("DRUMS", CL_STEMS["DRUMS"]),
        "other.wav": ("FULL_TRACK", CL_STEMS["FULL_TRACK"]), # other maps to melodic synths
        "vocals.wav": ("VOCALS", CL_STEMS["VOCALS"])
    }
    
    ray_tasks = []
    print("Launching parallel Ray workers for each stem...")
    for stem_file, (drum_type, ref_data) in stem_files.items():
        stem_path = os.path.join(stems_folder, stem_file)
        if os.path.exists(stem_path):
            # Queue Ray task
            task_ref = extract_stem_features_ray.remote(stem_path, drum_type, ref_data)
            ray_tasks.append(task_ref)
            
    # Gather results in parallel
    print("Gathering results from Ray workers...")
    ray_results = ray.get(ray_tasks)
    
    stem_results = {}
    for res in ray_results:
        if "error" not in res:
            dtype = res["drum_type"]
            stem_results[dtype] = res
            print(f"  [{dtype} Stem Analyzed]")
            print(f"    - RMS Delta: {res['rms_delta']:+.2f} dB (vs {res['chris_lake_ref_rms']:.2f})")
            print(f"    - Recommendation: {res['recommendation']}")
            
    # Shut down Ray
    ray.shutdown()
    
    # Save Report
    final_output = {
        "track": target_filename,
        "full_track_rms": full_rms,
        "stem_separation_ms": split_duration * 1000,
        "stems_analysis": stem_results
    }
    
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=4)
        
    print(f"\nSovereign Ray Stem Audit report successfully saved to:")
    print(f"  {OUTPUT_REPORT}")

if __name__ == "__main__":
    # Target come n get it.wav for separation and mastering comparison
    run_pipeline("come n get it.wav")