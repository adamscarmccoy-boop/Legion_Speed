import os
import sys
import json
import socket
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


# --- CONFIGURATION ---
LM_STUDIO_URL = "http://127.0.0.1:1234/v1"
LLM_MODEL = "nvidia/nemotron-3-nano-4b"
DEFAULT_LANCEDB_PATH = r"C:\STUDIES_BACKUP\vectors\lancedb_store"

# Initialize OpenAI client to hit local LM Studio C++ Engine
client = OpenAI(base_url=LM_STUDIO_URL, api_key="lm-studio")

# ==========================================
# 1. CORE SYSTEM DIAGNOSTIC TOOL DEFINITIONS
# ==========================================

def check_port(host: str, port: int) -> str:
    """Checks if a TCP port is open and listening. Useful for verifying gateway and Ray sockets."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.5)
            s.connect((host, port))
        return json.dumps({"port": port, "status": "ONLINE", "message": f"Successfully handshaked with {host}:{port}"})
    except Exception as e:
        return json.dumps({"port": port, "status": "OFFLINE", "error": str(e)})

def check_lancedb(path: str = DEFAULT_LANCEDB_PATH) -> str:
    """Connects to LanceDB on disk and checks for table schemas and lock files."""
    if not os.path.exists(path):
        return json.dumps({"status": "FAILED", "error": f"Path '{path}' does not exist on disk."})
    
    try:
        import lancedb
        db = lancedb.connect(path)
        tables = db.list_tables()
        table_details = {}
        for t in tables:
            tbl = db.open_table(t)
            table_details[t] = {
                "schema": list(tbl.schema.names),
                "count": len(tbl)
            }
        return json.dumps({"status": "SUCCESS", "tables": table_details})
    except ImportError:
        return json.dumps({"status": "WARNING", "message": "lancedb library is not installed in current environment."})
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": str(e)})

def check_ray_cluster() -> str:
    """Connects to the active local Ray GCS cluster to verify connection to raylets."""
    try:
        import ray
        if not ray.is_initialized():
            ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        nodes = ray.nodes()
        return json.dumps({
            "status": "SUCCESS",
            "cluster_namespace": "legion",
            "active_nodes_count": len(nodes),
            "nodes": [{"NodeID": n.get("NodeID"), "Alive": n.get("Alive")} for n in nodes]
        })
    except ImportError:
        return json.dumps({"status": "FAILED", "error": "Ray library is not installed."})
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": f"Failed to handshake with local Ray cluster: {str(e)}"})

def query_acp_actor() -> str:
    """Queries Ray GCS for the detached 'ACPControlPlane' actor handle to confirm registration."""
    try:
        import ray
        if not ray.is_initialized():
            ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
            
        try:
            acp_handle = ray.get_actor("ACPControlPlane", namespace="legion")
            # Pull dynamic remote methods
            exposed_methods = list(acp_handle._actor_method_names) if hasattr(acp_handle, "_actor_method_names") else []
            return json.dumps({
                "status": "FOUND",
                "actor_id": str(acp_handle._actor_id),
                "exposed_remote_methods": exposed_methods,
                "message": "ACPControlPlane is registered in GCS memory and ready for routing."
            })
        except ValueError:
            return json.dumps({
                "status": "NOT_FOUND",
                "error": "Actor 'ACPControlPlane' is missing from 'legion' namespace directory."
            })
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": str(e)})

def get_nvidia_smi() -> str:
    """Runs nvidia-smi in a subprocess to retrieve active VRAM consumption on GTX 1650 SUPER."""
    import subprocess
    try:
        res = subprocess.run(["nvidia-smi", "--query-gpu=memory.total,memory.used,utilization.gpu", "--format=csv,noheader,nounits"], 
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        stats = res.stdout.strip().split(",")
        return json.dumps({
            "status": "SUCCESS",
            "vram_total_mib": int(stats[0]),
            "vram_used_mib": int(stats[1]),
            "gpu_utilization_pct": int(stats[2])
        })
    except Exception as e:
        return json.dumps({
            "status": "FAILED", 
            "error": "nvidia-smi query failed. Make sure NVIDIA Drivers are installed and GPU is available."
        })

# ==========================================
# 2. TOOL EXECUTION ROUTING MAP
# ==========================================

TOOL_METADATA = [
    {
        "type": "function",
        "function": {
            "name": "check_port",
            "description": "Verifies if a local TCP port is open. Good for port 1234, 8001, 8005, 6379, 8265.",
            "parameters": {
                "type": "object",
                "properties": {
                    "host": {"type": "string", "default": "127.0.0.1"},
                    "port": {"type": "integer", "description": "The target TCP port number."}
                },
                "required": ["port"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_lancedb",
            "description": "Inspects local vector databases, schemas, and confirms tables are accessible.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to lancedb folder. Defaults to active studies backup."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_ray_cluster",
            "description": "Handshakes with the active local Raylet instance on port 6379 to confirm cluster topology."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_acp_actor",
            "description": "Queries GCS registry to lookup detached 'ACPControlPlane' actor handle and its available methods."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_nvidia_smi",
            "description": "Queries your GTX 1650 SUPER for exact live VRAM allocations and processing loads."
        }
    }
]

def dispatch_tool(name: str, arguments: dict) -> str:
    try:
        if name == "check_port":
            return check_port(arguments.get("host", "127.0.0.1"), arguments["port"])
        elif name == "check_lancedb":
            return check_lancedb(arguments.get("path", DEFAULT_LANCEDB_PATH))
        elif name == "check_ray_cluster":
            return check_ray_cluster()
        elif name == "query_acp_actor":
            return query_acp_actor()
        elif name == "get_nvidia_smi":
            return get_nvidia_smi()
        else:
            return json.dumps({"error": f"Tool '{name}' not found."})
    except Exception as e:
        return json.dumps({"error": f"Exception executing tool '{name}': {str(e)}"})

# ==========================================
# 3. AUTONOMOUS INTERFACE LOOP
# ==========================================

def execute_autonomous_diagnosis():
    print("=" * 80)
    print("💎 NEMOTRON-3-NANO SWARM DIAGNOSTIC AGENT INITIALIZED")
    print("  Interfacing with local LM Studio C++ Engine via Port 1234...")
    print("=" * 80)

    system_instructions = (
        "You are an autonomic diagnostic systems administrator. Your job is to analyze "
        "the local system health using your tools. Execute tool calls to check open ports "
        "and Ray cluster metadata, then summarize the network & database status "
        "clearly in Markdown. If any critical port (like 8005 or 6379) is offline, or "
        "if the ACPControlPlane actor is not found, state that in your final summary."
    )

    user_prompt = (
        "Please query your local NVIDIA GTX 1650 SUPER telemetry, check if port 8005 and "
        "6379 are active, confirm your LanceDB vector tables are open, and check if "
        "the ACPControlPlane actor is detached and registered inside the legion namespace. "
        "Then synthesize a full system health report based on the actual tool results."
    )

    messages = [
        {"role": "system", "content": system_instructions},
        {"role": "user", "content": user_prompt}
    ]

    for turn in range(5):
        print(f"\n📡 [TURN {turn+1}] Querying {LLM_MODEL}...")
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                tools=TOOL_METADATA,
                temperature=0.0
            )
        except Exception as e:
            print(f"❌ Failed to reach local LLM at {LM_STUDIO_URL}. Is LM Studio running?", file=sys.stderr)
            print("Traceback:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return

        choice = response.choices[0] if response.choices else None
        if not choice:
            print("❌ Empty response returned from LM Studio.", file=sys.stderr)
            break

        message = choice.message
        
        # Format assistant message for continuation
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
            print("\n🏁 [COMPLETE] System health diagnostics compiled successfully!")
            print("\n" + "="*50 + "\n" + message.content + "\n" + "="*50)
            break

        # Execute Tool Calls
        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
            
            print(f"🔨 [TOOL CALL] Assistant requested execution of '{name}' with args: {args}")
            tool_output = dispatch_tool(name, args)
            print(f"📥 [TOOL OUTPUT] Returned: {tool_output}")
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_output
            })

if __name__ == "__main__":
    execute_autonomous_diagnosis()