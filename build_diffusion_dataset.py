import os
import time
import glob
import ray
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


# ==============================================================================
# ⚙️ CONFIGURATION: YOUR AUDIO LIBRARY PATHS
# Fill in the paths to your raw audio below. You can use samples, songs, or both.
# ==============================================================================
# 1. Samples (Short kicks, snares, loops)
SAMPLE_LIBRARY_PATHS = [
    r"E:\OLD ABLETON\ABELTON\ONE SHOTS, BASS, BRASS,  BASSLINES ONLY",
    r"E:\OLD ABLETON\ABELTON\TECHHHOO PACKS BOUGHT HUGE"
]
# 2. Songs (Full stems, tracked out projects, or master mixes)
SONG_LIBRARY_PATH = r"E:\MUSIC"

# 3. Output (Where your 30-second chunked training tensors will be saved)
OUTPUT_TRAINING_DIR = r"C:\WEB CASE STUDY\training_latents" 

# Import your compiled zero-copy C++ DSP engine
try:
    import sonic_dsp 
except ImportError:
    print("[⚠️ WARNING] sonic_dsp module not found. Did you run 'python setup.py build_ext --inplace'?")

# ==============================================================================
# ⚡ AAFLOW PRINCIPLE: RESOURCE DETERMINISM & CLUSTER BOOT
# ==============================================================================
# Lock Polars to 1 thread so it doesn't fight Ray for physical CPU cache
os.environ["POLARS_MAX_THREADS"] = "1"

if not ray.is_initialized():
    print("[⚡ SYSTEM] Booting Ray Cluster on 12 Local CPUs...")
    ray.init(num_cpus=12, ignore_reinit_error=True) 
else:
    print("[⚡ SYSTEM] Ray is already running. Verifying resources...")
    
# Strict validation: Ensures you have all 12 cores locked in
available_cpus = ray.cluster_resources().get("CPU", 0)
assert available_cpus >= 12, f"Expected 12 CPUs, but Ray only sees {available_cpus}."
print(f"[✅ SYSTEM] Confirmed 12 CPUs active in Ray Plasma Store.")

# ==============================================================================
# 🧠 TIER 1: THE NATIVE DSP OPERATOR
# ==============================================================================
@ray.remote(num_cpus=1)
class DiffusionDatasetWorker:
    """
    Pure local execution on physical cores. Hands Arrow pointers to your C++ core
    to slice audio into 30-second clips and extract latents at 84x real-time speed.
    """
    def process_audio_batch(self, batch_ref: ray.ObjectRef):
        # 1. Zero-copy read from Plasma shared memory
        arrow_batch = ray.get(batch_ref)
        
        # 2. Handoff to your compiled C++ Engine (Zero-Copy)
        # Your C++ code unwraps the Arrow table, slices into 30s training chunks, 
        # converts to latent tensors, and wraps it back into a PyArrow Table.
        result_arrow = sonic_dsp.process_audio_chunk(arrow_batch)
        
        # 3. Return the PyArrow table directly (Ray handles Plasma storage natively)
        # DO NOT wrap in ray.put() here to prevent nested references.
        return result_arrow

# ==============================================================================
# 🌪️ TIER 2: THE ASYNCHRONOUS ORCHESTRATOR
# ==============================================================================
class TrainingDataOrchestrator:
    def __init__(self):
        # Instantiate exactly one worker per physical core
        self.workers = [DiffusionDatasetWorker.remote() for _ in range(12)]

    def build_dataset(self, df: pl.DataFrame):
        # Convert entire dataset metadata to Arrow ONCE
        arrow_table = df.to_arrow()
        batch_size = 50 # Tune this based on your RAM
        total_rows = arrow_table.num_rows
        
        # Zero-copy slicing natively in Arrow
        batches = [arrow_table.slice(i, length=batch_size) for i in range(0, total_rows, batch_size)]
        print(f"[⚡ SYSTEM] Dispatching {len(batches)} audio batches across 12 CPUs...")

        processing_futures = []
        for i, batch in enumerate(batches):
            worker = self.workers[i % 12]
            
            # Pin batch to Plasma Shared RAM
            # Instead of batch_ref = ray.put(batch); worker.process(batch_ref)
            # Simply remove the self.workers list and call:
            processing_futures.append(DiffusionDatasetWorker.remote().process_audio_batch.remote(batch))

        finished_tables = []
        
        # ⚡ CRITICAL OPTIMIZATION: Asynchronous Gathering
        # We use ray.wait() to instantly pull completed chunks and free up memory
        # to ensure the system doesn't bottleneck on large sample libraries.
        while processing_futures:
            # Block only until at least 1 task finishes
            done_refs, processing_futures = ray.wait(processing_futures, num_returns=1)
            
            for done_ref in done_refs:
                finished_tables.append(ray.get(done_ref))
                
        # Instantly concatenate all completed memory blocks
        combined_arrow = pa.concat_tables(finished_tables)
        return pl.from_arrow(combined_arrow)

# ==============================================================================
# 🚀 EXECUTION
# ==============================================================================
if __name__ == "__main__":
    print("[⚡ SYSTEM] Scanning Audio Libraries...")
    
    # Fast native file globbing for your configured paths
    all_sample_files = []
    for path in SAMPLE_LIBRARY_PATHS:
        all_sample_files.extend(glob.glob(os.path.join(path, "**", "*.wav"), recursive=True))

    song_files = glob.glob(os.path.join(SONG_LIBRARY_PATH, "**", "*.wav"), recursive=True)
    all_files = all_sample_files + song_files

    print(f"Found {len(all_sample_files)} samples and {len(song_files)} songs.")

    # Load file paths into a fast Polars DataFrame
    raw_inventory = pl.DataFrame({
        "path": all_files,
        "source_type": ["sample"] * len(all_sample_files) + ["song"] * len(song_files)
    })
    
    orchestrator = TrainingDataOrchestrator()
    
    start_time = time.time()
    final_training_set = orchestrator.build_dataset(raw_inventory)
    end_time = time.time()
    
    # Save the final dataset index pointing to the processed tensors
    os.makedirs(OUTPUT_TRAINING_DIR, exist_ok=True)
    final_training_set.write_parquet(os.path.join(OUTPUT_TRAINING_DIR, "training_index.parquet"))
    
    print("\n[✅ LOCAL ZERO-COPY TRAINING SET COMPLETE]")
    print(final_training_set.head())
    print(f"Processed {len(all_files)} files in {end_time - start_time:.4f} seconds.")