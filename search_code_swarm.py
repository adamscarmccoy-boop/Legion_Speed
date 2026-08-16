from LINDS_WINDOWS_VOICE_APP_TEST import main
import ray
import pyarrow.compute as pc
import pyarrow as pa
import sys
import duckdb

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


# Prevent windows unicode crashes
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

ray.init(address='auto', namespace='legion', ignore_reinit_error=True)

try:
    registry = ray.get_actor('CodeSwarmKnowledgeRegistry', namespace='legion')
except ValueError:
    print("CodeSwarmKnowledgeRegistry not found.")
    sys.exit(1)

    

@ray.remote(num_cpus=1)
def omni_swarm_search(registry_handle, search_term: str):
    hits = []
    summary = ray.get(registry_handle.get_registered_tables_summary.remote())
    for name in summary.keys():
        try:
            tbl = ray.get(registry_handle.get_table.remote(name))
            for col_name in tbl.schema.names:
                try:
                    col_str = tbl.column(col_name).cast(pa.string())
                    mask = pc.match_substring(col_str, search_term, ignore_case=True)
                    for record in tbl.filter(mask).to_pylist():
                        hits.append(f"[{name} | {col_name}] -> {str(record)[:200]}...")
                except Exception:
                    continue
        except Exception:
            pass
    return hits

queries = [".bin"]

for q in queries:
    print(f"\n--- SEARCHING SWARM FOR: '{q}' ---")
    results = ray.get(omni_swarm_search.remote(registry, q))
    if not results:
        print("No hits found.")
    for res in results[:20]: # Show top 20 hits
        print(res)
    
    try:
        #duckdb.execute(f"""
        #    SELECT filename, chunk_id, substring(text_chunk, 1, 300) as snippet, text_chunk
        #    FROM '{VECTORIZED_PARQUET}' 
        #    WHERE text_chunk ILIKE '%52%' 
        #       OR text_chunk ILIKE '%50%'
        #       OR text_chunk ILIKE '%49%'
        #       OR text_chunk ILIKE '%dna%'
        #""").df()
        print("done")
    except Exception:
        print("exception")
        pass