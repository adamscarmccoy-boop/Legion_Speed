
import os
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

import lancedb


import os
import json               # only for logging / fallback if you still need it
import pyarrow as pa

def ingest_and_convert_json(file_path: str):
    """
    Safely read a JSON file and return a PyArrow RecordBatch/Table.
    Handles Unicode, malformed JSON, and I/O errors gracefully.

    Returns:
        dict with keys:
            status          – "SUCCESS" or "ERROR"
            filename         – basename of the input file
            path             – full path to the input file
            size_kb          – size in kilobytes (float)
            rows             – number of records in the Arrow table (0 on error)
            columns          – list of column names (empty if error)
            arrow_table      – pa.Table or None (None on error)
    """
    filename = os.path.basename(file_path)

    # ------------------------------------------------------------------
    # 1️⃣  Try to read the file with PyArrow's JSON reader.
    #     This is fully Unicode‑aware and does NOT rely on Python's json module.
    # ------------------------------------------------------------------
    try:
        table = pa.json.read(file_path)          # <-- safe, no manual decode
    except Exception as exc:                     # catches malformed JSON, encoding errors, etc.
        # Log the problem – you can replace this with your own logger if needed
        print(f"[WARN] Could not read {file_path}: {exc}")

        # Build a consistent “ERROR” record so SwarmKnowledgeRegistry still sees it
        return {
            "status": "ERROR",
            "filename": filename,
            "path": file_path,
            "size_kb": round(os.path.getsize(file_path) / 1024, 2),
            "rows": 0,
            "columns": [],
            "arrow_table": None,
            "error": str(exc)
        }

    # ------------------------------------------------------------------
    # 2️⃣  Build the result dict (same shape as your original function)
    # ------------------------------------------------------------------
    return {
        "status": "SUCCESS",
        "filename": filename,
        "path": file_path,
        "size_kb": round(os.path.getsize(file_path) / 1024, 2),
        "rows": table.num_rows,
        "columns": list(table.schema.names),
        "arrow_table": table
    }

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

import numpy as np
import ray
from scipy.spatial.distance import cdist
from sklearn.preprocessing import StandardScaler


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
print("=== Starting System-Wide Ray-Arrow JSON Swarm Ingestion ===")

# Connect to local Ray cluster
PARQUET_AUDIT_PATH = r"c:\WEB CASE STUDY\code_notebook_knowledge_audit.parquet"

# Removed top-level ray.init() to prevent import crashes during orchestrator boot.

# -------------------------------------------------------------------
# Ray Remote Task: Parallel JSON Ingestion & Arrow Conversion
# -------------------------------------------------------------------
@ray.remote(num_cpus=1)
def ingest_and_convert_file(file_path):
    """Parses a JSON, IPYNB, MD, or TXT file and returns a serialized PyArrow RecordBatch/Table in shared memory."""
    filename = os.path.basename(file_path)
    try:
        sz = os.path.getsize(file_path)
        
        if filename.endswith(".json"):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
            
            # Normalize structural format
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
                
        elif filename.endswith(".ipynb"):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                nb = json.load(f)
            normalized_list = []
            for i, cell in enumerate(nb.get("cells", [])):
                source = "".join(cell.get("source", []))
                if source.strip():
                    normalized_list.append({
                        "cell_index": i,
                        "cell_type": cell.get("cell_type", "unknown"),
                        "source": source
                    })
            if not normalized_list:
                normalized_list = [{"cell_index": -1, "cell_type": "empty", "source": ""}]
                
        elif filename.endswith(".md") or filename.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            # Chunk by paragraph block as per agent rules
            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            normalized_list = [{"paragraph_index": i, "content": p} for i, p in enumerate(paragraphs)]
            if not normalized_list:
                normalized_list = [{"paragraph_index": -1, "content": ""}]
        else:
            raise ValueError("Unsupported file format")

        arrow_table = pa.Table.from_pylist(normalized_list)
        return {
            "status": "SUCCESS",
            "filename": filename,
            "path": file_path,
            "size_kb": round(sz / 1024, 2),
            "rows": len(arrow_table),
            "columns": arrow_table.schema.names,
            "arrow_table": arrow_table
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
class CodeSwarmKnowledgeRegistry:
    def __init__(self):
        # We store direct Tables inside the actor state itself, not ObjectRefs
        # So we do not need to call ray.get() inside the actor.
        self.registry = {}
        print("CodeSwarmKnowledgeRegistry Actor spawned.")

    def register_table(self, name: str, table: pa.Table):
        self.registry[name] = table
        print(f"Registered Code Swarm Table: '{name}' in Actor state.")

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
            "columns_csv": ",".join(res.get("columns", [])),
            "error": res.get("error", ""),
        })
    audit_table = pa.Table.from_pylist(audit_rows)
    pq.write_table(audit_table, output_path)
    print(f"\n[AUDIT] Parquet manifest written -> {output_path}")


