#!/usr/bin/env python3
"""
=============================================================================
🏛️ SOVEREIGN GEMINI MASTER KERNEL CLI (gemini_cli.py)
Dual-Channel Silicon Processing: Gemini 2.5 Cloud + C++ DLL 808-Byte Layout
Includes: Surgical AST Scanner, Swarm Memory, & Microsecond DLL In-Memory Steps
=============================================================================
"""

import os
import sys
import time
import ast
import json
import socket
import ctypes
import struct
import atexit
import signal
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

# Ensure robust UTF-8 output on Windows terminal
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ANSI Color escapes matching council_chat.py
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"

# -----------------------------------------------------------------------------
# 1. 808-BYTE ZERO-JSON BINARY C-STRUCT LAYOUT
# -----------------------------------------------------------------------------
STRUCT_FORMAT = "<64s64s32s512s32s12f12fd"
EXPECTED_SIZE = 808

class NativeSwarmNodeState(ctypes.Structure):
    _fields_ = [
        ("task_id", ctypes.c_char * 64),
        ("node_name", ctypes.c_char * 64),
        ("status", ctypes.c_char * 32),
        ("user_query", ctypes.c_char * 512),
        ("tool_target", ctypes.c_char * 32),
        ("dsp_features", ctypes.c_float * 12),
        ("output_scores", ctypes.c_float * 12),
        ("execution_time_us", ctypes.c_double),
    ]

class FlatSovereignState(BaseModel):
    task_id: bytes = Field(..., max_length=64)
    node_name: bytes = Field(..., max_length=64)
    status: bytes = Field(..., max_length=32)
    user_query: bytes = Field(..., max_length=512)
    tool_target: bytes = Field(..., max_length=32)
    dsp_features: list[float] = Field(..., min_length=12, max_length=12)
    output_scores: list[float] = Field(..., min_length=12, max_length=12)
    execution_time_us: float

    @field_validator("task_id", "node_name", "status", "user_query", "tool_target", mode="before")
    @classmethod
    def strip_null_padding(cls, value: bytes) -> bytes:
        if isinstance(value, bytes):
            return value.split(b"\x00", 1)[0]
        return value

    def to_binary_buffer(self) -> bytes:
        return struct.pack(
            STRUCT_FORMAT,
            self.task_id.ljust(64, b"\x00"),
            self.node_name.ljust(64, b"\x00"),
            self.status.ljust(32, b"\x00"),
            self.user_query.ljust(512, b"\x00"),
            self.tool_target.ljust(32, b"\x00"),
            *self.dsp_features,
            *self.output_scores,
            self.execution_time_us
        )

# -----------------------------------------------------------------------------
# 2. C++ DLL LOADER WITH SIMULATION FALLBACK
# -----------------------------------------------------------------------------
def load_sovereign_library(dll_path=None):
    if dll_path is None:
        dll_path = os.environ.get("SOVEREIGN_DLL_PATH", r"C:\WEB CASE STUDY\sovereign_kernel.dll")
    
    if not os.path.exists(dll_path):
        return None, f"{YELLOW}[-] Sovereign DLL not found at {dll_path} (Using simulated loopback fallback){RESET}"
        
    try:
        lib = ctypes.CDLL(dll_path)
        lib.step_state_agent.argtypes = [NativeSwarmNodeState]
        lib.step_state_agent.restype = NativeSwarmNodeState
        return lib, f"{GREEN}[+] Sovereign C++ DLL fully loaded and bound from: {dll_path}{RESET}"
    except Exception as e:
        return None, f"{RED}[-] Error linking C++ DLL: {e} (Using fallback simulation){RESET}"

# -----------------------------------------------------------------------------
# 3. SURGICAL AST EXTRACTOR (IMMUNE TO OS.WALK OVERFLOWS)
# -----------------------------------------------------------------------------
def inspect_file_ast(filepath: str) -> dict:
    target = Path(filepath)
    if not target.is_absolute():
        target = Path(r"C:\WEB CASE STUDY") / target
    if not target.exists():
        return {"status": "FAILED", "error": "File not found on disk."}
    
    try:
        content = target.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content, filename=str(target))
        imports = [a.name for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names]
        functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        
        return {
            "status": "SUCCESS",
            "filename": target.name,
            "classes": classes[:10],
            "functions": functions[:15],
            "imports": imports[:10],
            "lines_count": len(content.splitlines())
        }
    except Exception as e:
        return {"status": "FAILED", "error": str(e)}

def list_immediate_dir(target_dir: str = r"C:\WEB CASE STUDY") -> dict:
    try:
        files = [f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f))]
        return {"status": "SUCCESS", "files": [f for f in files if f.endswith(('.py', '.hpp', '.cpp', '.json', '.md'))]}
    except Exception as e:
        return {"status": "FAILED", "error": str(e)}

