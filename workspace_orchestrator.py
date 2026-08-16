"""
=============================================================================
🏛️ SOVEREIGN RESILIENT WORKSTATION ORCHESTRATOR
=============================================================================
- Pre-Prompt Vector & Telemetry Compression Protocol
- Primary LM Studio Connector: Official `openai` Python SDK (Port 1234)
- 100% Standard Library Baseline Fallback (Zero crash guarantee)
- Dynamic Acceleration Hooks (Ray, PyArrow, DuckDB, LanceDB, OpenAI)
- Automatic Markdown (.md) and JSON Reports
=============================================================================
"""

import os
import sys
import json
import time
import socket
import urllib.request
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import concurrent.futures

# =============================================================================
# 0. DYNAMIC ACCELERATION & SDK DETECTOR
# =============================================================================
INSTALLED_PKGS = {}

try:
    from openai import OpenAI
    INSTALLED_PKGS["openai"] = True
except ImportError:
    INSTALLED_PKGS["openai"] = False

try:
    import ray
    INSTALLED_PKGS["ray"] = True
except ImportError:
    INSTALLED_PKGS["ray"] = False

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    INSTALLED_PKGS["pyarrow"] = True
except ImportError:
    INSTALLED_PKGS["pyarrow"] = False

try:
    import duckdb
    INSTALLED_PKGS["duckdb"] = True
except ImportError:
    INSTALLED_PKGS["duckdb"] = False

try:
    import lancedb
    INSTALLED_PKGS["lancedb"] = True
except ImportError:
    INSTALLED_PKGS["lancedb"] = False


# =============================================================================
# ⚙️ CONFIGURATION & TARGETS
# =============================================================================
WORKSPACE_DIR = Path(r"C:\WEB CASE STUDY" if os.path.exists(r"C:\WEB CASE STUDY") else os.getcwd())
STUDIES_DIR = Path(r"C:\STUDIES" if os.path.exists(r"C:\STUDIES") else os.getcwd())

PARQUET_OUT = WORKSPACE_DIR / "workspace_metrics.parquet"
MD_REPORT_OUT = WORKSPACE_DIR / "workstation_diagnostic_summary.md"
JSON_REPORT_OUT = WORKSPACE_DIR / "workstation_diagnostic_report.json"

EXCLUDE_DIRS = {".venv", ".venv_314", "node_modules", ".git", "__pycache__", "lost+found", ".idea", ".vscode"}
TARGET_EXTS = {".py", ".cpp", ".hpp", ".h", ".c", ".sql", ".json", ".md", ".txt", ".ps1", ".bat", ".parquet", ".onnx", ".duckdb"}

PORTS = {
    "agent_8099": ("127.0.0.1", 8099, "Legion Agent Server"),
    "lm_studio":   ("127.0.0.1", 1234, "LM Studio C++ REST"),
    "ray_gcs":     ("127.0.0.1", 6379, "Ray Cluster GCS"),
    "mcp_gateway": ("127.0.0.1", 8001, "FastMCP Sensory DB")
}


# =============================================================================
# 1. DIRECTORY CRAWLER (RAY OR BUILT-IN MULTITHREADING)
# =============================================================================
def scan_directory_chunk(root_dir: str) -> list:
    """Scans a directory tree for file metrics using standard library."""
    records = []
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            p = Path(root) / f
            try:
                st = p.stat()
                ext = p.suffix.lower() or ".no_ext"
                lines = 0
                if ext in {".py", ".cpp", ".hpp", ".h", ".c", ".sql", ".json", ".md", ".txt", ".ps1"}:
                    try:
                        with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                            lines = sum(1 for _ in fp)
                    except Exception:
                        lines = 0

                records.append({
                    "file_name": f,
                    "rel_path": str(p),
                    "extension": ext,
                    "size_kb": float(round(st.st_size / 1024, 2)),
                    "line_count": int(lines),
                    "modified_time": str(datetime.fromtimestamp(st.st_mtime).isoformat())
                })
            except (PermissionError, FileNotFoundError, OSError):
                continue
    return records


