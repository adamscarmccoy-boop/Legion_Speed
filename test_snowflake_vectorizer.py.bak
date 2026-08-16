import sys
import os
import json
import ray
from openai import OpenAI

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


# Reconfigure stdout to prevent Windows encoding crashes
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def test_snowflake():
    print("Connecting to Ray Swarm...")
    ray.init(namespace="legion", ignore_reinit_error=True)
    
    # Retrieve the detached Swarm registry
    try:
        registry = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
    except ValueError:
        print("Error: SwarmKnowledgeRegistry actor not found. Ensure ray_arrow_swarm.py is running.")
        return

    # Let's see what tables are currently in memory
    tables = ray.get(registry.list_tables.remote())
    print(f"Active Swarm Tables: {tables}")
    
    # Try to grab some data to vectorize
    target_table = "chris_lake_fused_raw"
    if target_table not in tables:
        print(f"Table '{target_table}' not found in Swarm. Looking for fallback data...")
        # Fallback to the first available table with rows
        for t in tables:
            tbl = ray.get(registry.get_table.remote(t))
            if tbl.num_rows > 0:
                target_table = t
                break
                
    print(f"Reading from Swarm Table: '{target_table}'")
    arrow_table = ray.get(registry.get_table.remote(target_table))
    records = arrow_table.slice(0, 5).to_pylist() # Grab first 5 items to test
    
    # Initialize LM Studio Client
    client = OpenAI(
        base_url='http://127.0.0.1:1234/v1',
        api_key='lm-studio' 
    )
    
    print("\nStarting Vectorization Test (Snowflake 2.0)...")
    for idx, record in enumerate(records):
        # Build text string dynamically from columns present
        text_parts = []
        for k, v in record.items():
            if k not in ["vector", "lm_vector"] and v is not None:
                text_parts.append(f"{k}: {v}")
        payload = " | ".join(text_parts)
        
        print(f"\n[Record {idx}] String to Embed:")
        print(f"  {payload[:150]}...")
        
        try:
            t0 = os.times().elapsed
            response = client.embeddings.create(
                model="text-embedding-snowflake-arctic-embed-l-v2.0",
                input=payload
            )
            t1 = os.times().elapsed
            vector = response.data[0].embedding
            duration_ms = round((t1 - t0) * 1000, 2)
            
            print(f"✅ Success! Vector Dimension: {len(vector)} | Time: {duration_ms}ms")
            print(f"  Vector sample (first 5): {vector[:5]}")
        except Exception as e:
            print(f"❌ Failed to query LM Studio: {e}")
            print("  Check that LM Studio is running on http://127.0.0.1:1234 and the Snowflake model is loaded.")
            break

if __name__ == "__main__":
    test_snowflake()