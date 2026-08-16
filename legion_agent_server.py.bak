
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

"""
LEGION AGENT SERVER — Office Agent's Personal MCP+API
======================================================
Port: 8099 (dedicated, never conflicts with your stack)
Transport: FastMCP SSE + FastAPI REST on same port
Venv: C:\\WEB CASE STUDY\\.venv

What this gives Office Agent:
  - Direct read/write to YOUR DuckDB, LanceDB, Parquet
  - Real Snowflake embed via LM Studio :1234
  - Real Ollama inference :11434
  - Proxies to your mcp_api_server :8001/:8002 when live
  - Standalone when your stack is down
  - Logfire traced on every operation
  - SSE transport so Claude/MCP clients connect directly

Run:
  "C:\\WEB CASE STUDY\\.venv\\Scripts\\python.exe" legion_agent_server.py
"""

import os, sys, json, logging, socket, time, traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

# Force UTF-8 everywhere on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

# ── LOGFIRE ───────────────────────────────────────────────────────────────────
import logfire
logfire.configure(
    service_name="legion-agent-server",
    service_version="1.0.0",
    environment="local",
    send_to_logfire=os.getenv("LOGFIRE_TOKEN") is not None,
)

logging.basicConfig(
    level=logging.INFO, stream=sys.stderr,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("legion-agent")

# ── GROUND TRUTH PATHS ────────────────────────────────────────────────────────
DUCKDB_V1      = r"C:\STUDIES_BACKUP\data\metadata\sonic_core.duckdb"
DUCKDB_V2      = r"C:\STUDIES_BACKUP\data\metadata\sonic_core_v2.duckdb"
LANCE_STORE    = r"C:\STUDIES_BACKUP\vectors\lancedb_store"
PARQUET_DIR    = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\AI_Logs\parquet_exports"
TARGET_VEC     = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\AI_Logs\target_vector.json"
MCP_TOOLS      = os.getenv("MCP_TOOLS_EXEC",  "http://127.0.0.1:8002/tools/execute")
MCP_API        = os.getenv("MCP_API_BASE",    "http://127.0.0.1:8001")
LM_STUDIO      = os.getenv("LM_STUDIO_BASE",  "http://127.0.0.1:1234")
OLLAMA         = os.getenv("OLLAMA_BASE",      "http://127.0.0.1:11434")
SNOWFLAKE_MDL  = "text-embedding-snowflake-arctic-embed-l-v2.0"
PORT           = int(os.getenv("AGENT_PORT",   "8099"))

logfire.info("Legion Agent Server initializing", port=PORT,
             duckdb_v1=DUCKDB_V1, lance=LANCE_STORE)

# ── IMPORTS ───────────────────────────────────────────────────────────────────
import httpx
import duckdb
import lancedb
import numpy as np
from fastmcp import FastMCP
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# ── HELPERS ───────────────────────────────────────────────────────────────────
def port_up(port: int, host="127.0.0.1") -> bool:
    s = socket.socket(); s.settimeout(0.5)
    up = s.connect_ex((host, port)) == 0; s.close(); return up

def _post_local(url: str, payload: dict, timeout=20) -> dict:
    with httpx.Client(timeout=timeout) as c:
        r = c.post(url, json=payload); r.raise_for_status(); return r.json()

def _get_local(url: str, timeout=8) -> dict:
    with httpx.Client(timeout=timeout) as c:
        r = c.get(url); r.raise_for_status(); return r.json()

def _embed(text: str) -> list:
    """Snowflake arctic embed via LM Studio."""
    r = _post_local(f"{LM_STUDIO}/v1/embeddings",
                    {"model": SNOWFLAKE_MDL, "input": text}, timeout=15)
    return r["data"][0]["embedding"]

def _duckdb_query(sql: str, db: str = "v1") -> str:
    path = DUCKDB_V2 if db == "v2" else DUCKDB_V1
    if not Path(path).exists():
        return json.dumps({"error": f"DB not found: {path}"})
    con = duckdb.connect(path, read_only=True)
    try:
        df = con.execute(sql).fetchdf()
        return df.head(100).to_json(orient="records", date_format="iso")
    except Exception as e:
        return json.dumps({"error": str(e), "sql": sql})
    finally:
        con.close()

def _lance_search(query_vec: list, table: str, top_k: int) -> str:
    if not Path(LANCE_STORE).exists():
        return json.dumps({"error": f"LanceDB not found: {LANCE_STORE}"})
    try:
        db  = lancedb.connect(LANCE_STORE)
        tbl = db.open_table(table)
        res = tbl.search(query_vec).limit(top_k).to_pandas()
        drop = [c for c in res.columns if "vector" in c.lower()]
        if drop: res = res.drop(columns=drop)
        return res.to_json(orient="records", date_format="iso")
    except Exception as e:
        return json.dumps({"error": str(e)})

# ── FASTMCP SERVER ────────────────────────────────────────────────────────────
mcp = FastMCP(
    "Legion-Agent-Server",
    instructions=(
        "Office Agent's direct read/write interface to the Legion stack. "
        "Use read_duckdb for SQL queries, search_lancedb for vector search, "
        "embed_text for Snowflake embeddings, ask_ollama for local inference, "
        "stack_health to check all services, and proxy_tool to call any "
        "mcp_api_server tool when it's live."
    )
)

# ── TOOL 1: stack_health ──────────────────────────────────────────────────────
@mcp.tool()
def stack_health() -> str:
    """
    Full Legion stack health check. Returns live port status for all services
    plus DuckDB row counts and LanceDB table inventory.
    Deterministic — no LLM.
    """
    with logfire.span("stack_health"):
        ports = {
            6379:  "Ray GCS",
            8265:  "Ray Dashboard",
            10001: "Ray client",
            8000:  "api_bridge",
            8001:  "mcp_api_server",
            8002:  "MCP tool execution",
            8003:  "mcp_rag_server",
            8099:  "legion_agent_server (me)",
            1234:  "LM Studio / Snowflake",
            11434: "Ollama",
        }
        status = {label: ("🟢 UP" if port_up(p) else "⚫ DOWN")
                  for p, label in ports.items()}

        # DuckDB counts
        for label, path, sql in [
            ("duckdb_v1_rows", DUCKDB_V1, "SELECT COUNT(*) as n FROM t_core_memory"),
            ("duckdb_v2_rows", DUCKDB_V2, "SELECT COUNT(*) as n FROM audio_features"),
        ]:
            if Path(path).exists():
                try:
                    con = duckdb.connect(path, read_only=True)
                    n = con.execute(sql).fetchone()[0]; con.close()
                    status[label] = n
                except Exception as e:
                    status[label] = f"error: {e}"
            else:
                status[label] = "not found"

        # LanceDB tables
        if Path(LANCE_STORE).exists():
            try:
                db = lancedb.connect(LANCE_STORE)
                tables = db.table_names()
                status["lancedb_tables"] = {
                    t: lancedb.connect(LANCE_STORE).open_table(t).count_rows()
                    for t in tables
                }
            except Exception as e:
                status["lancedb_tables"] = f"error: {e}"

        logfire.info("stack_health complete", services_up=sum(
            1 for v in status.values() if v == "🟢 UP"))
        return json.dumps(status, indent=2, default=str)

# ── TOOL 2: read_duckdb ───────────────────────────────────────────────────────
@mcp.tool()
def read_duckdb(sql: str, db: str = "v1") -> str:
    """
    Execute SQL directly against DuckDB Sonic Core.
    db='v1': sonic_core.duckdb — t_core_memory (filename, bpm, key_signature,
             vibe_tags, genre_class, ingested_at). 3560 rows.
    db='v2': sonic_core_v2.duckdb — audio_features (46 cols),
             t_producer_dna_node0, t_sovereign_grading,
             t_musicological_registry_v10.
    Returns up to 100 rows as JSON.
    """
    with logfire.span("read_duckdb", db=db, sql=sql[:80]):
        result = _duckdb_query(sql, db)
        logfire.info("duckdb query complete", db=db)
        return result

# ── TOOL 3: write_duckdb ──────────────────────────────────────────────────────
@mcp.tool()
def write_duckdb(sql: str, db: str = "v2") -> str:
    """
    Execute a write SQL statement against DuckDB (INSERT/UPDATE/CREATE/DELETE).
    Defaults to v2 (sonic_core_v2.duckdb) to protect v1 production data.
    Returns rows_affected or error.
    """
    with logfire.span("write_duckdb", db=db, sql=sql[:80]):
        path = DUCKDB_V2 if db == "v2" else DUCKDB_V1
        if not Path(path).exists():
            return json.dumps({"error": f"DB not found: {path}"})
        con = duckdb.connect(path)
        try:
            con.execute(sql)
            con.commit()
            logfire.info("duckdb write complete", db=db)
            return json.dumps({"success": True, "sql": sql})
        except Exception as e:
            logfire.error("duckdb write failed", error=str(e))
            return json.dumps({"error": str(e), "sql": sql})
        finally:
            con.close()

# ── TOOL 4: embed_text ────────────────────────────────────────────────────────
@mcp.tool()
def embed_text(text: str) -> str:
    """
    Get Snowflake arctic embed from LM Studio (:1234).
    Model: text-embedding-snowflake-arctic-embed-l-v2.0
    Returns dim, first 8 values preview, and confirms full vector available.
    """
    with logfire.span("embed_text", text_len=len(text)):
        try:
            vec = _embed(text)
            logfire.info("embed complete", dim=len(vec))
            return json.dumps({
                "model": SNOWFLAKE_MDL,
                "dim": len(vec),
                "preview_8": vec[:8],
                "norm": float(np.linalg.norm(vec)),
                "status": "ok"
            })
        except Exception as e:
            logfire.error("embed failed", error=str(e))
            return json.dumps({"error": str(e),
                               "hint": "Is LM Studio running on :1234?"})

# ── TOOL 5: search_lancedb ────────────────────────────────────────────────────
@mcp.tool()
def search_lancedb(query: str, table: str = "audio_vibe_gpu", top_k: int = 5) -> str:
    """
    Semantic search via Snowflake embed → LanceDB.
    Tables: audio_vibe_gpu (384-dim, 2010 rows),
            audio_manifest_vectors (768-dim, 500 rows),
            mined_code_vectors, duckdb_metadata_vectors (1024-dim).
    Embeds query via LM Studio Snowflake model, searches LanceDB directly.
    """
    with logfire.span("search_lancedb", query=query, table=table, top_k=top_k):
        try:
            # Get Snowflake embed
            vec = _embed(query)
            logfire.info("embed done, searching LanceDB",
                        dim=len(vec), table=table)

            # Resize if needed (audio_vibe_gpu is 384-dim, Snowflake is 1024-dim)
            db_obj  = lancedb.connect(LANCE_STORE)
            tbl_obj = db_obj.open_table(table)
            schema  = tbl_obj.schema
            vec_dim = None
            for field in schema:
                if "vector" in field.name.lower():
                    try: vec_dim = field.type.list_size
                    except: pass
                    break

            if vec_dim and vec_dim != len(vec):
                # Truncate or pad to match table dim
                if vec_dim < len(vec):
                    q = np.array(vec[:vec_dim], dtype=np.float32)
                else:
                    q = np.pad(vec, (0, vec_dim - len(vec)))
                q = q / (np.linalg.norm(q) + 1e-9)
                vec = q.tolist()

            result = _lance_search(vec, table, top_k)
            logfire.info("lancedb search complete", table=table, top_k=top_k)
            return result
        except Exception as e:
            logfire.error("search_lancedb failed", error=str(e))
            return json.dumps({"error": str(e)})

# ── TOOL 6: write_lancedb ─────────────────────────────────────────────────────
@mcp.tool()
def write_lancedb(table: str, records: str) -> str:
    """
    Write records to a LanceDB table.
    records: JSON array string of dicts. Each dict must include a 'vector' field
             matching the table's dimension, plus any metadata fields.
    Example: '[{"vector": [0.1, ...], "filename": "track.wav", "bpm": 128}]'
    """
    with logfire.span("write_lancedb", table=table):
        try:
            data = json.loads(records)
            db_obj = lancedb.connect(LANCE_STORE)
            if table in db_obj.table_names():
                tbl = db_obj.open_table(table)
                tbl.add(data)
            else:
                db_obj.create_table(table, data=data)
            logfire.info("lancedb write complete",
                        table=table, rows=len(data))
            return json.dumps({"success": True,
                               "table": table, "rows_written": len(data)})
        except Exception as e:
            logfire.error("write_lancedb failed", error=str(e))
            return json.dumps({"error": str(e)})

# ── TOOL 7: ask_ollama ────────────────────────────────────────────────────────
@mcp.tool()
def ask_ollama(prompt: str, model: str = "gemma2:2b",
               max_tokens: int = 512) -> str:
    """
    Local inference via Ollama (:11434).
    Models available: gemma2:2b, phi3, any model you've pulled.
    Use for: DSP reasoning, track analysis, audio engineering advice.
    """
    with logfire.span("ask_ollama", model=model):
        try:
            result = _post_local(f"{OLLAMA}/api/generate", {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens}
            }, timeout=90)
            response = result.get("response", "")
            logfire.info("ollama inference complete",
                        model=model, tokens=len(response.split()))
            return response
        except Exception as e:
            logfire.error("ask_ollama failed", error=str(e))
            return json.dumps({"error": str(e),
                               "hint": "Is Ollama running on :11434?"})

