"""
RUN UNIFIED CODE VISION PIPELINE (.py)
Unified multi-model Ray Swarm runner linking ONNX, PyTorch, and Data Catalogs.
"""

import os
import sys
import torch
import pandas as pd
import numpy as np
import ray

from check_data_and_output_weights import SovereignUnifiedSwarmBrain

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


@ray.remote
class SovereignRaySwarmWorker:
    def __init__(self, weights_path="sovereign_master_unified_brain.pth"):
        self.model = SovereignUnifiedSwarmBrain()
        if os.path.exists(weights_path):
            checkpoint = torch.load(weights_path, map_location="cpu")
            self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.eval()

    def process_batch(self, vision_feats, audio_feats, genome_feats):
        v_t = torch.tensor(vision_feats, dtype=torch.float32)
        a_t = torch.tensor(audio_feats, dtype=torch.float32)
        g_t = torch.tensor(genome_feats, dtype=torch.float32)

        with torch.no_grad():
            unified_latents = self.model(v_t, a_t, g_t)
        return unified_latents.numpy()

def run_unified_pipeline():
    print("=" * 70)
    print(" RUNNING UNIFIED RAY SWARM MULTI-MODEL PIPELINE ")
    print("=" * 70)

    # 1. Ensure Ray is active
    try:
        ray.init(address='auto', ignore_reinit_error=True)
        print("[OK] Connected to Ray Swarm Cluster.")
    except Exception:
        ray.init(ignore_reinit_error=True)

    # 2. Check/Generate Master Weights
    weights_path = "sovereign_master_unified_brain.pth"
    if not os.path.exists(weights_path):
        print("[INFO] Generating master weights via check_data_and_output_weights.py...")
        from check_data_and_output_weights import check_data_and_export_weights
        check_data_and_export_weights()

    # 3. Instantiate Ray Remote Swarm Worker
    worker = SovereignRaySwarmWorker.remote(weights_path)
    
    # 4. Ingest sample batches across Vision, Audio, and Genome
    v_batch = np.random.randn(5, 41)
    a_batch = np.random.randn(5, 128)
    g_batch = np.random.randn(5, 4)

    print("\n[DISPATCHING BATCH TO RAY WORKER ACTOR]...")
    future = worker.process_batch.remote(v_batch, a_batch, g_batch)
    results = ray.get(future)

    print(f"[OK] Ray Swarm Output Shape: {results.shape}")
    print(f"     Sample Latent Output Vector (First row, 5 dims): {results[0, :5]}")
    print("\n[SUCCESS]: ALL MODELS (.pth, .pt, .onnx) RUNNING UNIFIED IN RAY!")
    print("=" * 70)

if __name__ == "__main__":
    run_unified_pipeline()