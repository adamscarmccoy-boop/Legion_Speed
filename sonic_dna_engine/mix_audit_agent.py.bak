# mix_audit_agent.py
import os
import sys
import json
import subprocess
import time
import numpy as np
import librosa
import ray
import pandas as pd
from typing import Dict, Any, List, Optional

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


# --- Configuration Paths ---
DOWNLOADS_DIR = r"C:\Users\adams\Downloads" # Default location for input mix files
SEPARATED_STEMS_DIR = r"C:\STUDIES_BACKUP\separated_stems" # Output for Demucs
PYTHON_FRESH = r"c:\STUDIES_BACKUP\.venv_fresh\Scripts\python.exe" # Python executable for Demucs
# Use the full path for chrislake_stems_duckdb.json, typically processed into the registry
# For the audit, we assume the registry holds this data
CHRIS_LAKE_STEMS_TABLE_NAME = "chrislake_stems_duckdb"

# Ensure output directory for stems exists
os.makedirs(SEPARATED_STEMS_DIR, exist_ok=True)

# Ensure Ray is initialized for actor creation
if not ray.is_initialized():
    try:
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        print("Connected to existing Ray cluster.")
    except ConnectionError:
        print("No existing Ray cluster found. Spinning up a new local Ray cluster with strict memory limits...")
        ray.init(namespace="legion", object_store_memory=1500 * 1024 * 1024, _temp_dir=r"C:\tmp\ray", ignore_reinit_error=True, runtime_env={"env_vars": {"PYTHONPATH": r"c:\WEB CASE STUDY;c:\WEB CASE STUDY\sonic_dna_engine;c:\WEB CASE STUDY\antigravity_vscode_ext\backend"}})

