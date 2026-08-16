#!/usr/bin/env python3
"""
=============================================================================
🏛️ SOVEREIGN GEMINI STREAMING CLI (Direct Codebase Harness)
Directly importing:
  - acp_control_plane.py (ACPControlPlane, ACPEvent)
  - sovereign_schemas.py (SovereignDAWDiagnostic, AudioTruth)
  - mcp_swarm_gateway_v2.py (_embed_snowflake, search_swarm_memory)
  - sovereign_warden_monty.py (run_pydantic_monty_lint, query_duckdb_logs)
  - antigravity_vscode_ext/backend/llm_router.py (LLMRouter)
=============================================================================
"""

import os
import sys
import time
import json
import socket
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Ensure local workspace root is in sys.path
WORKSPACE_ROOT = r"C:\WEB CASE STUDY"
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

BACKEND_DIR = os.path.join(WORKSPACE_ROOT, "antigravity_vscode_ext", "backend")
if os.path.exists(BACKEND_DIR) and BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# -----------------------------------------------------------------------------
# 1. LOAD VERIFIED ENVIRONMENT
# -----------------------------------------------------------------------------
for env_candidate in [r"C:\WEB CASE STUDY\.env", r"C:\STUDIES_BACKUP\.env"]:
    if os.path.exists(env_candidate):
        load_dotenv(env_candidate)

# -----------------------------------------------------------------------------
# 2. IMPORT REAL CODEBASE MODULES (NO MOCKS)
# -----------------------------------------------------------------------------
try:
    import acp_control_plane as acp
    from acp_control_plane import ACPControlPlane, AgentRegistration, ACPEvent
    print("✅ Imported acp_control_plane (A2A Control Plane)")
except Exception as e:
    acp = None
    print(f"⚠️ Could not import acp_control_plane: {e}")

try:
    import sovereign_schemas as s_schemas
    from sovereign_schemas import SovereignDAWDiagnostic, AudioTruth, Lane1DuckDBAnalytics
    print("✅ Imported sovereign_schemas (Sovereign Data Contracts)")
except Exception as e:
    s_schemas = None
    print(f"⚠️ Could not import sovereign_schemas: {e}")

try:
    import sovereign_warden_monty as warden
    print("✅ Imported sovereign_warden_monty (Rust Monty VM & DuckDB Logs)")
except Exception as e:
    warden = None
    print(f"⚠️ Could not import sovereign_warden_monty: {e}")

try:
    import mcp_swarm_gateway_v2 as swarm_gw
    print("✅ Imported mcp_swarm_gateway_v2 (Snowflake Arctic Embeddings & Swarm RAG)")
except Exception as e:
    swarm_gw = None
    print(f"⚠️ Could not import mcp_swarm_gateway_v2: {e}")

# -----------------------------------------------------------------------------
# 3. SETUP GEMINI CLIENT (VIA GOOGLE-GENAI SDK)
# -----------------------------------------------------------------------------
from google import genai
from google.genai import types

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ Error: GEMINI_API_KEY environment variable is missing.")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# -----------------------------------------------------------------------------
# 4. HOOK YOUR REAL CODEBASE FUNCTIONS AS TOOL DISPATCHERS
# -----------------------------------------------------------------------------
def tool_read_file(path: str) -> str:
    if warden and hasattr(warden, "read_file"):
        return warden.read_file(path)
    p = Path(path) if Path(path).is_absolute() else Path(WORKSPACE_ROOT) / path
    return p.read_text(encoding="utf-8", errors="ignore")[:4000] if p.exists() else f"File not found: {p}"

def tool_run_duckdb_sql(query: str) -> str:
    if warden and hasattr(warden, "query_duckdb_logs"):
        return warden.query_duckdb_logs(query)
    import duckdb
    conn = duckdb.connect(database=r"C:\WEB CASE STUDY\web_intel_sonicdb.duckdb", read_only=True)
    return conn.execute(query).df().to_string(index=False)

def tool_run_monty_lint(code: str) -> str:
    if warden and hasattr(warden, "run_pydantic_monty_lint"):
        return warden.run_pydantic_monty_lint(code)
    return "Warden Monty linter module not loaded."

