import os
import sys
import time
import numpy as np
import pyarrow as pa
import ray

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


def main():
    print("=== Legion Ray Task Submission Pipeline ===")
    
    # 1. Connect to the existing detached Ray cluster
    try:
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        print("Successfully linked to active Ray cluster (namespace: legion).")
    except ConnectionError:
        print("Error: Could not connect to the Ray cluster. Ensure Ray is running.")
        sys.exit(1)

    # ==========================================================================
    # >>>>> __________________ PLACE YOUR CODE BELOW __________________ <<<<<
    # ==========================================================================
    
    # Define your remote tasks or actors here. Example:
    @ray.remote(num_cpus=1)
    def my_custom_math_task(x):
        # Place your logic here
        return x * x
        
    print("\nSubmitting tasks to cluster...")
    t0 = time.time()
    
    # Submit tasks and fetch results
    futures = [my_custom_math_task.remote(i) for i in range(10)]
    results = ray.get(futures)
    
    # ==========================================================================
    # >>>>> __________________ PLACE YOUR CODE ABOVE __________________ <<<<<
    # ==========================================================================

    elapsed = time.time() - t0
    print("\n=== EXECUTION SUCCESS ===")
    print(f"Results: {results}")
    print(f"Time Elapsed: {elapsed:.4f}s")
    print("=========================")

if __name__ == "__main__":
    main()