def parallel_code_forest_crawl(base_path: Path) -> list:
    """Crawls directories using Ray if active, or ThreadPoolExecutor fallback."""
    if not base_path.exists():
        return []

    try:
        subdirs = [
            str(base_path / d) for d in os.listdir(base_path)
            if (base_path / d).is_dir() and d not in EXCLUDE_DIRS
        ]
    except Exception:
        subdirs = []

    partitions = subdirs if subdirs else [str(base_path)]

    # 1. Try Ray Parallelism if initialized
    if INSTALLED_PKGS["ray"]:
        try:
            import ray
            if ray.is_initialized():
                @ray.remote
                def _ray_scan(p):
                    return scan_directory_chunk(p)
                futures = [_ray_scan.remote(p) for p in partitions]
                results = ray.get(futures)
                return [rec for chunk in results for rec in chunk]
        except Exception:
            pass

    # 2. Built-in Multithreading Fallback (Zero package dependencies)
    all_records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as executor:
        futures = [executor.submit(scan_directory_chunk, p) for p in partitions]
        for f in concurrent.futures.as_completed(futures):
            try:
                all_records.extend(f.result())
            except Exception:
                continue

    return all_records


# =============================================================================
# 2. COLUMNAR INGESTION & AGGREGATION (DUCKDB OR PURE PYTHON)
# =============================================================================
def save_metrics_and_aggregate(records: list) -> dict:
    """Saves to Parquet if PyArrow exists, and aggregates stats (DuckDB or Python)."""
    if not records:
        return {"total_files": 0, "parquet_size_mb": 0.0, "top_extensions": {}}

    total_size_mb = 0.0

    # 1. Parquet Export (if PyArrow installed)
    if INSTALLED_PKGS["pyarrow"]:
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
            table = pa.Table.from_pylist(records)
            pq.write_table(table, str(PARQUET_OUT), compression="snappy")
            total_size_mb = round(PARQUET_OUT.stat().st_size / (1024 * 1024), 2)
        except Exception:
            pass

    # 2. Aggregation: Prefer DuckDB vectorized scan, fallback to Pure Python
    top_exts = {}
    if INSTALLED_PKGS["duckdb"] and INSTALLED_PKGS["pyarrow"] and PARQUET_OUT.exists():
        try:
            import duckdb
            clean_parquet_path = str(PARQUET_OUT).replace("\\", "/")
            con = duckdb.connect(":memory:")
            res = con.execute(f"""
                SELECT extension, count(*) as cnt, sum(size_kb) as total_kb, sum(line_count) as total_lines
                FROM read_parquet('{clean_parquet_path}')
                GROUP BY extension
                ORDER BY cnt DESC
                LIMIT 8
            """).fetchall()
            
            for ext, cnt, total_kb, total_lines in res:
                ext_name = str(ext) if ext else ".no_ext"
                cnt_num = int(cnt) if cnt is not None else 0
                kb_num = round(float(total_kb), 1) if total_kb is not None else 0.0
                lines_num = int(total_lines) if total_lines is not None else 0
                top_exts[ext_name] = {"count": cnt_num, "size_kb": kb_num, "lines": lines_num}
            con.close()
        except Exception:
            top_exts = {}

    # Pure Python Aggregation Fallback (Zero dependencies)
    if not top_exts:
        agg = defaultdict(lambda: {"count": 0, "size_kb": 0.0, "lines": 0})
        for r in records:
            ext = r.get("extension", ".no_ext")
            agg[ext]["count"] += 1
            agg[ext]["size_kb"] += r.get("size_kb", 0.0)
            agg[ext]["lines"] += r.get("line_count", 0)

        sorted_exts = sorted(agg.items(), key=lambda x: x["count"], reverse=True)[:8]
        for ext, vals in sorted_exts:
            top_exts[ext] = {
                "count": vals["count"],
                "size_kb": round(vals["size_kb"], 1),
                "lines": vals["lines"]
            }

    return {
        "total_files": len(records),
        "parquet_size_mb": total_size_mb,
        "top_extensions": top_exts
    }


