import os
import numpy as np
import ray
import torch
from sonic_to_visual_bridge import SonicToVisualBridgeActor

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


def run_tests():
    print("Starting Sovereign Bridge Validation Suite...\n")
    
    # 1. Initialize Ray
    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True)

    # 2. Instantiate Actor
    print("Testing Actor Initialization...")
    try:
        # Use the remote constructor
        actor = SonicToVisualBridgeActor.remote()
        # We call a dummy method or use ray.get on a remote call to ensure it's alive
        # ray.get(actor.__init__.remote()) is not valid for remote actors
        # Instead, we just check if the actor handle exists.
        print("Actor handle created.")
    except Exception as e:
        print(f"Initialization failed: {e}")
        return

    # 3. Test Valid Input
    print("\nTesting Valid DNA Vector (Dim=41)...")
    valid_dna = np.random.rand(41).astype(np.float32)
    try:
        result = ray.get(actor.bridge_dna_to_prompt.remote(valid_dna))
        print(f"Success! Prompt generated: {result.llm_expanded_prompt[:100]}...")
    except Exception as e:
        print(f"Valid input failed: {e}")

    # 4. Test Invalid Input (Too Short)
    print("\nTesting Invalid DNA Vector (Dim=10)...")
    invalid_dna = np.random.rand(10).astype(np.float32)
    try:
        ray.get(actor.bridge_dna_to_prompt.remote(invalid_dna))
        print("Failed: Actor should have raised a ValueError for short vector.")
    except Exception as e:
        if "Invalid DNA vector shape" in str(e):
            print(f"Success: Correctly caught invalid shape. Error: {e}")
        else:
            print(f"Caught unexpected error: {e}")

    # 5. Test None Input
    print("\nTesting None Input...")
    try:
        ray.get(actor.bridge_dna_to_prompt.remote(None))
        print("Failed: Actor should have raised a ValueError for None input.")
    except Exception as e:
        if "Invalid DNA vector shape" in str(e):
            print(f"Success: Correctly caught None input. Error: {e}")
        else:
            print(f"Caught unexpected error: {e}")

    print("\nValidation Suite Complete.")
    ray.shutdown()

if __name__ == "__main__":
    run_tests()