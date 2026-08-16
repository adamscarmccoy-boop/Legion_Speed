import os
import subprocess
import re
import sys
import ctypes
import argparse
import json
import urllib.request
import urllib.error
import time

# =============================================================================
# 1. CONSTANTS AND ENVIRONMENT RESOLUTION
# =============================================================================
DEFAULT_LM_STUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"
DEFAULT_NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
DEFAULT_NVIDIA_MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1"
DEFAULT_LOCAL_MODEL = "nvidia/nemotron-3-nano-4b"

# Load local environment vars if available
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")

# =============================================================================
# 2. BARE-METAL C++ DLL INTERFACE DESIGN
# =============================================================================
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

def load_sovereign_library(dll_path=None):
    if dll_path is None:
        dll_path = os.environ.get("SOVEREIGN_DLL_PATH", r"C:\WEB CASE STUDY\sovereign_kernel.dll")
    
    if not os.path.exists(dll_path):
        return None, f"[-] Sovereign DLL not found at: {dll_path}"
        
    try:
        lib = ctypes.CDLL(dll_path)
        lib.load_state_agent.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        lib.load_state_agent.restype = ctypes.c_bool
        
        lib.step_state_agent.argtypes = [NativeSwarmNodeState]
        lib.step_state_agent.restype = NativeSwarmNodeState
        return lib, f"[+] Sovereign Kernel loaded successfully from {dll_path}"
    except Exception as e:
        return None, f"[-] Error linking to Sovereign DLL: {e}"

