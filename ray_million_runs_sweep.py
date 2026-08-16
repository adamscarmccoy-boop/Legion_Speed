import os
import sys
import time
import pandas as pd
import numpy as np

# =============================================================================
# 1. CLUSTER INITIALIZATION
# =============================================================================
# Attempt importing Ray and ONNX Runtime safely
try:
    import ray
    import onnxruntime as ort
except ImportError:
    print("[-] Missing distributed runtime packages. Ensure 'pip install ray onnxruntime pandas pyarrow' is run locally.")
    sys.exit(1)

# Configurable workspace paths matching your Windows layout
WORKSPACE_C = r"C:\WEB CASE STUDY"
ONNX_MODEL_PATH = os.path.join(WORKSPACE_C, "mastered_output", "code_genome_brain.onnx")
PARQUET_PATH = os.path.join(WORKSPACE_C, "code_knowledge_audit.parquet")

# Fallback directories for sandbox or execution verification
if not os.path.exists(WORKSPACE_C):
    WORKSPACE_C = os.getcwd()
    ONNX_MODEL_PATH = os.path.join(WORKSPACE_C, "code_genome_brain.onnx")
    PARQUET_PATH = os.path.join(WORKSPACE_C, "code_knowledge_audit.parquet")

# =============================================================================
# 2. RAY PARALLEL SWEEP ACTOR
# =============================================================================
@ray.remote(num_cpus=0.5)
class HighFrequencySweepActor:
    """
    Stateful actor that holds an in-memory session of the ONNX model 
    and streams brute-force permutations without disk or network boundaries.
    """
    def __init__(self, model_bytes: bytes):
        # Initialize ONNX directly from in-memory bytes to bypass disk access bottlenecks
        self.session = ort.InferenceSession(model_bytes, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        self.output_names = [out.name for out in self.session.get_outputs()]

    def run_permutation_sweep(self, base_features: np.ndarray, duration_sec: float) -> tuple:
        """
        Runs random permutations on the features array for a set duration,
        calculating forward passes on ONNX in a tight loop.
        """
        run_count = 0
        results_accumulator = []
        
        start_time = time.perf_counter()
        end_time = start_time + duration_sec
        
        num_records = len(base_features)
        if num_records == 0:
            return 0, []

        # Convert to float32 matrix for high-speed tensor feeding
        features_matrix = np.array(base_features, dtype=np.float32)

        while time.perf_counter() < end_time:
            # AOT Mutation: Slightly perturb input features (size, lines, extension, source)
            # to simulate testing different pipeline configurations
            perturbations = np.random.uniform(0.9, 1.1, size=features_matrix.shape).astype(np.float32)
            mutated_batch = features_matrix * perturbations
            
            # Sub-millisecond forward pass over the batch
            raw_outputs = self.session.run(self.output_names, {self.input_name: mutated_batch})
            
            # Capture predicted classes (first output tensor)
            predictions = raw_outputs[0]
            run_count += num_records
            
            # Periodically log best-performing configurations to keep memory footprint tiny
            if run_count % 10000 == 0:
                results_accumulator.append({
                    "timestamp": time.time(),
                    "total_processed": run_count,
                    "avg_prediction": float(np.mean(predictions))
                })

        return run_count, results_accumulator

# =============================================================================
# 3. MASTER RUNNER & TELEMETRY
# =============================================================================
def main():
    print("=" * 80)
    print("⚡ HIGH-FREQUENCY AOT CLUSTER SWEEP: 20-SECOND BRUTE FORCE TRIAL")
    print("   Running multi-node parallel executions over your Parquet & ONNX data")
    print("=" * 80)

    # A. Ingest the Columnar Parquet File (AOT In-Memory)
    print("\n📥 [Step 1/4] Ingesting Parquet audit records...")
    if os.path.exists(PARQUET_PATH):
        df = pd.read_parquet(PARQUET_PATH)
        print(f"✅ Loaded existing Parquet: {len(df)} file records.")
    else:
        print("⚠️  No local code_knowledge_audit.parquet found. Generating high-density mock dataset...")
        # Generate 1,000 synthetic files to simulate a massive project codebase
        mock_data = {
            "size_kb": np.random.uniform(1.0, 500.0, 1000),
            "rows": np.random.randint(10, 5000, 1000).astype(float),
            "encoded_ext": np.random.randint(0, 5, 1000).astype(float),
            "encoded_source": np.random.randint(0, 2, 1000).astype(float)
        }
        df = pd.DataFrame(mock_data)
        print(f"✅ Spawned mock telemetry: {len(df)} records.")

    # Format the features array: [size_kb, rows, encoded_ext, encoded_source]
    base_features = df[["size_kb", "rows", "encoded_ext", "encoded_source"]].to_numpy()

    # B. Read the pre-compiled ONNX Model into memory
    print("\n🔮 [Step 2/4] Reading pre-compiled ONNX graph model...")
    if os.path.exists(ONNX_MODEL_PATH):
        with open(ONNX_MODEL_PATH, "rb") as f:
            model_bytes = f.read()
        print(f"✅ ONNX model read successfully ({len(model_bytes) / 1024:.1f} KB).")
    else:
        print("❌ [CRITICAL] ONNX Model file not found on disk at target locations.")
        print(f"   Missing: {ONNX_MODEL_PATH}")
        print("   Please make sure your ONNX file is uploaded to the workspace.")
        sys.exit(1)

    # C. Start or Connect to the Ray Cluster
    print("\n📡 [Step 3/4] Connecting to the distributed Ray GCS registry...")
    try:
        # Attaches to your local cluster; falls back to spawning an in-process worker mesh if needed
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        print("✅ Attached to live, high-performance Ray scheduler.")
    except Exception as e:
        print(f"[-] Node connection bypassed: {e}. Spawning in-process cluster workers...")
        ray.init(namespace="legion", ignore_reinit_error=True)
        print("✅ Local cluster context established.")

    # D. Deploy actors & dispatch parallel workers
    print("\n🚀 [Step 4/4] Deploying actors and starting 20-second countdown...")
    
    # We load-balance across 4 parallel actors to saturate logical CPU threads
    num_actors = 4
    run_duration_seconds = 20.0
    
    # Put the model bytes into the shared object store once to save worker IPC bandwidth
    model_ref = ray.put(model_bytes)
    base_features_ref = ray.put(base_features)

    actors = [HighFrequencySweepActor.remote(model_ref) for _ in range(num_actors)]

    print(f"🔥 Dispatched {num_actors} parallel workers. Sweeping configurations for exactly {run_duration_seconds} seconds...")
    start_t = time.perf_counter()

    # Fire off the asynchronous remote tasks
    futures = [
        actor.run_permutation_sweep.remote(base_features_ref, run_duration_seconds)
        for actor in actors
    ]

    # Block until all parallel sweep actors complete their countdown
    results = ray.get(futures)
    end_t = time.perf_counter()
    actual_duration = end_t - start_t

    # Aggregate outputs
    total_inferences = sum(res[0] for res in results)
    throughput = total_inferences / actual_duration

    print("\n" + "=" * 80)
    print("🏁 20-SECOND REAL-TIME TRIAL RESULTS:")
    print("=" * 80)
    print(f"📊 Total Successful Inferences Run : {total_inferences:,}")
    print(f"🕰️  Actual Execution Time           : {actual_duration:.2f} seconds")
    print(f"🚀 Combined Cluster Throughput     : {throughput:,.2f} inferences/second")
    print(f"📈 Estimated 1-Minute Capacity      : {throughput * 60:,.0f} trial iterations")
    print("=" * 80)
    
    # Clean up Ray connection
    ray.shutdown()

if __name__ == "__main__":
    main()
