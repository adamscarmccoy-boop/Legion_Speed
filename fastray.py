
import os
import ray
import time
import polars as pl
import pyarrow as pa

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


# 1. RESOURCE DETERMINISM: Prevent Polars from fighting Ray for CPU threads
os.environ["POLARS_MAX_THREADS"] = "1"

# 2. RAY 12-WORKER CONFIRMATION & STARTUP
if not ray.is_initialized():
    print("[⚡ SYSTEM] Booting Ray Cluster on 12 Local CPUs...")
    # ignore_reinit_error prevents crashes if a background Ray instance is lingering
    ray.init(num_cpus=12, ignore_reinit_error=True) 
else:
    print("[⚡ SYSTEM] Ray is already running. Verifying resources...")
    
# Strict validation: Ensures you have all 12 cores locked in
available_cpus = ray.cluster_resources().get("CPU", 0)
assert available_cpus >= 12, f"Expected 12 CPUs, but Ray only sees {available_cpus}."
print(f"[✅ SYSTEM] Confirmed 12 CPUs active in Ray Plasma Store.")

### --- TIER 1: THE AUDIO PREPROCESSING OPERATORS ---
@ray.remote(num_cpus=1)
class AudioDatasetWorker:
    """
    Pure local execution on physical cores [3].
    This worker handles the heavy DSP chunking for your diffusion model.
    """
    def __init__(self):
        # Optional: You could load your base VAE or pedalboard instances here 
        # so they initialize exactly once per core.
        pass

    def process_audio_batch(self, batch_ref: ray.ObjectRef):
        # 1. Zero-copy read from Plasma shared memory [2]
        arrow_batch = ray.get(batch_ref)
        df_chunk = pl.from_arrow(arrow_batch)
        
        # 2. Execute Vectorized Audio Logic
        # (This is where you would normally call pedalboard/librosa to slice 
        # audio into exactly 30-second clips for ACE-Step/MusicGen training)
        df_result = df_chunk.with_columns(
            status=pl.lit("CHUNKED_FOR_DIFFUSION"),
            # Mocking a rule: filtering out files that are too small for training
            training_ready=pl.when(pl.col("size") > 1000).then(pl.lit(True)).otherwise(pl.lit(False))
        )
        
        # 3. CRITICAL FIX: Return the PyArrow table directly. 
        # DO NOT wrap in ray.put(). Ray handles the return via Plasma automatically [4].
        return df_result.to_arrow()

### --- TIER 2: THE ASYNCHRONOUS ORCHESTRATOR ---
class DiffusionDataOrchestrator:
    def __init__(self):
        # Instantiate exactly one worker per physical core
        self.workers = [AudioDatasetWorker.remote() for _ in range(12)]

    def build_dataset(self, df: pl.DataFrame):
        # Convert entire dataset to Arrow ONCE
        arrow_table = df.to_arrow()
        batch_size = 50 # Micro-batching chunk size for audio files
        total_rows = arrow_table.num_rows
        
        # Zero-copy slicing natively in Arrow
        batches = [arrow_table.slice(i, length=batch_size) for i in range(0, total_rows, batch_size)]
        print(f"[⚡ SYSTEM] Dispatching {len(batches)} audio batches across 12 CPUs...")

        processing_futures = []
        for i, batch in enumerate(batches):
            worker = self.workers[i % 12]
            
            # Pin batch to Plasma Shared RAM
            batch_ref = ray.put(batch) 
            processing_futures.append(worker.process_audio_batch.remote(batch_ref))

        finished_tables = []
        
        # ⚡ ASYNCHRONOUS GATHERING: Prevent Pipeline Stalling
        # We use ray.wait() to instantly pull completed chunks and free up memory [1, 5].
        while processing_futures:
            # Block only until at least 1 task finishes
            done_refs, processing_futures = ray.wait(processing_futures, num_returns=1)
            
            for done_ref in done_refs:
                finished_tables.append(ray.get(done_ref))
                
        # Instantly concatenate all completed memory blocks
        combined_arrow = pa.concat_tables(finished_tables)
        return pl.from_arrow(combined_arrow)

if __name__ == "__main__":
    # Simulated raw audio inventory from your "Architect" and "Producer" domains
    print("[⚡ SYSTEM] Loading Raw Audio Inventory...")
    raw_inventory = pl.DataFrame({ 
        "path": [
            r"C:\WEB CASE STUDY\raw_sessions\session_2025_01_05_37892\audio\01-16_808-Kick-03.wav", 
            r"C:\WEB CASE STUDY\raw_sessions\session_2025_01_05_37892\Ableton\Project.als", 
            r"C:\WEB CASE STUDY\raw_sessions\session_2025_01_05_37892\audio\01-17_808-Kick-04.wav   ",
            r"C:\WEB CASE STUDY\raw_sessions\session_2025_01_06_37893\audio\01-18_808-Kick-05.wav   ",
            r"C:\WEB CASE STUDY\raw_sessions\session_2025_01_06_37894\audio\01-19_808-Kick-06.wav   ",
            r"C:\WEB CASE STUDY\raw_sessions\session_2025_01_06_37895\audio\01-20_808-Kick-07.wav   ",
        ],  
        "size": [48000, 120000, 96000, 24000, 120000, 240000],
        "flatness": [0.54, 0.12, 0.33, 0.88] 
    })
    
    orchestrator = DiffusionDataOrchestrator()
    
    start_time = time.time()
    final_training_set = orchestrator.build_dataset(raw_inventory)
    end_time = time.time()
    
    print("\n[✅ LOCAL ZERO-COPY TRAINING SET COMPLETE]")
    print(final_training_set)
    print(f"Processed in {end_time - start_time:.4f} seconds at Zero-Copy speed.")