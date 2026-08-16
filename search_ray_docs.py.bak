import ray
import pyarrow as pa
import pyarrow.compute as pc
import json
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


sys.stdout.reconfigure(encoding='utf-8')

print("Connecting to Ray cluster...")
ray.init(address='auto', namespace="legion", ignore_reinit_error=True)

try:
    registry = ray.get_actor("CodeSwarmKnowledgeRegistry", namespace="legion")
except ValueError:
    print("CodeSwarmKnowledgeRegistry actor not found. Ensure the swarm is running.")
    sys.exit(1)

summary = ray.get(registry.get_registered_tables_summary.remote())
print(f"Found {len(summary)} tables in the registry.")

hits = []
for name in summary.keys():
    try:
        tbl = ray.get(registry.get_table.remote(name))
        
        # Check 'value' or 'raw_value' columns
        search_cols = [c for c in tbl.schema.names if c in ["value", "raw_value", "key", "text", "content"]]
        
        for col in search_cols:
            col_data = tbl.column(col).cast(pa.string())
            
            # Simple substring matching
            combined_mask = pc.match_substring(col_data, "prometheus", ignore_case=True)
            
            for record in tbl.filter(combined_mask).to_pylist():
                hits.append({"table": name, "column": col, "record": record})
                
    except Exception as e:
        pass

print(f"\nFound {len(hits)} hits for 'prometheus'.\n")
for i, h in enumerate(hits[:10]):
    print(f"--- Hit {i+1} in Table '{h['table']}' ---")
    val = str(h['record'])
    # truncate if too long
    if len(val) > 1500:
        val = val[:1500] + "... [TRUNCATED]"
    print(val)
    print()
