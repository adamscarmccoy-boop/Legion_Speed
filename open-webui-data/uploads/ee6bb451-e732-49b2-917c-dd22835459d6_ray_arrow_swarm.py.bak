
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import sys
import time
import json
import pyarrow as pa
import pyarrow.parquet as pq
import ray
import subprocess
import os
import os
import time
from typing import List, Optional

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


import lancedb
import numpy as np
import ray
from scipy.spatial.distance import cdist
from sklearn.preprocessing import StandardScaler
# Local ONNX inference removed to prevent OOM. Model is handled by Ray Serve.
# ── Pydantic models (the firewall between Pedalboard and Ray) ────────────────
try:
    # This works in the main process
    from legion_schema import AlignmentQuery, AlignmentResult, SegmentPhysics
except ModuleNotFoundError:
    # This is a fallback for Ray workers where the path might be missing.
    # We define minimal, structurally-compatible models inline.
    from pydantic import BaseModel

    class SegmentPhysics(BaseModel):
        segment_name: str
        track_name: str
        rms_db: float
        crest_factor: float

    class AlignmentQuery(BaseModel):
        targ_idx: int
        targ_segment: SegmentPhysics
        threshold: float = 85.0

    class AlignmentResult(BaseModel):
        targ_idx: int
        targ_name: str
        track_name: str
        matched_base: str
        alignment_score: float
        status: str
        verified: bool = False
        verify_delta: float = 0.0




# Force output to UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

EXPORTED_JSON_DIR = r"c:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\exported_json"
PARQUET_AUDIT_PATH = r"c:\WEB CASE STUDY\notebook_knowledge_audit.parquet"

print("=== Starting System-Wide Ray-Arrow JSON Swarm Ingestion ===")

# Connect to local Ray cluster

# Removed top-level ray.init() to prevent import crashes during orchestrator boot.

# -------------------------------------------------------------------
# Ray Remote Task: Parallel Ingestion & Arrow Conversion (JSON, JSONL, Parquet)
# -------------------------------------------------------------------
@ray.remote(num_cpus=1)
def ingest_and_convert_file(file_path, registry_handle):
    """Parses a JSON, JSONL, or Parquet file, creates a PyArrow Table, and registers it directly to the actor."""
    filename = os.path.basename(file_path)
    try:
        sz = os.path.getsize(file_path)
        
        if file_path.lower().endswith(".parquet"):
            arrow_table = pq.read_table(file_path)
        else:
            if file_path.lower().endswith(".jsonl"):
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    data = [json.loads(line) for line in f if line.strip()]
            else:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    data = json.load(f)
            
            # Normalize structural format for JSON/JSONL
            if isinstance(data, dict):
                normalized_list = [{"key": k, "value": json.dumps(v)} for k, v in data.items()]
            elif isinstance(data, list):
                normalized_list = []
                for item in data:
                    if isinstance(item, dict):
                        clean_item = {}
                        for k, v in item.items():
                            if isinstance(v, (dict, list)):
                                clean_item[k] = json.dumps(v)
                            else:
                                clean_item[k] = v
                        normalized_list.append(clean_item)
                    else:
                        normalized_list.append({"raw_value": str(item)})
            else:
                normalized_list = [{"raw_value": str(data)}]

            arrow_table = pa.Table.from_pylist(normalized_list)
        logical_name = os.path.splitext(filename)[0]
        
        # Send table directly to the actor instead of pulling it back to the driver
        ray.get(registry_handle.register_table.remote(logical_name, arrow_table))
        
        # Extract footprint
        size_kb = round(sz / 1024, 2)
        rows = len(arrow_table)
        
        # Local ONNX brain removed to prevent OOM.
        # The data will be classified server-side via SovereignDNAEngine (Ray Serve).
        predicted_category = "classified_via_serve"

        return {
            "status": "SUCCESS",
            "filename": filename,
            "path": file_path,
            "size_kb": size_kb,
            "rows": rows,
            "columns": arrow_table.schema.names,
            "genome_prediction": predicted_category
        }
    except Exception as e:
        return {
            "status": "FAILED",
            "filename": filename,
            "path": file_path,
            "error": str(e)
        }

