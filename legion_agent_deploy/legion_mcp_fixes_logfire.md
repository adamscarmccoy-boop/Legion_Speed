# Legion MCP Server — Fixes + Logfire Instrumentation
**Based on:** LEGION MANIFEST §6 Known Issues, Ground-Truth Runbook  
**Date:** 2026-07-29  
**Status:** Apply to both `mcp_api_server.py` and `mcp_rag_server.py`

---

## PATCH 1 — mcp_api_server.py

### Fix #2 + #3 + #4 — sys.path + ray import guard
Add this block at the very top of `mcp_api_server.py`, BEFORE any other imports:

```python
# ── LEGION PATH BOOTSTRAP ─────────────────────────────────────────────────────
import sys
import os

# Fix #3: Add WEB CASE STUDY to sys.path so sovereign/forest imports resolve
_WCS = r"C:\WEB CASE STUDY"
if _WCS not in sys.path:
    sys.path.insert(0, _WCS)

# Fix #2/#4: Ray guard — .venv_fresh may not have ray installed
# mcp_api_server.py will still start; Ray-dependent endpoints degrade gracefully
_RAY_AVAILABLE = False
try:
    import ray
    _RAY_AVAILABLE = True
except ImportError:
    print("[LEGION BOOT] WARNING: ray not installed in this venv.")
    print("[LEGION BOOT] Ray-dependent endpoints will return 503.")
    print("[LEGION BOOT] Fix: c:\\STUDIES_BACKUP\\.venv_fresh\\Scripts\\python.exe -m pip install ray")
# ─────────────────────────────────────────────────────────────────────────────
```

### Logfire instrumentation for mcp_api_server.py
Add after the path bootstrap block, before FastAPI app creation:

```python
# ── LOGFIRE INSTRUMENTATION ───────────────────────────────────────────────────
import logfire

logfire.configure(
    service_name="legion-mcp-api-server",
    service_version="2.0.0",
    environment="local",
    # Set LOGFIRE_TOKEN env var or use send_to_logfire=False for local-only
    send_to_logfire=os.getenv("LOGFIRE_TOKEN") is not None,
)

# Instrument FastAPI — wraps all endpoints automatically
# Call this AFTER app = FastAPI(...) is created:
#   logfire.instrument_fastapi(app)
# ─────────────────────────────────────────────────────────────────────────────
```

Then immediately after `app = FastAPI(...)`:
```python
logfire.instrument_fastapi(app)
logfire.info("Legion MCP API Server starting", port=8001, tool_execution_port=8002)
```

### Wrap Ray-dependent endpoints with guard
Find every endpoint that calls `ray.init()` or `ray.get_actor()` and wrap:

```python
@app.get("/ray/actors")
async def get_ray_actors():
    if not _RAY_AVAILABLE:
        with logfire.span("ray_unavailable"):
            logfire.warn("Ray not available — venv missing ray package")
        raise HTTPException(status_code=503, detail={
            "error": "Ray not installed in this venv",
            "fix": "c:\\STUDIES_BACKUP\\.venv_fresh\\Scripts\\python.exe -m pip install ray"
        })
    with logfire.span("ray_actor_scan"):
        # ... existing ray actor code ...
        pass
```

### Instrument /tools/execute endpoint
```python
@app.post("/tools/execute")
async def execute_tool(request: ToolExecuteRequest):
    with logfire.span("mcp_tool_execute", tool=request.tool):
        logfire.info("Tool invoked", tool=request.tool, params=request.parameters)
        try:
            result = await _dispatch_tool(request.tool, request.parameters)
            logfire.info("Tool success", tool=request.tool)
            return result
        except Exception as e:
            logfire.error("Tool failed", tool=request.tool, error=str(e))
            raise
```

### Instrument /execute_langgraph endpoint
```python
@app.post("/execute_langgraph")
async def execute_langgraph(request: LangGraphRequest):
    with logfire.span("langgraph_invoke", thread_id=request.thread_id):
        logfire.info("LangGraph invoked", thread_id=request.thread_id)
        try:
            from legion_graph import app as lg_app
            result = lg_app.invoke({
                "messages": [HumanMessage(content=m["content"]) 
                             for m in request.input.get("messages", [])],
                "active_dna_context": {}
            })
            logfire.info("LangGraph complete", 
                        message_count=len(result.get("messages", [])))
            return result
        except Exception as e:
            logfire.error("LangGraph failed", error=str(e))
            raise
```

---

## PATCH 2 — mcp_rag_server.py

### Fix #1 — venv missing
The RAG server uses `c:\WEB CASE STUDY\.venv\Scripts\python.exe` which is MISSING.

**Recreate it on your machine:**
```powershell
# Run in PowerShell as admin
python -m venv "C:\WEB CASE STUDY\.venv"
& "C:\WEB CASE STUDY\.venv\Scripts\python.exe" -m pip install `
    fastmcp lancedb sentence-transformers numpy logfire
```

### Fix #7 — LANCEDB_PATH mismatch
Find this line in `mcp_rag_server.py`:
```python
# WRONG — whatever it currently says:
LANCEDB_PATH = "C:\\WEB CASE STUDY\\.vector_cache"
# or any other non-canonical path
```

Replace with:
```python
# CORRECT — canonical path from Manifest §8
LANCEDB_PATH = r"C:\STUDIES_BACKUP\vectors\lancedb_store"
```

### Logfire instrumentation for mcp_rag_server.py
Add at top after imports:

```python
# ── LOGFIRE INSTRUMENTATION ───────────────────────────────────────────────────
import logfire
import os

