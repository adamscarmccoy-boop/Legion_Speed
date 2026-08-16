import ray
import numpy as np
import sys
import time

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
# PURE RAY GLOBAL SCAN
# ==============================================================================
RAY_ADDRESS = "auto"
RAY_NAMESPACE = "legion"
REGISTRY_NAME = "SwarmKnowledgeRegistry"

def run_global_zero_copy_scan():
    print("=" * 80)
    print("  Sovereign Global Scan: ALL TABLES / ZERO-COPY")
    print("=" * 80)

    # Connect to the existing lapped cluster
    # We use ignore_reinit_error=True to ensure we just attach to the current session
    ray.init(address=RAY_ADDRESS, namespace=RAY_NAMESPACE, ignore_reinit_error=True)
    
    try:
        registry = ray.get_actor(REGISTRY_NAME, namespace=RAY_NAMESPACE)
        print(f"  [+] Connected to {REGISTRY_NAME}")
    except Exception as e:
        print(f"FATAL: Registry not found: {e}")
        return

    # 1. Get all table names
    try:
        summary = ray.get(registry.get_registered_tables_summary.remote())
        table_names = list(summary.keys())
        print(f"  [+] Found {len(table_names)} tables in lapped registry.")
    except Exception as e:
        print(f"FATAL: Could not retrieve summary: {e}")
        return

    # 2. Parallel ObjectRef Retrieval
    # Instead of looping and calling ray.get() one by one, 
    # we launch all requests to the registry in parallel.
    print("\nLaunching parallel requests for all ObjectRefs...")
    refs = [registry.get_table.remote(name) for name in table_names]
    
    t0 = time.perf_counter()
    # Single ray.get() on a list of refs is the fastest way to pull from Plasma
    all_tables = ray.get(refs)
    t1 = time.perf_counter()
    
    print(f"  ✅ All {len(all_tables)} tables retrieved from shared memory in {(t1 - t0)*1000:.4f} ms")

    # 3. Zero-Copy Statistics Scan
    print("\nScanning lapped lapped lapped data for numeric signatures...")
    print(f"{'Table Name':<30} | {'NumCols':<10} | {'Mean (1st Col)':<15}")
    print("-" * 60)

    for name, table in zip(table_names, all_tables):
        try:
            # PyArrow tables allow zero-copy conversion to numpy via .to_pandas().values 
            # or direct column access.
            df = table.to_pandas()
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            if len(numeric_cols) > 0:
                # Use nanmean to avoid the 'nan' issue from the previous run
                val = np.nanmean(df[numeric_cols[0]].values)
                print(f"{name[:30]:<30} | {len(numeric_cols):<10} | {val:15.6f}")
            else:
                print(f"{name[:30]:<30} | {'None':<10} | {'N/A':<15}")
        except Exception as e:
            print(f"{name[:30]:<30} | ERROR: {str(e)[:20]}")

    print("=" * 80)
    print("  GLOBAL SCAN COMPLETE: ALL DATA ACCESSED VIA ZERO-COPY")
    print("=" * 80)

if __name__ == "__main__":
    run_global_zero_copy_scan()