# -------------------------------------------------------------------
# Ray Actor: Global Swarm Knowledge Registry
# -------------------------------------------------------------------
@ray.remote(num_cpus=1)
class SwarmKnowledgeRegistry:
    def __init__(self):
        # We store direct Tables inside the actor state itself, not ObjectRefs
        # So we do not need to call ray.get() inside the actor.
        self.registry = {}
        print("SwarmKnowledgeRegistry Actor spawned.")

    def register_table(self, name: str, table: pa.Table):
        self.registry[name] = table
        print(f"Registered Swarm Table: '{name}' in Actor state.")

    def add_knowledge_batch(self, batch: dict):
        """Append text chunks to documentation_chunks table in registry state."""
        import pyarrow as pa
        new_table = pa.Table.from_pydict(batch)
        if "documentation_chunks" in self.registry:
            existing = self.registry["documentation_chunks"]
            self.registry["documentation_chunks"] = pa.concat_tables([existing, new_table])
        else:
            self.registry["documentation_chunks"] = new_table
        print(f"Appended {new_table.num_rows} chunks to 'documentation_chunks' table.")
        return f"Successfully added {new_table.num_rows} chunks."

    def get_table(self, name: str) -> pa.Table:
        if name in self.registry:
            return self.registry[name]
        raise ValueError(f"Table '{name}' not found.")

    def get_all_tables(self) -> dict:
        return dict(self.registry)

    def get_registered_tables_summary(self):
        summary = {}
        for name, tbl in self.registry.items():
            summary[name] = {
                "rows": tbl.num_rows,
                "columns": tbl.schema.names[:8]
            }
        return summary

    def table_count(self) -> int:
        return len(self.registry)

# -------------------------------------------------------------------
# Ray Remote Task: Swarm Search
# -------------------------------------------------------------------
@ray.remote(num_cpus=1)
def swarm_search(registry_handle, query_key: str, query_value: str):
    """
    Searches all registered Arrow tables for rows where `query_key`
    contains `query_value` (case-insensitive). Returns [{table, row}].
    """
    # pyrefly: ignore [missing-import]
    import pyarrow.compute as pc
    summary = ray.get(registry_handle.get_registered_tables_summary.remote())
    hits = []
    for name in summary.keys():
        try:
            tbl = ray.get(registry_handle.get_table.remote(name))
            if query_key not in tbl.schema.names:
                continue
            col_str = tbl.column(query_key).cast(pa.string())
            mask = pc.match_substring(col_str, query_value, ignore_case=True)
            for record in tbl.filter(mask).to_pylist():
                hits.append({"table": name, "row": record})
        except Exception:
            pass
    return hits


# -------------------------------------------------------------------
# Parquet Audit Flush
# -------------------------------------------------------------------
def flush_parquet_audit(results: list, output_path: str):
    """Write a flat Parquet audit manifest of all ingested files."""
    audit_rows = []
    for res in results:
        audit_rows.append({
            "filename": res["filename"],
            "path": res["path"],
            "status": res["status"],
            "size_kb": res.get("size_kb", 0.0),
            "rows": res.get("rows", 0),
            "genome_prediction": res.get("genome_prediction", "unknown"),
            "columns_csv": ",".join(res.get("columns", [])),
            "error": res.get("error", ""),
        })
    audit_table = pa.Table.from_pylist(audit_rows)
    pq.write_table(audit_table, output_path)
    print(f"\n[AUDIT] Parquet manifest written -> {output_path}")


