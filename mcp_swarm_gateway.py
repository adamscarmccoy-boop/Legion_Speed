import os
import sys
import json
import logging
import traceback
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Explicitly load the local .env file so the MCP gateway uses the correct C: drive Ray config
load_dotenv(r"C:\WEB CASE STUDY\.env")

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


# Ensure legion_graph is importable from the same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure debug logging to stderr
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("swarm-gateway")

try:
    from mcp.server.fastmcp import FastMCP
except Exception as e:
    sys.stderr.write(f"FATAL: FastMCP not importable: {e}\n")
    raise

# ─── Single MCP Server Instance ──────────────────────────────────────────────
mcp = FastMCP("Legion_Swarm_Gateway")

# ─── Load legion_graph for direct in-process execution ────────────────────────
_legion_graph_app = None
_legion_run_workflow = None

try:
    from legion_graph import app as _legion_graph_app, run_workflow as _legion_run_workflow
    log.info("legion_graph loaded — delegate_to_swarm will use direct in-process execution")
except Exception as graph_err:
    log.warning(f"legion_graph not available, falling back to HTTP: {graph_err}")

# ─── Optional: ACP Control Plane registration ────────────────────────────────
try:
    from acp_control_plane import ACPControlPlane, ACPEnvelope, AgentRegistration
    acp_plane = ACPControlPlane()
    acp_plane.register_agent(AgentRegistration(
        agent_id="legion_brain_api",
        agent_name="Legion Brain API Server",
        capabilities=["chat_v4", "swarm_orchestrator"],
        endpoint_uri="http://127.0.0.1:8001/tools/execute",
        last_heartbeat=__import__("time").time()
    ))
except Exception as acp_err:
    log.warning(f"ACP Control Plane failed to initialize in gateway: {acp_err}")
    acp_plane = None

# ─── Optional: Resolve live Ray actors for memory search ──────────────────────
_swarm_registry = None
_code_registry = None

def _resolve_ray_actors():
    """Try to connect to existing Ray actors in the 'legion' namespace.
    This is a best-effort lookup — if Ray isn't running, we skip gracefully."""
    global _swarm_registry, _code_registry
    try:
        import ray
        if not ray.is_initialized():
            ray.init(address='auto', namespace='legion', ignore_reinit_error=True)
        _swarm_registry = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
        log.info("Resolved SwarmKnowledgeRegistry actor")
    except Exception:
        _swarm_registry = None
    try:
        import ray
        _code_registry = ray.get_actor("CodeSwarmKnowledgeRegistry", namespace="legion")
        log.info("Resolved CodeSwarmKnowledgeRegistry actor")
    except Exception:
        _code_registry = None

_resolve_ray_actors()


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL 1: search_swarm_memory
# ═══════════════════════════════════════════════════════════════════════════════
@mcp.tool()
def search_swarm_memory(query: str, limit: int = 5) -> str:
    """
    Search the in-memory Ray Swarm PyArrow tables for matching data, skill guidance, or audio features.
    Falls back to HTTP if Ray actors are not reachable.
    """
    # Try direct Ray actor query first
    if _swarm_registry is not None:
        try:
            import ray
            summary = ray.get(_swarm_registry.get_registered_tables_summary.remote())
            return json.dumps({"source": "ray_actor", "registry": summary, "query": query})
        except Exception as ray_err:
            log.warning(f"Ray actor query failed, falling back to HTTP: {ray_err}")

    # Fallback: HTTP to mcp_api_server on port 8001
    try:
        payload = {
            "tool_name": "run_workflow",
            "parameters": {
                "workflow_name": "swarm_search",
                "initial_state": {"prompt": f"Search registry for {query}"}
            }
        }
        res = requests.post("http://127.0.0.1:8001/tools/execute", json=payload, timeout=30)
        return json.dumps(res.json())
    except Exception as e:
        return f"Error querying swarm memory: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL 2: run_code_lint
# ═══════════════════════════════════════════════════════════════════════════════
@mcp.tool()
def run_code_lint(module_name: str = "") -> str:
    """
    Run automated Python AST syntax linting and hardcoded path audits across registered code tables.
    """
    try:
        from mcp_rag_server import code_quality_lint_audit
        return code_quality_lint_audit(module_name)
    except Exception as e:
        return f"Error executing code lint audit: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL 3: delegate_to_swarm
# ═══════════════════════════════════════════════════════════════════════════════
@mcp.tool()
def delegate_to_swarm(instruction: str) -> str:
    """
    Delegate a complex task or action to the Legion Swarm Orchestrator.
    Use this single tool to interact with the system instead of calling individual tools.
    The swarm is capable of writing files, running commands, analyzing data, generating music,
    and executing LangGraph workflows.
    Just pass a natural language instruction describing exactly what you want the swarm to do.
    """
    # Primary path: direct in-process call to legion_graph (no network, no ports)
    if _legion_run_workflow is not None:
        try:
            result = _legion_run_workflow(instruction)
            return f"Swarm Execution Complete (direct):\n{json.dumps(result, indent=2)}"
        except Exception as direct_err:
            log.warning(f"Direct legion_graph execution failed, falling back to HTTP: {direct_err}")

    # Fallback: HTTP POST to mcp_api_server on port 8001
    try:
        response = requests.post(
            "http://127.0.0.1:8001/tools/execute",
            json={"tool_name": "chat_v4", "parameters": {"message": instruction}},
            timeout=180
        )
        if response.status_code == 200:
            result = response.json()
            return f"Swarm Execution Complete (http):\n{json.dumps(result, indent=2)}"
        else:
            return f"Swarm Execution Failed ({response.status_code}): {response.text}"
    except Exception as e:
        return f"Error delegating to swarm: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRYPOINT — Single server, no duplicates
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Starting Legion Swarm Gateway MCP Server", file=sys.stderr)
    try:
        if "--sse" in sys.argv:
            print("Running FastMCP on port 8006 (SSE Transport)...", file=sys.stderr)
            mcp.settings.port = 8006
            mcp.run(transport='sse')
        else:
            print("Running FastMCP over stdio...", file=sys.stderr)
            mcp.run()
    except BaseException as boot_err:
        print(f"FATAL: MCP server exited: {boot_err}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        raise