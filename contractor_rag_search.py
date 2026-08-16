import sys
import os
import json
import urllib.request
import ray

try:
    import lancedb
except ImportError:
    print("Please install lancedb (pip install lancedb)")
    sys.exit(1)

# Reconfigure stdout to prevent CP1252 character map crashes on unicode symbols
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

def get_snowflake_vector(text):
    """Query local LM Studio on port 1234 for 1024-dim Snowflake embeddings."""
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
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data["data"][0]["embedding"]
    except Exception as e:
        print(f"[WARN] Local LM Studio not responding: {e}")
        return None

def main():
    print("=== Contractor Job RAG Discovery Query ===")
    
    query = "contractor freelance upwork audio DSP programming engineer"
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        
    print(f"🔍 Searching for: '{query}'")
    
    # Check known LanceDB Paths from previous exports
    potential_db_paths = [
        r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag",
        r"C:\WEB CASE STUDY\lancedb_web_intel_rag",
        r"C:\WEB CASE STUDY\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag"
    ]
    
    db_path = None
    for path in potential_db_paths:
        if os.path.exists(path):
            db_path = path
            break
            
    if not db_path:
        print("FATAL: Could not find LanceDB directory.")
        sys.exit(1)
        
    print(f"Connecting to LanceDB at: {db_path}...")
    try:
        db = lancedb.connect(db_path)
    except Exception as e:
        print(f"Error connecting to LanceDB: {e}")
        sys.exit(1)
        
    query_vector = get_snowflake_vector(query)
    if not query_vector:
        print("Using zero vector fallback because LM Studio failed.")
        query_vector = [0.0] * 1024
        
    tables = db.table_names()
    print(f"Available tables: {tables}")
    
    for t_name in tables:
        print(f"\n--- Scanning Table: {t_name} ---")
        try:
            tbl = db.open_table(t_name)
            # Try to search using the embedding
            results = tbl.search(query_vector).limit(3).to_pandas()
            if results.empty:
                print("No results found.")
                continue
                
            for idx, row in results.iterrows():
                print(f"\n[{idx}] Distance: {row.get('_distance', 'N/A'):.4f}")
                if 'file_path' in row:
                    print(f"File: {row['file_path']}")
                if 'text' in row:
                    print(f"Content:\n{row['text'][:500]}...")
        except Exception as e:
            print(f"Error querying table {t_name}: {e}")

if __name__ == "__main__":
    main()