# -----------------------------------------------------------------------------
# 4. CONFIG, DUCKDB & GEMINI SETUP
# -----------------------------------------------------------------------------
WORKSPACE_ROOT = r"C:\WEB CASE STUDY"
DUCKDB_PATH = r"C:\WEB CASE STUDY\web_intel_sonicdb.duckdb"

for env_path in [r"C:\WEB CASE STUDY\.env", r"C:\STUDIES_BACKUP\.env"]:
    if os.path.exists(env_path): load_dotenv(env_path)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print(f"{RED}[-] Error: GEMINI_API_KEY is not set.{RESET}")
    sys.exit(1)

from google import genai
from google.genai import types

client = genai.Client(api_key=GEMINI_API_KEY)
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# Dynamic Port Discovery for Local LM Studio
PORT_OPTIONS = [1234, 1010, 56217, 61277]
def discover_active_port() -> int:
    for port in PORT_OPTIONS:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    return port
        except Exception:
            pass
    return 1234

LOCAL_PORT = discover_active_port()

def run_duckdb_sql(query: str) -> str:
    try:
        import duckdb
        conn = duckdb.connect(database=DUCKDB_PATH, read_only=True)
        return conn.execute(query).df().to_string(index=False)
    except Exception as e:
        return f"DuckDB Error: {e}"

# -----------------------------------------------------------------------------
# 5. CORE SILICON STEP (PASSES 808-BYTE STRUCT DIRECTLY TO C++ DLL)
# -----------------------------------------------------------------------------
def execute_silicon_step(dll_lib, prompt: str, features: List[float], active_node: str = "AcousticRouter", task_count: int = 100):
    task_id_str = f"t-{task_count}-gemini-silicon"
    flat_state = FlatSovereignState(
        task_id=task_id_str.encode("utf-8"),
        node_name=active_node.encode("utf-8"),
        status=b"PENDING_IN_MEMORY",
        user_query=prompt[:512].encode("utf-8"),
        tool_target=b"CPP_NATIVE",
        dsp_features=features,
        output_scores=[0.0] * 12,
        execution_time_us=0.0
    )
    
    binary_payload = flat_state.to_binary_buffer()
    assert len(binary_payload) == EXPECTED_SIZE, "Memory layout corruption!"

    if not dll_lib:
        flat_state.output_scores = [f * 1.58 for f in features]
        flat_state.status = b"COMPLETED_SIMULATION"
        flat_state.execution_time_us = 12.45
        print(f"{YELLOW}ℹ️  [MEMORY] Virtual memory pass modified flat struct (Simulated Loopback).{RESET}")
    else:
        native_struct = NativeSwarmNodeState()
        native_struct.task_id = flat_state.task_id.ljust(64, b"\x00")
        native_struct.node_name = flat_state.node_name.ljust(64, b"\x00")
        native_struct.status = flat_state.status.ljust(32, b"\x00")
        native_struct.user_query = flat_state.user_query.ljust(512, b"\x00")
        native_struct.tool_target = flat_state.tool_target.ljust(32, b"\x00")
        for i, val in enumerate(flat_state.dsp_features):
            native_struct.dsp_features[i] = float(val)
            
        start_t = time.perf_counter_ns()
        result_struct = dll_lib.step_state_agent(native_struct)
        end_t = time.perf_counter_ns()
        
        flat_state.output_scores = list(result_struct.output_scores[:12])
        flat_state.execution_time_us = (end_t - start_t) / 1000.0
        print(f"{GREEN}⚡ [MEMORY] Direct DLL Pointer modified. Latency: {flat_state.execution_time_us:.2f} µs{RESET}")

    print(f"\n{BOLD}{MAGENTA}" + "-" * 75)
    print("📈 ACTIVE COGNITIVE STEP OUTCOMES:")
    print("-" * 75 + RESET)
    print(f"📄 Task ID:          {GREEN}{flat_state.task_id.decode('utf-8').strip()}{RESET}")
    print(f"⚙️  Active Node:      {CYAN}{flat_state.node_name.decode('utf-8').strip()}{RESET}")
    print(f"📊 DSP Feats:        {list(round(x, 4) for x in flat_state.dsp_features[:4])}...")
    print(f"📈 Output Scores:    {list(round(x, 4) for x in flat_state.output_scores[:4])}...")
    print(f"🕰️  C++ DLL Speed:    {GREEN}{flat_state.execution_time_us:.2f} µs{RESET}")
    print(f"{BOLD}{MAGENTA}" + "-" * 75 + RESET + "\n")