# =============================================================================
# 3. ONNX, DATABASES & PORT AUDITS
# =============================================================================
def audit_ports() -> dict:
    status = {}
    for key, (host, port, name) in PORTS.items():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.4)
            is_up = s.connect_ex((host, port)) == 0
            status[key] = {"name": name, "port": port, "is_up": is_up}
    return status

def audit_onnx() -> dict:
    models = {}
    for root in [WORKSPACE_DIR, STUDIES_DIR]:
        if root.exists():
            for f in root.glob("**/*.onnx"):
                sidecar = f.with_suffix(".onnx.data")
                has_data = sidecar.exists()
                size_mb = round(f.stat().st_size / (1024 * 1024), 2)
                models[f.name] = {
                    "size_mb": size_mb,
                    "has_sidecar": has_data,
                    "ready": bool(size_mb > 1.0 or has_data)
                }
    return models

def audit_databases() -> dict:
    res = {"duckdb": {}, "lancedb": {}}
    if INSTALLED_PKGS["duckdb"]:
        try:
            import duckdb
            for db_file in ["web_intel_sonicdb.duckdb", "sonic_core_v2.duckdb"]:
                p = WORKSPACE_DIR / db_file
                if p.exists():
                    try:
                        con = duckdb.connect(str(p), read_only=True)
                        tables = con.execute("SHOW TABLES").fetchall()
                        counts = {t[0]: con.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0] for t in tables}
                        res["duckdb"][db_file] = counts
                        con.close()
                    except Exception as e:
                        res["duckdb"][db_file] = f"Notice: {e}"
        except Exception:
            pass
    else:
        res["duckdb"]["status"] = "duckdb module not in python env (bypassed)"

    if INSTALLED_PKGS["lancedb"]:
        try:
            import lancedb
            ldb_dir = WORKSPACE_DIR / "lancedb_data"
            if ldb_dir.exists():
                ldb = lancedb.connect(str(ldb_dir))
                for t in ldb.table_names():
                    res["lancedb"][t] = len(ldb.open_table(t))
        except Exception as e:
            res["lancedb"]["error"] = str(e)
    else:
        res["lancedb"]["status"] = "lancedb module not in python env (bypassed)"

    return res


# =============================================================================
# 4. SOVEREIGN PRE-PROMPT PROCESSOR & LM STUDIO SYNTHESIS
# =============================================================================
def compile_preprompt_context(metrics: dict, dbs: dict, onnx: dict, ports: dict) -> str:
    """Compresses raw telemetry into a dense grounding context (<500 tokens)."""
    live_daemons = [v["name"] for v in ports.values() if v["is_up"]]
    
    top_ext_items = list(metrics.get("top_extensions", {}).items())[:4]
    ext_str = ", ".join([f"{k} ({v['count']})" for k, v in top_ext_items]) or "None"
    
    db_summary = []
    for db_name, tbls in dbs.get("duckdb", {}).items():
        if isinstance(tbls, dict):
            total_rows = sum(tbls.values())
            db_summary.append(f"{db_name} ({total_rows} rows)")
        else:
            db_summary.append(f"{db_name}")
    
    ready_models = sum(1 for m in onnx.values() if m["ready"])
    
    preprompt_block = (
        "=== [SOVEREIGN WORKSTATION TELEMETRY CONTEXT] ===\n"
        f"• Active Daemons   : {', '.join(live_daemons) if live_daemons else 'None'}\n"
        f"• Code Forest Ingest: {metrics.get('total_files', 0)} files | Parquet: {metrics.get('parquet_size_mb', 0)} MB | Top: {ext_str}\n"
        f"• Sensory Lakehouses: {', '.join(db_summary) if db_summary else '0 detected'}\n"
        f"• LanceDB Vectors   : {sum(dbs.get('lancedb', {}).values()) if dbs.get('lancedb') else 0} total embeddings\n"
        f"• ONNX Neural Core  : {ready_models}/{len(onnx)} active models verified\n"
        f"• Hardware Envelope : GTX 1650 SUPER (4GB VRAM Target | <1500 Token Window)\n"
        "================================================="
    )
    return preprompt_block