def tool_search_swarm(query: str) -> str:
    if swarm_gw and hasattr(swarm_gw, "search_swarm_memory"):
        return str(swarm_gw.search_swarm_memory(query))
    return "Swarm Gateway module not loaded."

def tool_acp_status() -> str:
    if acp:
        plane = ACPControlPlane()
        agent = AgentRegistration(
            agent_id="GeminiAgentWorker",
            agent_name="Gemini 2.5 Live Streamer",
            capabilities=["gemini_stream", "tool_dispatcher", "duckdb"],
            endpoint_uri="https://scars-lab.taila0aac3.ts.net/mcp",
            last_heartbeat=time.time()
        )
        plane.register_agent(agent)
        return json.dumps({
            "status": "ACP_ACTIVE",
            "registered_agent": agent.agent_id,
            "capabilities": agent.capabilities
        }, indent=2)
    return "ACP Control Plane not loaded."

TOOL_DISPATCH_MAP = {
    "read_file": tool_read_file,
    "run_duckdb_sql": tool_run_duckdb_sql,
    "run_monty_lint": tool_run_monty_lint,
    "search_swarm_memory": tool_search_swarm,
    "check_acp_status": tool_acp_status
}

# -----------------------------------------------------------------------------
# 5. GEMINI TOOL SCHEMAS FOR YOUR CODEBASE
# -----------------------------------------------------------------------------
GEMINI_TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="read_file",
                description="Read local workspace file (Python, JSON, MD, HPP) via sovereign_warden_monty.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={"path": types.Schema(type="STRING", description="Path to file on disk")},
                    required=["path"]
                )
            ),
            types.FunctionDeclaration(
                name="run_duckdb_sql",
                description="Execute SQL on real DuckDB database (web_intel_sonicdb.duckdb: audio_features, sonic_dna, chris_lake_baseline).",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={"query": types.Schema(type="STRING", description="SQL SELECT statement")},
                    required=["query"]
                )
            ),
            types.FunctionDeclaration(
                name="run_monty_lint",
                description="Execute and statically analyze Python code in the Rust Monty VM sandbox via sovereign_warden_monty.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={"code": types.Schema(type="STRING", description="Python code string")},
                    required=["code"]
                )
            ),
            types.FunctionDeclaration(
                name="search_swarm_memory",
                description="Search LanceDB vectors using Snowflake Arctic Embeddings via mcp_swarm_gateway_v2.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={"query": types.Schema(type="STRING", description="Search query")},
                    required=["query"]
                )
            ),
            types.FunctionDeclaration(
                name="check_acp_status",
                description="Register Gemini as an ACP agent and verify zero-copy event loop via acp_control_plane.py.",
                parameters=types.Schema(type="OBJECT", properties={})
            )
        ]
    )
]

# -----------------------------------------------------------------------------
# 6. GEMINI INTERACTIONS (URL Context, etc.)
# -----------------------------------------------------------------------------
def run_gemini_interaction(user_input: str, model: str = "models/gemini-3.7-flash") -> str:
    """Run a Gemini interaction with URL context tool."""
    tools = [
        {
            'type': 'url_context',
        },
    ]

    generation_config = {
        'max_output_tokens': 65536,
        'top_p': 0.95,
        'thinking_level': 'medium',
    }

    interaction = client.interactions.create(
        model=model,
        input=user_input,
        tools=tools,
        generation_config=generation_config,
    )

    return str(interaction.steps[-1])


