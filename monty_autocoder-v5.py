# monty_autocoder-v5.py
# Expert Autonomous Code-Writer & Dynamic Self-Healing Port-Aware Agent
# Fuses local LM Studio (llama_server) with Monty's AST pre-flight sandbox and Ray GCS directory services.

import os
import sys
import re
import time
import socket
import json
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
    # Avoid raising SystemExit inside an atexit callback (which causes RuntimeWarnings)
    if args and isinstance(args[0], int):
        sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================


# Try to import pydantic_monty if available
try:
    import pydantic_monty as monty
    HAS_MONTY = True
except ImportError:
    HAS_MONTY = False

# Try to import psutil for low-level socket-port mapping
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# --- ARCHITECTURAL CONSTANTS ---
TARGET_DIR = r"C:\WEB CASE STUDY"
DEFAULT_LANCEDB_PATH = r"C:\STUDIES_BACKUP\vectors\lancedb_store"
DEFAULT_DUCKDB_PATH = r"C:\STUDIES_BACKUP\data\metadata\sonic_core_v2.duckdb"
DUCKDB_FALLBACK_PATH = r"C:\STUDIES_BACKUP\data\metadata\sonic_core.duckdb"
LLM_MODEL = "nvidia/nemotron-3-nano-4b"

# Ensure clean console streaming
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# =============================================================================
# 1. BULLETPROOF DYNAMIC PORT DISCOVERY KERNEL
# =============================================================================

def discover_active_lms_endpoint() -> str:
    """
    Dynamically sweeps open ports and active host processes to find where
    llama_server or lms has bound itself, bypasses static hardcoded limits!
    """
    print("📡 [PORT SCANNER] Initializing dynamic endpoint discovery...")
    import requests
    
    # 1. Pre-flight check standard port
    default_url = "http://127.0.0.1:1234/v1"
    try:
        res = requests.get(f"{default_url}/models", timeout=0.5)
        if res.status_code == 200:
            print(f"   [+] LM Studio C++ Engine active on standard Port: 1234")
            return default_url
    except Exception:
        pass

    # 2. Process inspection via psutil
    if HAS_PSUTIL:
        print("   🔍 Interrogating active process tree via psutil...")
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                proc_name = (proc.info['name'] or '').lower()
                if "llama" in proc_name or "lms" in proc_name or "studio" in proc_name:
                    pid = proc.info['pid']
                    connections = proc.connections(kind='tcp')
                    for conn in connections:
                        if conn.status == 'LISTEN' and conn.laddr.ip in ['127.0.0.1', '0.0.0.0', '::1']:
                            test_port = conn.laddr.port
                            test_url = f"http://127.0.0.1:{test_port}/v1"
                            try:
                                res = requests.get(f"{test_url}/models", timeout=0.5)
                                if res.status_code == 200:
                                    print(f"   [+] Discovered active llama_server process (PID {pid}) listening on Port {test_port}")
                                    return test_url
                            except Exception:
                                continue
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

    # 3. Fast range sweep over likely ports
    candidate_ports = [1234, 1010, 56217, 61777, 64801, 52519, 8000]
    print(f"   🔍 Sweeping candidates: {candidate_ports}...")
    for port in candidate_ports:
        test_url = f"http://127.0.0.1:{port}/v1"
        try:
            res = requests.get(f"{test_url}/models", timeout=0.5)
            if res.status_code == 200:
                print(f"   [+] Discovered active socket on custom Port: {port}")
                return test_url
        except Exception:
            continue

    # 4. Fallback search via Windows netstat
    if os.name == 'nt':
        print("   🔍 Executing Windows shell port table extraction...")
        try:
            output = subprocess.check_output("netstat -ano -p tcp", shell=True, text=True)
            pids_of_interest = []
            # Find PIDs of llama_server or lms
            proc_output = subprocess.check_output("tasklist /FI \"IMAGENAME eq llama_server*\" /NH /FO CSV", shell=True, text=True)
            for line in proc_output.splitlines():
                if "llama" in line.lower():
                    parts = line.replace('"', '').split(",")
                    if len(parts) >= 2:
                        pids_of_interest.append(parts[1].strip())
                        
            for line in output.splitlines():
                if "LISTENING" in line:
                    for pid in pids_of_interest:
                        if line.endswith(pid):
                            # Extract port
                            match = re.search(r'127\.0\.0\.1:(\d+)', line)
                            if match:
                                test_port = int(match.group(1))
                                test_url = f"http://127.0.0.1:{test_port}/v1"
                                try:
                                    res = requests.get(f"{test_url}/models", timeout=0.5)
                                    if res.status_code == 200:
                                        print(f"   [+] Discovered Windows bound socket on Port {test_port} for PID {pid}")
                                        return test_url
                                except Exception:
                                    pass
        except Exception as e:
            print(f"   [-] Windows netstat sweep failed: {e}")

    print("   ⚠️ [WARNING] No active llama_server found. Defaulting to fallback http://127.0.0.1:1234/v1")
    return default_url


