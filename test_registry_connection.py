import ray
import json

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


def test_registry():
    print("Connecting to Ray cluster...")
    ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
    
    print("Grabbing SwarmKnowledgeRegistry actor...")
    try:
        registry = ray.get_actor("SwarmKnowledgeRegistry")
    except ValueError:
        print("ERROR: Could not find 'SwarmKnowledgeRegistry' actor. Is the swarm running?")
        return
        
    summary = ray.get(registry.get_registered_tables_summary.remote())
    tables = list(summary.keys())
    print(f"\n✅ SUCCESSFULLY CONNECTED! Found {len(tables)} registered tables in live memory.")
    
    table_name = "chrislake_stems_duckdb"
    print(f"\nAttempting to instantly pull table '{table_name}' from RAM...")
    
    if table_name in tables:
        data = ray.get(registry.get_table.remote(table_name))
        print(f"✅ Success! Pulled {len(data)} rows.")
        print("\n--- FIRST ROW ---")
        print(json.dumps(data[0], indent=2))
    else:
        print(f"Table '{table_name}' not found. Here are the first 10 tables available:")
        print(tables[:10])

if __name__ == "__main__":
    test_registry()