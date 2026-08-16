import os
import ray
import polars as pl
import pyarrow as pa
import sonic_dsp  # Your newly compiled zero-copy C++ engine

# 1. Prevent Polars from thrashing Ray's physical CPU scheduler
os.environ["POLARS_MAX_THREADS"] = "1"

if not ray.is_initialized():
    ray.init(num_cpus=12, ignore_reinit_error=True)

### --- LOCAL SPEED TIER: THE OPERATORS ---
@ray.remote(num_cpus=1)
class DSPAlignmentActor:
    """
    Pure local execution using the C++ pybind11 module.
    No LLMs, no network latency.
    """
    def process_arrow_batch(self, batch_ref: ray.ObjectRef):
        # 1. Zero-copy read from Plasma shared memory
        arrow_batch = ray.get(batch_ref)
        
        # 2. Pass the PyArrow table pointer directly to C++
        # The C++ module unwraps it, processes it, and returns an Arrow table [2]
        result_arrow = sonic_dsp.process_audio_chunk(arrow_batch)
        
        # 3. Return the PyArrow table directly (Ray handles Plasma storage natively)
        return result_arrow

### --- THE ASYNCHRONOUS ORCHESTRATOR ---
class LocalSwarmOrchestrator:
    def __init__(self):
        # Instantiate exactly one worker per physical core
        self.workers = [DSPAlignmentActor.remote() for _ in range(12)]

    def run_pipeline(self, df: pl.DataFrame):
        # Convert entire dataset to Arrow ONCE
        arrow_table = df.to_arrow()
        batch_size = 250 
        total_rows = arrow_table.num_rows
        
        # Zero-copy slicing natively in Arrow
        batches = [arrow_table.slice(i, length=batch_size) for i in range(0, total_rows, batch_size)]
        print(f"[⚡ SYSTEM] Dispatching {len(batches)} batches across 12 CPUs...")

        processing_futures = []
        for i, batch in enumerate(batches):
            worker = self.workers[i % 12]
            # Pin batch to Plasma Shared RAM
            batch_ref = ray.put(batch) 
            processing_futures.append(worker.process_arrow_batch.remote(batch_ref))

        finished_tables = []
        
        # ⚡ CRITICAL OPTIMIZATION: Asynchronous Gathering with ray.wait() [3]
        # We process completed chunks instantly and free up memory.
        while processing_futures:
            # Wait for exactly 1 task to finish [3]
            done_refs, processing_futures = ray.wait(processing_futures, num_returns=1)
            
            for done_ref in done_refs:
                finished_tables.append(ray.get(done_ref))
                
        # Instantly concatenate all completed memory blocks
        combined_arrow = pa.concat_tables(finished_tables)
        return pl.from_arrow(combined_arrow)

if __name__ == "__main__":
    # Native Polars ingestion (Bypassing slow Python list iteration)
    print("[SYSTEM] Loading Studio Inventory...")
import polars as pl

studio_inventory = pl.DataFrame({ 
    # Exactly 3 paths
    "path": [
        r"C:\WEB CASE STUDY\ray_category_results.json"
    ], 
    # Exactly 3 sizes (in bytes)
    "size": , 
    # Exactly 3 flatness scores
    "flatness": [0.54, 0.12, 0.33] 
})
import os
import glob
# pyrefly: ignore [missing-import]
import polars as pl

# 1. Grab all the actual files
all_files = glob.glob(r"C:\WEB CASE STUDY\**\*.wav  ", recursive=True)

# 2. Dynamically calculate sizes so the list lengths ALWAYS match perfectly
file_sizes = [os.path.getsize(f) for f in all_files]

# 3. Create the dataframe
studio_inventory = pl.DataFrame({
    "path": all_files,
    "size": file_sizes
})

print(f"Successfully loaded {   .height} files into the DataFrame.")        
                                "path": [ r"e:\music", r"C:\WEB CASE STUDY\Kick_Raw.wav", r"C:\Ableton\Projects\Synth_Line.als", r"C:\WEB CASE STUDY\Long_Take.wav"],
        "size": [1024*1024*1024*1024*1024*1024, 1024*1024*1024*1024*1024*1024, 1024*1024*1024*1024*1024*1024], 
        "flatness":  [0.54, 0.12, 0.33] 
    })
    
    orchestrator = LocalSwarmOrchestrator()
    final_output = orchestrator.run_pipeline(studio_inventory)
    
    print("\n[✅ LOCAL ZERO-COPY PIPELINE COMPLETE]")
    print(final_output)