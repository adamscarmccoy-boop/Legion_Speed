import ray
import sys
import duckdb
import lancedb

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


try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

VECTORIZED_PARQUET = r"C:\WEB CASE STUDY\takeout_vectorized.parquet"
LANCEDB_PATH = r"C:\WEB CASE STUDY\vectors\lancedb_omni_snowflake_rag"

try:
    ray.init(address='auto', namespace='legion', ignore_reinit_error=True)
    registry = ray.get_actor('CodeSwarmKnowledgeRegistry', namespace='legion')
except Exception as e:
    print("CodeSwarmKnowledgeRegistry not found:", e)

def main():
    con = duckdb.connect(database=LANCEDB_PATH)
    
    print("=" * 60)
    print(" 🦆 Legion DuckDB: Querying NotebookLM Takeout Data for 'POINT DNA'")
    print("=" * 60)
    
    try:
        hits = con.execute(f"""
            SELECT filename, chunk_id, text_chunk
            FROM '{VECTORIZED_PARQUET}' 
            WHERE text_chunk ILIKE '%52%' 
               OR text_chunk ILIKE '%50%'
               OR text_chunk ILIKE '%49%'
               OR text_chunk ILIKE '%DNA%'
        """).df()
        
        filtered_hits = hits[hits['text_chunk'].str.contains(r'(dna adamscarmccoy)', case=False, regex=True)]
        
        print(f"Found {len(filtered_hits)} highly relevant chunks.")
        for idx, row in filtered_hits.iterrows():
            text = row['text_chunk']
            if 'DNA' in text.upper() or 'POINT' in text.upper():
                print(f"\n[{row['filename']} - Chunk {row['chunk_id']}]")
                print(text[:400].replace('\n', ' ') + "...")
                
    except Exception as e:
        print(f"Search failed: {e}")

if __name__ == "__main__":
    main()