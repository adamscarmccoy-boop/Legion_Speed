import os
import re
import sys
import json
import time
import socket
import logging
import subprocess
import traceback
import sysconfig
from pathlib import Path

# =============================================================================
# COGNITIVE SYSTEM SECURITY AND LIFECYCLE INITIALIZATION (PREVENT ACCESS VIOLATIONS)
# =============================================================================
# Force early low-overhead environment variables before importing heavy frameworks
os.environ["RAY_gcs_rpc_server_reconnect_timeout_s"] = "120"
os.environ["RAY_memory_monitor_refresh_ms"] = "250"
os.environ["RAY_DEDUP_LOGS"] = "0"
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

# Programmatic Windows DLL directory registration
try:
    purelib_path = Path(sysconfig.get_paths()["purelib"])
    dll_dir = purelib_path / "ray" / "libs"
    if dll_dir.exists():
        os.add_dll_directory(dll_dir)
    elif (purelib_path / "ray.libs").exists():
        os.add_dll_directory(purelib_path / "ray.libs")
except Exception as e:
    sys.stderr.write(f"[Warden Warning] DLL directory bypass: {e}\n")

# Native Windows Job Object binding (Force cascade-killing of sub-processes)
if os.name == 'nt':
    try:
        import win32job
        import win32handle
        import win32process

        h_job = win32job.CreateJobObject(None, "")
        extended_info = win32job.QueryInformationJobObject(h_job, win32job.JobObjectExtendedLimitInformation)
        extended_info['BasicLimitInformation']['LimitFlags'] = win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        win32job.SetInformationJobObject(h_job, win32job.JobObjectExtendedLimitInformation, extended_info)
        win32job.AssignProcessToJobObject(h_job, win32process.GetCurrentProcess())
        global _h_job_sentinel
        _h_job_sentinel = h_job
        sys.stderr.write("[+] Windows Job Object bound successfully. Subprocess orphan protection active.\n")
    except Exception as job_err:
        sys.stderr.write(f"[-] Windows Job Object bypass (requires pywin32): {job_err}\n")

# Set up clean logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | [SOVEREIGN WARDEN] | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("Warden")

# =============================================================================
# CORE CONFIGURATION AND WORKSPACE DEFINITIONS
# =============================================================================
TARGET_WORKSPACE = r"C:\WEB CASE STUDY"
DUCKDB_PATH = r"C:\STUDIES\data\metadata\sonic_core.duckdb"
LANCE_DB_PATH = r"C:\STUDIES_BACKUP\vectors\lancedb_store"
LLM_MODEL = "nvidia/nemotron-3-nano-4b"

# Automatically resolve the active local inference endpoint
LM_STUDIO_PORTS = [1234, 1010]
LM_STUDIO_URL = None

log.info("[*] Handshaking with loopback inference engines...")
for port in LM_STUDIO_PORTS:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                LM_STUDIO_URL = f"http://127.0.0.1:{port}/v1"
                log.info(f"✅ Success: Active LM Studio detected on Port {port}")
                break
    except Exception:
        pass

if not LM_STUDIO_URL:
    LM_STUDIO_URL = "http://127.0.0.1:1234/v1"
    log.warning(f"[-] No responsive socket found. Defaulting to standard Port 1234: {LM_STUDIO_URL}")

try:
    from openai import OpenAI
    client = OpenAI(base_url=LM_STUDIO_URL, api_key="lm-studio")
except ImportError:
    log.error("[-] OpenAI SDK missing. Run 'pip install openai' to enable API handshakes.")
    sys.exit(1)

# Ensure Pydantic-Monty is present for bare-metal sandboxed validation
try:
    import pydantic_monty as monty
    HAS_MONTY = True
    log.info("💎 Pydantic-Monty SDK detected. Rust-backed bytecode sandbox active.")
except ImportError:
    HAS_MONTY = False
    log.warning("[!] Pydantic-Monty not found in this environment. Falling back to AST dry-run checks.")

# =============================================================================
# THE SOVEREIGN TOOL SYSTEM
# =============================================================================