# ── TOOL 8: proxy_tool ────────────────────────────────────────────────────────
@mcp.tool()
def proxy_tool(tool: str, parameters: str = "{}") -> str:
    """
    Proxy any tool call to mcp_api_server (:8002/tools/execute).
    Use when mcp_api_server is live for: pipeline_health_summary,
    get_asset_grid, get_artist_dna, search_tracks, check_ingestion_status,
    execute_langgraph, generate_music_track, analyze_audio_file, etc.
    parameters: JSON string of tool parameters.
    """
    with logfire.span("proxy_tool", tool=tool):
        if not port_up(8002):
            return json.dumps({
                "error": "mcp_api_server not running on :8002",
                "hint": "Start with: c:\\STUDIES_BACKUP\\.venv_fresh\\Scripts\\python.exe mcp_api_server.py"
            })
        try:
            params = json.loads(parameters)
            result = _post_local(MCP_TOOLS, {
                "tool": tool, "parameters": params
            }, timeout=60)
            logfire.info("proxy_tool complete", tool=tool)
            return json.dumps(result, indent=2)
        except Exception as e:
            logfire.error("proxy_tool failed", tool=tool, error=str(e))
            return json.dumps({"error": str(e), "tool": tool})

# ── TOOL 9: read_parquet ──────────────────────────────────────────────────────
@mcp.tool()
def read_parquet(file: str, sql: str = "SELECT * FROM {table} LIMIT 20") -> str:
    """
    Query a Parquet file via DuckDB SQL.
    Available files: collision_results_final, audio_manifest_vectors,
    audio_vibe_gpu, duckdb_metadata_vectors, interaction_logs,
    legion_memory, skill_brain, t_core_memory.
    Use {table} in SQL as placeholder for the file path.
    """
    with logfire.span("read_parquet", file=file):
        path = os.path.join(PARQUET_DIR, file)
        if not path.endswith(".parquet"):
            path += ".parquet"
        if not Path(path).exists():
            avail = [f for f in os.listdir(PARQUET_DIR)
                     if f.endswith(".parquet")] if Path(PARQUET_DIR).exists() else []
            return json.dumps({"error": f"Not found: {file}",
                               "available": avail})
        con = duckdb.connect()
        try:
            actual_sql = sql.replace("{table}", f"'{path}'")
            df = con.execute(actual_sql).fetchdf()
            logfire.info("parquet read complete", file=file, rows=len(df))
            return df.head(100).to_json(orient="records", date_format="iso")
        except Exception as e:
            return json.dumps({"error": str(e)})
        finally:
            con.close()

