import os
import json
import time
import sys
import re
import socket
import subprocess
import traceback
from openai import OpenAI

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


# --- 1. ATTEMPT PYDANTIC-MONTY IMPORT ---
try:
    import pydantic_monty as monty
    HAS_MONTY = True
except ImportError:
    HAS_MONTY = False

# --- CONFIGURATION ---
TARGET_DIR = r"C:\WEB CASE STUDY"
# Support standard 1234 and alternate 1010 ports
LM_STUDIO_URL = "http://127.0.0.1:1234/v1"
client = OpenAI(base_url=LM_STUDIO_URL, api_key="lm-studio")
LLM_MODEL = "nvidia/nemotron-3-nano-4b"

DEFAULT_STUDIES_DIR = r"C:\STUDIES"
DEFAULT_LANCEDB_PATH = r"C:\STUDIES_BACKUP\vectors\lancedb_store"
DEFAULT_DUCKDB_PATH = r"C:\STUDIES\data\metadata\sonic_core.duckdb"

TARGET_PORTS = [
    1234,  # LM Studio Standard
    1010,  # LM Studio Alternate
    6379,  # Ray GCS Broker / Redis
    8000,  # Ray Serve Routing Proxy
    8001,  # MCP API Gateway (Onyx)
    8005,  # MCP RAG Control Channel (Warden)
    8265   # Ray Web Dashboard
]

# ==============================================================================
# 2. EXPERT-LEVEL COGNITIVE DISCOVERY TOOLS (SYSTEM & HARDWARE SENSORY MATRIX)
# ==============================================================================

def discover_files(root_dir: str = DEFAULT_STUDIES_DIR, target_extensions: list = None) -> str:
    """
    Recursively scans directory tree to discover active scripts, configurations, and database files.
    Allows LM Studio to find physical paths without guessing.
    """
    print(f"📂 [DISCOVERY] Recursively scanning '{root_dir}'...")
    if not os.path.exists(root_dir):
        return json.dumps({"status": "FAILED", "error": f"Root directory '{root_dir}' does not exist on disk."})
    
    if target_extensions is None:
        target_extensions = [".py", ".md", ".json", ".db", ".duckdb", ".lance", ".onnx", ".bin"]

    discovered_files = []
    file_count = 0
    max_files = 150  # Prevent blowing up LLM context window

    try:
        for root, dirs, files in os.walk(root_dir):
            # Skip heavy virtual environments, node modules, and git internals
            dirs[:] = [d for dirs_to_skip in [".venv", "node_modules", ".git", "venv", "__pycache__"] for d in dirs if d.lower() != dirs_to_skip]
            
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in target_extensions:
                    full_path = os.path.join(root, file)
                    discovered_files.append({
                        "name": file,
                        "relative_path": os.path.relpath(full_path, root_dir),
                        "absolute_path": full_path,
                        "size_bytes": os.path.getsize(full_path)
                    })
                    file_count += 1
                    if file_count >= max_files:
                        break
            if file_count >= max_files:
                break
                
        return json.dumps({
            "status": "SUCCESS",
            "root_scanned": root_dir,
            "total_matched": len(discovered_files),
            "files": discovered_files
        })
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": str(e)})

def query_duckdb_schema(db_path: str = DEFAULT_DUCKDB_PATH) -> str:
    """
    Programmatically connects to local DuckDB and returns the schemas of all tables.
    Gives the LLM structural awareness of our relational analytical store.
    """
    print(f"🦆 [DISCOVERY] Reading DuckDB Schema at '{db_path}'...")
    if not os.path.exists(db_path):
        return json.dumps({"status": "FAILED", "error": f"DuckDB file '{db_path}' does not exist."})
        
    try:
        import duckdb
        con = duckdb.connect(db_path, read_only=True)
        # Fetch tables
        tables_df = con.execute("SHOW TABLES").df()
        tables = list(tables_df['name']) if 'name' in tables_df.columns else list(tables_df.iloc[:,0])
        
        table_schemas = {}
        for table in tables:
            schema_df = con.execute(f"PRAGMA table_info('{table}')").df()
            row_count_df = con.execute(f"SELECT COUNT(*) FROM '{table}'").df()
            row_count = int(row_count_df.iloc[0, 0])
            
            columns = []
            for _, row in schema_df.iterrows():
                columns.append({
                    "name": row['name'],
                    "type": row['type'],
                    "notnull": bool(row['notnull']),
                    "dflt_value": str(row['dflt_value']) if row['dflt_value'] is not None else None
                })
            
            table_schemas[table] = {
                "row_count": row_count,
                "columns": columns
            }
            
        con.close()
        return json.dumps({"status": "SUCCESS", "db_path": db_path, "tables": table_schemas})
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": f"DuckDB query failed: {str(e)}"})

