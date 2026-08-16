
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
LEGION SWARM GATEWAY — v2.0
============================
FastMCP server. Deterministic tool dispatch — no LLM in the execution path.
Every tool makes a direct HTTP call to the correct local endpoint.

Endpoints:
  mcp_api_server  → http://127.0.0.1:8001  (FastAPI, 22 endpoints)
  tool execution  → http://127.0.0.1:8002/tools/execute
  mcp_rag_server  → http://127.0.0.1:8003  (Snowflake embed + LanceDB)
  lm_studio       → http://127.0.0.1:1234  (Snowflake arctic embed)
  ollama          → http://127.0.0.1:11434 (Gemma 2B ONNX)

Run:
  c:\\WEB CASE STUDY\\.venv\\Scripts\\python.exe mcp_swarm_gateway_v2.py
  or with SSE: ... mcp_swarm_gateway_v2.py --sse
"""

import os
import sys
import json
import logging
import traceback
import requests
from typing import Optional

# ── LOGFIRE ───────────────────────────────────────────────────────────────────
import logfire
logfire.configure(
    service_name="legion-swarm-gateway",
    service_version="2.0.0",
    environment="local",
    send_to_logfire=os.getenv("LOGFIRE_TOKEN") is not None,
)
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("swarm-gateway")

try:
    from mcp.server.fastmcp import FastMCP
except Exception as e:
    sys.stderr.write(f"FATAL: FastMCP not importable: {e}\n")
    raise

# ── GROUND TRUTH ENDPOINTS ────────────────────────────────────────────────────
MCP_API_BASE    = os.getenv("MCP_API_BASE",    "http://127.0.0.1:8001")
MCP_TOOLS_EXEC  = os.getenv("MCP_TOOLS_EXEC",  "http://127.0.0.1:8002/tools/execute")
MCP_RAG_BASE    = os.getenv("MCP_RAG_BASE",    "http://127.0.0.1:8003")
LM_STUDIO_BASE  = os.getenv("LM_STUDIO_BASE",  "http://100.113.76.102:1234")
OLLAMA_BASE     = os.getenv("OLLAMA_BASE",      "http://127.0.0.1:11434")
TAILSCALE_IP    = os.getenv("TAILSCALE_IP",     "100.113.76.102")
LANCE_STORE     = os.getenv("LANCE_STORE",      r"C:\STUDIES_BACKUP\vectors\lancedb_store")
SNOWFLAKE_MODEL = "text-embedding-snowflake-arctic-embed-l-v2.0"

logfire.info("Legion Swarm Gateway starting",
             mcp_api=MCP_API_BASE,
             mcp_tools=MCP_TOOLS_EXEC,
             mcp_rag=MCP_RAG_BASE,
             lm_studio=LM_STUDIO_BASE,
             ollama=OLLAMA_BASE)

# ── MCP SERVER ────────────────────────────────────────────────────────────────
mcp = FastMCP("Legion_Swarm_Gateway")

# ── HELPER ────────────────────────────────────────────────────────────────────
def _post(url: str, payload: dict, timeout: int = 30) -> dict:
    """Deterministic POST — raises on non-200."""
    r = requests.post(url, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()

def _get(url: str, timeout: int = 10) -> dict:
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()

def _embed_snowflake(text: str) -> list:
    """
    Get Snowflake arctic embed from LM Studio.
    Returns 1024-D float list.
    """
    payload = {
        "model": SNOWFLAKE_MODEL,
        "input": text
    }
    r = requests.post(
        f"{LM_STUDIO_BASE}/v1/embeddings",
        json=payload,
        timeout=15
    )
    r.raise_for_status()
    data = r.json()
    return data["data"][0]["embedding"]

# ══════════════════════════════════════════════════════════════════════════════
# TOOL 1 — delegate_to_swarm
# Primary dispatch — natural language → mcp_api_server chat_v4
# ══════════════════════════════════════════════════════════════════════════════
@mcp.tool()
def delegate_to_swarm(instruction: str) -> str:
    """
    Delegate a complex task to the Legion Swarm Orchestrator.
    Routes through mcp_api_server chat_v4 → LangGraph → tools.
    Use for: file ops, shell commands, audio generation, workflows.
    """
    with logfire.span("delegate_to_swarm", instruction=instruction[:100]):
        try:
            result = _post(MCP_TOOLS_EXEC, {
                "tool": "chat_v4",
                "parameters": {"message": instruction}
            }, timeout=180)
            logfire.info("delegate_to_swarm complete")
            return json.dumps(result, indent=2)
        except Exception as e:
            logfire.error("delegate_to_swarm failed", error=str(e))
            return f"Error delegating to swarm: {e}"

# ══════════════════════════════════════════════════════════════════════════════
# TOOL 2 — search_swarm_memory
# Ray SwarmKnowledgeRegistry search via mcp_api_server
# ══════════════════════════════════════════════════════════════════════════════
@mcp.tool()
def search_swarm_memory(query: str, limit: int = 5) -> str:
    """
    Search the Ray Swarm PyArrow tables (SwarmKnowledgeRegistry).
    Returns matching audio features, skill guidance, or session data.
    """
    with logfire.span("search_swarm_memory", query=query):
        try:
            result = _post(MCP_TOOLS_EXEC, {
                "tool": "run_workflow",
                "parameters": {
                    "workflow_name": "swarm_search",
                    "initial_state": {"prompt": f"Search registry for {query}"}
                }
            })
            logfire.info("swarm_memory search complete", query=query)
            return json.dumps(result)
        except Exception as e:
            logfire.error("search_swarm_memory failed", error=str(e))
            return f"Error querying swarm memory: {e}"

# ══════════════════════════════════════════════════════════════════════════════
# TOOL 3 — query_rag
# Snowflake embed → LanceDB semantic search (DETERMINISTIC — no LLM)
# ══════════════════════════════════════════════════════════════════════════════
@mcp.tool()
def query_rag(query: str, table: str = "audio_vibe_gpu", top_k: int = 5) -> str:
    """
    Semantic search via Snowflake arctic embed (LM Studio :1234) → LanceDB.
    table options: audio_vibe_gpu (384-dim), audio_manifest_vectors (768-dim),
                   mined_code_vectors, duckdb_metadata_vectors.
    Deterministic — no LLM in path.
    """
    with logfire.span("query_rag", query=query, table=table, top_k=top_k):
        try:
            # Step 1: Get Snowflake embed from LM Studio
            logfire.info("Embedding query via Snowflake arctic", query=query)
            vector = _embed_snowflake(query)
            logfire.info("Embed complete", dim=len(vector))

            # Step 2: Search LanceDB via mcp_rag_server
            result = _post(f"{MCP_RAG_BASE}/search", {
                "query_vector": vector,
                "table": table,
                "top_k": top_k
            })
            logfire.info("RAG search complete", results=len(result.get("results", [])))
            return json.dumps(result, indent=2)
        except Exception as e:
            logfire.error("query_rag failed", error=str(e))
            # Fallback: try mcp_api_server search_tracks tool
            try:
                logfire.info("Falling back to search_tracks tool")
                result = _post(MCP_TOOLS_EXEC, {
                    "tool": "search_tracks",
                    "parameters": {"query": query, "limit": top_k}
                })
                return json.dumps(result, indent=2)
            except Exception as e2:
                return f"RAG search failed: {e} | Fallback failed: {e2}"

# ══════════════════════════════════════════════════════════════════════════════
# TOOL 4 — inference_local
# Ollama Gemma 2B ONNX inference (DETERMINISTIC)
# ══════════════════════════════════════════════════════════════════════════════
@mcp.tool()
def inference_local(prompt: str, model: str = "gemma2:2b", max_tokens: int = 512) -> str:
    """
    Local LLM inference via Ollama (Gemma 2B ONNX on :11434).
    Use for: audio reasoning, DSP analysis, track diagnosis.
    model options: gemma2:2b, phi3, gemma-2-2b-it-onnx
    """
    with logfire.span("inference_local", model=model, prompt_len=len(prompt)):
        try:
            result = _post(f"{OLLAMA_BASE}/api/generate", {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens}
            }, timeout=60)
            response = result.get("response", "")
            logfire.info("inference_local complete",
                        model=model,
                        response_len=len(response))
            return response
        except Exception as e:
            logfire.error("inference_local failed", error=str(e))
            return f"Inference failed: {e}"

# ══════════════════════════════════════════════════════════════════════════════
# TOOL 5 — query_duckdb
# Direct DuckDB SQL via mcp_api_server
# ══════════════════════════════════════════════════════════════════════════════
@mcp.tool()
def query_duckdb(sql: str, db_version: str = "v1") -> str:
    """
    Execute SQL against DuckDB Sonic Core.
    db_version='v1': sonic_core.duckdb (3560 rows, t_core_memory: filename/bpm/key/vibe_tags/genre_class)
    db_version='v2': sonic_core_v2.duckdb (audio_features 46 cols, t_producer_dna_node0,
                     t_sovereign_grading, t_musicological_registry_v10)
    """
    with logfire.span("query_duckdb", db_version=db_version, sql=sql[:100]):
        try:
            result = _post(MCP_TOOLS_EXEC, {
                "tool": "query_duckdb",
                "parameters": {"sql_query": sql, "db_version": db_version}
            })
            logfire.info("duckdb query complete")
            return json.dumps(result, indent=2)
        except Exception as e:
            logfire.error("query_duckdb failed", error=str(e))
            return f"DuckDB query failed: {e}"

# ══════════════════════════════════════════════════════════════════════════════
# TOOL 6 — pipeline_health
# Full stack health check — deterministic port scan + tool ping
# ══════════════════════════════════════════════════════════════════════════════
@mcp.tool()
def pipeline_health() -> str:
    """
    Full Legion stack health check.
    Checks: mcp_api_server (8001/8002), mcp_rag_server (8003),
            LM Studio/Snowflake (1234), Ollama (11434), Ray (6379/8265).
    Returns live status table. Deterministic — no LLM.
    """
    with logfire.span("pipeline_health"):
        import socket
        ports = {
            6379:  "Ray GCS",
            8265:  "Ray Dashboard",
            10001: "Ray client",
            8001:  "mcp_api_server",
            8002:  "MCP tool execution",
            8003:  "mcp_rag_server (Snowflake/RAG)",
            8000:  "api_bridge",
            1234:  "LM Studio (Snowflake embed)",
            11434: "Ollama (Gemma)",
        }
        results = {}
        for port, label in ports.items():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            up = s.connect_ex(("127.0.0.1", port)) == 0
            s.close()
            results[label] = "🟢 UP" if up else "⚫ DOWN"

        # Also try real tool ping
        try:
            health = _post(MCP_TOOLS_EXEC, {
                "tool": "pipeline_health_summary",
                "parameters": {}
            }, timeout=10)
            results["pipeline_health_summary"] = health
        except Exception as e:
            results["pipeline_health_summary"] = f"unreachable: {e}"

        logfire.info("pipeline_health complete", results=results)
        return json.dumps(results, indent=2)

# ══════════════════════════════════════════════════════════════════════════════
# TOOL 7 — get_asset_grid
# DuckDB asset catalog — 1082 assets
# ══════════════════════════════════════════════════════════════════════════════
@mcp.tool()
def get_asset_grid(limit: int = 10, filter_genre: str = "") -> str:
    """
    Query the DuckDB asset catalog (1082 assets).
    Returns track metadata: filename, bpm, key, genre, vibe_tags.
    """
    with logfire.span("get_asset_grid", limit=limit):
        try:
            params = {"limit": limit}
            if filter_genre:
                params["genre"] = filter_genre
            result = _post(MCP_TOOLS_EXEC, {
                "tool": "get_asset_grid",
                "parameters": params
            })
            logfire.info("asset_grid fetched", count=limit)
            return json.dumps(result, indent=2)
        except Exception as e:
            logfire.error("get_asset_grid failed", error=str(e))
            return f"Asset grid failed: {e}"

# ══════════════════════════════════════════════════════════════════════════════
# TOOL 8 — get_artist_dna
# Producer DNA profile from DuckDB
# ══════════════════════════════════════════════════════════════════════════════
@mcp.tool()
def get_artist_dna(workspace_id: str = "ADAMSCARMCCOY") -> str:
    """
    Retrieve producer DNA profile from DuckDB.
    Returns: dominant BPM, key, RMS target, crest factor, lineage.
    """
    with logfire.span("get_artist_dna", workspace_id=workspace_id):
        try:
            result = _post(MCP_TOOLS_EXEC, {
                "tool": "get_artist_dna",
                "parameters": {"workspace_id": workspace_id}
            })
            logfire.info("artist_dna fetched", workspace_id=workspace_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            logfire.error("get_artist_dna failed", error=str(e))
            return f"Artist DNA failed: {e}"

# ══════════════════════════════════════════════════════════════════════════════
# TOOL 9 — run_code_lint
# AST lint + hardcoded path audit via mcp_rag_server
# ══════════════════════════════════════════════════════════════════════════════
@mcp.tool()
def run_code_lint(module_name: str = "") -> str:
    """
    Run Python AST syntax linting and hardcoded path audits
    across registered code tables in LanceDB.
    """
    with logfire.span("run_code_lint", module=module_name):
        try:
            result = _post(f"{MCP_RAG_BASE}/lint", {
                "module_name": module_name
            })
            logfire.info("code_lint complete", module=module_name)
            return json.dumps(result, indent=2)
        except Exception as e:
            logfire.error("run_code_lint failed", error=str(e))
            return f"Code lint failed: {e}"

# ══════════════════════════════════════════════════════════════════════════════
# TOOL 10 — execute_shell
# Shell command via mcp_api_server (deterministic)
# ══════════════════════════════════════════════════════════════════════════════
@mcp.tool()
def execute_shell(command: str, working_dir: str = "") -> str:
    """
    Execute a shell command via mcp_api_server.
    Returns stdout/stderr. Use for: file ops, git, pip installs.
    """
    with logfire.span("execute_shell", command=command[:80]):
        try:
            params = {"command": command}
            if working_dir:
                params["working_dir"] = working_dir
            result = _post(MCP_TOOLS_EXEC, {
                "tool": "execute_shell",
                "parameters": params
            })
            logfire.info("shell executed", command=command[:80])
            return json.dumps(result, indent=2)
        except Exception as e:
            logfire.error("execute_shell failed", error=str(e))
            return f"Shell execution failed: {e}"

# ══════════════════════════════════════════════════════════════════════════════
# TOOL 11 — snowflake_embed
# Direct Snowflake arctic embed from LM Studio (exposed as standalone tool)
# ══════════════════════════════════════════════════════════════════════════════
@mcp.tool()
def snowflake_embed(text: str) -> str:
    """
    Get Snowflake arctic embed vector from LM Studio (:1234).
    Model: text-embedding-snowflake-arctic-embed-l-v2.0
    Returns 1024-D embedding vector.
    Use for: custom similarity search, vector injection, RAG prep.
    """
    with logfire.span("snowflake_embed", text_len=len(text)):
        try:
            vector = _embed_snowflake(text)
            logfire.info("snowflake_embed complete", dim=len(vector))
            return json.dumps({
                "model": SNOWFLAKE_MODEL,
                "dim": len(vector),
                "vector": vector[:8],  # first 8 dims for preview
                "full_vector_available": True
            })
        except Exception as e:
            logfire.error("snowflake_embed failed", error=str(e))
            return f"Embed failed: {e}"

# ══════════════════════════════════════════════════════════════════════════════
# TOOL 12 — langgraph_invoke
# Direct LangGraph AgentState invocation
# ══════════════════════════════════════════════════════════════════════════════
@mcp.tool()
def langgraph_invoke(prompt: str, thread_id: str = "gateway-001") -> str:
    """
    Invoke the LangGraph AgentState orchestrator directly.
    Routes: Agent(phi3/Gemma) → Tools(6 specialists) → Agent → END
    Returns full AgentState with messages and tool results.
    """
    with logfire.span("langgraph_invoke", thread_id=thread_id):
        try:
            result = _post(f"{MCP_API_BASE}/execute_langgraph", {
                "thread_id": thread_id,
                "input": {
                    "messages": [{"role": "human", "content": prompt}]
                }
            }, timeout=120)
            msgs = result.get("messages", [])
            logfire.info("langgraph_invoke complete",
                        thread_id=thread_id,
                        message_count=len(msgs))
            return json.dumps(result, indent=2)
        except Exception as e:
            logfire.error("langgraph_invoke failed", error=str(e))
            return f"LangGraph invocation failed: {e}"

# ══════════════════════════════════════════════════════════════════════════════
# STARTUP
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    logfire.info("Legion Swarm Gateway MCP Server starting")
    print("Starting Legion Swarm Gateway MCP Server v2.0", file=sys.stderr)
    print(f"  mcp_api_server : {MCP_API_BASE}", file=sys.stderr)
    print(f"  tool execution : {MCP_TOOLS_EXEC}", file=sys.stderr)
    print(f"  mcp_rag_server : {MCP_RAG_BASE}", file=sys.stderr)
    print(f"  LM Studio      : {LM_STUDIO_BASE} ({SNOWFLAKE_MODEL})", file=sys.stderr)
    print(f"  Ollama         : {OLLAMA_BASE}", file=sys.stderr)
    print(f"  Logfire        : {'cloud' if os.getenv('LOGFIRE_TOKEN') else 'local-only'}", file=sys.stderr)
    print(f"  Tools          : 12 deterministic tools registered", file=sys.stderr)

    try:
        if "--sse" in sys.argv:
            print("Running FastMCP on port 8006 (SSE Transport)...", file=sys.stderr)
            mcp.settings.port = 8006
            mcp.run(transport="sse")
        else:
            print("Running FastMCP over stdio...", file=sys.stderr)
            mcp.run()
    except BaseException as boot_err:
        logfire.error("Gateway fatal error", error=str(boot_err))
        print(f"FATAL: MCP server exited: {boot_err}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        raise