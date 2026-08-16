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

# ==============================================================================
# CONFIG
# ==============================================================================
RAY_ADDRESS = "auto"
RAY_NAMESPACE = "legion"
REGISTRY_NAME = "SwarmKnowledgeRegistry"

# The Absolute Target Keywords
TUNING_KEYWORDS = ['gain', 'compress', 'ratio', 'threshold', 'attack', 'release']

def universal_tuning_scan():
    print("=" * 80)
    print("  Sovereign Universal Tuning Scan: BRUTE FORCE MODE")
    print("=" * 80)

    ray.init(address=RAY_ADDRESS, namespace=RAY_NAMESPACE, ignore_reinit_error=True)
    
    try:
        registry = ray.get_actor(REGISTRY_NAME, namespace=RAY_NAMESPACE)
        print(f"  [+] Connected to {REGISTRY_NAME}")
    except Exception as e:
        print(f"FATAL: Registry not found: {e}")
        return

    # 1. Get every single table in the registry
    try:
        summary = ray.get(registry.get_registered_tables_summary.remote())
        print(f"  [+] Found {len(summary)} total tables in the registry.")
    except Exception as e:
        print(f"FATAL: Could not retrieve summary: {e}")
        return

    # 2. Scan every column of every table
    found_tuning_data = {}
    
    print("\nScanning all tables for Gain/Compressor parameters...")
    
    for table_name, info in summary.items():
        cols = info.get('columns', [])
        if not cols:
            continue
            
        # Find any column that matches our tuning keywords
        matching_cols = [col for col in cols if any(k in col.lower() for k in TUNING_KEYWORDS)]
        
        if matching_cols:
            found_tuning_data[table_name] = matching_cols
            print(f"  ✅ Found in [{table_name}]: {matching_cols}")

    # 3. Final Report
    print("\n" + "=" * 80)
    print(f"  TOTAL TUNING TABLES FOUND: {len(found_tuning_data)}")
    print("=" * 80)
    
    if not found_tuning_data:
        print("❌ No tables containing Gain or Compressor parameters were found.")
    else:
        print(json.dumps(found_tuning_data, indent=2))
    
    print("=" * 80)

if __name__ == "__main__":
    universal_tuning_scan()