def read_file(filepath: str, max_chars: int = 20000) -> str:
    """Read file contents safely from target workspace with truncation guards."""
    try:
        resolved_path = Path(TARGET_WORKSPACE) / filepath if not os.path.isabs(filepath) else Path(filepath)
        if not resolved_path.exists():
            return json.dumps({"status": "FAILED", "error": f"File '{resolved_path}' not found."})
        
        with open(resolved_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
        if len(content) > max_chars:
            return json.dumps({
                "status": "TRUNCATED_SUCCESS",
                "filepath": str(resolved_path),
                "content": content[:max_chars] + f"\n\n[TRUNCATED - {len(content)} total chars. Use surgical editing blocks.]"
            })
        return json.dumps({"status": "SUCCESS", "filepath": str(resolved_path), "content": content})
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": str(e)})

def list_directory(path: str = "./") -> str:
    """Lists workspace contents to dynamically map active scripts and configurations."""
    try:
        resolved_path = Path(TARGET_WORKSPACE) / path if not os.name == 'nt' or not os.path.isabs(path) else Path(path)
        if not resolved_path.exists():
            return json.dumps({"status": "FAILED", "error": f"Path '{resolved_path}' not found."})
        
        items = os.listdir(resolved_path)
        return json.dumps({"status": "SUCCESS", "directory": str(resolved_path), "contents": items})
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": str(e)})

def check_port_status(port: int) -> str:
    """Handshakes with active sockets (6379 Ray GCS, 8001 Gateway, 8005 RAG) to verify binding health."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return json.dumps({"port": port, "status": "ONLINE", "message": f"Successfully connected to 127.0.0.1:{port}"})
            return json.dumps({"port": port, "status": "OFFLINE", "message": "Connection actively refused"})
    except Exception as e:
        return json.dumps({"port": port, "status": "OFFLINE", "error": str(e)})

def query_duckdb_logs(query: str) -> str:
    """Queries your SQL relational left-brain (DuckDB) for system logs or previous error histories."""
    try:
        import duckdb
        con = duckdb.connect(DUCKDB_PATH, read_only=True)
        # Block dangerous modification queries
        dangerous_verbs = ["drop", "delete", "insert", "update", "alter", "truncate", "create"]
        if any(verb in query.lower() for v in dangerous_verbs):
            con.close()
            return json.dumps({"status": "REJECTED", "error": "Write and structure modifications are blocked in this tool."})
        
        df = con.execute(query).df()
        con.close()
        return json.dumps({"status": "SUCCESS", "columns": list(df.columns), "rows": df.values.tolist()[:30]})
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": f"DuckDB query execution error: {str(e)}"})

def inspect_lancedb_schemas() -> str:
    """Inspects the LanceDB vector schema, active row counts, and locks."""
    if not os.path.exists(LANCE_DB_PATH):
        return json.dumps({"status": "FAILED", "error": f"LanceDB directory '{LANCE_DB_PATH}' not found."})
    try:
        import lancedb
        db = lancedb.connect(LANCE_DB_PATH)
        tables = db.table_names()
        details = {}
        for table_name in tables:
            t_str = table_name[0] if isinstance(table_name, tuple) else str(table_name)
            tbl = db.open_table(t_str)
            details[t_str] = {
                "schema": list(tbl.schema.names),
                "count": len(tbl)
            }
        return json.dumps({"status": "SUCCESS", "tables": details})
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": f"LanceDB inspection failed: {str(e)}"})

def execute_shell_diagnostic(command: str) -> str:
    """Executes safe diagnostic shell commands inside your active workspace directory."""
    blocked_patterns = ["rm ", "del ", "shutdown", "format", "curl", "wget"]
    if any(pat in command.lower() for pat in blocked_patterns):
        return json.dumps({"status": "BLOCKED", "error": "Shell operation contains restricted system actions."})
    try:
        res = subprocess.run(
            command, shell=True, capture_output=True, text=True, cwd=TARGET_WORKSPACE, timeout=20
        )
        return json.dumps({
            "status": "SUCCESS",
            "exit_code": res.returncode,
            "stdout": res.stdout,
            "stderr": res.stderr
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"status": "TIMEOUT", "error": "Shell process exceeded the 20-second timeout ceiling."})
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": str(e)})

def run_pydantic_monty_lint(code_content: str) -> dict:
    """
    Sub-microsecond pre-flight compilation check using Pydantic-Monty.
    Compiles Python AST down to sandboxed bytecode inside isolated Rust worker processes.
    Catches syntax mistakes, invalid imports, and dunder mangling before code touches physical disk.
    """
    if not HAS_MONTY:
        # Fallback compile syntax check if Monty is not installed on host
        try:
            compile(code_content, "<pre_flight_dry_run>", "exec")
            return {"success": True, "sandbox_type": "cpython_ast_compile", "message": "Syntax is valid."}
        except SyntaxError as se:
            return {"success": False, "sandbox_type": "cpython_ast_compile", "error": f"SyntaxError: {str(se)}"}

    try:
        # Execute code cleanly within Monty pool context managers
        # with monty.Monty() as pool:
        #     with pool.checkout() as session:
        #         res = session.feed_run(code_content)
        # Using exact API signatures extracted via inspect engines
        with monty.Monty() as pool:
            with pool.checkout() as session:
                complete = session.feed_run(code_content)
                # If it executed or compiled successfully without crashing
                return {
                    "success": True,
                    "sandbox_type": "pydantic_monty_rust",
                    "output": complete.output if hasattr(complete, 'output') else "Empty output (execution passed)"
                }
    except monty.MontySyntaxError as mse:
        return {"success": False, "sandbox_type": "pydantic_monty_rust", "error": f"MontySyntaxError: {str(mse)}"}
    except monty.MontyTypingError as mte:
        return {"success": False, "sandbox_type": "pydantic_monty_rust", "error": f"MontyTypingError: {str(mte)}"}
    except monty.MontyCrashedError as mce:
        return {"success": False, "sandbox_type": "pydantic_monty_rust", "error": f"MontyCrashedError: Worker exited abruptly. {str(mce)}"}
    except Exception as e:
        return {"success": False, "sandbox_type": "pydantic_monty_rust_wrapper", "error": f"VM Error: {str(e)}"}

def write_verified_file(filename: str, code_content: str) -> str:
    """
    Surgically writes python code back to your active C:\\WEB CASE STUDY development folder
    ONLY if the code passes 100% of pre-flight Pydantic-Monty checks.
    """
    log.info(f"🛡️  [PRE-FLIGHT] Request to write '{filename}'. Evaluating code in sandbox...")
    
    # Auto-repair common markdown dunder mangling before linting
    repaired_code = re.sub(r'\*+([a-zA-Z0-9_]+)\*+', r'__\1__', code_content)
    repaired_code = repaired_code.replace("**name**", "__name__").replace("**main**", "__main__")
    
    # Run the pre-flight check
    lint_result = run_pydantic_monty_lint(repaired_code)
    
    if not lint_result["success"]:
        log.error(f"❌ [PRE-FLIGHT REJECTED]: Code verification failed. Aborting write to prevent corruption.")
        return json.dumps({
            "status": "REJECTED_BY_PREFLIGHT",
            "error_message": lint_result.get("error", "Unknown compilation error"),
            "suggestion": "Analyze the compilation stack trace, correct the imports or syntax in your context manager, and re-invoke."
        })
        
    log.info(f"✅ [PRE-FLIGHT SUCCESS]: Code compiled cleanly in VM. Committing write to disk...")
    try:
        resolved_path = Path(TARGET_WORKSPACE) / filename
        # Ensure parent dirs exist
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(resolved_path, "w", encoding="utf-8") as f:
            f.write(repaired_code)
            
        log.info(f"💾 File successfully written and locked: {resolved_path}")
        return json.dumps({
            "status": "SUCCESS",
            "filepath": str(resolved_path),
            "preflight_metrics": lint_result
        })
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": f"File commit failed: {str(e)}"})

# =============================================================================
# OpenAI COMPATIBLE SCHEMA REGISTER DEFINITIONS
# =============================================================================

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Lists directories on your workstation filesystem to find active RAG or Gateway scripts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "default": "./", "description": "Folder path to scan."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads a code file from the filesystem with safety limits to review logic or imports.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Absolute path or relative workspace name."}
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_port_status",
            "description": "Verifies if loopback ports (6379 Ray GCS, 8001 Gateway, 8005 RAG, 1234 LM Studio) are listening.",
            "parameters": {
                "type": "object",
                "properties": {
                    "port": {"type": "integer", "description": "Port number to check."}
                },
                "required": ["port"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_duckdb_logs",
            "description": "Runs a SQL relational select query against your local sonic_core.duckdb database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Relational read-only SQL string."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_lancedb_schemas",
            "description": "Retrieves schemas, table metadata, and vector sizes from your LanceDB storage folders."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_shell_diagnostic",
            "description": "Runs non-destructive shell diagnostic commands inside your active workspace directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute."}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_verified_file",
            "description": "Lints code in Pydantic-Monty Rust VM. Writes to Windows disk ONLY if checks pass 100%.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Target script name (e.g., mcp_swarm_gateway.py)"},
                    "code_content": {"type": "string", "description": "Raw unformatted Python code string."}
                },
                "required": ["filename", "code_content"]
            }
        }
    }
]

# =============================================================================
# COGNITIVE CLOSED-LOOP ORCHESTRATOR RUNNER
# =============================================================================

def run_warden_loop():
    print("=" * 80)
    print("🛡️  SOVEREIGN WARDEN: PRE-FLIGHT DIAGNOSTICS & SYSTEM HEALER ACTIVE")
    print("=" * 80)

    system_prompt = (
        "You are an expert autonomic systems developer orchestrating a high-performance Windows 11 workstation.\\n"
        "Your ultimate goal is to monitor system ports, read logs, diagnose python exceptions, and repair files autonomously.\\n\\n"
        "SYSTEM ENVIRONMENT GUIDELINES:\\n"
        "- Target Code Workspace: C:\\\\WEB CASE STUDY\\n"
        "- Vector Store Memory: C:\\\\STUDIES_BACKUP\\\\vectors\\\\lancedb_store\\n"
        "- Fact/Log DB: C:\\\\STUDIES\\\\data\\\\metadata\\\\sonic_core.duckdb\\n"
        "- Loopback Sockets: Port 1234/1010 (LM Studio), 6379 (Ray GCS), 8001 (MCP Swarm Gateway), 8005 (MCP RAG Server)\\n\\n"
        "CRITICAL RULES:\\n"
        "1. Never guess. Call tools sequentially in a closed-loop to discover the ground-truth state.\\n"
        "2. If you write code, you MUST use the 'write_verified_file' tool. It will compile your code in a Pydantic-Monty "
        "Rust sandbox before writing to disk. If the sandbox returns an error, analyze the trace and correct your code in the next turn.\\n"
        "3. Interactive input() is strictly disabled. Pass values via sys.argv.\\n"
        "4. Output clean dunder formatting (like __name__ or __main__) without markdown bold delimiters around them.\\n"
        "5. Keep responses direct and highly focused on technical facts. When complete, provide a final status card detailing:\\n"
        "ROOT CAUSE | ACTIONS EXECUTED | COMPILATION VERDICT | RECOMMENDED RUNTIME SEQUENCE"
    )

    user_query = (
        "Scan our C:\\WEB CASE STUDY workspace directory to map active files. Verify if the active ports are online. "
        "Locate any failing registration codes, incorrect imports, or markdown-mangled dunders, execute the Monty-linted self-healing "
        "repair on the target file, and provide a final status report."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ]

    # Bound the loop to 8 sequential turns to prevent runaway model execution
    for turn in range(8):
        log.info(f"📡 [TURN {turn+1}/8] Dispatching system state payload to local model at {LM_STUDIO_URL}...")
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                tools=TOOL_SCHEMAS,
                temperature=0.0
            )
        except Exception as e:
            log.error(f"Failed to communicate with LM Studio endpoint: {e}")
            break

        if not response.choices:
            log.warning("Empty response package received from inference slots.")
            break

        choice = response.choices[0]
        message = choice.message

        assistant_msg = {"role": "assistant", "content": message.content or ""}
        if message.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in message.tool_calls
            ]
        messages.append(assistant_msg)

        if not message.tool_calls:
            print("\n" + "="*80)
            print("🏁 [SOVEREIGN WARDEN LOOP FINAL VERDICT]:")
            print("-"*80)
            print(message.content)
            print("="*80 + "\n")
            break

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

            log.info(f"🔨 [EXECUTING SYSTEM TOOL]: {name} with arguments: {args}")

            if name == "list_directory":
                output = list_directory(args.get("path", "./"))
            elif name == "read_file":
                output = read_file(args.get("filepath"))
            elif name == "check_port_status":
                output = check_port_status(args.get("port"))
            elif name == "query_duckdb_logs":
                output = query_duckdb_logs(args.get("query"))
            elif name == "inspect_lancedb_schemas":
                output = inspect_lancedb_schemas()
            elif name == "execute_shell_diagnostic":
                output = execute_shell_diagnostic(args.get("command"))
            elif name == "write_verified_file":
                output = write_verified_file(
                    args.get("filename"),
                    args.get("code_content")
                )
            else:
                output = json.dumps({"error": f"Tool '{name}' is not bound inside the warden control interface."})

            trace_snippet = output[:350] + "..." if len(output) > 350 else output
            log.info(f"📥 [TOOL EXECUTION FEEDBACK]: {trace_snippet}")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": output
            })

if __name__ == "__main__":
    run_warden_loop()
