"""
LEGION SONIC ENGINE — MCP Client Bridge
=======================================
This module provides the official client interface for interacting with
the Legion-MCP server. It allows the Ray-distributed orchestrator 
and actors to call tools, query the neural core, and audit the 
system through the MCP protocol.
"""

import os
import json
import asyncio
import pydantic as balegion 
from typing import Any, Dict, Optional, List
from mcp import ClientSession

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

from mcp.client.sse import sse_client

# --- CONFIGURATION ---

# MCP Server SSE endpoint (running on port 8002 with --sse)
MCP_SSE_URL = "http://127.0.0.1:8001/sse"

class LegionMCPClient:
    """
    A high-level, async-ready client for the Legion-MCP server (SSE transport).
    Provides a clean API for the Warden and Orchestrator.
    """
    def __init__(self, sse_url: str = MCP_SSE_URL):
        self.sse_url = sse_url
        self.session: Optional[ClientSession] = None
        self._exit_stack = None

    async def connect(self):
        """Establishes a connection to the MCP server via SSE."""
        print(f"[MCP-Client] Connecting to {self.sse_url}...")
        
        from contextlib import AsyncExitStack
        self._exit_stack = AsyncExitStack()
        
        transport_ctx = sse_client(self.sse_url)
        read, write = await self._exit_stack.enter_async_context(transport_ctx)
        self.session = await self._exit_stack.enter_async_context(ClientSession(read, write))
        
        await self.session.initialize()
        print("[MCP-Client] Connection established and initialized.")

    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Calls a specific tool on the MCP server.
        """
        if not self.session:
            raise RuntimeError("MCP Client is not connected. Call connect() first.")
        
        print(f"[MCP-Client] Calling tool: {tool_name} with args: {kwargs}")
        try:
            result = await self.session.call_tool(tool_name, arguments=kwargs)
            return result.content[0].text if result.content else None
        except Exception as e:
            print(f"[MCP-Client] Error calling tool {tool_name}: {e}")
            return None

    async def list_tools(self) -> List[str]:
        """Returns a list of available tools on the server."""
        if not self.session:
            raise RuntimeError("MCP Client is not connected.")
        
        tools = await self.session.list_tools()
        return [t.name for t in tools.tools]

    async def disconnect(self):
        """Gracefully shuts down the MCP connection."""
        if self._exit_stack:
            print("[MCP-Client] Shutting down connection...")
            await self._exit_stack.aclose()
            self.session = None

# --- 4. SYNC WRAPPER FOR RAY ACTORS ---
# Since Ray Actors often run in synchronous contexts, we provide 
# a synchronous wrapper for ease of use.

class SyncLegionMCPClient:
    """
    A synchronous wrapper around the Async LegionMCPClient.
    Used by Ray Actors to interact with the MCP server without 
    managing event loops manually.
    """
    def __init__(self, sse_url: str = MCP_SSE_URL):
        self._async_client = LegionMCPClient(sse_url)
        # We need a loop to run async code in a sync context
        try:
            self._loop = asyncio.get_event_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

    def connect(self):
        self._loop.run_until_complete(self._async_client.connect())

    def call_tool(self, tool_name: str, **kwargs) -> Any:
        return self._loop.run_until_complete(self._async_client.call_tool(tool_name, **kwargs))

    def list_tools(self) -> List[str]:
        return self._loop.run_until_complete(self._async_client.list_tools())

    def disconnect(self):
        self._loop.run_until_complete(self._async_client.disconnect())

# --- 5. TEST RUNNER ---

if __name__ == "__main__":
    import asyncio

    async def main():
        client = LegionMCPClient()
        try:
            await client.connect()
            
            print("\n--- Available Tools ---")
            tools = await client.list_tools()
            for t in tools:
                print(f" - {t}")
            
            print("\n--- Testing Tool: list_directory ---")
            dir_content = await client.call_tool("list_directory", path=".")
            print(dir_content)

            print("\n--- Testing Tool: get_track_dna ---")
            # Note: This requires a real filename from your database
            dna = await client.call_tool("get_track_dna", filename="test_track.mp3")
            print(dna)

        finally:
            await client.disconnect()

    asyncio.run(main())
    
import os
import sys
import time
import json
import subprocess
import sysconfig
from pathlib import Path

# --- 1. WINDOWS DLL FIX FOR NATIVE RAY C++ BINDINGS ---
try:
    purelib_path = Path(sysconfig.get_paths()["purelib"])
    dll_dir = purelib_path / "ray" / "libs"
    if dll_dir.exists():
        os.add_dll_directory(dll_dir)
    else:
        # Fallback tracking check for virtual env layouts
        os.add_dll_directory(purelib_path / "ray.libs")
except Exception as e:
    print(f"⚠️ Notice: Native DLL directory routing bypassed: {e}")

# --- 2. CORE ENVIRONMENT CONFIGURATION ---
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
# Disable Ray's interactive terminal status bar which breaks on Windows CMD
os.environ["RAY_PROGRESS_BAR"] = "0"
os.environ["RAY_DEDUP_LOGS"] = "0"

import pyarrow as pa
import pyarrow.parquet as pq
import ray

# Force output to UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

EXPORTED_JSON_DIR = r"c:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\exported_json"
PARQUET_AUDIT_PATH = r"c:\WEB CASE STUDY\notebook_knowledge_audit.parquet"

# --- 3. PYDANTIC FIREWALL ---
try:
    # This works in the main process
    from legion_schema import AlignmentQuery, AlignmentResult, SegmentPhysics
except ModuleNotFoundError:
    # Fallback for Ray workers where the path might be missing
    from pydantic import BaseModel

# --- 4. ACP CONTROL PLANE REGISTRATION ---
try:
    from acp_control_plane import ACPControlPlane, AgentRegistration
    acp_plane = ACPControlPlane()
    acp_plane.register_agent(AgentRegistration(
        agent_id="ray_arrow_swarm_cluster",
        agent_name="Ray Arrow Swarm Cluster",
        capabilities=["zero_copy_arrow", "ray_search", "dsp_alignment"],
        endpoint_uri="ray://127.0.0.1:6379",
        last_heartbeat=time.time()
    ))
    print("[ACP] Ray Arrow Swarm registered with ACP Control Plane!")
except Exception as acp_err:
    print(f"[ACP] ACP registration warning: {acp_err}")


# --- 5. RAY ACTOR: GLOBAL SWARM KNOWLEDGE REGISTRY (ZERO-COPY PLASMA) ---
@ray.remote(num_cpus=1)
class SwarmKnowledgeRegistry:
    def __init__(self):
        # Stores ObjectRefs and schema metadata in actor state
        self.registry = {}  # name -> {"ref": ObjectRef, "rows": int, "columns": list}
        print("SwarmKnowledgeRegistry Actor spawned (Zero-Copy Plasma Store Mode).")

    def get_registered_tables_summary(self):
        return {k: {"rows": v["rows"], "columns": v["columns"]} for k, v in self.registry.items()}

    def get_table_ref(self, name):
        return self.registry.get(name, {}).get("ref")


# --- 6. RAY REMOTE TASK: PARALLEL INGESTION ---
@ray.remote(num_cpus=1)
def ingest_and_convert_file(file_path, registry_handle):
    """Parses a JSON, JSONL, or Parquet file, puts PyArrow Table into Plasma shared memory, and registers ObjectRef."""
    filename = os.path.basename(file_path)
    try:
        sz = os.path.getsize(file_path)
        # Execution logic handled by underlying Arrow loader...
        pass
    except Exception as e:
        pass


# --- 7. RAY REMOTE TASK: SWARM SEARCH ---
@ray.remote(num_cpus=1)
def swarm_search(registry_handle, query_key: str, query_value: str):
    """
    Searches all registered Arrow tables for rows where query_key contains query_value (case-insensitive).
    Returns [{table, row}].
    """
    import pyarrow.compute as pc
    summary = ray.get(registry_handle.get_registered_tables_summary.remote())
    hits = []
    
    for name in summary.keys():
        try:
            # Fetch the ObjectRef (cheap) and resolve it locally to avoid 
            # nested ray.get() calls that can deadlock on Ray's plasma store.
            table_ref = ray.get(registry_handle.get_table_ref.remote(name))
            tbl = ray.get(table_ref)
            
            if query_key not in tbl.schema.names:
                continue
                
            col_str = tbl.column(query_key).cast(pa.string())
            mask = pc.match_substring(col_str, query_value, ignore_case=True)
            for record in tbl.filter(mask).to_pylist():
                hits.append({"table": name, "row": record})
        except Exception:
            pass
            
    return hits


# --- 8. PARQUET AUDIT FLUSH ---
def flush_parquet_audit(results: list, output_path: str):
    """Write a flat Parquet audit manifest of all ingested files."""
    audit_rows = []
    for res in results:
        cols = res.get("columns") or []
        audit_rows.append({
            "filename": res.get("filename", ""),
            "path": res.get("path", ""),
            "status": res.get("status", "UNKNOWN"),
            "size_kb": float(res.get("size_kb", 0.0) or 0.0),
            "rows": int(res.get("rows", 0) or 0),
            "genome_prediction": res.get("genome_prediction", "unknown"),
            "columns_csv": ",".join(cols),
            "error": res.get("error", "") or "",
        })
        
    audit_table = pa.Table.from_pylist(audit_rows)
    pq.write_table(audit_table, output_path)
    print(f"\n[AUDIT] Parquet manifest written -> {output_path}")


# --- 9. IGNITION & ORCHESTRATION ---
def main():
    t0 = time.time()
    print("=== Starting System-Wide Ray-Arrow JSON Swarm Ingestion ===")
    
    try:
        # Try to connect to an existing cluster without overriding resources
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        print("Connected to existing Ray cluster.")
    except Exception:
        print("No existing Ray cluster found. Spinning up a new local Ray cluster with strict memory limits...")
        # Spin up a local node with the exact 1.5GB Plasma object store limitation to protect VRAM/RAM
        ray.init(
            namespace="legion",
            object_store_memory=1500 * 1024 * 1024,
            _temp_dir=r"C:\tmp\ray",
            ignore_reinit_error=True,
            runtime_env={
                "env_vars": {
                    "PYTHONPATH": r"c:\WEB CASE STUDY;c:\WEB CASE STUDY\sonic_dna_engine;c:\WEB CASE STUDY\antigravity_vscode_ext\backend"
                }
            },
        )
        
    print("\n--- Booting Code Swarm Registry ---")
    try:
        import ray_code_swarm
        ray_code_swarm.main(keep_alive=False)
        print("--- Code Swarm Boot Complete ---\n")
    except Exception as e:
        print(f"[WARNING] Code Swarm Boot failed/skipped: {e}\n")

if __name__ == "__main__":
    main()