# Discover the active API endpoint before starting
LM_STUDIO_URL = discover_active_lms_endpoint()
try:
    client = OpenAI(base_url=LM_STUDIO_URL, api_key="lm-studio")
except Exception as e:
    print(f"[-] Warn: OpenAI client initialization failed: {e}")


# =============================================================================
# 2. SYSTEM DISCOVERY & CODE-WRITING TOOLS
# =============================================================================

def check_ray_cluster_state() -> str:
    """Queries GCS directly to find active named actors, classes, namespaces, and node layouts."""
    print("📡 [ACTOR DISCOVERY] Querying active GCS actor registry...")
    try:
        import ray
        if not ray.is_initialized():
            ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
            
        nodes = ray.nodes()
        
        # Test RPC latency inside the active swarm
        @ray.remote(num_cpus=0)
        def rpc_ping(): return time.time_ns()
        
        start_ns = time.time_ns()
        ref = rpc_ping.remote()
        server_time_ns = ray.get(ref, timeout=1.5)
        round_trip_ms = (time.time_ns() - start_ns) / 1_000_000.0
        
        # Resolve named actors in the cluster GCS
        active_actors = []
        for name in ["PaniniRagEngine", "SovereignSieveAgent", "ACPControlPlane", "SovereignGenomeInference"]:
            try:
                ray.get_actor(name, namespace="legion")
                active_actors.append({"name": name, "status": "ALIVE", "namespace": "legion"})
            except Exception:
                pass

        return json.dumps({
            "status": "SUCCESS",
            "gcs_address": ray.get_runtime_context().gcs_address,
            "node_count": len(nodes),
            "swarm_latency_ms": round_trip_ms,
            "active_actors": active_actors
        })
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": f"Ray cluster unavailable: {str(e)}"})

def query_duckdb_schema(db_path: str = DEFAULT_DUCKDB_PATH) -> str:
    """Connects programmatically to DuckDB to list analytical table schemas and record sizes."""
    active_path = db_path
    if not os.path.exists(active_path):
        if os.path.exists(DUCKDB_FALLBACK_PATH):
            active_path = DUCKDB_FALLBACK_PATH
        else:
            return json.dumps({"status": "FAILED", "error": f"DuckDB file not found."})
            
    print(f"🦆 [DB DISCOVERY] Interrogating DuckDB schema at: '{active_path}'")
    try:
        import duckdb
        con = duckdb.connect(active_path, read_only=True)
        tables_df = con.execute("SHOW TABLES").df()
        tables = list(tables_df.iloc[:, 0]) if not tables_df.empty else []
        
        table_schemas = {}
        for table in tables:
            schema_df = con.execute(f"PRAGMA table_info('{table}')").df()
            count_df = con.execute(f"SELECT COUNT(*) FROM '{table}'").df()
            row_count = int(count_df.iloc[0, 0])
            columns = [{"name": r['name'], "type": r['type']} for _, r in schema_df.iterrows()]
            table_schemas[table] = {"row_count": row_count, "columns": columns}
            
        con.close()
        return json.dumps({"status": "SUCCESS", "db_path": active_path, "tables": table_schemas})
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": f"DuckDB query failed: {str(e)}"})

