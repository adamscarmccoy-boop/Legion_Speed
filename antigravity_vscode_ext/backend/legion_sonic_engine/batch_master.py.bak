import os
import time
import ray
from typing import Set, Dict, Any
from tqdm import tqdm # For progress bar

from legion_sonic_engine.utils import ensure_utf8_output, MasteringJobConfig
from legion_sonic_engine.mastering_agent_actor import MasteringAgentActor

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


# Configuration
WATCH_FOLDER = r"C:\Users\adams\Music\Mastering_Inputs" # Folder to watch for new audio files
OUTPUT_FOLDER = r"C:\Users\adams\Music\Mastering_Outputs" # Path to the exported Vector database, now strictly local to the extension backend
LANCEDB_PATH = os.path.join(os.path.dirname(__file__), "..", "lancedb_omni_snowflake_rag")
LANCEDB_TABLE_NAME = "sonic_engine_baselines"
DEFAULT_BASELINE_TRACK_NAME = "Chris Lake - Somebody (2024)" # Default baseline to use

FILE_EXTENSIONS = ('.wav', '.mp3', '.flac') # Supported audio file extensions
SCAN_INTERVAL_SEC = 10 # How often to scan the watch folder

# Initialize Ray if not already done
if not ray.is_initialized():
    ray.init(log_to_stdout=False)

ensure_utf8_output()

def create_folders_if_not_exists():
    """Ensures watch and output folders exist."""
    os.makedirs(WATCH_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print(f"✅ Watch folder: {WATCH_FOLDER}")
    print(f"✅ Output folder: {OUTPUT_FOLDER}")

def batch_master_watcher():
    """
    Watches a directory for new audio files and submits them for mastering
    via the Ray MasteringAgentActor.
    """
    create_folders_if_not_exists()

    mastering_agent = MasteringAgentActor.remote(LANCEDB_PATH, LANCEDB_TABLE_NAME)
    
    processed_files: Set[str] = set()
    active_jobs: Dict[ray.ObjectRef, str] = {} # Map object ref to original filename

    print(f"🚀 Starting Legion Batch Mastering Watcher. Scanning '{WATCH_FOLDER}' every {SCAN_INTERVAL_SEC} seconds...")
    print(f"    New files will be mastered against baseline: '{DEFAULT_BASELINE_TRACK_NAME}'")

    try:
        while True:
            # 1. Check for completed jobs
            completed_refs, pending_refs = ray.wait(list(active_jobs.keys()), timeout=0)
            for ref in completed_refs:
                filename = active_jobs.pop(ref)
                try:
                    result = ray.get(ref)
                    if result.get("status") == "success":
                        print(f"✅ Job completed for '{filename}': {result.get('output_file')}")
                    else:
                        print(f"❌ Job failed for '{filename}': {result.get('message')}")
                except Exception as e:
                    print(f"❌ Error retrieving result for '{filename}': {e}")
            
            # 2. Scan for new files
            current_files = set(
                f for f in os.listdir(WATCH_FOLDER) 
                if os.path.isfile(os.path.join(WATCH_FOLDER, f)) and f.lower().endswith(FILE_EXTENSIONS)
            )
            
            new_files = current_files - processed_files - set(active_jobs.values())
            
            if new_files:
                print(f"\n📁 Detected {len(new_files)} new audio files in '{WATCH_FOLDER}'. Submitting for mastering...")
                for filename in tqdm(list(new_files), desc="Submitting jobs"):
                    input_filepath = os.path.join(WATCH_FOLDER, filename)
                    output_filename = f"{os.path.splitext(filename)[0]}_MASTERED{os.path.splitext(filename)[1]}"
                    output_filepath = os.path.join(OUTPUT_FOLDER, output_filename)

                    job_config = MasteringJobConfig(
                        input_filepath=input_filepath,
                        output_filepath=output_filepath,
                        baseline_track_name=DEFAULT_BASELINE_TRACK_NAME,
                        segment_length_sec=6.0 # Can be configured
                    )
                    
                    try:
                        obj_ref = mastering_agent.adaptive_master_track.remote(job_config.model_dump())
                        active_jobs[obj_ref] = filename
                        print(f"  ⚡ Submitted '{filename}' for mastering.")
                        processed_files.add(filename) # Mark as processed once submitted
                    except Exception as e:
                        print(f"  ❌ Failed to submit '{filename}': {e}")
                        
            if not new_files and not active_jobs:
                print(f"💤 No new files detected and no active jobs. Waiting {SCAN_INTERVAL_SEC}s...", end='\r')

            time.sleep(SCAN_INTERVAL_SEC)

    except KeyboardInterrupt:
        print("\n👋 Legion Batch Mastering Watcher stopped by user.")
    except Exception as e:
        print(f"\nFatal error in watcher: {e}")

if __name__ == "__main__":
    batch_master_watcher()