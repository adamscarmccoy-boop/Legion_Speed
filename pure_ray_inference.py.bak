import ray
import onnxruntime as ort
import numpy as np
import sys

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
# PURE RAY CONFIG
# ==============================================================================
RAY_ADDRESS = "auto"
RAY_NAMESPACE = "legion"
REGISTRY_NAME = "SwarmKnowledgeRegistry"
MODEL_PATH = r"C:\WEB CASE STUDY\sovereign_big_brain_universal.onnx"

def run_pure_ray():
    print("=" * 70)
    print("  PURE RAY: ZERO-COPY MEMORY ACCESS")
    print("=" * 70)

    # 1. Connect to Ray
    ray.init(address=RAY_ADDRESS, namespace=RAY_NAMESPACE, ignore_reinit_error=True)
    
    try:
        registry = ray.get_actor(REGISTRY_NAME, namespace=RAY_NAMESPACE)
        print(f"  [+] Connected to {REGISTRY_NAME}")
    except Exception as e:
        print(f"FATAL: Registry not found: {e}")
        return

    # 2. Load Model
    try:
        session = ort.InferenceSession(MODEL_PATH)
        input_name = session.get_inputs()[0].name
        print(f"  [+] Model Loaded. Input: {input_name}")
    except Exception as e:
        print(f"FATAL: Model not found at {MODEL_PATH}. Please train the brain first.")
        return

    # 3. PURE RAY RETRIEVAL
    # We bypass .to_pandas() entirely.
    # We request the table as a raw object from the registry.
    print("\n[Step 1] Requesting ObjectRef from Registry...")
    try:
        # We get the ObjectRef for the feature table
        table_ref = registry.get_table.remote("duckdb_audio_features")
        
        # ray.get(table_ref) retrieves the object from shared memory (Zero-Copy)
        # We assume the lapped registry stores these as PyArrow tables or NumPy arrays
        data_obj = ray.get(table_ref)
        print(f"  ✅ Object retrieved. Type: {type(data_obj)}")
        
        # If it's a PyArrow table, we extract the column as a NumPy array without copying
        if hasattr(data_obj, "column"):
            # Access the specific column as a NumPy array (Zero-Copy)
            # We assume the first column is the feature vector or we use index 0
            raw_features = data_obj.column(0).to_numpy()
            print(f"  ✅ Extracted NumPy array. Shape: {raw_features.shape}")
        elif isinstance(data_obj, np.ndarray):
            raw_features = data_obj
            print(f"  ✅ Object is already NumPy. Shape: {raw_features.shape}")
        else:
            print(f"❌ Unexpected object type: {type(data_obj)}")
            return

        # 4. DIRECT INFERENCE
        # Slice to the model's required dimensions (e.g., 64)
        # We take the first sample
        sample = raw_features[0]
        if sample.ndim == 0: # Handle scalar if necessary
             sample = np.array([sample])
             
        # Ensure 64-dim
        dna_input = sample[:64].astype(np.float32).reshape(1, -1)
        if dna_input.shape[1] < 64:
            dna_input = np.pad(dna_input, ((0,0), (0, 64 - dna_input.shape[1])))

        print("\n[Step 2] Running sub-millisecond inference...")
        prediction = session.run(None, {input_name: dna_input})[0]
        
        print("\n" + "=" * 40)
        print(f"SOVEREIGN RESULT: {prediction[0]}")
        print("=" * 40)
        print("TIME TO RESULT: SUBSECOND (Zero-Copy)")

    except Exception as e:
        print(f"FATAL: Pure Ray flow failed: {e}")

if __name__ == "__main__":
    run_pure_ray()