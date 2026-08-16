import json
import time
import ray
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


# -------------------------------------------------------------------
# 1. CONNECT TO LOCAL RAY & LM STUDIO
# -------------------------------------------------------------------
if not ray.is_initialized():
    ray.init(address="auto", namespace="legion", ignore_reinit_error=True)

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

LLM_MODEL = "nvidia/nemotron-3-nano-4b"

print("=" * 80)
print("🔍 INSPECTING LIVE ACP CONTROL PLANE & DESIGNING ADAPTIVE PATCH")
print("=" * 80)

# -------------------------------------------------------------------
# 2. LOCAL TOOL TO INSPECT LIVE ACP CONTROL PLANE
# -------------------------------------------------------------------
def get_live_acp_state():
    """Queries the Ray actor registry for existing ACPControlPlane handles."""
    try:
        # Check for existing ACPControlPlane actor
        named_actors = ray.util.list_named_actors(all_namespaces=True)
        acp_actors = [a for a in named_actors if "ACP" in a["name"] or "ControlPlane" in a["name"]]
        
        return json.dumps({
            "status": "SUCCESS",
            "cluster_namespace": "legion",
            "existing_acp_actors": acp_actors,
            "active_nodes": len(ray.nodes()),
            "plasma_store_status": "ONLINE (PyArrow Zero-Copy)",
            "embedding_dim": 1024
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to list Ray actors: {str(e)}"})

TOOL_MAP = {
    "get_live_acp_state": get_live_acp_state
}

tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_live_acp_state",
            "description": "Inspects the active Ray cluster to locate existing ACPControlPlane actor handles and runtime state.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]

# -------------------------------------------------------------------
# 3. PROMPT NEMOTRON FOR DIRECT ARCHITECTURAL PATCH
# -------------------------------------------------------------------
prompt = """
1. Execute `get_live_acp_state` to inspect our active Ray cluster and locate the existing ACPControlPlane actor.
2. Based on the live cluster state, write a complete, drop-in Python extension script for `ACPControlPlane` that implements Step 1 (ACP Persistent Daemon) WITHOUT recreating or duplicating existing actors.
3. Show us how this patch prepares the cluster for Steps 2 through 10 of our 10-stage roadmap.
"""

messages = [{"role": "user", "content": prompt}]

print("\n📡 Step 1: Querying Nemotron to inspect live ACP state...")
start_time = time.time()

response = client.chat.completions.create(
    model=LLM_MODEL,
    messages=messages,
    tools=tools_schema,
    tool_choice="auto",
    temperature=0.2
)

msg = response.choices[0].message
messages.append(msg)

if msg.tool_calls:
    for tool_call in msg.tool_calls:
        fn_name = tool_call.function.name
        print(f"\n🎯 [TOOL CALL EXECUTED]: {fn_name}()")
        
        if fn_name in TOOL_MAP:
            result_str = TOOL_MAP[fn_name]()
            print(f"⚡ [RAY CLUSTER TELEMETRY]: {result_str}")
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_str
            })

    print("\n📡 Step 2: Requesting complete Python patch from Nemotron...")
    second_response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.2
    )
    
    latency = (time.time() - start_time) * 1000
    print(f"\n✅ CODE PATCH GENERATED ({latency:.2f} ms total)\n")
    print("-" * 80)
    print(second_response.choices[0].message.content)

print("\n" + "=" * 80)
print("🏁 INSPECTION & PATCH GENERATION COMPLETE")
print("=" * 80)