# -----------------------------------------------------------------------------
# 6. INTERACTIVE REPL
# -----------------------------------------------------------------------------
def main():
    os.system("cls" if os.name == "nt" else "clear")
    print(BOLD + CYAN + "=" * 75)
    print("🏛️  SOVEREIGN GEMINI MASTER SILICON & SWARM CLI")
    print("   Dual-Channel 808-Byte C++ Memory Layout • Surgical AST • Zero Bloat")
    print("=" * 75 + RESET)

    dll_lib, status_msg = load_sovereign_library()
    print(status_msg)

    active_node = "AcousticRouter"
    active_model = DEFAULT_MODEL
    task_count = 100

    print("\n" + BOLD + "Sensory Commands:" + RESET)
    print(f"  {YELLOW}/node <name>{RESET}   : Switch C++ state agent node (Current: {active_node})")
    print(f"  {YELLOW}/sql <query>{RESET}   : Run DuckDB SQL query (0 tokens)")
    print(f"  {YELLOW}/ast <file>{RESET}    : Surgical AST analysis (0 tokens)")
    print(f"  {YELLOW}/ls{RESET}            : Flat non-recursive directory scan (0 tokens)")
    print(f"  {YELLOW}/info{RESET}          : Workstation diagnostics & memory limits")
    print(f"  {YELLOW}/exit{RESET}          : Exit cleanly")
    print("-" * 75 + "\n")

    while True:
        try:
            prompt_tag = f"{CYAN}[GEMINI - {active_node}]{RESET}"
            user_input = input(f"👤 {prompt_tag} ❯ ").strip()
            if not user_input: continue

            if user_input.lower() in ["/exit", "exit", "quit"]:
                print(f"\n{CYAN}🛸 De-registering lifecycles. Stay sovereign.{RESET}\n")
                break

            if user_input.lower().startswith("/node "):
                active_node = user_input[6:].strip()
                print(f"{GREEN}✅ State agent node switched to: {active_node}{RESET}")
                continue

            if user_input.lower().startswith("/sql "):
                q = user_input[5:].strip()
                print(f"\n🦆 Running DuckDB SQL: {q}")
                print(run_duckdb_sql(q) + "\n")
                continue

            if user_input.lower().startswith("/ast "):
                fpath = user_input[5:].strip()
                print(json.dumps(inspect_file_ast(fpath), indent=2))
                continue

            if user_input.lower() == "/ls":
                print(json.dumps(list_immediate_dir(), indent=2))
                continue

            if user_input.lower() == "/info":
                print(f"\n{BOLD}{CYAN}📟 PHYSICAL WORKSTATION TELEMETRY:{RESET}")
                print(f"  - Active State Node : {active_node}")
                print(f"  - Gemini Model      : {active_model}")
                print(f"  - Local LM Port     : {LOCAL_PORT}")
                print(f"  - C++ Memory Layout : 808-byte static binary struct (<64s64s32s512s32s12f12fd)")
                print(f"  - DLL Memory Link   : {GREEN}BOUND & ACTIVE{RESET}" if dll_lib else f"{YELLOW}SIMULATED BYPASS ACTIVE{RESET}")
                print("-" * 75 + "\n")
                continue

            # --- DUAL PASS: GEMINI REASONING -> SILICON C++ PASS ---
            t0 = time.time()
            print(f"\n[✨ GEMINI STREAM] ", end="", flush=True)

            response = client.models.generate_content_stream(
                model=active_model,
                contents=user_input,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "You are the Sovereign System Intelligence Engine. Analyze the user prompt and provide an authoritative, concise response. "
                        "If audio calibration is mentioned, summarize target acoustic parameters."
                    ),
                    temperature=0.2,
                    max_output_tokens=1024
                )
            )

            full_text = []
            for chunk in response:
                if chunk.text:
                    print(chunk.text, end="", flush=True)
                    full_text.append(chunk.text)

            elapsed = time.time() - t0
            print(f"\n\n📊 [~{int(len(''.join(full_text))/4)} tokens | {len(''.join(full_text))/(4*elapsed):.1f} tok/s | Time: {elapsed:.2f}s]")

            # Run 808-byte C++ memory pass in microseconds
            task_count += 1
            sample_feats = [1.0] * 12
            execute_silicon_step(dll_lib, user_input, sample_feats, active_node=active_node, task_count=task_count)

        except (KeyboardInterrupt, EOFError):
            print("\n👋 Session interrupted. Exiting.")
            break
        except Exception as e:
            print(f"\n{RED}[-] Error: {e}{RESET}")

if __name__ == "__main__":
    main()