def main(keep_alive=True):
    t0 = time.time()
    
    try:
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        print("Connected to existing Ray cluster.")
    except ConnectionError:
        print("No existing Ray cluster found. Spinning up a new local Ray cluster with strict memory limits...")
        ray.init(namespace="legion", object_store_memory=1500 * 1024 * 1024, _temp_dir=r"C:\tmp\ray", ignore_reinit_error=True)
    
    # Check if it already exists to prevent re-ingesting every spin-up
    try:
        registry = ray.get_actor("CodeSwarmKnowledgeRegistry", namespace="legion")
        print("Connected to existing CodeSwarmKnowledgeRegistry actor. Skipping re-ingestion.")
        
        # Just pull summary and go to loop
        summary = ray.get(registry.get_registered_tables_summary.remote())
        print(f"\nTotal Registered Tables: {len(summary)}")
        if keep_alive:
            print("\n[INFO] Keeping driver process alive to preserve the Ray cluster and actor. Press Ctrl+C to exit.")
            while True:
                time.sleep(60)
            
    except ValueError:
        registry = CodeSwarmKnowledgeRegistry.options(name="CodeSwarmKnowledgeRegistry", namespace="legion", lifetime="detached").remote()
    
    # 1. Discover all candidate target data sources
    file_targets = []
    
    # 1a. Discover JSON files in GDU dir
    gdu_dir = r"c:\WEB CASE STUDY\gdu_per_dir"
    if os.path.exists(gdu_dir):
        for root, dirs, files in os.walk(gdu_dir):
            for file in files:
                if file.endswith(".json") and not file.startswith("."):
                    file_targets.append(os.path.join(root, file))
                    
    # 1b. Discover Notebooks and Markdown/Text files in the workspace root
    workspace_dir = r"c:\WEB CASE STUDY"
    if os.path.exists(workspace_dir):
        for file in os.listdir(workspace_dir):
            if file.endswith((".ipynb", ".md", ".txt")) and not file.startswith("."):
                file_targets.append(os.path.join(workspace_dir, file))
        # Optional: Also add docs directory
        docs_dir = os.path.join(workspace_dir, "docs")
        if os.path.exists(docs_dir):
            for file in os.listdir(docs_dir):
                if file.endswith((".md", ".txt")) and not file.startswith("."):
                    file_targets.append(os.path.join(docs_dir, file))

    print(f"\nFound {len(file_targets)} total files to ingest.")

    print(f"\nDistributing {len(file_targets)} files to Ray workers for parallel Arrow conversion...")

    # 2. Fire Ray remote tasks (parallel)
    futures = [ingest_and_convert_file.remote(path) for path in file_targets]
    results = ray.get(futures)

    # 3. Register successfully parsed Arrow tables — await all futures before flushing
    success_count = 0
    register_futures = []
    for res in results:
        if res["status"] == "SUCCESS":
            logical_name = os.path.splitext(res["filename"])[0]
            f = registry.register_table.remote(logical_name, res["arrow_table"])
            register_futures.append(f)
            success_count += 1
        else:
            print(f"  [FAIL] {res['filename']}: {res['error']}")

    ray.get(register_futures)  # wait for all registrations to land

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
    print(f"  CODE SWARM INGESTION COMPLETE")
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
    print("\n[DETACH] CodeSwarmKnowledgeRegistry is LIVE and DETACHED.")
    print("  Reconnect with:")
    print("    import ray")
    print("    ray.init(namespace='legion', ignore_reinit_error=True)")
    print("    registry = ray.get_actor('CodeSwarmKnowledgeRegistry', namespace='legion')")
    print("    summary  = ray.get(registry.get_registered_tables_summary.remote())")
    print(f"\n  Parquet audit : {PARQUET_AUDIT_PATH}")
    print(f"  JSON snapshot : {snapshot_path}")
    print("\nProcess exiting — Ray cluster keeps the registry alive.")
    
    # [WINDOWS FIX] Keep the driver process alive so the local Ray cluster doesn't terminate
    if keep_alive:
        print("\n[INFO] Keeping driver process alive to preserve the Ray cluster and actor. Press Ctrl+C to exit.")
        while True:
            time.sleep(60)


if __name__ == "__main__":
    main()
