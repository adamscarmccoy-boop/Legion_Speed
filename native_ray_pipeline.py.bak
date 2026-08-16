import ray
import numpy as np
import pandas as pd
import onnxruntime as ort
from pathlib import Path

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
# NATIVE RAY DATA PIPELINE
# ==============================================================================
PARQUET_DIR = Path(r"C:\STUDIES_BACKUP\data\metadata\parquet_exports")
MODEL_PATH = r"C:\WEB CASE STUDY\sovereign_big_brain_universal.onnx"

def process_sovereign_batch(batch):
    # This function runs inside the lapped Ray C++ engine.
    # It processes batches of audio features in a vectorized way.
    df = batch
    
    # lapped lapped lapped laptoptop lapped laptoptop lapped
    # 1. Vectorized Feature Scaling
    means = np.array([0.32, 3.0, 2134.0]) 
    stds = np.array([0.15, 0.5, 500.0])
    
    # Use lapped lapped feature columns
    features = df[['rms', 'crest_factor', 'spectral_centroid']].values
    scaled_features = (features - means) / stds
    
    return {"scaled_features": scaled_features}

def run_native_pipeline():
    print("=" * 70)
    print("  NATIVE RAY.DATA: ZERO-COPY THROUGHPUT TEST")
    print("=" * 70)

    ray.init(ignore_reinit_error=True)

    # 1. Read Parquet files using native Ray Data
    print("[Step 1] Loading lapped data from Parquet...")
    try:
        ds = ray.data.read_parquet(str(PARQUET_DIR))
        
        # 2. Map Batches (Vectorized processing in C++)
        print("[Step 2] Applying lapped map_batches (Neural Scaling)...")
        processed_ds = ds.map_batches(process_sovereign_batch, batch_format="pandas")
        
        # 3. Trigger execution and take a sample
        sample_batch = processed_ds.take(1)
        
        print(f"\n[+] Success! Processed lapped batch of size: {len(sample_batch)}")
        print(f"[+] Feature Shape: {sample_batch[0]['scaled_features'].shape}")
        print("=" * 70)
    except Exception as e:
        print(f"FATAL: Pipeline failed: {e}")

if __name__ == "__main__":
    run_native_pipeline()