def query_lancedb_schema(path: str = DEFAULT_LANCEDB_PATH) -> str:
    """
    Programmatically connects to local LanceDB to retrieve vector table schemas and counts.
    Allows the model to understand the state of our semantic vector lakehouse store.
    """
    print(f"🗄️ [DISCOVERY] Connecting programmatically to LanceDB at '{path}'...")
    if not os.path.exists(path):
        return json.dumps({"status": "FAILED", "error": f"LanceDB path '{path}' does not exist on disk."})
    try:
        import lancedb
        db = lancedb.connect(path)
        try:
            tables = db.table_names()
        except Exception:
            tables = db.list_tables()
            
        table_details = {}
        for t in tables:
            t_str = t[0] if isinstance(t, tuple) else str(t)
            try:
                tbl = db.open_table(t_str)
                table_details[t_str] = {
                    "schema": list(tbl.schema.names),
                    "count": len(tbl)
                }
            except Exception as table_err:
                table_details[t_str] = {"error": f"Failed to open table: {str(table_err)}"}
        return json.dumps({"status": "SUCCESS", "lancedb_path": path, "tables": table_details})
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": str(e)})

def check_ray_cluster_state() -> str:
    """
    Connects to the active Ray cluster and returns actor states, GCS endpoints, and node metadata.
    Essential tool for using Ray Serve topology and Swarm knowledge correctly.
    """
    print("📡 [DISCOVERY] Pinging Ray cluster state...")
    try:
        import ray
        if not ray.is_initialized():
            ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
            
        nodes = ray.nodes()
        
        # Test latency using a remote ping task
        @ray.remote(num_cpus=0)
        def rpc_ping():
            return time.time_ns()
            
        start_ns = time.time_ns()
        ref = rpc_ping.remote()
        server_time_ns = ray.get(ref, timeout=2.0)
        end_ns = time.time_ns()
        
        round_trip_ms = (end_ns - start_ns) / 1_000_000.0
        
        # Fetch active Ray actors (uses internal API)
        try:
            from ray._private.state import state
            actors_info = state.actors()
            active_actors = []
            for actor_id, actor_data in actors_info.items():
                if actor_data.get("State") == "ALIVE":
                    active_actors.append({
                        "id": actor_id,
                        "name": actor_data.get("Name"),
                        "class": actor_data.get("ClassName"),
                        "namespace": actor_data.get("Namespace"),
                        "pid": actor_data.get("Pid")
                    })
        except Exception:
            active_actors = "Ray actor state API restricted or unavailable in local client."

        return json.dumps({
            "status": "SUCCESS",
            "ray_gcs_address": ray.get_runtime_context().gcs_address,
            "node_count": len(nodes),
            "round_trip_latency_ms": round_trip_ms,
            "active_actors": active_actors,
            "message": "Swarm is functional and fully connected."
        })
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": f"Ray cluster discovery failed: {str(e)}"})

