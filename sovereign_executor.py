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
# CONFIGURATION
# ==============================================================================
RAY_ADDRESS = "auto"
RAY_NAMESPACE = "legion"
REGISTRY_NAME = "SwarmKnowledgeRegistry"

# The "Sovereign" Weights
MODEL_PATH = r"C:\WEB CASE STUDY\real_data_brain.onnx"

# The Sovereign State Tables
SOURCE_TABLE = "duckdb_audio_features"
TARGET_TABLE = "chris_lake_omni_baseline"

# THE TWO KEYS: Based on the Possibility Map (Strongest Correlations)
# If these aren't the keys, we will adjust based on the baseline.
SOVEREIGN_KEYS = ["spectral_centroid", "spectral_rolloff"]

def run_sovereign_inference():
    print("=" * 70)
    print("  SOVEREIGN NEURAL INFERENCE: ZERO-COPY EXECUTION")
    print("=" * 70)

    # 1. Connect to the existing Swarm
    ray.init(address=RAY_ADDRESS, namespace=RAY_NAMESPACE, ignore_reinit_error=True)
    
    try:
        registry = ray.get_actor(REGISTRY_NAME, namespace=RAY_NAMESPACE)
        print(f"  [+] Connected to {REGISTRY_NAME}")
    except Exception as e:
        print(f"FATAL: Could not find registry: {e}")
        return

    # 2. Retrieve Zero-Copy ObjectRefs
    print(f"  [+] Retrieving Source: {SOURCE_TABLE}...")
    source_data = ray.get(registry.get_table.remote(SOURCE_TABLE))
    
    print(f"  [+] Retrieving Target: {TARGET_TABLE}...")
    target_data = ray.get(registry.get_table.remote(TARGET_TABLE))
    
    # Convert to pandas for the ONNX runtime
    df_src = source_data.to_pandas() if hasattr(source_data, "to_pandas") else pd.DataFrame(source_data)
    df_tgt = target_data.to_pandas() if hasattr(target_data, "to_pandas") else pd.DataFrame(target_data)
    
    print(f"  [+] Data retrieved. Source: {len(df_src)} rows | Target: {len(df_tgt)} rows")

    # 3. Load the Frozen Brain
    print(f"  [+] Loading Sovereign Brain: {MODEL_PATH}...")
    session = ort.InferenceSession(MODEL_PATH)
    input_name = session.get_inputs()[0].name
    
    # 4. Inference (The "Translation")
    # We only take the TWO KEYS required by the model
    try:
        X = df_src[SOVEREIGN_KEYS].values.astype(np.float32)[0:1]
    except KeyError as e:
        print(f"FATAL: Source table {SOURCE_TABLE} is missing keys {SOVEREIGN_KEYS}. Error: {e}")
        return
    
    print(f"  [+] Running Inference on {X.shape} tensor using keys {SOVEREIGN_KEYS}...")
    prediction = session.run(None, {input_name: X})[0]
    
    # 5. The Sovereign Output
    print("\n" + "=" * 70)
    print("  SOVEREIGN MASTERING PARAMETERS")
    print("=" * 70)
    params = prediction[0]
    print(f"  GAIN_DB:      {params[0]:.2f}")
    print(f"  COMP_RATIO:   {params[1]:.2f}")
    print(f"  THRESH_DB:    {params[2]:.2f}")
    print("=" * 70)
    print("  Sovereign translation complete.")

if __name__ == "__main__":
    run_sovereign_inference()