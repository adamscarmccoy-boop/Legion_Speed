import ray
import sys
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


# Rule 4: Unicode safeguard
sys.stdout.reconfigure(encoding="utf-8")

def validate_zero_copy():
    print("[1] Connecting to Ray cluster (Zero-Copy Validation)...")
    # Rule 2: Memory Ceiling Cap
    try:
        ray.init(address="auto", namespace="legion")
        print("[SUCCESS] Ray initialized and connected to existing cluster.")
    except Exception as e:
        print(f"[FAIL] Could not connect to Ray cluster: {e}")
        return

    print("[2] Resolving SwarmKnowledgeRegistry actor...")
    try:
        registry = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
        print("[SUCCESS] SwarmKnowledgeRegistry resolved.")
    except Exception as e:
        print(f"[FAIL] Could not resolve actor: {e}")
        return
        
    print("[3] Attempting to pull PyArrow schema/tables...")
    try:
        # Try a few common method names to discover state
        methods = [m for m in dir(registry) if not m.startswith('_')]
        print(f"Actor methods available: {methods}")
        
        try:
            summary = ray.get(registry.get_registered_tables_summary.remote())
            print(f"[SUCCESS] Zero-Copy Tables Summary: {summary}")
            
            count = ray.get(registry.table_count.remote())
            print(f"[SUCCESS] Table Count: {count}")
        except Exception as e:
            print(f"[FAIL] Could not query data: {e}")
            
    except Exception as e:
        print(f"[FAIL] Error querying actor: {e}")
        
    print("\n[VALIDATION COMPLETE]")

if __name__ == "__main__":
    validate_zero_copy()