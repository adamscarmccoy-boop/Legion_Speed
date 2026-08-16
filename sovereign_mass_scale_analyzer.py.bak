# -*- coding: utf-8 -*-
import os
import sys
import numpy as np
import pandas as pd
import ray
import ray.data
import json
from pathlib import Path
import time
from datetime import datetime

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
# SOVEREIGN MASS-SCALE RENDER & DNA EXPORTER (C++ NATIVE)
# ==============================================================================
RAY_ADDRESS = "auto"
RAY_NAMESPACE = "legion"
REGISTRY_NAME = "SwarmKnowledgeRegistry"
from swarm_knowledge_daemon import CodeSwarmRegistry

AUDIO_INDEX_TABLE = "duckdb_t_core_memory"

# Native Binary Path
BINARY_PATH = r"C:\WEB CASE STUDY"
if BINARY_PATH not in sys.path:
    sys.path.insert(0, BINARY_PATH)

try:
    # The C++ Render Engine (compiled as .pyd)
    import sovereign_hijack as sovereign_render
except ImportError:
    sovereign_render = None

def process_sovereign_render_batch(batch):
    """
    The "Physical Layer" - Using the C++ Render Engine to produce 
    audio and DNA sidecars at scale.
    """
    results = []
    
    if sovereign_render is None:
        return pd.DataFrame([{"error": "C++ Render Binary Missing"} for _ in range(len(batch["filepath"]))])

    for i in range(len(batch["filepath"])):
        filepath = batch["filepath"][i]
        filename = batch["filename"][i]
        
        try:
            # 1. Generate Sovereign Parameters via the C++ Brain
            # This calls the native C++ logic to determine the optimal DSP settings
            # for this specific audio asset.
            params = sovereign_render.generate_sovereign_params(filepath)
            
            # 2. The .CPP RENDER: Physical Audio Generation
            # This is the native render call that produces the high-fidelity .wav
            output_wav = filepath.replace(".wav", "_SOV_RENDER.wav")
            sovereign_render.render_audio(filepath, output_wav, params)
            
            # 3. DNA Sidecar Export
            # Export the raw math used for the render
            dna_vector = sovereign_render.get_dna_vector(filepath)
            dna_payload = {
                "filename": filename,
                "dna_vector": dna_vector.tolist(),
                "params": params,
                "timestamp": datetime.now().isoformat(),
                "engine": "Sovereign_Native_CPP"
            }
            
            sidecar_path = Path(filepath).with_suffix(".dna.json")
            with open(sidecar_path, "w") as f:
                json.dump(dna_payload, f, indent=4)
            
            results.append({
                "filepath": filepath,
                "output_wav": output_wav,
                "dna_sum": float(np.sum(dna_vector)),
                "status": "RENDERED"
            })
        except Exception as e:
            results.append({"filepath": filepath, "status": "FAILED", "error": str(e)})
            
    return pd.DataFrame(results)

def run_global_sovereign_render():
    print("=" * 80)
    print("  SOVEREIGN MASS-SCALE NATIVE RENDER (C++ PHYSICAL LAYER)")
    print("=" * 80)

    ray.init(address=RAY_ADDRESS, namespace=RAY_NAMESPACE, ignore_reinit_error=True)
    
    try:
        registry = ray.get_actor(REGISTRY_NAME, namespace=RAY_NAMESPACE)
        print(f"  [+] Connected to {REGISTRY_NAME}")
    except Exception as e:
        print(f"FATAL: Registry not found: {e}")
        return

    print(f"[Step 1] Accessing Master Index: {AUDIO_INDEX_TABLE}...")
    try:
        table_ref = registry.get_table.remote(AUDIO_INDEX_TABLE)
        arrow_table = ray.get(table_ref)
        print(f"  [+] Retrieved {len(arrow_table)} audio assets.")
    except Exception as e:
        print(f"FATAL: Registry error: {e}")
        return

    print("[Step 2] Streaming to Ray Data (Zero-Copy)...")
    ds = ray.data.from_arrow(arrow_table)
    
    print(f"[Step 3] Launching Distributed C++ Render Pipeline...")
    t0 = time.perf_counter()
    
    # Map batches to the C++ Render Engine
    processed_ds = ds.map_batches(process_sovereign_render_batch, batch_format="pandas")
    final_results = processed_ds.take_all()
    
    t1 = time.perf_counter()
    
    success_count = sum(1 for r in final_results if r.get("status") == "RENDERED")
    
    print("\n" + "=" * 80)
    print(f"  NATIVE RENDER COMPLETE")
    print(f"  Total Assets Processed: {len(final_results)}")
    print(f"  WAVs Rendered: {success_count}")
    print(f"  Total Time: {(t1 - t0):.4f} seconds")
    print(f"  Throughput: {success_count/(t1-t0):.2f} renders/sec")
    print("=" * 80)

if __name__ == "__main__":
    run_global_sovereign_render()