def scan_network_and_processes() -> str:
    """
    Sweeps active loops and TCP port registers to verify the state of loopback pathways,
    and runs a local process table diagnostic matching Node/Python/Ray/LM Studio instances.
    """
    print("🔌 [DISCOVERY] Running process and network socket registry check...")
    open_ports = []
    for port in TARGET_PORTS:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                res = s.connect_ex(("127.0.0.1", port))
                if res == 0:
                    open_ports.append(port)
        except Exception:
            pass

    active_processes = []
    target_substrings = ["node", "python", "ray", "lmstudio", "duckdb", "lancedb"]
    try:
        if os.name == 'nt':  # Windows
            cmd = "tasklist /FO CSV /NH"
            output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
            for line in output.splitlines():
                if any(sub in line.lower() for sub in target_substrings):
                    clean_line = line.replace('"', '')
                    parts = clean_line.split(",")
                    if len(parts) >= 5:
                        active_processes.append({
                            "ImageName": parts[0].strip(),
                            "PID": parts[1].strip(),
                            "SessionName": parts[2].strip(),
                            "MemUsage": parts[4].strip()
                        })
        else:  # POSIX / Linux
            cmd = "ps -eo pid,ppid,rss,comm,args"
            output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
            for line in output.splitlines():
                if any(sub in line.lower() for sub in target_substrings):
                    parts = line.strip().split(None, 4)
                    if len(parts) >= 4:
                        active_processes.append({
                            "PID": parts[0],
                            "PPID": parts[1],
                            "RSS_KB": parts[2],
                            "Command": parts[3],
                            "FullArgs": parts[4] if len(parts) > 4 else ""
                        })
    except Exception as e:
        active_processes = f"Process scan failed: {str(e)}"

    return json.dumps({
        "status": "SUCCESS",
        "active_ports": open_ports,
        "processes_found": len(active_processes) if isinstance(active_processes, list) else 0,
        "active_processes": active_processes[:20] if isinstance(active_processes, list) else active_processes
    })

def read_active_file(filepath: str, lines: int = 50) -> str:
    """
    Loads a specific file or log into context slot for dynamic structural analysis.
    Prevents guessing by reading files directly.
    """
    print(f"📖 [DISCOVERY] Loading active file content: '{filepath}'...")
    if not os.path.exists(filepath):
        # Retry with target directory base if path is relative
        fallback_path = os.path.join(TARGET_DIR, filepath)
        if not os.path.exists(fallback_path):
            return json.dumps({"status": "FAILED", "error": f"File '{filepath}' not found."})
        filepath = fallback_path

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content_lines = f.readlines()
        tail = content_lines[-min(len(content_lines), lines):]
        return json.dumps({
            "status": "SUCCESS",
            "filepath": filepath,
            "total_lines": len(content_lines),
            "tail_content": "".join(tail)
        })
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": str(e)})


# ==============================================================================
# 3. SELF-HEALING PRE-FLIGHT SANDBOX AND FILE ENGINE
# ==============================================================================

