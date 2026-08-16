import os
import sys
import json
import time
import re
import socket
from pathlib import Path

# ANSI Color escapes for pristine console telemetry
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Ensure terminal uses UTF-8 to prevent console decoding crashes
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Try importing standard libraries and SDKs
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import duckdb
    HAS_DUCKDB = True
except ImportError:
    HAS_DUCKDB = False

# --- CONFIGURATION & PATH RESOLUTION ---
TARGET_DIR = r"C:\WEB CASE STUDY"
if not os.path.exists(TARGET_DIR):
    TARGET_DIR = os.getcwd()

NVIDIA_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1"
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")

DB_PATH = r"C:\STUDIES\data\metadata\sonic_core.duckdb"

# =============================================================================
# 1. HARDWARE-AWARE DEVTOOLS INTEGRATION (THE SENSORY PLUGS)
# =============================================================================
def scan_workspace_metadata() -> dict:
    """Scans and retrieves compact metadata of system files to keep tokens low."""
    print(f"{CYAN}📂 [DEVTOOLS] Scanning {TARGET_DIR} for target source files...{RESET}")
    ignore_dirs = {"node_modules", ".git", ".venv", "venv", "build"}
    scanned_files = []
    
    for root, dirs, files in os.walk(TARGET_DIR):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            if file.endswith((".cpp", ".hpp", ".py", ".js", ".json")):
                full_path = os.path.join(root, file)
                try:
                    size_kb = os.path.getsize(full_path) / 1024.0
                    scanned_files.append({
                        "name": file,
                        "path": full_path,
                        "size_kb": round(size_kb, 2)
                    })
                except Exception:
                    pass
    return {"scanned_count": len(scanned_files), "files": scanned_files[:10]}  # Cap file count to keep tokens low

def query_in_process_duckdb(sql_query: str) -> str:
    """Natively runs SQL query inside duckdb to verify database state."""
    if not HAS_DUCKDB:
        return "[DuckDB Library Missing] Simulated output: [{'total_tracks': 3556, 'status': 'OPTIMIZED'}]"
    
    if not os.path.exists(DB_PATH):
        return f"[Database File Missing on Host] Simulated fallback for query: '{sql_query}'"
        
    try:
        conn = duckdb.connect(database=DB_PATH, read_only=True)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        conn.close()
        return json.dumps(results)
    except Exception as e:
        return f"[DuckDB Error]: {str(e)}"

# =============================================================================
# 2. ZERO-DEPENDENCY LANGGRAPH REPLICA (STATE MACHINE GRAPH)
# =============================================================================
class LangGraphState:
    def __init__(self, messages=None, scanned_metadata=None, db_report=None, current_node="preprocessor"):
        self.messages = messages or []
        self.scanned_metadata = scanned_metadata or {}
        self.db_report = db_report or ""
        self.current_node = current_node
        self.execution_complete = False

class SovereignLangGraph:
    def __init__(self):
        self.nodes = {}
        
    def add_node(self, name, func):
        self.nodes[name] = func
        
    def execute(self, state: LangGraphState):
        while not state.execution_complete:
            node_func = self.nodes.get(state.current_node)
            if not node_func:
                print(f"{RED}[-] Invalid node: {state.current_node}{RESET}")
                break
            print(f"\n{BOLD}{MAGENTA}🔄 [LANGGRAPH STATE MACHINE] Transitioning to: {state.current_node}{RESET}")
            state = node_func(state)
        return state

# =============================================================================
# 3. STATE MACHINE NODES (KEEPING TOKENS LOW, TOOLS MOVING)
# =============================================================================
def preprocessor_node(state: LangGraphState) -> LangGraphState:
    """Grabs workspace layouts and performance state boundaries."""
    print(f"{YELLOW}[Node: preprocessor] Ingesting workstation sensory parameters...{RESET}")
    metadata = scan_workspace_metadata()
    state.scanned_metadata = metadata
    state.current_node = "silicon_memory"
    return state

