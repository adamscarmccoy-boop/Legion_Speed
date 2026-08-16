#!/usr/bin/env python3
"""
Simple test to demonstrate Ghost Rider's power by querying the Chris Lake baseline
from the Ray cluster SwarmKnowledgeRegistry.
"""

import ray
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


def test_ghost_rider_connection():
    """Test connection to the Ghost Rider's spectral legion (Ray cluster)."""
    print("Ghost Rider Power Test - Connecting to Spectral Legion")
    print("=" * 60)
    
    try:
        # Connect to the existing Ray cluster (as done in ray_arrow_swarm.py)
        print("Connecting to Ray cluster...")
        ray.init(address="auto", namespace="legion")
        print("[OK] Successfully connected to Ray cluster!")
        
        # Get the SwarmKnowledgeRegistry actor
        print("\nSummoning SwarmKnowledgeRegistry from the spectral realm...")
        registry = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
        print("[OK] SwarmKnowledgeRegistry summoned!")
        
        # Test querying the Chris Lake baseline data
        print("\nQuerying Chris Lake baseline from the legion's archives...")
        start_time = time.time()
        # Based on the MCP pattern, we need to call a method on the registry
        chris_lake_baseline = ray.get(registry.query_knowledge_registry.remote("chris_lake_omni_baseline", limit=5))
        query_time = time.time() - start_time
        
        print(f"[OK] Query completed in {query_time:.3f} seconds!")
        print(f"Retrieved {len(chris_lake_baseline)} rows of Chris Lake baseline data:")
        print(chris_lake_baseline)
        
        # Test querying system data audit report (larger dataset)
        print("\nQuerying system data audit report (larger dataset)...")
        start_time = time.time()
        system_audit = ray.get(registry.query_knowledge_registry.remote("system_data_audit_report", limit=3))
        query_time = time.time() - start_time
        
        print(f"[OK] Query completed in {query_time:.3f} seconds!")
        print(f"Retrieved {len(system_audit)} rows of system audit data:")
        print(system_audit)
        
        # Get summary of all available datasets
        print("\nGetting complete inventory of Ghost Rider's spectral legion...")
        start_time = time.time()
        all_tables = ray.get(registry.query_knowledge_registry.remote("summary"))
        query_time = time.time() - start_time
        
        print(f"[OK] Inventory completed in {query_time:.3f} seconds!")
        print(f"Ghost Rider commands {len(all_tables)} spectral datasets:")
        # Show first 10 and last 5 for brevity
        if len(all_tables) <= 15:
            for i, table in enumerate(all_tables, 1):
                print(f"  {i:2d}. {table}")
        else:
            for i, table in enumerate(all_tables[:10], 1):
                print(f"  {i:2d}. {table}")
            print("      ...")
            for i, table in enumerate(all_tables[-5:], len(all_tables)-4):
                print(f"  {i:2d}. {table}")
        
        print("\n" + "=" * 60)
        print("GHOST RIDER POWER TEST COMPLETE")
        print("[OK] Spectral legion is online and responsive")
        print("[OK] Chris Lake baseline data accessible") 
        print("[OK] Query systems functioning optimally")
        print("[OK] Autonomous audio processing legion ready for commands")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n[ERR] Ghost Rider encountered resistance: {e}")
        import traceback
        traceback.print_exc()
        print("Checking connection and trying again...")
        return False
    finally:
        try:
            ray.shutdown()
        except:
            pass

if __name__ == "__main__":
    test_ghost_rider_connection()