# ── TOOL 10: list_data ────────────────────────────────────────────────────────
@mcp.tool()
def list_data() -> str:
    """
    Full inventory of all data sources: DuckDB tables, LanceDB tables,
    Parquet files. Use this first to understand what's available.
    """
    with logfire.span("list_data"):
        inv = {"duckdb": {}, "lancedb": {}, "parquet": []}

        for label, path in [("v1", DUCKDB_V1), ("v2", DUCKDB_V2)]:
            if Path(path).exists():
                con = duckdb.connect(path, read_only=True)
                try:
                    tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
                    inv["duckdb"][label] = {}
                    for t in tables:
                        n = con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
                        cols = [r[0] for r in con.execute(f'DESCRIBE "{t}"').fetchall()]
                        inv["duckdb"][label][t] = {"rows": n, "cols": cols}
                finally:
                    con.close()

        if Path(LANCE_STORE).exists():
            try:
                db_obj = lancedb.connect(LANCE_STORE)
                for t in db_obj.table_names():
                    tbl = db_obj.open_table(t)
                    inv["lancedb"][t] = {
                        "rows": tbl.count_rows(),
                        "schema": [{"name": f.name, "type": str(f.type)}
                                   for f in tbl.schema]
                    }
            except Exception as e:
                inv["lancedb"]["error"] = str(e)

        if Path(PARQUET_DIR).exists():
            for f in sorted(os.listdir(PARQUET_DIR)):
                if f.endswith(".parquet"):
                    p = os.path.join(PARQUET_DIR, f)
                    con = duckdb.connect()
                    try:
                        n = con.execute(f"SELECT COUNT(*) FROM '{p}'").fetchone()[0]
                        inv["parquet"].append({"file": f, "rows": n,
                                               "size_kb": Path(p).stat().st_size // 1024})
                    except: inv["parquet"].append({"file": f, "rows": "error"})
                    finally: con.close()

        logfire.info("list_data complete")
        return json.dumps(inv, indent=2, default=str)

# ── FASTAPI SIDECAR (REST endpoints for direct HTTP access) ───────────────────
app = FastAPI(title="Legion Agent Server", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "legion-agent-server",
            "port": PORT, "timestamp": datetime.utcnow().isoformat()}

@app.get("/inventory")
def inventory():
    return json.loads(list_data())

@app.post("/query")
def query(body: dict):
    sql = body.get("sql", "SELECT 1")
    db  = body.get("db", "v1")
    return json.loads(read_duckdb(sql, db))

@app.post("/search")
def search(body: dict):
    return json.loads(search_lancedb(
        body.get("query", ""),
        body.get("table", "audio_vibe_gpu"),
        body.get("top_k", 5)
    ))

@app.post("/embed")
def embed(body: dict):
    return json.loads(embed_text(body.get("text", "")))

@app.post("/infer")
def infer(body: dict):
    return {"response": ask_ollama(
        body.get("prompt", ""),
        body.get("model", "gemma2:2b"),
        body.get("max_tokens", 512)
    )}

@app.get("/stack")
def stack():
    return json.loads(stack_health())

# ── ENTRY POINT ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logfire.info("Legion Agent Server starting", port=PORT)
    print(f"""
====================================================
  LEGION AGENT SERVER v1.0 - Port {PORT}
====================================================
  MCP SSE  : http://127.0.0.1:{PORT}/mcp/sse
  REST API : http://127.0.0.1:{PORT}/
  Health   : http://127.0.0.1:{PORT}/health
  Inventory: http://127.0.0.1:{PORT}/inventory
  Stack    : http://127.0.0.1:{PORT}/stack
----------------------------------------------------
  DuckDB v1: {DUCKDB_V1[:50]}
  LanceDB  : {LANCE_STORE[:50]}
  LM Studio: {LM_STUDIO}
  Ollama   : {OLLAMA}
  Logfire  : {"cloud" if os.getenv("LOGFIRE_TOKEN") else "local-only"}
====================================================
""", file=sys.stderr)

    # Mount MCP SSE on the FastAPI app
    mcp_app = mcp.http_app()

    from fastapi.routing import Mount
    app.mount("/mcp", mcp_app)

    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")