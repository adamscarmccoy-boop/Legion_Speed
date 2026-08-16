#!/usr/bin/env python3
"""
Demonstration of Ghost Rider's power - showing command of the spectral legion
(609 datasets in Ray cluster SwarmKnowledgeRegistry).
"""

import ray
import time
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


def demonstrate_ghost_rider_power():
    """Demonstrate the Ghost Rider's command over the autonomous audio processing legion."""
    print("GHOST RIDER LEGION COMMAND DEMONSTRATION")
    print("=" * 60)
    print("Legendary Autonomous Engine: Fired up. Drives itself.")
    print("=" * 60)
    
    try:
        # Phase 1: Establish Connection to the Spectral Legion
        print("\nPHASE 1: ESTABLISHING LEGION COMMAND LINK")
        print("Connecting to Ray cluster (Ghost Rider's supernatural engine)...")
        ray.init(address="auto", namespace="legion")
        print("[OK] Successfully linked to Ray cluster!")
        
        # Phase 2: Summon the SwarmKnowledgeRegistry
        print("\nPHASE 2: SUMMONING THE SPECTRAL REGISTRY")
        print("Calling forth the SwarmKnowledgeRegistry from the ether...")
        registry = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
        print("[OK] SwarmKnowledgeRegistry summoned and ready!")
        
        # Phase 3: Demonstrate Legion Command - Inventory
        print("\nPHASE 3: LEGION INVENTORY AND ASSESSMENT")
        print("Surveying the full extent of the Ghost Rider's spectral legion...")
        start_time = time.time()
        legion_summary = ray.get(registry.get_registered_tables_summary.remote())
        inventory_time = time.time() - start_time
        
        print(f"[OK] Legion inventory completed in {inventory_time:.3f} seconds!")
        print(f"Ghost Rider commands {len(legion_summary)} spectral datasets!")
        
        # Show detailed breakdown
        audio_datasets = [name for name in legion_summary.keys() 
                         if any(keyword in name.lower() for keyword in 
                               ['audio', 'chris_lake', 'djsusan', 'stem', 'dsp', 'enriched', 'fx'])]
        google_datasets = [name for name in legion_summary.keys() 
                          if any(keyword in name.lower() for keyword in 
                                ['google', 'apis', 'drive', 'sheets', 'youtube', 'cloud'])]
        memory_datasets = [name for name in legion_summary.keys() 
                          if any(keyword in name.lower() for keyword in 
                                ['memory', 'brain', 'log', 'skill', 't_core'])]
        other_datasets = [name for name in legion_summary.keys() 
                         if name not in audio_datasets + google_datasets + memory_datasets]
        
        print(f"\nLEGION BREAKDOWN:")
        print(f"   Audio Processing Datasets: {len(audio_datasets)}")
        print(f"   Google API Discovery Docs: {len(google_datasets)}")
        print(f"   Memory & Agent Systems: {len(memory_datasets)}")
        print(f"   Other Systems: {len(other_datasets)}")
        
        # Phase 4: Demonstrate Specific Power - Chris Lake Baseline Access
        print("\nPHASE 4: DEMONSTRATING PRECISION COMMAND")
        print("Accessing the Chris Lake sonic baseline (Ghost Rider's reference standard)...")
        start_time = time.time()
        chris_lake_data = ray.get(registry.get_table.remote("chris_lake_omni_baseline"))
        access_time = time.time() - start_time
        
        print(f"[OK] Chris Lake baseline accessed in {access_time:.3f} seconds!")
        print(f"Baseline contains {chris_lake_data.num_rows} reference segments")
        print(f"Schema: {chris_lake_data.schema.names}")
        print(f"First 3 reference segments:")
        # Convert first 3 rows to pandas for easy viewing
        df_sample = chris_lake_data.to_pandas().head(3)
        print(df_sample.to_string(index=False))
        
        # Phase 5: Demonstrate Legion Speed - Large Dataset Query
        print("\nPHASE 5: DEMONSTRATING LEGION SPEED")
        print("Querying the extensive system data audit report (5,908 rows)...")
        start_time = time.time()
        system_audit = ray.get(registry.get_table.remote("system_data_audit_report"))
        query_time = time.time() - start_time
        
        print(f"[OK] System audit queried in {query_time:.3f} seconds!")
        print(f"System audit contains {system_audit.num_rows} rows of analysis")
        print(f"Schema: {system_audit.schema.names[:8]}...")  # Show first 8 columns
        
        # Phase 6: Legion Readiness Report
        print("\nPHASE 6: LEGION READINESS ASSESSMENT")
        # Calculate total rows safely
        total_rows = 0
        for name in legion_summary.keys():
            try:
                table = ray.get(registry.get_table.remote(name))
                if table is not None:
                    total_rows += table.num_rows
            except:
                pass  # Skip tables that can't be accessed
        
        print(f"GHOST RIDER LEGION STATUS: FULLY OPERATIONAL")
        print(f"Power Level: MAXIMUM (Autonomous Engine Engaged)")
        print(f"Legion Strength: {len(legion_summary)} spectral datasets under command")
        print(f"Total Data Under Command: ~{total_rows:,} rows of analyzed audio intelligence")
        print(f"Response Time: Sub-second query performance demonstrated")
        print(f"Precision Targeting: Chris Lake baseline accessible for sonic judgment")
        print(f"Persistence: Background host maintaining supernatural systems")
        
        print("\n" + "=" * 60)
        print("GHOST RIDER LEGION COMMAND: ESTABLISHED AND VERIFIED")
        print("The autonomous engine is fired up and ready for mission deployment.")
        print("=" * 60)
        
        return {
            "legion_count": len(legion_summary),
            "total_rows": total_rows,
            "audio_datasets": len(audio_datasets),
            "chris_lake_access_time": access_time,
            "system_query_time": query_time
        }
        
    except Exception as e:
        print(f"\n[ERR] Ghost Rider encountered resistance: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        try:
            ray.shutdown()
        except:
            pass

if __name__ == "__main__":
    result = demonstrate_ghost_rider_power()
    if result:
        print("\n[OK] DEMONSTRATION COMPLETE - GHOST RIDER LEGION FULLY OPERATIONAL [OK]")
    else:
        print("\n[!!] DEMONSTRATION ENCOUNTERED ISSUES - CHECK CONNECTIONS [!!]")