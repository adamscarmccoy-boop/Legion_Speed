import os
import sys
import time
import glob
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

# =============================================================================
# 1. FAULT-TOLERANT CLUSTER INITIALIZATION
# =============================================================================
try:
    import ray
    import onnxruntime as ort
except ImportError:
    print("[-] Missing required packages. Please run: pip install ray onnxruntime pandas pyarrow scikit-learn")
    sys.exit(1)

# Target Windows workspaces
WORKSPACE_C = r"C:\WEB CASE STUDY"
WORKSPACE_STUDIES = r"C:\STUDIES"

# Fallback for local sandbox execution
if not os.path.exists(WORKSPACE_C):
    WORKSPACE_C = os.getcwd()
if not os.path.exists(WORKSPACE_STUDIES):
    WORKSPACE_STUDIES = os.getcwd()

# =============================================================================
# 2. FAULT-PROTECTED RAY SWEEP ACTOR
# =============================================================================
@ray.remote(num_cpus=0.5, max_restarts=-1, max_task_retries=-1)
class HighFrequencySweepActor:
    """
    Robust stateful actor executing high-frequency brute-force ONNX sweeps.
    Fully isolated with individual try-catch blocks to prevent cluster-wide crashes.
    """
    def __init__(self, model_bytes: bytes, model_name: str, expected_features: int):
        self.model_name = model_name
        self.expected_features = expected_features
        self.initialized = False
        try:
            # Load the model directly from shared memory bytes to avoid disk bottleneck
            self.session = ort.InferenceSession(model_bytes, providers=["CPUExecutionProvider"])
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [out.name for out in self.session.get_outputs()]
            self.initialized = True
        except Exception as e:
            print(f"❌ [ACTOR ERROR] Failed to initialize model {model_name}: {e}")

    def run_permutation_sweep(self, base_features: np.ndarray, duration_sec: float) -> dict:
        """
        Runs high-speed mutation sweeps on input arrays for a set time limit.
        """
        if not self.initialized:
            return {"runs": 0, "status": "UNINITIALIZED", "error": "Model failed startup"}

        run_count = 0
        results_accumulator = []
        
        start_time = time.perf_counter()
        end_time = start_time + duration_sec
        
        num_records = len(base_features)
        if num_records == 0:
            return {"runs": 0, "status": "EMPTY_INPUT", "error": "No features provided"}

        try:
            # Force dimension safety: ensure input columns match model expectations
            features_matrix = np.array(base_features, dtype=np.float32)
            if features_matrix.shape[1] != self.expected_features:
                # Dynamically pad or slice feature space to prevent execution crash
                if features_matrix.shape[1] < self.expected_features:
                    padding = np.zeros((features_matrix.shape[0], self.expected_features - features_matrix.shape[1]))
                    features_matrix = np.hstack((features_matrix, padding))
                else:
                    features_matrix = features_matrix[:, :self.expected_features]

            features_matrix = np.ascontiguousarray(features_matrix, dtype=np.float32)

            while time.perf_counter() < end_time:
                # Mutate: Slight perturbations to mimic testing different system parameters
                perturbations = np.random.uniform(0.9, 1.1, size=features_matrix.shape).astype(np.float32)
                mutated_batch = features_matrix * perturbations
                
                # Execute ONNX graph forward pass in microseconds
                raw_outputs = self.session.run(self.output_names, {self.input_name: mutated_batch})
                predictions = raw_outputs[0]
                run_count += num_records
                
                if run_count % 10000 == 0:
                    results_accumulator.append({
                        "timestamp": time.time(),
                        "processed": run_count,
                        "avg_score": float(np.mean(predictions))
                    })

            return {
                "runs": run_count,
                "status": "SUCCESS",
                "samples": results_accumulator[:10]
            }

        except Exception as e:
            return {
                "runs": run_count,
                "status": "CRASHED",
                "error": str(e)
            }

# =============================================================================
# 3. STATIC FILE DISCOVERY AND INGESTION (AOT DATA LAKEHOUSE)
# =============================================================================
def discover_system_files():
    """
    Locates all physical Parquet tables and ONNX files in the workspace.
    """
    parquet_files = []
    onnx_files = []
    
    # Search targets
    search_paths = [WORKSPACE_C, WORKSPACE_STUDIES]
    
    for path in search_paths:
        if not os.path.exists(path):
            continue
        # Scan for Parquets recursively
        for f in glob.glob(os.path.join(path, "**", "*.parquet"), recursive=True):
            parquet_files.append(os.path.abspath(f))
        # Scan for ONNX models recursively
        for f in glob.glob(os.path.join(path, "**", "*.onnx"), recursive=True):
            onnx_files.append(os.path.abspath(f))
            
    # Remove duplicates
    return list(set(parquet_files)), list(set(onnx_files))

