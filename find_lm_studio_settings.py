import ray
import pyarrow as pa
import pyarrow.compute as pc
import json
import sys
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


sys.stdout.reconfigure(encoding='utf-8')

print("Connecting to Ray cluster (namespace: legion)...")
ray.init(namespace="legion", ignore_reinit_error=True)

registry = None
for actor_name in ["CodeSwarmKnowledgeRegistry", "SwarmKnowledgeRegistry"]:
    try:
        registry = ray.get_actor(actor_name, namespace="legion")
        print(f"Found {actor_name}!")
        break
    except ValueError:
        pass

if not registry:
    print("No registry actor found.")
    sys.exit(1)

summary = ray.get(registry.get_registered_tables_summary.remote())
print(f"Connected! Found {len(summary)} tables in the registry.")

print("\n[*] Querying PyArrow RAG for 'mistral', 'manifest' and 'gpu'...")
start_time = time.time()

hits = []
for name in summary.keys():
    try:
        tbl = ray.get(registry.get_table.remote(name))
        search_cols = [c for c in tbl.schema.names if c in ["value", "raw_value", "key", "text", "content"]]
        for col in search_cols:
            col_data = tbl.column(col).cast(pa.string())
            
            mask_mistral = pc.match_substring(col_data, "mistral", ignore_case=True)
            mask_manifest = pc.match_substring(col_data, "manifest", ignore_case=True)
            mask_gpu = pc.match_substring(col_data, "gpu", ignore_case=True)
            
            combined_mask = pc.and_(mask_mistral, mask_manifest)
            combined_mask = pc.and_(combined_mask, mask_gpu)
            
            for record in tbl.filter(combined_mask).to_pylist():
                hits.append({"table": name, "column": col, "record": record})
    except Exception as e:
        pass

elapsed = time.time() - start_time
print(f"\n=== PYARROW SEARCH RESULTS ===")
print(f"Found {len(hits)} hits in {elapsed:.2f} seconds.")

if hits:
    for i, h in enumerate(hits):
        print(f"\n  [HIT {i+1}] Table: {h['table']}")
        val = str(h['record'])
        print(f"    Content: {val}")
else:
    print("  Zero instances found.")
print("==============================")