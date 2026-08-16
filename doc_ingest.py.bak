import ray
import os
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


# Connect to the running Ray cluster
try:
    ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
    print("Connected to existing Ray cluster.")
except ConnectionError:
    print("Error: Could not connect to the Ray cluster. Ensure Ray is running.")
    sys.exit(1)

# Grab the active SwarmKnowledgeRegistry actor
try:
    registry = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
except ValueError:
    print("Error: SwarmKnowledgeRegistry actor not found. Run ray_arrow_swarm.py first.")
    sys.exit(1)

def chunk_document(text, chunk_size=1000, overlap=100):
    """Splits a full document text into overlapping paragraph chunks."""
    results = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            results.append(chunk)
        start += chunk_size - overlap
    return results

def main():
    docs_dir = "C:/WEB CASE STUDY/docs/"
    print(f"Reading full documentation files from: {docs_dir}")
    
    if not os.path.exists(docs_dir):
        print(f"Error: Directory {docs_dir} does not exist.")
        sys.exit(1)
        
    all_chunks = []
    
    # Read each file as a complete document
    for filename in os.listdir(docs_dir):
        filepath = os.path.join(docs_dir, filename)
        if os.path.isfile(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                file_chunks = chunk_document(content)
                all_chunks.extend(file_chunks)
                print(f"  -> Read {filename} ({len(content)} chars) -> Split into {len(file_chunks)} chunks.")
            except Exception as e:
                print(f"  -> Error reading {filename}: {e}")
                
    if not all_chunks:
        print("Error: No documentation text found to ingest.")
        sys.exit(1)
        
    print(f"\nDistributing {len(all_chunks)} rich paragraph chunks into Ray Swarm registry...")
    
    # Parallelize the ingestion using Ray Data
    ds = ray.data.from_items([{"text": chunk} for chunk in all_chunks])
    
    def ingest_to_registry(batch):
        ray.get(registry.add_knowledge_batch.remote(batch))
        return {"status": ["success"] * len(batch["text"])}
        
    ds = ds.map_batches(ingest_to_registry, compute=ray.data.TaskPoolStrategy())
    results = ds.take_all()
    
    # Force clean re-fetch of the table to confirm total count
    tbl = ray.get(registry.get_table.remote("documentation_chunks"))
    print(f"\nDocumentation successfully ingested. Total chunks in hot memory: {tbl.num_rows}")

if __name__ == "__main__":
    main()