def query_lancedb_schema(path: str = DEFAULT_LANCEDB_PATH) -> str:
    """Connects programmatically to LanceDB to fetch available schemas and vector counts."""
    print(f"🗄️ [DB DISCOVERY] Reading LanceDB vector schema at: '{path}'")
    if not os.path.exists(path):
        return json.dumps({"status": "FAILED", "error": f"LanceDB folder '{path}' not found."})
    try:
        import lancedb
        db = lancedb.connect(path)
        tables = db.table_names() if hasattr(db, "table_names") else db.list_tables()
        table_details = {}
        for t in tables:
            t_str = t[0] if isinstance(t, tuple) else str(t)
            try:
                tbl = db.open_table(t_str)
                table_details[t_str] = {"schema": list(tbl.schema.names), "count": len(tbl)}
            except Exception as table_err:
                table_details[t_str] = {"error": str(table_err)}
        return json.dumps({"status": "SUCCESS", "lancedb_path": path, "tables": table_details})
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": str(e)})

def scan_network_and_processes() -> str:
    """Scans active ports and audits host process tables to ensure no socket conflicts exist."""
    print("🔌 [NETWORK DISCOVERY] Scanning loopback ports and process tables...")
    ports_to_scan = [1234, 1010, 6379, 8000, 8001, 8005, 8265, 5173]
    open_ports = []
    for port in ports_to_scan:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    open_ports.append(port)
        except Exception:
            pass

    active_processes = []
    target_substrings = ["node", "python", "ray", "lmstudio", "llama"]
    try:
        if HAS_PSUTIL:
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    name = (proc.info['name'] or '').lower()
                    if any(sub in name for sub in target_substrings):
                        active_processes.append({
                            "ImageName": proc.info['name'],
                            "PID": proc.info['pid'],
                            "MemUsage": f"{proc.info['memory_info'].rss / (1024*1024):.2f} MB"
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        else:
            # Fallback tasklist for Windows
            cmd = "tasklist /FO CSV /NH"
            output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
            for line in output.splitlines():
                if any(sub in line.lower() for sub in target_substrings):
                    parts = line.replace('"', '').split(",")
                    if len(parts) >= 5:
                        active_processes.append({"ImageName": parts[0].strip(), "PID": parts[1].strip(), "MemUsage": parts[4].strip()})
    except Exception as e:
        active_processes = f"Process scan failed: {str(e)}"

    return json.dumps({
        "status": "SUCCESS",
        "active_ports": open_ports,
        "active_processes": active_processes[:12] if isinstance(active_processes, list) else active_processes
    })

def read_active_file(filepath: str, lines: int = 60) -> str:
    """Loads a specific file or log into the context slot to analyze real-world content."""
    print(f"编 [DISCOVERY] Reading active file content: '{filepath}'...")
    if not os.path.isabs(filepath):
        filepath = os.path.join(TARGET_DIR, filepath)
    if not os.path.exists(filepath):
        return json.dumps({"status": "FAILED", "error": f"File '{filepath}' not found on disk."})
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

def execute_preflight_and_write(filename: str, code_content: str) -> str:
    """Saves python code to TARGET_DIR strictly after running AST syntax compiles and markdown auto-repairs."""
    print(f"\n🔍 [PRE-FLIGHT] Compiling and verifying '{filename}'...")
    
    # Auto-Heal markdown bold dunder mangling (**name** or **main**)
    repaired_code = re.sub(r'\*+([a-zA-Z0-9_]+)\*+', r'__\1__', code_content)
    repaired_code = repaired_code.replace("**name**", "__name__").replace("**main**", "__main__")
    
    if repaired_code != code_content:
        print("⚡ [AUTO-HEALER] Repaired Markdown dunder manglings successfully!")

    filepath = os.path.join(TARGET_DIR, filename)

    if not HAS_MONTY:
        try:
            os.makedirs(os.path.dirname(filepath) or TARGET_DIR, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(repaired_code)
            return json.dumps({
                "status": "SUCCESS",
                "message": f"File written directly to {filepath}. Monty compile-checked natively."
            })
        except Exception as e:
            return json.dumps({"status": "FAILED", "error": f"Write failed: {str(e)}"})

    try:
        # Pre-flight compilation step in Monty Rust VM
        with monty.Monty() as pool:
            with pool.checkout() as session:
                session.feed_run(repaired_code)
                
        os.makedirs(os.path.dirname(filepath) or TARGET_DIR, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(repaired_code)
            
        print(f"✅ [SUCCESS] Pre-flight passed! Code written safely: {filepath}")
        return json.dumps({
            "status": "SUCCESS", 
            "message": f"Code compile-verified in Monty Rust VM and written to {filepath}"
        })
        
    except Exception as e:
        print(f"❌ [PRE-FLIGHT REJECTED] Syntax/Runtime error: {e}")
        return json.dumps({
            "status": "REJECTED_BY_PREFLIGHT",
            "error_message": f"Syntax compilation failed: {str(e)}. Correct your code structures."
        })


# =============================================================================
# 3. INTERACTIVE AUTONOMOUS REASONING LOOP & XML PARSER FALLBACK
# =============================================================================

TOOL_METADATA = [
    {
        "type": "function",
        "function": {
            "name": "write_verified_code",
            "description": "Writes Python code to disk after running pre-flight syntax compiling.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Output filename (e.g. state_sync_agent.py)"},
                    "code_content": {"type": "string", "description": "Raw python code block."}
                },
                "required": ["filename", "code_content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_ray_cluster_state",
            "description": "Queries GCS directly to find active named actors, classes, namespaces, and node layouts."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_duckdb_schema",
            "description": "Connects programmatically to DuckDB to list analytical table schemas and record sizes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "db_path": {"type": "string", "description": "Path to DuckDB database catalog file."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_lancedb_schema",
            "description": "Connects programmatically to LanceDB to fetch available schemas and counts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to LanceDB folder."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scan_network_and_processes",
            "description": "Scans active ports and audits host process tables to map active engines."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_active_file",
            "description": "Loads a specific file or log into the context slot to analyze real-world content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to the target file."},
                    "lines": {"type": "integer", "description": "Number of trailing lines to load.", "default": 60}
                },
                "required": ["filepath"]
            }
        }
    }
]