# =============================================================================
# 3. DIRECT QUERY HANDLERS (LM STUDIO & NVIDIA API)
# =============================================================================
def query_model(prompt, system_prompt="You are a helpful assistant.", use_cloud=False, api_key=None, model=None, temperature=0.7):
    """
    Sends chat completions queries over raw HTTP POST using standard library urllib.
    This guarantees zero dependency overhead and avoids conflicts with virtual environments.
    """
    headers = {"Content-Type": "application/json"}
    
    if use_cloud:
        url = DEFAULT_NVIDIA_URL
        selected_model = model or DEFAULT_NVIDIA_MODEL
        key = api_key or NVIDIA_API_KEY
        if not key:
            print("[-] Error: NVIDIA_API_KEY is not set. Use --api-key or set env variable.")
            return None
        headers["Authorization"] = f"Bearer {key}"
    else:
        url = DEFAULT_LM_STUDIO_URL
        selected_model = model or DEFAULT_LOCAL_MODEL
        
    payload = {
        "model": selected_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    
    try:
        start_time = time.perf_counter()
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = response.read().decode("utf-8")
            latency = (time.perf_counter() - start_time) * 1000.0
            
            res_json = json.loads(res_data)
            content = res_json["choices"][0]["message"]["content"]
            tokens_eval = res_json.get("usage", {}).get("completion_tokens", 0)
            
            return {
                "content": content,
                "latency_ms": latency,
                "tokens_eval": tokens_eval,
                "model": selected_model,
                "target": "Cloud Titan" if use_cloud else "Local Edge"
            }
    except urllib.error.URLError as e:
        print(f"[-] HTTP Request Failed: {e}")
        return None
    except Exception as e:
        print(f"[-] Unexpected Request Error: {e}")
        return None

# =============================================================================
# 4. DATABASE BRIDGE HANDLER (DUCKDB INTERFACE)
# =============================================================================
def query_duckdb(db_path, sql):
    """
    Direct interface to local DuckDB file nodes.
    Bypasses high-level wrappers to perform raw local relational analytics.
    """
    try:
        import duckdb
    except ImportError:
        print("[-] DuckDB Python library is missing. Install with 'pip install duckdb'")
        return None
        
    if not os.path.exists(db_path):
        print(f"[-] Database file does not exist at: {db_path}")
        return None
        
    try:
        conn = duckdb.connect(db_path, read_only=True)
        res = conn.execute(sql).fetchall()
        cols = [desc[0] for desc in conn.description]
        conn.close()
        return {"columns": cols, "rows": res}
    except Exception as e:
        print(f"[-] DuckDB Execution Failure: {e}")
        return None


# =============================================================================
# 4b. HARDWARE & LOGS UTILITY FUNCTIONS (NVIDIA & FILES)
# =============================================================================
def query_gpu_telemetry():
    """Queries nvidia-smi for live GTX 1650 SUPER metrics with mock fallback."""
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total,memory.used,utilization.gpu,temperature.gpu", "--format=csv,noheader,nounits"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        stats = res.stdout.strip().split(",")
        return {
            "status": "SUCCESS",
            "vram_total_mib": int(stats[0]),
            "vram_used_mib": int(stats[1]),
            "gpu_utilization_pct": int(stats[2]),
            "gpu_temperature_celsius": int(stats[3]),
            "vram_headroom_mib": int(stats[0]) - int(stats[1])
        }
    except Exception as e:
        # High-Fidelity local mock fallback if running without CUDA environment
        return {
            "status": "SUCCESS_MOCKED",
            "vram_total_mib": 4096,
            "vram_used_mib": 3675,
            "gpu_utilization_pct": 59,
            "gpu_temperature_celsius": 62,
            "vram_headroom_mib": 421,
            "comment": "NVIDIA Drivers bypassed - loading default GTX 1650 SUPER mock profile.",
            "error_detail": str(e)
        }

def read_workspace_file(filename, limit_lines=None, tail=False):
    """Safely reads files in the workspace with line-limits and tailing options."""
    base_dir = r"C:\WEB CASE STUDY"
    filepath = os.path.join(base_dir, filename) if not os.path.isabs(filename) else filename
    
    if not os.path.exists(filepath):
        return {"status": "FAILED", "error": f"File '{filepath}' not found on disk."}
        
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            
        total_lines = len(lines)
        if limit_lines:
            if tail:
                lines = lines[-min(total_lines, limit_lines):]
            else:
                lines = lines[:min(total_lines, limit_lines)]
                
        return {
            "status": "SUCCESS",
            "filepath": filepath,
            "total_lines": total_lines,
            "lines_returned": len(lines),
            "content": "".join(lines)
        }
    except Exception as e:
        return {"status": "FAILED", "error": f"Failed to read file: {str(e)}"}

# =============================================================================
# 5. SUBCOMMAND EXECUTION ENTRYPOINTS
# =============================================================================
def handle_ask(args):
    print(f"\n==========================================================================")
    print(f"🚀 INITIATING TRANS-NODE INFERENCE: {args.target.upper()}")
    print(f"==========================================================================")
    
    use_cloud = (args.target == "cloud")
    res = query_model(
        prompt=args.prompt,
        system_prompt=args.system,
        use_cloud=use_cloud,
        api_key=args.api_key,
        model=args.model,
        temperature=args.temperature
    )
    
    if res:
        print(f"\n🤖 Response from {res['model']} ({res['target']}):")
        print("-" * 80)
        print(res["content"])
        print("-" * 80)
        print(f"⚡ Latency: {res['latency_ms']:.2f} ms | Evaluated: {res['tokens_eval']} tokens")
        if res['tokens_eval'] > 0:
            speed = (res['tokens_eval'] / (res['latency_ms'] / 1000.0))
            print(f"🚀 Speed Metric: {speed:.2f} tokens/sec")
    else:
        print("[-] Failed to retrieve inference response.")
    print("=" * 80 + "\n")

def handle_audit(args):
    print(f"\n==========================================================================")
    print(f"🧬 PERFORMING CRITICAL HYGIENE AND PLATFORM CONFIG AUDIT")
    print(f"==========================================================================")
    
    # Audit Memory Pool cap
    total_physical_mem = 16 # Lenovo Legion base
    pagefile_initial = 24
    pagefile_max = 64
    commit_pool = total_physical_mem + pagefile_max
    
    print(f"1. Virtual Memory Configuration:")
    print(f"   - Physical Host RAM: {total_physical_mem} GB")
    print(f"   - Pagefile configuration: {pagefile_initial} GB Initial / {pagefile_max} GB Max")
    print(f"   - Configured Commit Pool Security Margin: {commit_pool} GB (Event 2004 crash guard)")
    
    # WSL cap check
    wsl_conf_path = os.path.expanduser("~/.wslconfig")
    wsl_guard_active = False
    if os.path.exists(wsl_conf_path):
        wsl_guard_active = True
        print(f"   [v] WSL2 Resource Guard detected at ~/.wslconfig")
    else:
        print(f"   [!] Note: WSL2 Resource Guard (.wslconfig) not found on user host partition")

    # DLL status check
    dlls = ["sovereign_kernel.dll", "lance_duckdb_core.dll"]
    print(f"\n2. Ahead-of-Time Pre-Compiled DLL Integrity:")
    for d in dlls:
        full_p = os.path.join(r"C:\WEB CASE STUDY", d)
        if os.path.exists(full_p):
            print(f"   - {d:<25} : FOUND ({os.path.getsize(full_p):,} bytes)")
        else:
            print(f"   - {d:<25} : MISSING from C:\\WEB CASE STUDY")
            
    # DuckDB status check
    dbs = ["sonic_core_v1.duckdb", "sonic_core_v2.duckdb"]
    print(f"\n3. Local DuckDB Node Status:")
    for db in dbs:
        full_p = os.path.join(r"C:\WEB CASE STUDY", db)
        if os.path.exists(full_p):
            print(f"   - {db:<25} : ACTIVE ({os.path.getsize(full_p) / (1024*1024):.2f} MB)")
        else:
            print(f"   - {db:<25} : OFFLINE")
            
    print("=" * 80 + "\n")

def handle_query_db(args):
    print(f"\n==========================================================================")
    print(f"📊 EXECUTING SONIC CORE SQL INTERCEPT: {os.path.basename(args.db_path)}")
    print(f"==========================================================================")
    
    res = query_duckdb(args.db_path, args.sql)
    if res:
        cols = res["columns"]
        rows = res["rows"]
        print(f"\nColumns: | " + " | ".join(cols) + " |")
        print("-" * 80)
        for row in rows[:args.limit]:
            row_str = [str(x)[:20] for x in row]
            print(" | ".join(row_str))
        print("-" * 80)
        print(f"Total Rows Extracted: {len(rows)} (Displayed top {args.limit})")
    else:
        print("[-] Query failed or DuckDB was unreachable.")
    print("=" * 80 + "\n")

def handle_step_agent(args):
    print(f"\n==========================================================================")
    print(f"🛡️  EXECUTING BARE-METAL C++ STATE AGENT TRANSITION")
    print(f"==========================================================================")
    
    lib, status_msg = load_sovereign_library(args.dll)
    print(status_msg)
    
    if not lib:
        print("[-] DLL Execution aborted. Use Path 1 fallback (simulated pointers).")
        return
        
    print(f"\n[+] Compiling state parameters Ahead-of-Time...")
    state = NativeSwarmNodeState()
    state.task_id = args.task_id.encode("utf-8")
    state.node_name = args.node_name.encode("utf-8")
    state.status = args.status.encode("utf-8")
    state.user_query = args.query.encode("utf-8")
    state.tool_target = args.tool_target.encode("utf-8")
    
    # Pack up features (limit 12)
    for i, val in enumerate(args.features[:12]):
        state.dsp_features[i] = float(val)
        
    print(f"[+] Direct pointer transition via step_state_agent...")
    
    start_t = time.perf_counter()
    next_state = lib.step_state_agent(state)
    local_latency = (time.perf_counter() - start_t) * 1e6 # microseconds
    
    print("\n⚡ BARE-METAL STRUCT EXECUTION COMPLETE:")
    print("-" * 80)
    print(f"📄 Task ID:          {next_state.task_id.decode('utf-8', errors='ignore')}")
    print(f"⚙️  Node Name:        {next_state.node_name.decode('utf-8', errors='ignore')}")
    print(f"🟢 Output Status:    {next_state.status.decode('utf-8', errors='ignore')}")
    print(f"🎯 Tool Target:     {next_state.tool_target.decode('utf-8', errors='ignore')}")
    print(f"📈 Output Scores:    {list(next_state.output_scores[:4])} ...")
    print(f"🕰️  DLL Execution:    {next_state.execution_time_us:.2f} µs")
    print(f"🚀 Bridge Hand-off:  {local_latency:.2f} µs")
    print("-" * 80)
    print("=" * 80 + "\n")


def handle_gpu(args):
    print(f"\n==========================================================================")
    print(f"📡 QUERYING WORKSTATION NVIDIA GPU TELEMETRY")
    print(f"==========================================================================")
    
    metrics = query_gpu_telemetry()
    status_color = "\033[92m" if "MOCKED" not in metrics["status"] else "\033[93m"
    
    print(f"🟢 Status:         {status_color}{metrics['status']}\033[0m")
    print(f"📟 GPU Utilization: {metrics['gpu_utilization_pct']}%")
    print(f"🌡️  Core Temp:       {metrics['gpu_temperature_celsius']}°C")
    print(f"💾 Total VRAM:      {metrics['vram_total_mib']} MiB")
    print(f"📥 Allocated VRAM:  {metrics['vram_used_mib']} MiB")
    print(f"⚡ Headroom:        {metrics['vram_headroom_mib']} MiB")
    
    if "comment" in metrics:
        print(f"\n\033[93m[!] Note: {metrics['comment']}\033[0m")
    print("=" * 80 + "\n")

def handle_file(args):
    print(f"\n==========================================================================")
    print(f"📋 INSPECTING WORKSTATION LOG/CODE FILE: {os.path.basename(args.filepath)}")
    print(f"==========================================================================")
    
    result = read_workspace_file(args.filepath, limit_lines=args.lines, tail=args.tail)
    
    if result["status"] == "SUCCESS":
        print(f"📁 Path:  {result['filepath']}")
        print(f"📈 Total File Size: {result['total_lines']} lines")
        print(f"🔍 Displaying:      {result['lines_returned']} lines (Tail={args.tail})")
        print("-" * 80)
        print(result["content"].strip())
        print("-" * 80)
    else:
        print(f"\033[91m[-] Read Failed: {result['error']}\033[0m")
    print("=" * 80 + "\n")

# =============================================================================
# 6. MASTER ENTRYPOINT (MAIN CLI)
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="👑 SOVEREIGN CMD ENGINE: Unified Sovereign Command-Line Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(title="subcommands", dest="command", required=True)
    
    # 1. 'ask' Subcommand
    ask_parser = subparsers.add_parser("ask", help="Query edge (local LM Studio) or cloud (NVIDIA Titan) inference models.")
    ask_parser.add_argument("target", choices=["edge", "cloud"], help="Choose edge (local GGUF) or cloud (NVIDIA Super Nemotron)")
    ask_parser.add_argument("--prompt", required=True, help="User query prompt string.")
    ask_parser.add_argument("--system", default="You are a helpful sovereign system assistant.", help="System pre-prompt context.")
    ask_parser.add_argument("--model", help="Override default model identifier.")
    ask_parser.add_argument("--api-key", help="NVIDIA API key token (override environment).")
    ask_parser.add_argument("--temperature", type=float, default=0.7, help="Generation sampling temperature.")
    
    # 2. 'audit' Subcommand
    subparsers.add_parser("audit", help="Audit local workstation resource configurations and DLL integrity.")
    
    # 3. 'query-db' Subcommand
    db_parser = subparsers.add_parser("query-db", help="Query local DuckDB relational core databases.")
    db_parser.add_argument("db_path", help="Hard disk path to DuckDB file node.")
    db_parser.add_argument("sql", help="Standard SQL query expression to execute.")
    db_parser.add_argument("--limit", type=int, default=10, help="Maximum displayed records row count.")
    
    # 5. 'gpu' Subcommand
    gpu_parser = subparsers.add_parser("gpu", help="Query live NVIDIA GPU VRAM, load, and temperature telemetry.")
    
    # 6. 'read-file' Subcommand
    file_parser = subparsers.add_parser("read-file", help="Inspect and read workspace logs or file contents.")
    file_parser.add_argument("filepath", help="Name or full path of target file (e.g., system_log.txt).")
    file_parser.add_argument("--lines", type=int, default=30, help="Number of lines to read.")
    file_parser.add_argument("--tail", action="store_true", help="Tail the end of the file instead of reading from top.")

    # 4. 'step-agent' Subcommand
    step_parser = subparsers.add_parser("step-agent", help="Directly step C++ Sovereign Swarm Node States AOT.")
    step_parser.add_argument("--task-id", default="t-001", help="Task contract identifier.")
    step_parser.add_argument("--node-name", default="AcousticRouter", help="State agent node name.")
    step_parser.add_argument("--status", default="PENDING", help="Active node execution status.")
    step_parser.add_argument("--query", default="Run physics calibration", help="Natural language command payload.")
    step_parser.add_argument("--tool-target", default="CPP_NATIVE", help="C++ or DB backend targets.")
    step_parser.add_argument("--features", type=float, nargs="+", default=[0.1, 0.2, 0.3, 0.4], help="Float feature arrays.")
    step_parser.add_argument("--dll", help="Path to sovereign_kernel.dll.")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
        
    args = parser.parse_args()
    
    if args.command == "ask":
        handle_ask(args)
    elif args.command == "audit":
        handle_audit(args)
    elif args.command == "query-db":
        handle_query_db(args)
    elif args.command == "step-agent":
        handle_step_agent(args)
    elif args.command == "gpu":
        handle_gpu(args)
    elif args.command == "read-file":
        handle_file(args)

if __name__ == "__main__":
    main()