# -----------------------------------------------------------------------------
# 7. STREAMING & MULTI-TURN RECURSIVE REPL
# -----------------------------------------------------------------------------
def stream_gemini_turn(chat_history: List[types.Content], user_text: str, model: str = DEFAULT_MODEL, depth: int = 0) -> str:
    if depth > 4:
        print("⚠️ Maximum sub-agent tool recursion reached.")
        return ""

    if depth == 0:
        chat_history.append(types.Content(role="user", parts=[types.Part.from_text(text=user_text)]))

    config = types.GenerateContentConfig(
        tools=GEMINI_TOOLS,
        temperature=0.2,
        max_output_tokens=2048
    )

    t0 = time.time()
    first_token_time = None
    collected_text = []
    function_calls = []

    label = f"[✨ GEMINI: {model}]"
    print(f"\n{label} " if depth == 0 else f"\n↳ {label} ", end="", flush=True)

    try:
        response_stream = client.models.generate_content_stream(
            model=model,
            contents=chat_history,
            config=config
        )

        for chunk in response_stream:
            if chunk.text:
                if first_token_time is None:
                    first_token_time = time.time() - t0
                print(chunk.text, end="", flush=True)
                collected_text.append(chunk.text)

            if chunk.function_calls:
                for fc in chunk.function_calls:
                    function_calls.append(fc)

        elapsed = time.time() - t0
        full_text = "".join(collected_text)

        # Dispatch real codebase functions when requested
        if function_calls:
            for call in function_calls:
                t_name = call.name
                t_args = dict(call.args)
                print(f"\n⚙️  [SOVEREIGN CODEBASE TOOL EXECUTING]: {t_name}({json.dumps(t_args)})")

                fn = TOOL_DISPATCH_MAP.get(t_name)
                tool_res = fn(**t_args) if (fn and t_args) else (fn() if fn else f"Tool {t_name} not found.")

                chat_history.append(types.Content(
                    role="model",
                    parts=[types.Part.from_function_call(name=t_name, args=t_args)]
                ))
                chat_history.append(types.Content(
                    role="tool",
                    parts=[types.Part.from_function_response(name=t_name, response={"result": str(tool_res)})]
                ))

            # Loop back with tool result to finish the reasoned turn
            return stream_gemini_turn(chat_history, user_text, model=model, depth=depth + 1)

        est_tok = int(len(full_text) / 4)
        speed = est_tok / elapsed if elapsed > 0 else 0
        ttft_str = f" | TTFT: {first_token_time*1000:.0f}ms" if first_token_time else ""
        print(f"\n\n📊 [Tokens: ~{est_tok} output | Speed: {speed:.1f} tok/s{ttft_str} | Time: {elapsed:.2f}s]\n")
        return full_text

    except Exception as e:
        print(f"\n❌ Stream Error: {e}")
        return ""

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Sovereign Gemini Codebase CLI")
    subparsers = parser.add_subparsers(dest="subcommand")

    # chat
    chat_p = subparsers.add_parser("chat", help="Launch interactive REPL connected to real local engines")
    chat_p.add_argument("--model", default=DEFAULT_MODEL, help="Gemini model")

    # ask
    ask_p = subparsers.add_parser("ask", help="One-shot streaming query")
    ask_p.add_argument("prompt", nargs="+", help="Prompt text")
    ask_p.add_argument("--model", default=DEFAULT_MODEL, help="Gemini model")

    # interact
    interact_p = subparsers.add_parser("interact", help="Run Gemini interaction with URL context tool")
    interact_p.add_argument("prompt", nargs="+", help="Prompt text")
    interact_p.add_argument("--model", default="models/gemini-3.7-flash", help="Gemini model for interaction")

    args = parser.parse_args()

    if len(sys.argv) == 1 or args.subcommand == "chat":
        model = getattr(args, "model", DEFAULT_MODEL)
        print("=" * 70)
        print(f" 💬 SOVEREIGN GEMINI AGENT REPL (Connected to Real Workspace)")
        print(f" Model: {model} | MCP Route: https://scars-lab.taila0aac3.ts.net/mcp")
        print(" Connected Codebase Modules: acp_control_plane, sovereign_warden_monty, mcp_swarm_gateway_v2")
        print("=" * 70 + "\n")
        
        history: List[types.Content] = []
        while True:
            try:
                user_input = input(f"[✨ {model}] You ❯ ").strip()
                if not user_input or user_input.lower() in ["/exit", "exit", "quit"]:
                    break
                stream_gemini_turn(history, user_input, model=model)
            except (KeyboardInterrupt, EOFError):
                break
    elif args.subcommand == "ask":
        p = " ".join(args.prompt)
        history = []
        stream_gemini_turn(history, p, model=args.model)
    elif args.subcommand == "interact":
        p = " ".join(args.prompt)
        result = run_gemini_interaction(p, model=args.model)
        print(result)

if __name__ == "__main__":
    main()