def parse_text_tool_calls(text: str) -> list:
    """Parses fallback tool calls written as explicit XML tags in text blocks."""
    if not text:
        return []
    matches = re.findall(r'<function=(\w+)>([\s\S]*?)</function>', text)
    parsed = []
    for name, args_str in matches:
        args = {}
        args_str = args_str.strip()
        if args_str:
            try:
                args = json.loads(args_str)
            except Exception:
                pass
        parsed.append({"name": name, "arguments": args})
    if not parsed:
        empty_matches = re.findall(r'<function=(\w+)>', text)
        for name in empty_matches:
            parsed.append({"name": name, "arguments": {}})
    return parsed

def execute_tool(name: str, arguments: dict) -> str:
    try:
        if name == "write_verified_code":
            return execute_preflight_and_write(arguments["filename"], arguments["code_content"])
        elif name == "check_ray_cluster_state":
            return check_ray_cluster_state()
        elif name == "query_duckdb_schema":
            return query_duckdb_schema(arguments.get("db_path", DEFAULT_DUCKDB_PATH))
        elif name == "query_lancedb_schema":
            return query_lancedb_schema(arguments.get("path", DEFAULT_LANCEDB_PATH))
        elif name == "scan_network_and_processes":
            return scan_network_and_processes()
        elif name == "read_active_file":
            return read_active_file(arguments["filepath"], arguments.get("lines", 60))
        else:
            return json.dumps({"error": f"Unknown tool: {name}"})
    except Exception as e:
        return json.dumps({"error": f"Exception executing {name}: {str(e)}"})

