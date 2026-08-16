import os
import sys
import ray
import lancedb
import pandas as pd
import numpy as np
import urllib.request
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


# Connect to Ray and grab the documentation chunks
try:
    ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
    registry = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
    tbl = ray.get(registry.get_table.remote("documentation_chunks"))
    chunks = tbl.column("text").to_pylist()
    print(f"Loaded {len(chunks)} text chunks from Ray Swarm registry.")
except Exception as e:
    print(f"Error connecting to Ray or fetching tables: {e}")
    sys.exit(1)

# Connect to LanceDB
db_path = r"c:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag"
if not os.path.exists(db_path):
    db_path = r"C:\WEB CASE STUDY\lancedb_web_intel_rag"

print(f"Connecting to LanceDB at: {db_path}...")
try:
    db = lancedb.connect(db_path)
except Exception as e:
    print(f"Error connecting to LanceDB: {e}")
    sys.exit(1)

# Helper function to generate Snowflake embeddings via LM Studio local server
def get_snowflake_embeddings(texts):
    payload = {
        "input": texts,
        "model": "text-embedding-snowflake-arctic-embed-l-v2.0"
    }
    req = urllib.request.Request(
        "http://localhost:1234/v1/embeddings",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            # Extract lists of floats
            return [item["embedding"] for item in data["data"]]
    except Exception as e:
        print(f"Error during LM Studio embedding query: {e}")
        return None

# Process in batches of 50
batch_size = 50
records = []
limit_count = min(1000, len(chunks)) # Embed first 1000 chunks for deep coverage

print(f"Generating 1024-dim Snowflake embeddings locally for {limit_count} chunks...")

for i in range(0, limit_count, batch_size):
    batch_texts = chunks[i:i+batch_size]
    vectors = get_snowflake_embeddings(batch_texts)
    
    if vectors:
        for idx, (text, vector) in enumerate(zip(batch_texts, vectors)):
            records.append({
                "id": str(i + idx),
                "text": text,
                "vector": vector,
                "source": "ray_docs_swarm"
            })
        print(f"  -> Processed chunks {i} to {i + len(batch_texts)}")
    else:
        print(f"  -> Skipping batch {i} due to LM Studio connection error.")
        break

if not records:
    print("Error: No records were successfully embedded.")
    sys.exit(1)

# Save to LanceDB
try:
    table_name = "mined_documentation_vectors"
    df = pd.DataFrame(records)
    
    # Overwrite the table with the new Snowflake vectors
    tbl = db.create_table(table_name, data=df, mode="overwrite")
    print(f"\nSuccessfully stored {len(df)} 1024-dim Snowflake vectors in LanceDB table '{table_name}'.")
    
except Exception as e:
    print(f"Error saving to LanceDB: {e}")