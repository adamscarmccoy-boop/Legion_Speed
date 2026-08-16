import ray
import json
import time
import os

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


# Connect to the running Ray cluster
print("Connecting to Ray...")
ray.init(address="auto", namespace="legion", ignore_reinit_error=True)

print("Fetching SwarmKnowledgeRegistry actor...")
try:
    registry = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
except ValueError:
    print("Error: SwarmKnowledgeRegistry actor not found. Is the ray_arrow_swarm.py script still running?")
    exit(1)

# Import the swarm_search function from the main script
from ray_arrow_swarm import swarm_search

# Let's do a couple of test queries
queries = [
    ("raw_value", "warden"),
    ("raw_value", "langgraph"),
    ("value", "warden"),
    ("value", "langgraph"),
    ("filename", "warden"),
    ("filename", "langgraph")
]

for query_key, query_value in queries:
    print(f"\n--- Querying Swarm for '{query_key}' containing '{query_value}' ---")
    start_time = time.time()
    
    # Run the distributed search
    hits = ray.get(swarm_search.remote(registry, query_key, query_value))
    
    elapsed = time.time() - start_time
    print(f"Search completed in {elapsed:.3f} seconds.")
    
    if hits:
        print(f"Found {len(hits)} hit(s). Showing up to 5 results:")
        for h in hits[:5]:
            print(f"  [{h['table']}] -> {json.dumps(h['row'])[:200]}...")
    else:
        print("No hits found.")

print("\nQuery complete.")