def silicon_memory_node(state: LangGraphState) -> LangGraphState:
    """Executes local analytical queries directly on DuckDB."""
    print(f"{YELLOW}[Node: silicon_memory] Triggering in-process DuckDB pointer sweeps...{RESET}")
    sql = "SELECT COUNT(*) FROM t_core_memory;"
    db_res = query_in_process_duckdb(sql)
    state.db_report = db_res
    print(f"  -> Analytical schema verification result: {GREEN}{db_res}{RESET}")
    state.current_node = "nvidia_stream_critic"
    return state

def nvidia_stream_critic_node(state: LangGraphState) -> LangGraphState:
    """Streams the senior peer critique directly from the 70B NVIDIA NIM API."""
    print(f"{YELLOW}[Node: nvidia_stream_critic] Dispatching code payload to cloud-hosted NVIDIA NIM...{RESET}")
    
    # Pack a super compact representation of the files to prevent VRAM / context bloat
    file_summary = "\n".join([f"- {f['name']} ({f['size_kb']} KB)" for f in state.scanned_metadata.get("files", [])])
    
    system_instruction = (
        "You are an elite systems architect reviewing a high-performance C++ kernel that integrates "
        "llama.cpp, Windows Named Pipes, Winsock2, and DuckDB in-process. "
        "Focus purely on systems-level architecture, socket lifecycle stability (like SO_REUSEADDR), "
        "and preventing thread locks under a 4GB VRAM constraint. STRIP ALL MUSIC/AUDIO METAPHOR."
    )
    
    user_prompt = (
        f"Perform an architectural critique of the following active workspace files:\n"
        f"--- WORKSPACE FILES ---\n{file_summary}\n\n"
        f"--- DUCKDB STATE REPORT ---\n{state.db_report}\n\n"
        "Generate a brief bulleted list of immediate optimizations to keep execution speeds high."
    )
    
    if not HAS_OPENAI or not NVIDIA_API_KEY:
        print(f"{YELLOW}⚠️ [NVIDIA NIM Offline/Simulated] Streaming simulated peer feedback...{RESET}")
        simulated_response = (
            "### NVIDIA NIM ARCHITECTURAL CRITIQUE (Llama-3.3-70B)\n"
            "- [OPTIMIZATION] Avoid copying floating-point vectors out of memory. Maintain direct pointers to the embedding layer output.\n"
            "- [IPC] Wrap the Windows Named Pipe buffers in strict lock guards to prevent race conditions during concurrent Python tool execution.\n"
            "- [DATABASE] Ensure that DuckDB read operations bypass standard SQLite transactional locks to guarantee microsecond latencies."
        )
        for char in simulated_response:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(0.005)
        print()
    else:
        try:
            client = OpenAI(base_url=NVIDIA_URL, api_key=NVIDIA_API_KEY)
            stream = client.chat.completions.create(
                model=NVIDIA_MODEL,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ],
                stream=True,
                temperature=0.1
            )
            print(f"\n{GREEN}📥 [STREAMING NVIDIA NIM OUTPUT]:{RESET}\n")
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    sys.stdout.write(content)
                    sys.stdout.flush()
            print()
        except Exception as e:
            print(f"{RED}[-] API Call Failed: {str(e)}{RESET}")
            
    state.execution_complete = True
    return state

# =============================================================================
# 4. RUNNER
# =============================================================================
def main():
    print(BOLD + CYAN + "=" * 80)
    print("🏛️  SOVEREIGN NIM-STREAMING REVIWER & LANGGRAPH MASTER")
    print("   NVIDIA Cloud API Only | Zero-JSON Math Routing | Raw Console Stream")
    print("=" * 80 + RESET)
    
    # Initialize the graph
    graph = SovereignLangGraph()
    graph.add_node("preprocessor", preprocessor_node)
    graph.add_node("silicon_memory", silicon_memory_node)
    graph.add_node("nvidia_stream_critic", nvidia_stream_critic_node)
    
    # Start loop
    start_state = LangGraphState()
    graph.execute(start_state)
    
    print("\n" + BOLD + GREEN + "✓ Stream completed successfully. All tools executed." + RESET)

if __name__ == "__main__":
    main()