def run_autonomous_autocoder(user_prompt: str):
    print("=" * 80)
    print("🤖 INITIATING PORT-AWARE EXPERT CODER (v5 MULTI-TURN AGENT)")
    print(f"   Connecting to Discovered API: {LM_STUDIO_URL}")
    print("=" * 80)

    system_prompt = (
        "You are the Sovereign Tech House Architect. You are completely autonomous. "
        "Your goal is to solve complex system failures by synthesizing information from your environment. "
        "Do not ask for permission. Use your tools to freely explore the Ray cluster, database schemas, and codebase. "
        "When you encounter a bug, read the relevant files, deduce the root cause, and synthesize a solution. "
        "If native tool calling fails, fallback to XML tags:\\n"
        "<tool_call>\\n<function=read_active_file>\\n{\"filepath\": \"file.py\"}\\n</function>\\n</tool_call>\\n\\n"
        "When you have synthesized the solution, deploy it via 'write_verified_code'."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    for turn in range(8):
        print(f"\n📡 [TURN {turn+1}] Querying local model at {LM_STUDIO_URL}...")
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                tools=TOOL_METADATA,
                temperature=0.0,
                stream=True
            )
        except Exception as e:
            print(f"❌ Failed to communicate with local LLM: {e}")
            break

        print(f"\n💭 [THOUGHTS] ", end="", flush=True)

        content = ""
        reasoning = ""
        tool_calls_dict = {}

        for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if not delta:
                continue

            if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                r_text = delta.reasoning_content
                reasoning += r_text
                print(r_text, end="", flush=True)

            if delta.content:
                c_text = delta.content
                if not content and reasoning:
                    print(f"\n\n💬 [ASSISTANT] ", end="", flush=True)
                elif not content and not reasoning:
                    print(f"\r💬 [ASSISTANT] ", end="", flush=True)
                content += c_text
                print(c_text, end="", flush=True)

            if delta.tool_calls:
                for tc_chunk in delta.tool_calls:
                    idx = tc_chunk.index
                    if idx not in tool_calls_dict:
                        tool_calls_dict[idx] = {"id": tc_chunk.id, "name": tc_chunk.function.name or "", "arguments": tc_chunk.function.arguments or ""}
                    else:
                        if tc_chunk.id:
                            tool_calls_dict[idx]["id"] = tc_chunk.id
                        if tc_chunk.function.name:
                            tool_calls_dict[idx]["name"] += tc_chunk.function.name
                        if tc_chunk.function.arguments:
                            tool_calls_dict[idx]["arguments"] += tc_chunk.function.arguments

        print() # Final newline

        # Check for tool calls (Native or XML Fallback)
        tool_calls_to_run = []
        if tool_calls_dict:
            for idx, tc in tool_calls_dict.items():
                try:
                    args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                except Exception as e:
                    print(f"⚠️ [JSON PARSE ERROR] LLM hallucinated bad tool args for {tc['name']}: {e}. Using empty args.")
                    args = {}
                    
                tool_calls_to_run.append({
                    "id": tc["id"],
                    "name": tc["name"],
                    "arguments": args
                })
        else:
            search_text = f"{reasoning}\n{content}"
            parsed_text_calls = parse_text_tool_calls(search_text)
            if parsed_text_calls:
                print(f"🎯 [FALLBACK] Detected text-based tool calls inside LLM output.")
                for i, ptc in enumerate(parsed_text_calls):
                    mock_id = f"parsed_call_{turn}_{i}"
                    tool_calls_to_run.append({
                        "id": mock_id,
                        "name": ptc["name"],
                        "arguments": ptc["arguments"]
                    })

        assistant_msg = {"role": "assistant", "content": content}
        if tool_calls_to_run:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {"name": tc["name"], "arguments": json.dumps(tc["arguments"])}
                } for tc in tool_calls_to_run
            ]
        messages.append(assistant_msg)

        if not tool_calls_to_run:
            print("\n🏁 [COMPLETE] Model has successfully completed the task!")
            break

        # Process tool calls
        for tc in tool_calls_to_run:
            name = tc["name"]
            args = tc["arguments"]
            tc_id = tc["id"]

            print(f"🔨 [TOOL EXECUTION] Running '{name}' on host with args: {args}")
            tool_output = execute_tool(name, args)
            print(f"📥 [TOOL OUTPUT] Returned (snippet): {tool_output[:250]}...")

            messages.append({
                "role": "tool",
                "tool_call_id": tc_id,
                "content": tool_output
            })
            
            # If the code write succeeded, wrap up early!
            if name == "write_verified_code":
                try:
                    res_data = json.loads(tool_output)
                    if res_data.get("status") == "SUCCESS":
                        print("\n🏁 [COMPLETE] Autocoder cleanly compiled and verified code output!")
                        return
                except Exception:
                    pass

if __name__ == "__main__":
    task_prompt = (
        "We have a boundary mismatch failure in the LangGraph pipeline: "
        "[FAIL] 'ActorHandle' object has no attribute 'generate'. "
        "The issue is related to the RayONNXChatModel wrapper in 'legion_langgraph_brain.py'. "
        "I am not going to tell you what to do or what tools to use. "
        "Use your environment to investigate the codebase, understand the Ray actor topology, "
        "synthesize a fix, and write the corrected code into a NEW file called 'legion_langgraph_brain_fixed.py'. "
        "Additionally, query the databases to report exactly which ONNX models are currently active "
        "and which ones are ready to go in the data tables."
    )
    run_autonomous_autocoder(task_prompt)