def ingest_and_normalize_parquet(file_path: str) -> np.ndarray:
    """
    Reads a Parquet file and guarantees robust conversion to a 4-feature space,
    completely eliminating KeyErrors by dynamically engineering missing columns.
    """
    try:
        df = pd.read_parquet(file_path)
        if df.empty:
            return np.empty((0, 4))
            
        # 1. Handle File Size Mapping
        if "size_kb" not in df.columns:
            if "size_bytes" in df.columns:
                df["size_kb"] = df["size_bytes"] / 1024.0
            elif "size" in df.columns:
                df["size_kb"] = df["size"] / 1024.0
            else:
                df["size_kb"] = 1.0  # Safe default fallback
                
        # 2. Handle Code Row Mapping
        if "rows" not in df.columns:
            if "lines" in df.columns:
                df["rows"] = df["lines"]
            elif "line_count" in df.columns:
                df["rows"] = df["line_count"]
            else:
                df["rows"] = float(len(df))  # Estimate rows based on table size
                
        # 3. Dynamically Encode Categorical Extensions (encoded_ext)
        if "encoded_ext" not in df.columns:
            if "ext" in df.columns:
                try:
                    le = LabelEncoder()
                    df["encoded_ext"] = le.fit_transform(df["ext"].astype(str)).astype(float)
                except Exception:
                    df["encoded_ext"] = 0.0
            else:
                # Generate stable hashes if ext is completely missing
                df["encoded_ext"] = df.index.map(lambda x: float(hash(str(x)) % 10))
                
        # 4. Dynamically Encode System Sources (encoded_source)
        if "encoded_source" not in df.columns:
            if "source" in df.columns:
                try:
                    le = LabelEncoder()
                    df["encoded_source"] = le.fit_transform(df["source"].astype(str)).astype(float)
                except Exception:
                    df["encoded_source"] = 0.0
            else:
                df["encoded_source"] = 1.0  # Safe default constant
                
        # Extract features tightly
        features = df[["size_kb", "rows", "encoded_ext", "encoded_source"]].to_numpy()
        return features
        
    except Exception as e:
        print(f"⚠️  [INGESTION WARNING] Skipping malformed Parquet {os.path.basename(file_path)}: {e}")
        return np.empty((0, 4))