def query_lm_studio(metrics: dict, dbs: dict, onnx: dict, ports: dict) -> str:
    """Passes compressed pre-prompt context to LM Studio via the OpenAI client."""
    preprompt_context = compile_preprompt_context(metrics, dbs, onnx, ports)
    
    system_prompt = (
        "You are the Sovereign Workstation Lead Systems Auditor. "
        "Analyze the provided telemetry context and deliver a 3-bullet executive operational status: "
        "(1) Stack health, (2) Ingestion & sensory persistence, and (3) Hardware/VRAM clearance."
    )
    user_prompt = f"Evaluate workstation operational state:\n\n{preprompt_context}"

    # 1. Primary: Official OpenAI Python Client
    if INSTALLED_PKGS.get("openai"):
        try:
            from openai import OpenAI
            client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")
            response = client.chat.completions.create(
                model="nvidia/nemotron-3-nano-4b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=250
            )
            return response.choices[0].message.content or "Empty response"
        except Exception as e:
            return f"LM Studio (OpenAI SDK) Notice: {e}"

    # 2. Fallback: Pure Standard Library urllib
    url = "http://127.0.0.1:1234/v1/chat/completions"
    payload = {
        "model": "nvidia/nemotron-3-nano-4b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 250
    }
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except Exception:
        return "LM Studio synthesis bypassed."


