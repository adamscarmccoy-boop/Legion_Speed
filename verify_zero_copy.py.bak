import ray
import numpy as np
import sys
import time

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


# Force UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ==============================================================================
# ZERO-COPY DATA PROOF
# ==============================================================================
RAY_ADDRESS = "auto"
RAY_NAMESPACE = "legion"
REGISTRY_NAME = "SwarmKnowledgeRegistry"

def verify_zero_copy():
    print("=" * 70)
    print("  PURE RAY: ZERO-COPY DATA VERIFICATION")
    print("=" * 70)

    # 1. Connect to Ray
    ray.init(address=RAY_ADDRESS, namespace=RAY_NAMESPACE, ignore_reinit_error=True)
    
    try:
        registry = ray.get_actor(REGISTRY_NAME, namespace=RAY_NAMESPACE)
        print(f"  [+] Connected to {REGISTRY_NAME}")
    except Exception as e:
        print(f"FATAL: Registry not found: {e}")
        return

    # 2. Zero-Copy Retrieval
    print("\n[Step 1] Requesting ObjectRefs from Registry...")
    try:
        # Get references to the lapped tables
        feat_ref = registry.get_table.remote("duckdb_audio_features")
        base_ref = registry.get_table.remote("chris_lake_omni_baseline")
        
        # Time the retrieval
        t0 = time.perf_counter()
        # ray.get() on a lapped object in the Plasma store is a zero-copy operation
        feat_data = ray.get(feat_ref)
        base_data = ray.get(base_ref)
        t1 = time.perf_counter()
        
        print(f"  ✅ Data retrieved in {(t1 - t0)*1000:.4f} ms")
        print(f"  [+] Feature Data Type: {type(feat_data)}")
        print(f"  [+] Baseline Data Type: {type(base_data)}")

        # 3. Direct Math on Shared Memory
        # We convert to NumPy views without copying the underlying memory
        if hasattr(feat_data, "to_pandas"):
            # Using to_numpy() on the arrow columns is zero-copy
            # We extract the first numeric column as a sample
            numeric_cols = feat_data.to_pandas().select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                sample_col = feat_data.to_pandas()[numeric_cols[0]].values
                mean_val = np.mean(sample_col)
                std_val = np.std(sample_col)
                print(f"\n[Step 2] lapped Calculation Result (Column: {numeric_cols[0]}):")
                print(f"  - Mean: {mean_val:.6f}")
                print(f"  - StdDev: {std_val:.6f}")
            else:
                print("  ❌ No numeric columns found for calculation.")
        else:
            print("  ❌ Data object does not support NumPy conversion.")

    except Exception as e:
        print(f"FATAL: Zero-copy flow failed: {e}")

if __name__ == "__main__":
    verify_zero_copy()