def execute_preflight_and_write(filename: str, code_content: str) -> str:
    """
    Evaluates Python AST and syntax in a sub-microsecond Pydantic-Monty Rust VM.
    Automatically repairs Markdown dunder formatting corruption before execution.
    """
    print(f"\n🔍 [PRE-FLIGHT] Verifying '{filename}' via Pydantic-Monty...")
    
    # --- AUTO-HEALING REGEX REGION ---
    # Detects markdown-bold 'mangled' dunders like **name** or **main** and converts them to valid __name__ / __main__
    repaired_code = re.sub(r'\*\*([a-zA-Z0-9_]+)\*\*', r'__\1__', code_content)
    repaired_code = repaired_code.replace("**name**", "__name__").replace("**main**", "__main__")
    
    if repaired_code != code_content:
        print("⚡ [AUTO-HEALER] Intercepted and repaired Markdown-bold dunder mangling in source code!")

    if not HAS_MONTY:
        filepath = os.path.join(TARGET_DIR, filename)
        try:
            os.makedirs(TARGET_DIR, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(repaired_code)
            return json.dumps({
                "status": "WARNING",
                "message": f"File written to {filepath} but Monty was unavailable for pre-flight verification."
            })
        except Exception as e:
            return json.dumps({"status": "FAILED", "error": str(e)})

    try:
        # Physical runtime execution of code block inside Rust VM to verify import & AST structures
        with monty.Monty() as pool:
            with pool.checkout() as session:
                session.feed_run(repaired_code)
                
        # If execution reaches here, code is syntactically perfect and robust
        os.makedirs(TARGET_DIR, exist_ok=True)
        filepath = os.path.join(TARGET_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(repaired_code)
            
        print(f"✅ [SUCCESS] Pre-flight passed! Repaired code written to: {filepath}")
        return json.dumps({
            "status": "SUCCESS", 
            "message": f"Code successfully verified in Rust VM sandbox and written to {filepath}"
        })
        
    except Exception as e:
        print(f"❌ [PRE-FLIGHT FAILED] Intercepted syntax/runtime error: {e}")
        return json.dumps({
            "status": "REJECTED_BY_PREFLIGHT",
            "error_message": f"Syntax/Runtime verification failed: {str(e)}. Please fix the script and resubmit."
        })


# ==============================================================================
# 4. MASTER ORCHESTRATOR LOOP WITH TOTAL DISCOVERY MATRIX
# ==============================================================================

def run_expert_coder_with_discovery(prompt: str):
    print("=" * 80)
    print("🤖 INITIATING EXPERT SELF-HEALING CODER (V3 DISCOVERY ENGINE)")
    print("=" * 80)
    
    # Combined Tool Schemas: Writing + All Sensory Discovery Tools
    tools = [
        {
            "type": "function",
            "function": {
                "name": "write_verified_code",
                "description": "Writes Python code to a file ONLY IF it passes Rust VM syntax verification.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string", "description": "Filename (e.g. telemetry_cleaner.py)"},
                        "code_content": {"type": "string", "description": "Raw Python code string."}
                    },
                    "required": ["filename", "code_content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "discover_files",
                "description": "Scans root folders (like C:\\STUDIES) recursively to locate active files, configs, and notebooks.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "root_dir": {"type": "string", "description": "Base directory to start search.", "default": DEFAULT_STUDIES_DIR},
                        "target_extensions": {"type": "array", "items": {"type": "string"}, "description": "Filter by extension (e.g. ['.py', '.json'])"}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "query_duckdb_schema",
                "description": "Programmatically connects to DuckDB to read schemas and row counts for analytical store verification.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "db_path": {"type": "string", "description": "Absolute path to duckdb catalog file.", "default": DEFAULT_DUCKDB_PATH}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "query_lancedb_schema",
                "description": "Connects programmatically to LanceDB to fetch available table schemas and record sizes.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Absolute path to LanceDB folder.", "default": DEFAULT_LANCEDB_PATH}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_ray_cluster_state",
                "description": "Interrogates Ray GCS and returns active actors, namespaces, GCS broker info, and latency metrics."
            }
        },
        {
            "type": "function",
            "function": {
                "name": "scan_network_and_processes",
                "description": "Checks daemon ports and scans host process tables to map active Node, Python, and Raylet engines."
            }
        },
        {
            "type": "function",
            "function": {
                "name": "read_active_file",
                "description": "Reads trailing lines of any target configuration, python script, or log file to analyze its real-world content.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string", "description": "Target absolute or relative filename."},
                        "lines": {"type": "integer", "description": "Lines of tail log to return.", "default": 50}
                    },
                    "required": ["filepath"]
                }
            }
        }
    ]
    
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert systems developer operating in a strict pre-flight sandbox. "
                "You have access to a filesystem writer and an expanded system-wide sensory discovery matrix.\\n\\n"
                "SANDBOX ENVIRONMENT CONSTRAINTS:\\n"
                "1. Built-in `input()` is DISABLED. Calling it causes a NameError. Never use it.\\n"
                "2. `sys.argv` is not initialized by default. Referencing it directly throws an AttributeError. "
                "Always safeguard command-line checks with `if hasattr(sys, 'argv') and len(sys.argv) > 1:`.\\n"
                "3. Double-underscores like __name__ or __main__ can sometimes be mangled by Markdown converters "
                "into bold markers (**name** or **main**). Your file writer will attempt to auto-repair this, "
                "but you should write cleanly and avoid Markdown syntax inside your raw code content.\\n\\n"
                "OPERATIONAL STRATEGY:\\n"
                "Do NOT guess file directories, tables, schemas, or active ports. Use your tools sequentially to discover:\\n"
                "- Find all active files and configurations using `discover_files` and `read_active_file`.\\n"
                "- Inspect database layouts using `query_duckdb_schema` and `query_lancedb_schema`.\\n"
                "- Verify Ray cluster status with `check_ray_cluster_state`.\\n"
                "- Detect ports and active system processes with `scan_network_and_processes`.\\n"
                "Write files by calling `write_verified_code` so your scripts are checked by Pydantic-Monty pre-flight."
            )
        },
        {"role": "user", "content": prompt}
    ]
    
    for turn in range(10):  # Expand turn headroom to support deep discovery + write
        print(f"\n📡 [TURN {turn+1}] Querying local model at {LM_STUDIO_URL}...")
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                tools=tools,
                temperature=0.0
            )
        except Exception as e:
            print(f"❌ Connection to LM Studio failed: {e}")
            break
            
        if not response.choices:
            print("❌ Empty response choices returned.")
            break
            
        choice = response.choices[0]
        message = choice.message
        
        # Display thoughts if available
        if hasattr(message, "reasoning_content") and message.reasoning_content:
            print(f"\n💭 [THOUGHTS] {message.reasoning_content}")
        elif message.content:
            print(f"\n💬 [ASSISTANT] {message.content}")

        # Build clean message structure, stripping non-standard fields
        assistant_msg = {
            "role": "assistant",
            "content": message.content or ""
        }
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
        
        if message.tool_calls:
            for tool_call in message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                
                print(f"🔨 [TOOL CALL] Assistant requested execution of '{fn_name}' with args: {fn_args}")
                
                # Dynamic routing of sensory discovery and writing tools
                if fn_name == "write_verified_code":
                    result = execute_preflight_and_write(**fn_args)
                elif fn_name == "discover_files":
                    result = discover_files(
                        fn_args.get("root_dir", DEFAULT_STUDIES_DIR),
                        fn_args.get("target_extensions")
                    )
                elif fn_name == "query_duckdb_schema":
                    result = query_duckdb_schema(fn_args.get("db_path", DEFAULT_DUCKDB_PATH))
                elif fn_name == "query_lancedb_schema":
                    result = query_lancedb_schema(fn_args.get("path", DEFAULT_LANCEDB_PATH))
                elif fn_name == "check_ray_cluster_state":
                    result = check_ray_cluster_state()
                elif fn_name == "scan_network_and_processes":
                    result = scan_network_and_processes()
                elif fn_name == "read_active_file":
                    result = read_active_file(fn_args["filepath"], fn_args.get("lines", 50))
                else:
                    result = json.dumps({"error": f"Unknown discovery tool: {fn_name}"})
                
                print(f"📥 [TOOL OUTPUT] Returned (snippet): {result[:300]}...")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
                
                # Exit early if write succeeds cleanly
                if fn_name == "write_verified_code":
                    res_data = json.loads(result)
                    if res_data.get("status") == "SUCCESS":
                        print("\n🏁 [COMPLETE] Coder completed task and wrote clean verified file!")
                        return
        else:
            print("\n🏁 [COMPLETE] Model finished response without further tool calls:")
            print(message.content)
            break

if __name__ == "__main__":
    task_prompt = (
        "Scan our system files and directories, find our DuckDB database and inspect its schema, "
        "and verify if our Ray cluster is active. Once system state is audited, write a python "
        "re-synchronizer called 'lakehouse_sync.py' that syncs new .wav files between C:\\STUDIES\\generated_audio "
        "and our active analytical tables, logging the sync stats back into the database."
    )
    run_expert_coder_with_discovery(task_prompt)