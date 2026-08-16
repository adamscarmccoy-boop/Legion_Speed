import ray
import pandas as pd
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
# CONFIGURATION
# ==============================================================================
RAY_ADDRESS = "auto"
RAY_NAMESPACE = "legion"
REGISTRY_NAME = "SwarmKnowledgeRegistry"

def probe_registry():
    print("=" * 70)
    print("  SOVEREIGN REGISTRY PROBE: MULTIPATH DISCOVERY")
    print("=" * 70)

    ray.init(address=RAY_ADDRESS, namespace=RAY_NAMESPACE, ignore_reinit_error=True)
    
    try:
        registry = ray.get_actor(REGISTRY_NAME, namespace=RAY_NAMESPACE)
        print(f"  [+] Connected to {REGISTRY_NAME}")
    except Exception as e:
        print(f"FATAL: Registry Actor not found: {e}")
        return

    results = {"path_a": None, "path_b": None, "path_c": None}

    # --------------------------------------------------------------------------
    # PATH A: The Direct Hit (Highest Speed, Low Flexibility)
    # --------------------------------------------------------------------------
    print("\n[Path A] Attempting Direct Table Access...")
    try:
        # We try to pull the two most critical tables for Sovereign training
        src_ref = registry.get_table.remote("duckdb_audio_features")
        tgt_ref = registry.get_table.remote("chris_lake_omni_baseline")
        
        # We only check if they exist (don't pull full data yet to save time)
        # ray.get() on the ref is the test
        ray.get([src_ref, tgt_ref], timeout=2.0)
        results["path_a"] = ("SUCCESS", "Direct Hit: duckdb_audio_features & chris_lake_omni_baseline")
        print("  ✅ Path A: SUCCESS")
    except Exception as e:
        results["path_a"] = ("FAIL", str(e))
        print(f"  ❌ Path A: FAIL - {e}")

    # --------------------------------------------------------------------------
    # PATH B: The Discovery Hit (Moderate Speed, High Flexibility)
    # --------------------------------------------------------------------------
    print("\n[Path B] Attempting Summary-Based Discovery...")
    try:
        summary = ray.get(registry.get_registered_tables_summary.remote())
        # Search for tables that look like they contain 'omni' and 'baseline'
        potential_targets = [name for name in summary.keys() if "baseline" in name.lower() or "omni" in name.lower()]
        
        if len(potential_targets) >= 2:
            # Try to pull the top two matches
            refs = [registry.get_table.remote(name) for name in potential_targets[:2]]
            ray.get(refs, timeout=2.0)
            results["path_b"] = ("SUCCESS", f"Discovery Hit: Found {len(potential_targets)} matches")
            print(f"  ✅ Path B: SUCCESS - Matches: {potential_targets[:2]}")
        else:
            results["path_b"] = ("FAIL", "Not enough matching tables found in summary")
            print("  ❌ Path B: FAIL - Insufficient matches")
    except Exception as e:
        results["path_b"] = ("FAIL", str(e))
        print(f"  ❌ Path B: FAIL - {e}")

    # --------------------------------------------------------------------------
    # PATH C: The Metadata Hit (Slower, Highest Reliability)
    # --------------------------------------------------------------------------
    print("\n[Path C] Attempting Metadata Resolution...")
    try:
        # We look for any table that contains the word 'features' or 'vectors'
        summary = ray.get(registry.get_registered_tables_summary.remote())
        all_tables = list(summary.keys())
        
        # We try to find any table that has 'audio' and 'feature' in the name
        best_fit = [t for t in all_tables if "audio" in t.lower() and "feature" in t.lower()]
        if best_fit:
            ref = registry.get_table.remote(best_fit[0])
            ray.get(ref, timeout=2.0)
            results["path_c"] = ("SUCCESS", f"Metadata Hit: {best_fit[0]}")
            print(f"  ✅ Path C: SUCCESS - Resolved {best_fit[0]}")
        else:
            results["path_c"] = ("FAIL", "No suitable metadata matches found")
            print("  ❌ Path C: FAIL - No matches")
    except Exception as e:
        results["path_c"] = ("FAIL", str(e))
        print(f"  ❌ Path C: FAIL - {e}")

    print("\n" + "=" * 70)
    print("  FINAL DISCOVERY REPORT")
    print("=" * 70)
    for path, res in results.items():
        print(f"{path.upper():<12} | Status: {res[0]:<10} | Detail: {res[1]}")
    print("=" * 70)

if __name__ == "__main__":
    probe_registry()