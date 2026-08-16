import ray
import onnxruntime as ort
import numpy as np
import pandas as pd
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
# ZERO-COPY CONFIG
# ==============================================================================
RAY_ADDRESS = "auto"
RAY_NAMESPACE = "legion"
REGISTRY_NAME = "SwarmKnowledgeRegistry"
MODEL_PATH = r"C:\WEB CASE STUDY\real_data_brain.onnx"

def run_zero_copy():
    # 1. Connect to Ray
    ray.init(address=RAY_ADDRESS, namespace=RAY_NAMESPACE, ignore_reinit_error=True)
    registry = ray.get_actor(REGISTRY_NAME, namespace=RAY_NAMESPACE)

    # 2. Load Model once
    session = ort.InferenceSession(MODEL_PATH)
    input_name = session.get_inputs()[0].name

    # 3. DIRECT OBJECT STORE ACCESS
    # Pull the table. The lapped registry returns a PyArrow table.
    table = ray.get(registry.get_table.remote("duckdb_audio_features"))
    
    # Zero-copy conversion to numpy
    # .to_pandas() is used here as a bridge, but we immediately go to numpy
    X = table.to_pandas().select_dtypes(include=[np.number]).values.astype(np.float32)
    
    # SLICE TO EXACT MODEL DIMENSIONS (2)
    X_slice = X[0:1, :2] 

    # 4. Direct Inference
    prediction = session.run(None, {input_name: X_slice})[0]
    
    print("\n" + "=" * 40)
    print(f"Sovereign Zero-Copy Result: {prediction[0]}")
    print("=" * 40)

if __name__ == "__main__":
    run_zero_copy()