def main():
    t0 = time.time()
    try:
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        print("Connected to existing Ray cluster.")
    except ConnectionError:
        print("No existing Ray cluster found. Spinning up a new local Ray cluster with strict memory limits...")
        ray.init(namespace="legion", object_store_memory=1500 * 1024 * 1024, _temp_dir=r"C:\tmp\ray", ignore_reinit_error=True, runtime_env={"env_vars": {"PYTHONPATH": r"c:\WEB CASE STUDY;c:\WEB CASE STUDY\sonic_dna_engine;c:\WEB CASE STUDY\antigravity_vscode_ext\backend"}})
        
    print("\n--- Booting Code Swarm Registry ---")
    import ray_code_swarm
    ray_code_swarm.main(keep_alive=False)
    print("--- Code Swarm Boot Complete ---\n")
    
    print("\n--- Booting Sovereign Neural Relay (Ray Serve) ---")
    import sovereign_serve_app
    sovereign_serve_app.deploy_sovereign_relay()
    print("--- Sovereign Neural Relay Boot Complete ---\n")
    
    print("\n--- Booting MCP Servers ---")
    import subprocess
    import sys
    
    print("Starting MCP RAG Server (LegionLakehouse_RAG) on port 8003...")
    subprocess.Popen(
        [sys.executable, "mcp_rag_server.py", "--sse"],
        cwd=r"C:\WEB CASE STUDY"
    )
    
    print("Starting MCP API Server (Legion Unified Onyx) on port 8001...")
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "mcp_api_server:app", "--port", "8001", "--host", "127.0.0.1"],
        cwd=r"C:\WEB CASE STUDY"
    )
    
    print("Starting Prometheus Server on port 9090...")
    log_dir = r"C:\WEB CASE STUDY\sovereign_production\08_logs"
    os.makedirs(log_dir, exist_ok=True)
    prom_log_file = open(os.path.join(log_dir, "prometheus.log"), "a", encoding="utf-8")
    subprocess.Popen(
        [
            r"C:\WEB CASE STUDY\prometheus-3.13.0.windows-amd64\prometheus.exe",
            "--config.file=C:\WEB CASE STUDY\prometheus-3.13.0.windows-amd64\prometheus.yml",
            "--web.listen-address=0.0.0.0:9090"
        ],
        cwd=r"C:\WEB CASE STUDY\prometheus-3.13.0.windows-amd64",
        stdout=prom_log_file,
        stderr=prom_log_file
    )
    print("--- MCP Servers Boot Complete ---\n")
    
    print("\n--- Booting Additional Ray Serve Apps ---")
    import sys
    from ray import serve
    
    sys.path.insert(0, r"c:\WEB CASE STUDY\antigravity_vscode_ext\backend")
    import legion_status_service
    serve.run(legion_status_service.LegionStatusService.bind(), name="legion-status", route_prefix="/legion-status")
    print("[SUCCESS] Legion Status Service deployed via Ray Serve.")
    
    sys.path.insert(0, r"c:\WEB CASE STUDY\sonic_dna_engine")
    import ray_serve_audio_llm
    serve.run(ray_serve_audio_llm.AudioLLMDeployment.bind(), name="AudioLLM", route_prefix="/audio-llm")
    print("[SUCCESS] Audio LLM Service deployed via Ray Serve.")
    print("--- Additional Ray Serve Apps Boot Complete ---\n")
    
    print("\n--- Booting Legion Orchestrator & Warden ---")
    try:
        from run_simulation_with_stem_mastering import LegionOrchestratorV2
        # Keep a reference so actors aren't garbage collected
        global_orchestrator = LegionOrchestratorV2()
        global_orchestrator.boot_swarm()
        print("--- Legion Orchestrator Boot Complete ---\n")
    except Exception as e:
        print(f"--- Failed to boot Legion Orchestrator: {e} ---\n")
    
    # Check if it already exists to prevent re-ingesting every spin-up
    try:
        registry = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
        print("Connected to existing SwarmKnowledgeRegistry actor. Skipping re-ingestion.")
        
        # Just pull summary and exit
        summary = ray.get(registry.get_registered_tables_summary.remote())
        print(f"\nTotal Registered Tables: {len(summary)}")
        print("\n[DETACH] SwarmKnowledgeRegistry is LIVE and DETACHED.")
        return
    except ValueError:
        registry = SwarmKnowledgeRegistry.options(name="SwarmKnowledgeRegistry", namespace="legion", lifetime="detached").remote()
    
    # 1. Discover all candidate target data sources (.json, .jsonl, .parquet)
    valid_extensions = (".json", ".jsonl", ".parquet")
    file_targets = []
    
    # Ableton session exported JSONs
    if os.path.exists(EXPORTED_JSON_DIR):
        for file in os.listdir(EXPORTED_JSON_DIR):
            if file.lower().endswith(valid_extensions) and not file.startswith("."):
                file_targets.append(os.path.join(EXPORTED_JSON_DIR, file))
                
    system_report_path = r"c:\WEB CASE STUDY\system_data_audit_report.json"
    if os.path.exists(system_report_path):
        file_targets.append(system_report_path)

    # Added local data directory
    local_data_dir = r"c:\WEB CASE STUDY\data"
    if os.path.exists(local_data_dir):
        for file in os.listdir(local_data_dir):
            if file.lower().endswith(valid_extensions) and not file.startswith("."):
                file_targets.append(os.path.join(local_data_dir, file))
                
    # Add scattered shards from temp ray folders so we catch ALL the data you processed
    temp_ray_dirs = [r"C:\Users\adams\Local Settings\Temp\ray", r"C:\tmp\ray", r"c:\WEB CASE STUDY\ray_cat_shards"]
    for temp_dir in temp_ray_dirs:
        if os.path.exists(temp_dir):
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith(valid_extensions) and not file.startswith("."):
                        file_targets.append(os.path.join(root, file))

    # Google API Discovery documents (COMMENTED OUT TO PREVENT MEMORY CRASH)
    # discovery_docs_dir = r"C:\WEB CASE STUDY\.venv\Lib\site-packages\googleapiclient\discovery_cache\documents"
    # if os.path.exists(discovery_docs_dir):
    #     for file in os.listdir(discovery_docs_dir):
    #         if file.endswith(".json") and not file.startswith("."):
    #             json_targets.append(os.path.join(discovery_docs_dir, file))


    print(f"\nDistributing {len(file_targets)} files (.json, .jsonl, .parquet) to Ray workers for parallel Arrow conversion...")

    # 2. Fire Ray remote tasks (parallel)
    futures = [ingest_and_convert_file.remote(path, registry) for path in file_targets]
    results = ray.get(futures)

    # 3. Track successes (registration already handled by the workers)
    success_count = 0
    for res in results:
        if res["status"] == "SUCCESS":
            success_count += 1
        else:
            print(f"  [FAIL] {res['filename']}: {res['error']}")

    # 4. Flush Parquet audit manifest
    flush_parquet_audit(results, PARQUET_AUDIT_PATH)

    # 5. Pull summary and flush live snapshot JSON
    summary = ray.get(registry.get_registered_tables_summary.remote())
    snapshot_path = r"c:\WEB CASE STUDY\live_registry_snapshot.json"
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_tables": len(summary),
            "tables": summary,
        }, f, indent=2)
    print(f"[SNAPSHOT] Live registry snapshot -> {snapshot_path}")

    # 6. Console Report
    elapsed = time.time() - t0
    keys = list(summary.keys())
    print("\n" + "=" * 60)
    print(f"  SWARM INGESTION COMPLETE")
    print(f"  Files processed : {len(file_targets)}")
    print(f"  Registered      : {success_count} Arrow tables")
    print(f"  Failed          : {len(file_targets) - success_count}")
    print(f"  Time elapsed    : {elapsed:.2f}s")
    print("=" * 60)
    print(f"\nTotal Registered Tables: {len(keys)}")
    print("Sample Registered Tables (first 10):")
    print(json.dumps({k: summary[k] for k in keys[:10]}, indent=2))

    # 7. Quick search demo
    print("\n[DEMO] Swarm search: 'chris_lake' in 'key' column...")
    hits = ray.get(swarm_search.remote(registry, "key", "chris_lake"))
    if hits:
        print(f"  Found {len(hits)} hit(s):")
        for h in hits[:3]:
            print(f"    [{h['table']}] {h['row']}")
    else:
        print("  No hits — try swarm_search(registry, 'value', 'chris_lake').")

    # 8. Detach cleanly — actor lives in Ray namespace independently
    print("\n[DETACH] SwarmKnowledgeRegistry is LIVE and DETACHED.")
    print("  Reconnect with:")
    print("    import ray")
    print("    ray.init(namespace='legion', ignore_reinit_error=True)")
    print("    registry = ray.get_actor('SwarmKnowledgeRegistry', namespace='legion')")
    print("    summary  = ray.get(registry.get_registered_tables_summary.remote())")
    print(f"\n  Parquet audit : {PARQUET_AUDIT_PATH}")
    print(f"  JSON snapshot : {snapshot_path}")
    print("\nProcess exiting — Ray cluster keeps the registry alive.")
    
    # [WINDOWS FIX] Keep the driver process alive so the local Ray cluster doesn't terminate
    print("\n[INFO] Keeping driver process alive to preserve the Ray cluster and actor. Press Ctrl+C to exit.")
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()