# --- Ray Actor for Feature Extraction ---
@ray.remote
class StemFeatureExtractorActor:
    def __init__(self):
        print("StemFeatureExtractorActor initialized.")

    def extract_features(self, file_path: str) -> Dict[str, float]:
        """Extracts key acoustic features from a stem."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Stem file not found: {file_path}")
            
        y, sr = librosa.load(file_path, sr=22050, mono=True) # Downsample and mono for consistent feature extraction
        
        rms = librosa.feature.rms(y=y)
        avg_rms = np.mean(rms)
        rms_db = 20 * np.log10(avg_rms) if avg_rms > 0 else -100.0
        
        peak = np.max(np.abs(y))
        crest_factor = peak / avg_rms if avg_rms > 0 else 0.0
        
        S = np.abs(librosa.stft(y))
        freqs = librosa.fft_frequencies(sr=sr)
        
        sub_bass = np.sum(S[(freqs >= 20) & (freqs < 60), :])
        bass = np.sum(S[(freqs >= 60) & (freqs < 250), :])
        mids = np.sum(S[(freqs >= 250) & (freqs < 2000), :])
        highs = np.sum(S[freqs >= 2000, :])
        
        centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
        
        return {
            "rms_db": float(rms_db),
            "crest_factor": float(crest_factor),
            "spectral_centroid": centroid,
            "sub_bass_energy": float(sub_bass),
            "bass_energy": float(bass),
            "mid_energy": float(mids),
            "high_energy": float(highs)
        }

# --- Mix Audit Agent ---
class MixAuditAgent:
    def __init__(self):
        self.registry = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
        self.feature_extractor = StemFeatureExtractorActor.options(name="StemFeatureExtractorActor", namespace="legion", lifetime="detached").remote()
        print("MixAuditAgent initialized, connected to SwarmKnowledgeRegistry and StemFeatureExtractorActor.")

    def _get_chris_lake_baselines(self) -> Dict[str, Dict[str, float]]:
        """Retrieves Chris Lake stem baselines from the SwarmKnowledgeRegistry."""
        try:
            chris_lake_stems_arrow = ray.get(self.registry.get_table.remote(CHRIS_LAKE_STEMS_TABLE_NAME))
            df_cl_stems = chris_lake_stems_arrow.to_pandas()
            
            baselines = {}
            for _, row in df_cl_stems.iterrows():
                baselines[row["drum_type"]] = {
                    "rms_db": row["rms_db"],
                    "crest_factor": row["crest_factor"],
                    "spectral_centroid": row["spectral_centroid"],
                    "sub_bass_energy": row["sub_bass_energy"],
                    "bass_energy": row["bass_energy"],
                    "mid_energy": row["mid_energy"],
                    "high_energy": row["high_energy"]
                }
            print(f"Loaded {len(baselines)} Chris Lake stem baselines from registry.")
            return baselines
        except Exception as e:
            print(f"ERROR: Failed to load Chris Lake stem baselines from registry: {e}", file=sys.stderr)
            return {}

    def _run_demucs_separation(self, mix_filepath: str, output_dir: str) -> Optional[str]:
        """Executes Demucs for stem separation."""
        print(f"Running Demucs for stem separation on: {os.path.basename(mix_filepath)}...")
        t_start = time.perf_counter()
        
        # Ensure output directory for Demucs exists
        demucs_output_root = os.path.join(output_dir, "htdemucs")
        os.makedirs(demucs_output_root, exist_ok=True) # Demucs will create subfolders

        cmd = [
            PYTHON_FRESH,
            "-m", "demucs.separate",
            "-o", output_dir, # Demucs creates a 'htdemucs' subfolder here
            "--name", os.path.splitext(os.path.basename(mix_filepath))[0], # Name the output folder after the track
            mix_filepath
        ]
        
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=600) # 10 min timeout
            split_duration = time.perf_counter() - t_start
            print(f"Demucs split completed in {split_duration:.1f} seconds. Output:\n{res.stdout}")

            # Find the actual output folder created by Demucs
            song_folder_name = os.path.splitext(os.path.basename(mix_filepath))[0]
            stem_output_path = os.path.join(demucs_output_root, song_folder_name)
            if not os.path.exists(stem_output_path): # Fallback logic if Demucs names it differently
                potential_folders = [d for d in os.listdir(demucs_output_root) if os.path.isdir(os.path.join(demucs_output_root, d))]
                for folder in potential_folders:
                    if song_folder_name.lower() in folder.lower() or folder.lower() in song_folder_name.lower():
                        stem_output_path = os.path.join(demucs_output_root, folder)
                        break
            
            if not os.path.exists(stem_output_path):
                raise FileNotFoundError(f"Demucs output folder not found at expected path: {stem_output_path}")

            return stem_output_path
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Demucs split failed (return code {e.returncode}): {e.stderr}", file=sys.stderr)
            return None
        except subprocess.TimeoutExpired:
            print(f"ERROR: Demucs split timed out after 600 seconds.", file=sys.stderr)
            return None
        except Exception as e:
            print(f"ERROR: An unexpected error occurred during Demucs separation: {e}", file=sys.stderr)
            return None

    def audit_mix(self, mix_filepath: str) -> Dict[str, Any]:
        """
        Audits a stereo mix, separates stems, and provides actionable mix corrections.
        """
        print(f"\n==========================================")
        print(f"🚀 INITIATING MIX AUDIT FOR: {os.path.basename(mix_filepath)}")
        print(f"==========================================")

        if not os.path.exists(mix_filepath):
            return {"status": "FAILED", "error": f"Mix file not found: {mix_filepath}"}
        
        baselines = self._get_chris_lake_baselines()
        if not baselines:
            return {"status": "FAILED", "error": "Could not load Chris Lake baselines. Audit cannot proceed."}

        # 1. Separate stems
        stems_folder = self._run_demucs_separation(mix_filepath, SEPARATED_STEMS_DIR)
        if not stems_folder:
            return {"status": "FAILED", "error": "Stem separation failed. Check Demucs installation/paths."}
        
        # 2. Extract features from each stem in parallel using Ray actor
        stem_types_to_process = {
            "drums.wav": "DRUMS",
            "bass.wav": "BASS",
            "vocals.wav": "VOCALS",
            "other.wav": "OTHER" # Mapping 'other' stem to 'OTHER' in baseline
        }
        
        feature_extraction_tasks = []
        for stem_file, stem_type in stem_types_to_process.items():
            stem_path = os.path.join(stems_folder, stem_file)
            if os.path.exists(stem_path):
                feature_extraction_tasks.append(self.feature_extractor.extract_features.remote(stem_path))
            else:
                print(f"WARNING: Stem file not found: {stem_path}. Skipping analysis for {stem_type}.", file=sys.stderr)
        
        print(f"Launching {len(feature_extraction_tasks)} parallel stem feature extraction tasks...")
        all_stem_features = ray.get(feature_extraction_tasks)

        # 3. Compare and generate recommendations
        audit_results = {}
        for stem_idx, features in enumerate(all_stem_features):
            stem_type_key = list(stem_types_to_process.values())[stem_idx] # Crude way to map back
            
            if stem_type_key not in baselines:
                print(f"WARNING: No baseline found for {stem_type_key}. Skipping recommendation.", file=sys.stderr)
                audit_results[stem_type_key] = {"status": "NO_BASELINE", "features": features}
                continue

            ref_features = baselines[stem_type_key]
            recommendations = []

            # RMS (Loudness)
            rms_delta = features["rms_db"] - ref_features["rms_db"]
            if rms_delta > 2.0:
                recommendations.append(f"Reduce {stem_type_key} gain by {abs(rms_delta):.1f} dB to match baseline loudness.")
            elif rms_delta < -2.0:
                recommendations.append(f"Increase {stem_type_key} gain by {abs(rms_delta):.1f} dB to match baseline loudness.")
            
            # Crest Factor (Dynamics/Punch)
            crest_delta = features["crest_factor"] - ref_features["crest_factor"]
            if crest_delta > 1.0:
                recommendations.append(f"The {stem_type_key} is too dynamic ({features['crest_factor']:.1f} vs {ref_features['crest_factor']:.1f}). Apply light compression with ratio 2:1 and threshold {features['rms_db'] - 3.0:.1f} dB.")
            elif crest_delta < -1.0:
                recommendations.append(f"The {stem_type_key} is too squashed ({features['crest_factor']:.1f} vs {ref_features['crest_factor']:.1f}). Reduce compressor ratio or increase threshold.")

            # Spectral Centroid (Brightness)
            centroid_delta = features["spectral_centroid"] - ref_features["spectral_centroid"]
            if centroid_delta > 300: # 300 Hz is a noticeable difference
                recommendations.append(f"The {stem_type_key} is too bright. Apply a high-shelf EQ cut around 8-10 kHz by {abs(centroid_delta/300):.1f} dB.")
            elif centroid_delta < -300:
                recommendations.append(f"The {stem_type_key} is dull. Apply a high-shelf EQ boost around 8-10 kHz by {abs(centroid_delta/300):.1f} dB.")

            # Sub-Bass Energy (Critical for drums/bass)
            if stem_type_key in ["DRUMS", "BASS"]:
                sub_bass_delta = features["sub_bass_energy"] - ref_features["sub_bass_energy"]
                # This is a very rough comparison; proper comparison needs normalized energy
                if sub_bass_delta < -500: # Significant deficit
                     recommendations.append(f"Critically low sub-bass energy in {stem_type_key}. Check phase alignment or boost sub frequencies around 40-60 Hz.")
                elif sub_bass_delta > 500: # Too much sub
                    recommendations.append(f"Excessive sub-bass energy in {stem_type_key}. Apply a gentle high-pass filter around 30 Hz or reduce gain below 60 Hz.")
            
            audit_results[stem_type_key] = {
                "analyzed_features": features,
                "baseline_features": ref_features,
                "recommendations": recommendations if recommendations else ["Mix matches baseline metrics. Excellent work!"],
                "status": "AUDITED"
            }
        
        final_report = {
            "track_name": os.path.basename(mix_filepath),
            "audit_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "overall_status": "COMPLETED",
            "stem_audit_results": audit_results
        }

        print(f"\n✅ Mix Audit Complete for {os.path.basename(mix_filepath)}. Report generated.")
        print(f"==========================================")
        return final_report

if __name__ == "__main__":
    # --- DEMO ---
    # Ensure a test WAV file exists in your Downloads directory for separation
    # E.g., copy "come n get it.wav" to C:\Users\adams\Downloads
    TEST_MIX_FILE = r"C:\Users\adams\Downloads\come n get it.wav" # Adjust path as needed

    if not os.path.exists(TEST_MIX_FILE):
        print(f"ERROR: Test mix file not found at '{TEST_MIX_FILE}'. Please ensure it exists.")
        sys.exit(1)

    # Instantiate the agent
    agent = MixAuditAgent()

    print("--- Running Mix Audit Agent Demo ---")
    audit_report = agent.audit_mix(TEST_MIX_FILE)

    print("\n--- Generated Mix Audit Report (JSON) ---")
    print(json.dumps(audit_report, indent=4))

    # Example of how to iterate and print recommendations
    print("\n--- Actionable Recommendations Summary ---")
    for stem_type, data in audit_report.get("stem_audit_results", {}).items():
        print(f"\n[{stem_type}]")
        for rec in data.get("recommendations", []):
            print(f" - {rec}")

    # To ensure detached actors clean up (optional, Ray handles this mostly)
    # ray.shutdown()