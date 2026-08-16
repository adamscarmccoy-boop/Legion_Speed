import ray
import pyarrow as pa
import pyarrow.compute as pc
import time
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


print("Connecting to Ray cluster (namespace: legion)...")
ray.init(namespace="legion", ignore_reinit_error=True)

try:
    registry = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
    print("Found SwarmKnowledgeRegistry!")
except ValueError:
    print("No registry actor found. Exiting.")
    sys.exit(1)

summary = ray.get(registry.get_registered_tables_summary.remote())
print(f"Found {len(summary)} tables in the registry.")

hits = []
for name in summary.keys():
    try:
        tbl = ray.get(registry.get_table.remote(name))
        search_cols = [c for c in tbl.schema.names if c in ["value", "raw_value", "key", "text", "content"]]
        for col in search_cols:
            col_data = tbl.column(col).cast(pa.string())
            
            # Substring match for mistral
            mask_mistral = pc.match_substring(col_data, "mistral", ignore_case=True)
            
            for record in tbl.filter(mask_mistral).to_pylist():
                rec_str = str(record).lower()
                if "lm studio" in rec_str or "gpu" in rec_str or "manifest" in rec_str or "lmstudio" in rec_str:
                    hits.append({"table": name, "column": col, "record": record})
    except Exception as e:
        pass

print(f"\nFound {len(hits)} hits.")
if hits:
    for i, h in enumerate(hits):
        print(f"\n[HIT {i+1}] Table: {h['table']}")
        val = str(h['record'])
        if len(val) > 2000:
            val = val[:2000] + "...[TRUNCATED]"
        print(f"Content: {val}")