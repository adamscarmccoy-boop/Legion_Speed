
import ray
import pyarrow.compute as pc
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


def search_swarm_for_mastering():
    print("=== Ray Swarm Mastering & Audit Search ===")
    try:
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        registry = ray.get_actor("SwarmKnowledgeRegistry")
        summary = ray.get(registry.get_registered_tables_summary.remote())
        
        hits = []
        keywords = ["master", "check", "audit", "quality", "binary", "lapped"]
        
        for name in summary.keys():
            tbl = ray.get(registry.get_table.remote(name))
            for col_name in tbl.schema.names:
                try:
                    col_str = tbl.column(col_name).cast("string")
                    for kw in keywords:
                        mask = pc.match_substring(col_str, kw, ignore_case=True)
                        if tbl.filter(mask).num_rows > 0:
                            hits.append({"table": name, "column": col_name, "keyword": kw})
                except Exception:
                    continue
        
        # deduplicate and print
        unique_hits = {f"{h['table']}_{h['column']}": h for h in hits}.values()
        print(f"Found {len(unique_hits)} matching columns across the swarm:\n")
        for h in unique_hits:
            print(f"Table: {h['table']} | Column: {h['column']} | Keyword: {h['keyword']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    search_swarm_for_mastering()