import os
import json
import subprocess
import librosa
import numpy as np
import time
import ray
import pandas as pd
from pydantic import BaseModel
from typing import List, Optional

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


class StemAudit(BaseModel):
    stem_type: str
    file: str
    rms_db: float
    crest_factor: float
    spectral_centroid: float
    sub_bass_energy: float
    bass_energy: float
    mid_energy: float
    high_energy: float
    chris_lake_ref_rms: Optional[float] = None
    chris_lake_ref_crest: Optional[float] = None
    rms_delta: float
    crest_delta: float
    recommendation: str

class AuditReportData(BaseModel):
    track_filename: str
    demucs_separation_duration_sec: float
    stems_audit: List[StemAudit]

# Inject FFmpeg into PATH (installed via winget, needs shell restart to auto-detect)
_ffmpeg_path = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links")
if os.path.exists(_ffmpeg_path) and _ffmpeg_path not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _ffmpeg_path + os.pathsep + os.environ.get("PATH", "")

DEMUCS_BRIDGE = r"C:\WEB CASE STUDY\demucs_bridge.py"

# --- Configuration Paths ---
DOWNLOADS_DIR = r"C:\Users\adams\Downloads"
ASSETS_DIR = r"C:\WEB CASE STUDY\Acoustic-DNA-Audio-Engine\assets"
SEPARATED_DIR = r"C:\STUDIES_BACKUP\separated_stems"
PYTHON_FRESH = r"c:\STUDIES_BACKUP\.venv_fresh\Scripts\python.exe" # Path to Python with Demucs installed

# Ensure assets folder exists
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(SEPARATED_DIR, exist_ok=True)

# --- Ray Initialization (ensure it's running detached) ---
LEGION_NAMESPACE = "legion"
if not ray.is_initialized():
    try:
        ray.init(address="auto", namespace=LEGION_NAMESPACE, ignore_reinit_error=True)
        print(f"Connected to Ray cluster (namespace: {LEGION_NAMESPACE}).")
    except Exception as e:
        print(f"Failed to connect to Ray cluster: {e}. Ensure 'ray start --head --dashboard-port 8265' is running.")
        exit(1)

# --- Ray Actor for Knowledge Registry Access ---
@ray.remote
class RegistryClient:
    def __init__(self):
        self.registry = ray.get_actor("SwarmKnowledgeRegistry", namespace=LEGION_NAMESPACE)
        print("RegistryClient connected to SwarmKnowledgeRegistry.")

    def get_table(self, table_name: str):
        return ray.get(self.registry.get_table.remote(table_name))

# --- Ray Remote Task for Parallel Stem Feature Extraction ---
@ray.remote
def extract_stem_features_ray(file_path: str, stem_type: str, ref_stem_data: dict) -> dict:
    """
    Extracts acoustic features from a given stem file and compares them
    against a reference stem profile, returning actionable recommendations.
    """
    if not os.path.exists(file_path):
        return {"error": f"File {file_path} not found"}

    y, sr = librosa.load(file_path, sr=22050, mono=True) # Always load mono for core feature analysis

    # Standard RMS
    rms = librosa.feature.rms(y=y)
    avg_rms = np.mean(rms)
    rms_db = 20 * np.log10(avg_rms) if avg_rms > 1e-9 else -100.0

    # Peak & Crest Factor
    peak = np.max(np.abs(y))
    crest_factor = peak / avg_rms if avg_rms > 1e-9 else 0.0

    # Frequency energy bands
    S = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)

    # Sum magnitudes within bands
    sub_bass_energy = float(np.sum(S[(freqs >= 20) & (freqs < 60), :]))
    bass_energy = float(np.sum(S[(freqs >= 60) & (freqs < 250), :]))
    mid_energy = float(np.sum(S[(freqs >= 250) & (freqs < 2000), :]))
    high_energy = float(np.sum(S[freqs >= 2000, :]))

    spectral_centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))

    # Compute deltas against reference
    rms_delta = rms_db - ref_stem_data.get("rms_db", -20.0) # Default ref if missing
    crest_delta = crest_factor - ref_stem_data.get("crest_factor", 4.0)
    centroid_delta = spectral_centroid - ref_stem_data.get("spectral_centroid", 2000.0) # Default ref if missing

    # --- Generate Corrective Recommendation ---
    recommendation = []
    if rms_delta > 3.0:
        recommendation.append(f"Reduce {stem_type} gain by {abs(rms_delta):.1f} dB.")
    elif rms_delta < -3.0:
        recommendation.append(f"Increase {stem_type} gain by {abs(rms_delta):.1f} dB.")

    if crest_delta < -1.5:
        recommendation.append(f"{stem_type} too compressed/squashed. Reduce limiter/compressor ratio.")
    elif crest_delta > 1.5:
        recommendation.append(f"{stem_type} too dynamic. Add light compression.")

    if sub_bass_energy < ref_stem_data.get("sub_bass_energy", 1000) * 0.5:
        recommendation.append(f"{stem_type} sub-bass is weak. Check low-end filtering or phase.")
    elif sub_bass_energy > ref_stem_data.get("sub_bass_energy", 1000) * 1.5:
        recommendation.append(f"{stem_type} sub-bass is too dominant. Apply a highpass filter.")
        
    if high_energy < ref_stem_data.get("high_energy", 1000) * 0.5 and stem_type in ["DRUMS", "OTHER"]:
        recommendation.append(f"{stem_type} high-end is dull. Add a high-shelf boost around 8-12 kHz.")
    elif high_energy > ref_stem_data.get("high_energy", 1000) * 1.5 and stem_type in ["DRUMS", "OTHER"]:
        recommendation.append(f"{stem_type} high-end is harsh. Apply a high-shelf cut around 8-12 kHz.")

    if not recommendation:
        recommendation.append("Sonic signature aligns well with Chris Lake baseline. Good mix!")

    return {
        "stem_type": stem_type,
        "file": os.path.basename(file_path),
        "rms_db": float(rms_db),
        "crest_factor": float(crest_factor),
        "spectral_centroid": spectral_centroid,
        "sub_bass_energy": sub_bass_energy,
        "bass_energy": bass_energy,
        "mid_energy": mid_energy,
        "high_energy": high_energy,
        "chris_lake_ref_rms": ref_stem_data.get("rms_db"),
        "chris_lake_ref_crest": ref_stem_data.get("crest_factor"),
        "rms_delta": rms_delta,
        "crest_delta": crest_delta,
        "recommendation": ". ".join(recommendation).strip()
    }