logfire.configure(
    service_name="legion-mcp-rag-server",
    service_version="2.0.0", 
    environment="local",
    send_to_logfire=os.getenv("LOGFIRE_TOKEN") is not None,
)
logfire.info("Legion MCP RAG Server starting",
             lancedb_path=LANCEDB_PATH,
             port=8003)
# ─────────────────────────────────────────────────────────────────────────────
```

### Instrument semantic_code_search tool
```python
@mcp.tool()
async def semantic_code_search(query: str, top_k: int = 10) -> str:
    """Semantic search across LanceDB code vectors (Snowflake embed entry point)."""
    with logfire.span("semantic_code_search", query=query, top_k=top_k):
        logfire.info("RAG search invoked", query=query)
        try:
            db = lancedb.connect(LANCEDB_PATH)
            tbl = db.open_table("audio_vibe_gpu")  # or mined_code_vectors
            # ... existing search logic ...
            logfire.info("RAG search complete", results=top_k)
            return results
        except Exception as e:
            logfire.error("RAG search failed", error=str(e), 
                         lancedb_path=LANCEDB_PATH)
            raise
```

---

## PATCH 3 — legion_graph.py

### Fix _get_model() config path
```python
def _get_model():
    # WRONG:
    # mcp_config_path = os.path.join(BASE_DIR, "data", "config", "mcp.json")
    
    # CORRECT — mcp_config.json is at pipeline root:
    mcp_config_path = os.path.join(BASE_DIR, "mcp_config.json")
    
    ollama_url = "http://localhost:11434"
    model_id = "phi3"  # confirmed running on your Ollama
    
    if os.path.exists(mcp_config_path):
        with open(mcp_config_path, "r") as f:
            config = json.load(f)
            if "model_config" in config:
                ollama_url = config["model_config"].get("ollama_url", ollama_url)
                model_id = config["model_config"].get("model_id", model_id)
```

### Add Logfire to legion_graph.py
```python
import logfire

logfire.configure(service_name="legion-langgraph", environment="local",
                  send_to_logfire=os.getenv("LOGFIRE_TOKEN") is not None)

def call_model(state: AgentState) -> dict:
    with logfire.span("langgraph_agent_node"):
        llm_with_tools = _get_model()
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(state["messages"])
        logfire.info("Agent node invoked", message_count=len(messages))
        response = llm_with_tools.invoke(messages)
        tool_calls = getattr(response, "tool_calls", [])
        logfire.info("Agent node complete", 
                    has_tool_calls=bool(tool_calls),
                    tool_names=[t["name"] for t in tool_calls])
        return {"messages": [response]}
```

---

## PATCH 4 — mcp_config.json additions

Add `model_config` block so `_get_model()` picks up the right Ollama model:

```json
{
  "mcpServers": {
    "legion-architect": {
      "active": true,
      "command": "c:\\STUDIES_BACKUP\\.venv_fresh\\Scripts\\python.exe",
      "entry": "mcp_api_server.py",
      "serves": "http://127.0.0.1:8001"
    },
    "legion-mcp-rag-server": {
      "active": true,
      "command": "c:\\WEB CASE STUDY\\.venv\\Scripts\\python.exe",
      "entry": "mcp_rag_server.py",
      "serves": "http://127.0.0.1:8003"
    }
  },
  "model_config": {
    "ollama_url": "http://localhost:11434",
    "model_id": "phi3"
  },
  "lancedb": {
    "canonical_path": "C:\\STUDIES_BACKUP\\vectors\\lancedb_store",
    "fallback_path": "C:\\WEB CASE STUDY\\lancedb_store"
  },
  "logfire": {
    "enabled": true,
    "services": ["legion-mcp-api-server", "legion-mcp-rag-server", "legion-langgraph"]
  }
}
```

---

## STARTUP ORDER (with Logfire active)

```
1. Ray cluster (already live — gcs PID 8928, raylet PID 20812)
2. SwarmKnowledgeRegistry — ray_arrow_swarm.py (venv_fresh)
3. mcp_api_server.py (venv_fresh) → logfire traces on port 8001/8002
4. mcp_rag_server.py (WCS venv) → logfire traces on port 8003
5. api_bridge.py (E: venv) → port 8000 → Tailscale funneled
6. server.ts → npm run dev → port 3000/8444
```

---

## LOGFIRE LOCAL DASHBOARD

To view traces locally without a Logfire account:
```powershell
# In any terminal with logfire installed:
logfire inspect
# Or view at: https://logfire.pydantic.dev (free tier)
```

Set env var for cloud push (optional):
```powershell
$env:LOGFIRE_TOKEN = "your-token-here"
```

Without the token, all traces are local-only — zero data egress, 
consistent with the sovereign-edge design principle.

---

## WHAT LOGFIRE GIVES YOU

```
mcp_tool_execute spans    → see every tool call, latency, params
langgraph_invoke spans    → see every graph traversal, node path
semantic_code_search spans→ see every RAG query, LanceDB response time
ray_actor_scan spans      → see actor health checks with timing
startup spans             → see exactly what loaded and what failed
```

All traces correlate by `service_name` so you can see the full 
request path: api_bridge → mcp_api_server → legion_graph → tools