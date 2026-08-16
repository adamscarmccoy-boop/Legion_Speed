import os
import sys
import lancedb
import urllib.request
import json

# Setup database path
db_path = r"c:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag"
if not os.path.exists(db_path):
    db_path = r"C:\WEB CASE STUDY\lancedb_web_intel_rag"

print(f"Connecting to LanceDB at: {db_path}...")
try:
    db = lancedb.connect(db_path)
    table_name = "mined_documentation_vectors"
    if table_name not in db.table_names():
        print(f"Error: Table '{table_name}' does not exist.")
        sys.exit(1)
    tbl = db.open_table(table_name)
except Exception as e:
    print(f"Database error: {e}")
    sys.exit(1)

# Helper function to generate query vector
def get_snowflake_vector(text):
    payload = {
        "input": [text],
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
            return data["data"][0]["embedding"]
    except Exception as e:
        print(f"Error during LM Studio embedding query: {e}")
        return None

def search(query_text, limit=3):
    print(f"\nSearching locally for: '{query_text}'...")
    query_vector = get_snowflake_vector(query_text)
    
    if not query_vector:
        print("Error: Could not generate query vector.")
        return
        
    # Perform vector search
    results = tbl.search(query_vector).limit(limit).to_list()
    
    print(f"\nFound {len(results)} matches:")
    for idx, r in enumerate(results):
        print(f"\n--- Match #{idx+1} (Distance: {r.get('_distance', 'N/A'):.4f}) ---")
        print(r["text"])
        print("-" * 50)

if __name__ == "__main__":
    # Test searches based on Ray core features we ingested
    search("how to use map_batches and ActorPoolStrategy")