# =============================================================================
# 4. SWEEP COORDINATOR
# =============================================================================
def main():
    print("=" * 80)
    print("🛡️  SOVEREIGN HIGH-FREQUENCY AOT CLUSTER SWEEP - VERSION 2")
    print("   Fault-Protected Parallel Execution Over All Parquets & ONNX Models")
    print("=" * 80)

    # Step 1: Discover Assets
    print("\n🔍 [1/4] Discovering workspace assets...")
    parquet_paths, onnx_paths = discover_system_files()
    print(f"   -> Found {len(parquet_paths)} physical Parquet tables.")
    print(f"   -> Found {len(onnx_paths)} physical ONNX models.")
    
    if not onnx_paths:
        print("❌ [CRITICAL] No ONNX models found. Please make sure models are uploaded to workspace.")
        sys.exit(1)

    # Step 2: Establish Ray Connection
    print("\n📡 [2/4] Initializing fault-tolerant cluster registry...")
    try:
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        print("✅ Attached to live active Ray GCS Plane.")
    except Exception as e:
        print(f"[-] Local GCS attachment bypassed: {e}. Spawning clean in-process workers...")
        ray.init(namespace="legion", ignore_reinit_error=True)
        print("✅ Single-node testing registry established.")

    # Step 3: Align Assets and Prep Shared Object Store
    print("\n🧬 [3/4] Aligning dataset features and packing model binaries...")
    
    # Store compiled model bytes and feature references to prevent IPC bottlenecking
    onnx_registry = {}
    for opath in onnx_paths:
        mname = os.path.basename(opath)
        try:
            with open(opath, "rb") as f:
                mbytes = f.read()
            
            # Inspect model format properties to determine expected features
            temp_session = ort.InferenceSession(mbytes, providers=["CPUExecutionProvider"])
            expected_feats = temp_session.get_inputs()[0].shape[1]
            if expected_feats is None or isinstance(expected_feats, str):
                expected_feats = 4 # Code genome model default
                
            onnx_registry[mname] = {
                "ref": ray.put(mbytes),
                "expected_features": expected_feats,
                "path": opath
            }
            print(f"   🔹 Registered: {mname:<30} | Expects: {expected_feats} Features | Mapped to Shared Memory.")
        except Exception as e:
            print(f"   ⚠️  Skipping unreadable ONNX model {mname}: {e}")

    # Process and normalize Parquet dataframes
    dataset_registry = {}
    for ppath in parquet_paths:
        pname = os.path.basename(ppath)
        feats = ingest_and_normalize_parquet(ppath)
        if len(feats) > 0:
            dataset_registry[pname] = {
                "ref": ray.put(feats),
                "count": len(feats)
            }
            print(f"   🔹 Normalized: {pname:<30} | {len(feats):<5} Active Records Mapped.")

    if not onnx_registry or not dataset_registry:
        print("❌ [CRITICAL] Registration failed. Insufficient valid ONNX models or Parquets.")
        ray.shutdown()
        sys.exit(1)

    # Step 4: Dispatch Distributed Fault-Tolerant Sweeps
    print("\n🚀 [4/4] Starting parallel high-frequency test sweeps...")
    run_duration_seconds = 20.0
    
    # Grid search mappings (Evaluating every model against every normalized parquet file)
    dispatch_queue = []
    
    for mname, mdata in onnx_registry.items():
        for pname, pdata in dataset_registry.items():
            # Deploy a fresh, resource-constrained isolated actor for this specific trial run
            actor = HighFrequencySweepActor.remote(mdata["ref"], mname, mdata["expected_features"])
            
            future = actor.run_permutation_sweep.remote(pdata["ref"], run_duration_seconds)
            dispatch_queue.append({
                "model": mname,
                "parquet": pname,
                "future": future,
                "records": pdata["count"]
            })

    total_combinations = len(dispatch_queue)
    print(f"🔥 Successfully launched {total_combinations} model-parquet trial runs in parallel across cluster!")
    print(f"⏱️  Counting down exactly {run_duration_seconds} seconds for trial completions...")
    
    start_time = time.perf_counter()
    
    # Gather outcomes with fault protection (timeouts and exceptions won't crash the script)
    completed_runs = []
    total_inferences = 0
    crashed_runs_count = 0
    
    for item in dispatch_queue:
        try:
            # We enforce a timeout ceiling of duration + 5 seconds to prevent hung actors from blocking results
            result = ray.get(item["future"], timeout=run_duration_seconds + 5.0)
            
            if result["status"] == "SUCCESS":
                total_inferences += result["runs"]
                completed_runs.append({
                    "model": item["model"],
                    "parquet": item["parquet"],
                    "runs": result["runs"],
                    "status": "SUCCESS"
                })
            else:
                crashed_runs_count += 1
                completed_runs.append({
                    "model": item["model"],
                    "parquet": item["parquet"],
                    "runs": 0,
                    "status": "FAILED",
                    "error": result.get("error", "Unknown error")
                })
        except Exception as e:
            crashed_runs_count += 1
            completed_runs.append({
                "model": item["model"],
                "parquet": item["parquet"],
                "runs": 0,
                "status": "CRASHED",
                "error": str(e)
            })

    actual_duration = time.perf_counter() - start_time
    combined_throughput = total_inferences / actual_duration

    # Output highly detailed diagnostic summaries
    print("\n" + "=" * 80)
    print("🏁 DISTRIBUTED FAULT-TOLERANT CLUSTER SUMMARY:")
    print("=" * 80)
    print(f"📈 Total Parallel Trials Scheduled : {total_combinations}")
    print(f"🟢 Successfully Executed Trials    : {total_combinations - crashed_runs_count}")
    print(f"🔴 Skipped/Crashed Trial Runs      : {crashed_runs_count}")
    print(f"📊 Total High-Frequency Inferences  : {total_inferences:,}")
    print(f"🕰️  Actual Convergence Time        : {actual_duration:.2f} seconds")
    print(f"🚀 Integrated Cluster Throughput   : {combined_throughput:,.2f} inferences/second")
    print("=" * 80)

    print("\n📋 GRID TRIAL PERFORMANCE MATRIX:")
    print("-" * 80)
    for run in completed_runs:
        status_color = "✅ SUCCESS" if run["status"] == "SUCCESS" else "❌ FAILED"
        print(f" Model: {run['model']:<25} | Table: {run['parquet']:<25} | Status: {status_color} | Sweeps: {run['runs']:,}")
        if run["status"] != "SUCCESS":
            print(f"   └─> Warning: {run.get('error', 'Unknown Error')}")
    print("-" * 80)

    ray.shutdown()

if __name__ == "__main__":
    main()