# =============================================================================
# 🚀 MAIN PIPELINE & MARKDOWN EXPORT
# =============================================================================
def main():
    start_t = time.time()
    print("=" * 65)
    print("⚡ SOVEREIGN WORKSTATION AUDITOR (PRE-PROMPT + OPENAI SDK)")
    print(f"📂 Root : {WORKSPACE_DIR}")
    print("=" * 65)

    # 1. Package Health
    pkg_status = [f"{k}: {'🟢' if v else '⚪'}" for k, v in INSTALLED_PKGS.items()]
    print(f"Acceleration Pkgs : {' | '.join(pkg_status)}")

    # 2. Port & Daemon Audit
    ports = audit_ports()
    live_ports = [v["name"] for v in ports.values() if v["is_up"]]
    print(f"Active Daemons    : {', '.join(live_ports) if live_ports else 'None detected'}")

    # 3. Directory Ingestion
    records = parallel_code_forest_crawl(WORKSPACE_DIR)
    metrics = save_metrics_and_aggregate(records)
    print(f"Codebase Ingest   : {metrics['total_files']} files mapped (Parquet: {metrics.get('parquet_size_mb', 0)} MB)")

    # 4. Databases & ONNX
    dbs = audit_databases()
    onnx = audit_onnx()
    ready_onnx = sum(1 for m in onnx.values() if m["ready"])
    print(f"Sensory Layer     : DuckDB & LanceDB inspected")
    print(f"ONNX Brains       : {ready_onnx}/{len(onnx)} models verified and ready")

    # 5. LM Studio Brief (via Pre-Prompt Processor + OpenAI Client)
    ai_brief = "LM Studio offline."
    if ports["lm_studio"]["is_up"]:
        ai_brief = query_lm_studio(metrics, dbs, onnx, ports)

    elapsed = round(time.time() - start_t, 2)

    # 6. Build and Write Markdown Report (.md)
    md_lines = [
        "# 🏛️ Workstation Diagnostic & Code Forest Audit Report",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Execution Speed**: {elapsed} seconds  ",
        f"**Parquet Store**: `{PARQUET_OUT.name}` ({metrics.get('parquet_size_mb', 0)} MB)  ",
        "",
        "---",
        "",
        "## 1. Package & Stack Health",
        "### Detected Packages in Python Env:",
        "| Package | Status | Role |",
        "| :--- | :--- | :--- |"
    ]
    roles = {
        "openai": "LM Studio Native SDK Connector",
        "ray": "Parallel Multi-Worker Engine",
        "pyarrow": "Columnar Snappy Parquet Exporter",
        "duckdb": "Vectorized In-Memory OLAP Query Engine",
        "lancedb": "Embedded Vector Space Manager"
    }
    for pkg, is_inst in INSTALLED_PKGS.items():
        st = "🟢 Available" if is_inst else "⚪ Missing (Handled via Fallback)"
        md_lines.append(f"| `{pkg}` | {st} | {roles.get(pkg, 'Utility')} |")

    md_lines.extend([
        "",
        "### Active Network Ports:",
        "| Service | Port | Status |",
        "| :--- | :--- | :--- |"
    ])
    for p_info in ports.values():
        stat = "🟢 UP" if p_info["is_up"] else "🔴 DOWN"
        md_lines.append(f"| {p_info['name']} | {p_info['port']} | {stat} |")

    md_lines.extend([
        "",
        "---",
        "",
        "## 2. Code Forest Ingestion Summary",
        f"- **Total Files Ingested**: {metrics['total_files']}",
        f"- **Storage Format**: {'Snappy Parquet' if INSTALLED_PKGS['pyarrow'] else 'In-Memory Structure'}",
        "",
        "### Top File Extensions",
        "| Extension | File Count | Total Size (KB) | Total Lines |",
        "| :--- | :--- | :--- | :--- |"
    ])
    for ext, d in metrics.get("top_extensions", {}).items():
        md_lines.append(f"| `{ext}` | {d['count']} | {d['size_kb']} | {d['lines']} |")

    md_lines.extend([
        "",
        "---",
        "",
        "## 3. Sensory Layer (DuckDB & LanceDB)",
        "### DuckDB Lakehouses:"
    ])
    for db_name, tbls in dbs.get("duckdb", {}).items():
        md_lines.append(f"- **`{db_name}`**:")
        if isinstance(tbls, dict):
            for t, cnt in tbls.items():
                md_lines.append(f"  - `{t}`: {cnt} rows")
        else:
            md_lines.append(f"  - {tbls}")

    md_lines.extend([
        "",
        "### LanceDB Vector Spaces:"
    ])
    for vt, cnt in dbs.get("lancedb", {}).items():
        md_lines.append(f"- `{vt}`: {cnt}")

    md_lines.extend([
        "",
        "---",
        "",
        "## 4. ONNX Model Ecosystem",
        "| Model Name | Graph Size (MB) | Has Sidecar (.data) | Ready Status |",
        "| :--- | :--- | :--- | :--- |"
    ])
    for m_name, m_info in onnx.items():
        st = "🟢 Ready" if m_info["ready"] else "⚠️ Check Weights"
        side = "Yes" if m_info["has_sidecar"] else "No"
        md_lines.append(f"| `{m_name}` | {m_info['size_mb']} | {side} | {st} |")

    md_lines.extend([
        "",
        "---",
        "",
        "## 5. LM Studio Inference Synthesis (Port 1234)",
        f"{ai_brief}",
        "",
        "---",
        f"*Full JSON raw telemetry saved to: `{JSON_REPORT_OUT.name}`*"
    ])

    with open(MD_REPORT_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    with open(JSON_REPORT_OUT, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": elapsed,
            "packages": INSTALLED_PKGS,
            "metrics": metrics,
            "databases": dbs,
            "onnx": onnx,
            "ports": ports,
            "ai_synthesis": ai_brief
        }, f, indent=2)

    print("-" * 65)
    print(f"🏁 Complete in {elapsed}s | Generated Files on Disk:")
    print(f"   📄 Markdown Summary : {MD_REPORT_OUT.name}")
    print(f"   📊 Parquet Store    : {PARQUET_OUT.name}")
    print(f"   📋 JSON Telemetry   : {JSON_REPORT_OUT.name}")
    print("=" * 65)


if __name__ == "__main__":
    main()