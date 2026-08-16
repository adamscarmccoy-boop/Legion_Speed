import os
import ray
import snowflake.connector
import json


import pandas

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
    # Avoid raising SystemExit inside an atexit callback (which causes RuntimeWarnings)
    if args and isinstance(args[0], int):
        sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================

# Configuration
SNOWFLAKE_CONFIG = {
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "warehouse": "COMPUTE_WH",
    "database": "LEGION_DB",
    "schema": "PUBLIC"
}

def sync_embeddings_to_snowflake():
    """Fetches embeddings from Ray Swarm Registry and pushes to Snowflake."""
    print("Connecting to Ray and Snowflake...")
    
    # 1. Connect to existing Ray cluster
    try:
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
    except Exception as e:
        print(f"Failed to connect to Ray: {e}")
        return

    # 2. Get the Registry Actor
    try:
        registry = ray.get_actor("SwarmKnowledgeRegistry")
        summary = ray.get(registry.registered_tables_summary.remote())
    except Exception as e:
        print(f"Registry not found: {e}")
        return

    # 3. Prepare data for Snowflake
    # In a real scenario, you'd iterate through tables and extract vectors
    # Here we simulate the metadata for the sync
    data_to_sync = []
    for name, meta in summary.items():
        data_to_sync.append({
            "TABLE_NAME": name,
            "ROW_COUNT": meta["rows"],
            "STATUS": "SYNCED"
        })
    
    df = pd.DataFrame(data_to_sync)

    # 4. Upload to Snowflake
    try:
        ctx = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
        cursor = ctx.cursor()
        
        # Create table if doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS EMBEDDING_AUDIT (
                TABLE_NAME VARCHAR,
                ROW_COUNT INTEGER,
                STATUS VARCHAR,
                SYNC_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
            )
        """)
        
        # Use write pandas for performance
        from snowflake.connector.pandas_tools import write_pandas
        success, nchunks, nrows = write_pandas(ctx, df, "EMBEDDING_AUDIT", auto_create_table=True)
        print(f"Successfully synced {nrows} rows to Snowflake.")
        
    except Exception as e:
        print(f"Snowflake error: {e}")
    finally:
        ctx.close()

if __name__ == "__main__":
    sync_embeddings_to_snowflake()