def run_mix_audit_agent(stereo_mix_filepath: str, reference_artist: str = "Chris Lake") -> str:
    """
    Automates the mix auditing process by separating stems, analyzing their acoustic features,
    and comparing them against a chosen reference artist's baseline (e.g., Chris Lake).
    Provides actionable recommendations for mix corrections.
    """
    track_path = os.path.abspath(stereo_mix_filepath)
    if not os.path.exists(track_path):
        return f"[ERROR] Stereo mix file not found at: {track_path}"

    print(f"\n=======================================================")
    print(f" MIX AUDIT AGENT INITIATED FOR: {os.path.basename(track_path)}")
    print(f"  Reference Artist: {reference_artist}")
    print(f"=======================================================")

    # Initialize RegistryClient actor
    registry_client = RegistryClient.remote()

    # Load Chris Lake Stem Baselines from SwarmKnowledgeRegistry
    # The 'chrislake_stems_duckdb' table holds pre-calculated stem features
    print(f"Loading {reference_artist} stem baselines from SwarmKnowledgeRegistry...")
    try:
        chris_lake_stems_table = ray.get(registry_client.get_table.remote("chrislake_stems_duckdb"))
        df_cl_stems = chris_lake_stems_table.to_pandas()
        CL_STEMS = {row["drum_type"]: row for idx, row in df_cl_stems.iterrows()}
        print(f"Loaded {len(CL_STEMS)} reference stem profiles.")
    except Exception as e:
        return f"[ERROR] Failed to load reference stem baselines from SwarmKnowledgeRegistry: {e}"

    # Default fallback references if specific types are missing or for generic 'OTHER'
    default_ref_bass = {"rms_db": -12, "crest_factor": 3.5, "sub_bass_energy": 5000, "bass_energy": 15000, "mid_energy": 500, "high_energy": 100, "spectral_centroid": 1000}
    default_ref_drums = {"rms_db": -10, "crest_factor": 2.8, "sub_bass_energy": 3000, "bass_energy": 10000, "mid_energy": 1000, "high_energy": 2000, "spectral_centroid": 2500}
    default_ref_vocals = {"rms_db": -9, "crest_factor": 4.0, "sub_bass_energy": 50, "bass_energy": 200, "mid_energy": 5000, "high_energy": 1500, "spectral_centroid": 3500}
    default_ref_other = {"rms_db": -14, "crest_factor": 5.0, "sub_bass_energy": 100, "bass_energy": 1000, "mid_energy": 2000, "high_energy": 1000, "spectral_centroid": 2800}

    # Step 1: Split Stems using Demucs bridge (bypasses torchcodec/torchaudio)
    print("\n[STEP 1] Separating stems via Demucs bridge (soundfile loader)...")
    t_start_demucs = time.perf_counter()

    cmd = [PYTHON_FRESH, DEMUCS_BRIDGE, track_path, SEPARATED_DIR]

    try:
        res = subprocess.run(cmd, capture_output=False, text=True, check=True, timeout=900)
        print(f"Demucs split completed in {time.perf_counter() - t_start_demucs:.1f} seconds.")
    except subprocess.CalledProcessError as e:
        return f"[ERROR] Demucs bridge failed (exit code {e.returncode})"
    except FileNotFoundError:
        return f"[ERROR] Python executable not found at {PYTHON_FRESH}."
    except Exception as e:
        return f"[ERROR] Unexpected error during stem separation: {e}"

    # Step 2: Locate separated stems (bridge saves to SEPARATED_DIR/track_name/)
    song_folder_name = os.path.splitext(os.path.basename(track_path))[0]
    stems_output_dir = os.path.join(SEPARATED_DIR, song_folder_name)

    if not os.path.exists(stems_output_dir):
        return f"[ERROR] Could not find stems folder at: {stems_output_dir}"

    print(f"Found separated stems at: {stems_output_dir}")

    # Step 3: Run parallel feature extraction and comparison
    print("\n[STEP 2] Launching parallel Ray workers for stem analysis...")
    stem_mappings = {
        "bass.wav": ("BASS", CL_STEMS.get("BASS", default_ref_bass)),
        "drums.wav": ("DRUMS", CL_STEMS.get("DRUMS", default_ref_drums)),
        "other.wav": ("OTHER", CL_STEMS.get("OTHER", default_ref_other)), # melodic elements
        "vocals.wav": ("VOCALS", CL_STEMS.get("VOCALS", default_ref_vocals))
    }
    
    ray_tasks = []
    for stem_file, (stem_type, ref_data) in stem_mappings.items():
        stem_path = os.path.join(stems_output_dir, stem_file)
        if os.path.exists(stem_path):
            task_ref = extract_stem_features_ray.remote(stem_path, stem_type, ref_data)
            ray_tasks.append(task_ref)
        else:
            print(f" Missing expected stem file: {stem_path}. Skipping analysis for {stem_type}.")
            
    # Gather results in parallel
    print("Gathering results from Ray workers...")
    all_stem_results = ray.get(ray_tasks)

    audit_report_data = {
        "track_filename": os.path.basename(track_path),
        "demucs_separation_duration_sec": time.perf_counter() - t_start_demucs,
        "stems_audit": []
    }

    print("\n--- Stem Audit Report ---")
    for res in all_stem_results:
        if "error" not in res:
            audit_report_data["stems_audit"].append(res)
            print(f"\n[ {res['stem_type']} Stem Analysis]")
            print(f"  - Current RMS: {res['rms_db']:.2f} dB (Ref: {res['chris_lake_ref_rms']:.2f} dB)")
            print(f"  - Current Crest: {res['crest_factor']:.2f} (Ref: {res['chris_lake_ref_crest']:.2f})")
            print(f"  - Energy (Sub/Bass/Mid/High): {res['sub_bass_energy']:.0f}/{res['bass_energy']:.0f}/{res['mid_energy']:.0f}/{res['high_energy']:.0f}")
            print(f"  - Recommendation: {res['recommendation']}")
        else:
            print(f"[ERROR] Stem analysis failed for a task: {res['error']}")
            
    # Save Report
    output_report_path = os.path.join(ASSETS_DIR, f"{os.path.basename(track_path)}_mix_audit_report.json")
    try:
        report_model = AuditReportData(
            track_filename=audit_report_data["track_filename"],
            demucs_separation_duration_sec=float(audit_report_data["demucs_separation_duration_sec"]),
            stems_audit=[StemAudit(**res) for res in audit_report_data["stems_audit"]]
        )
        with open(output_report_path, 'w', encoding='utf-8') as f:
            f.write(report_model.model_dump_json(indent=4))
    except Exception as save_err:
        print(f"[WARNING] Pydantic serialization failed: {save_err}. Falling back to float coercion.")
        def coerce_value(d):
            if isinstance(d, dict):
                return {k: coerce_value(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [coerce_value(v) for v in d]
            elif isinstance(d, (np.float32, np.float64, np.single, np.double)):
                return float(d)
            elif isinstance(d, (np.int32, np.int64)):
                return int(d)
            return d
        with open(output_report_path, 'w', encoding='utf-8') as f:
            json.dump(coerce_value(audit_report_data), f, indent=4)

    return f" Mix Audit Report generated and saved to: {output_report_path}"

if __name__ == "__main__":
    # Test with a sample stereo mix
    TEST_STEREO_MIX = r"C:\Users\adams\Downloads\putting in the work.wav" # Replace with your actual mix
    
    if not os.path.exists(TEST_STEREO_MIX):
        print(f"TEST ERROR: Input stereo mix not found at {TEST_STEREO_MIX}. Please update the path.")
    else:
        report_message = run_mix_audit_agent(TEST_STEREO_MIX, reference_artist="Chris Lake")
        print(report_message)

    # Clean up Ray actors (silently, they may not be named actors)
    try:
        ray.kill(ray.get_actor("RegistryClient", namespace=LEGION_NAMESPACE))
    except Exception:
        pass
    print("Done.")