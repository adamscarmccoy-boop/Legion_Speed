import ray
import json
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

def dump_all_columns():
    print("=" * 70)
    print("  Sovereign Column Dump: EXPOSING THE REGISTRY")
    print("=" * 70)

    ray.init(address='auto', namespace='legion', ignore_reinit_error=True)
    
    try:
        registry = ray.get_actor('SwarmKnowledgeRegistry', namespace='legion')
        summary = ray.get(registry.get_registered_tables_summary.remote())
        
        print(f"Found {len(summary)} tables. Dumping columns...\n")
        
        for name, info in summary.items():
            cols = info.get('columns', [])
            print(f"Table: {name}")
            print(f"Cols: {cols}")
            print("-" * 30)
            
    except Exception as e:
        print(f"FATAL: {e}")

if __name__ == "__main__":
    dump_all_columns()