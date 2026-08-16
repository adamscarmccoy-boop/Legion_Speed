
import ray
import json
from ray_arrow_swarm import SwarmKnowledgeRegistry, swarm_search, LEGION_NAMESPACE

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
    # Connect to the existing cluster using the parameters from ray_arrow_swarm.py
    try:
        # We use address="auto" as per the source script
        ray.init(address="auto", namespace=LEGION_NAMESPACE, ignore_reinit_error=True)
        print("Connected to Ray cluster.")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    try:
        # Get the detached actor
        registry = ray.get_actor("SwarmKnowledgeRegistry", namespace=LEGION_NAMESPACE)
        print("Connected to SwarmKnowledgeRegistry.")
    except Exception as e:
        print(f"Could not find registry actor: {e}")
        return

    # Perform the search for 'parser'
    print("Searching for 'parser' in Knowledge Registry...")
    
    # Search in 'key' column
    key_hits = ray.get(swarm_search.remote(registry, "key", "parser"))
    # Search in 'value' column
    val_hits = ray.get(swarm_search.remote(registry, "value", "parser"))
    
    all_hits = key_hits + val_hits
    
    if all_hits:
        print(f"\nFound {len(all_hits)} hit(s):")
        print(json.dumps(all_hits, indent=2))
    else:
        print("\nNo hits found for 'parser'.")

if __name__ == "__main__":
    main()