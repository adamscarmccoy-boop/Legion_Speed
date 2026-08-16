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
# 1. INITIALIZE RAY & OPENAI CLIENT
# -------------------------------------------------------------------
# Connect to running Ray cluster on 127.0.0.1:6379
if not ray.is_initialized():
    ray.init(address="auto", namespace="legion", ignore_reinit_error=True)

# Connect to LM Studio local server
client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

LLM_MODEL = "nvidia/nemotron-3-nano-4b"

print("=" * 80)
print("🤖 SCARS_LAB AUTONOMOUS TRIAGE & RECOVERY AGENT (NEMOTRON-3-NANO)")
print("=" * 80)

# -------------------------------------------------------------------
# 2. LOCAL RAY CLUSTER TOOL IMPLEMENTATIONS
# -------------------------------------------------------------------

def get_cluster_health_telemetry():
    """Fetches actor states from ACPControlPlane / Ray Runtime."""
    # Simulated cluster state reflecting an active issue in SovereignSieve actor
    return json.dumps({
        "timestamp": time.time(),
        "cluster_name": "SCARS_LAB",
        "active_nodes": 1,
        "plasma_memory_used_mb": 4120,
        "plasma_memory_total_mb": 8192,
        "actors": [
            {
                "actor_id": "actor_panini_01",
                "name": "PaniniRagEngine",
                "status": "HEALTHY",
                "cpu_utilization": 12.4,
                "memory_mb": 512,
                "queue_backlog": 0
            },
            {
                "actor_id": "actor_sieve_04",
                "name": "SovereignSieve_Shard_04",
                "status": "DEGRADED",
                "cpu_utilization": 99.8,
                "memory_mb": 3410,
                "queue_backlog": 14200,
                "last_error": "PlasmaBufferFull: Zero-copy buffer overflow on shard partition 4."
            },
            {
                "actor_id": "actor_acp_01",
                "name": "ACPControlPlane",
                "status": "HEALTHY",
                "cpu_utilization": 3.1,
                "memory_mb": 256,
                "queue_backlog": 0
            }
        ]
    })


def restart_ray_actor(actor_id: str, force: bool = True):
    """Restarts a specific Ray actor by ID or Name."""
    print(f"\n⚙️ [EXECUTING RAY RECOVERY]: Restarting actor '{actor_id}' (force={force})...")
    # Real Ray lifecycle call logic:
    # actor_handle = ray.get_actor(actor_id)
    # ray.kill(actor_handle, force=force)
    time.sleep(1)
    return json.dumps({
        "status": "SUCCESS",
        "action": "RESTART_ACTOR",
        "actor_id": actor_id,
        "new_actor_status": "INITIALIZING",
        "message": f"Actor {actor_id} successfully terminated and scheduled for restart."
    })


def purge_plasma_object_store(partition_id: str):
    """Flushes stale or unreferenced PyArrow tables in Plasma RAM."""
    print(f"\n⚙️ [EXECUTING RAY RECOVERY]: Purging stale Plasma RAM objects on partition '{partition_id}'...")
    time.sleep(1)
    return json.dumps({
        "status": "SUCCESS",
        "action": "PURGE_PLASMA_RAM",
        "partition": partition_id,
        "freed_memory_mb": 2048,
        "message": f"Plasma object store partition '{partition_id}' cleared successfully."
    })

# Mapping tool names to executable python functions
TOOL_MAP = {
    "get_cluster_health_telemetry": get_cluster_health_telemetry,
    "restart_ray_actor": restart_ray_actor,
    "purge_plasma_object_store": purge_plasma_object_store
}

# -------------------------------------------------------------------
# 3. DEFINE NATIVE JSON TOOL SCHEMAS FOR NEMOTRON
# -------------------------------------------------------------------
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_cluster_health_telemetry",
            "description": "Retrieves real-time telemetry, actor health statuses, and memory usage across the Ray cluster.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "restart_ray_actor",
            "description": "Terminates and restarts a hung or degraded Ray actor by its actor_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "actor_id": {"type": "string", "description": "The target actor ID/name (e.g., 'actor_sieve_04')"},
                    "force": {"type": "boolean", "description": "Whether to force kill (SIGKILL) immediately."}
                },
                "required": ["actor_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "purge_plasma_object_store",
            "description": "Flushes unreferenced PyArrow shared-memory tables from Plasma object store to free memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "partition_id": {"type": "string", "description": "Partition identifier or 'all'"}
                },
                "required": ["partition_id"]
            }
        }
    }
]

# -------------------------------------------------------------------
# 4. AGENTIC REASONING & EXECUTION LOOP
# -------------------------------------------------------------------
system_instruction = (
    "You are the Autonomous Cluster Reliability Engineer for SCARS_LAB.\n"
    "Your objective:\n"
    "1. Inspect cluster telemetry using available tools.\n"
    "2. Diagnose any DEGRADED, HUNG, or ERRORED Ray actors.\n"
    "3. Execute targeted recovery tool calls (purge memory buffers, restart actors) to restore cluster health.\n"
    "4. Summarize the incident, root cause, and recovery steps taken."
)

messages = [
    {"role": "system", "content": system_instruction},
    {"role": "user", "content": "Run a diagnostic check on the SCARS_LAB cluster, identify any failures, and execute immediate remediation."}
]

max_turns = 5
turn_count = 0

while turn_count < max_turns:
    turn_count += 1
    print(f"\n📡 [AGENT LOOP - STEP {turn_count}] Querying Nemotron-3-Nano...")
    start_time = time.time()
    
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        tools=tools_schema,
        tool_choice="auto",
        temperature=0.1
    )
    
    latency = (time.time() - start_time) * 1000
    msg = response.choices[0].message
    messages.append(msg)
    
    # Check if Nemotron wants to call a tool
    if msg.tool_calls:
        print(f"✅ Tool call(s) requested in {latency:.2f} ms:")
        for tool_call in msg.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
            
            print(f"  • Tool: {fn_name}")
            print(f"  • Args: {json.dumps(fn_args)}")
            
            # Execute the tool
            if fn_name in TOOL_MAP:
                result_str = TOOL_MAP[fn_name](**fn_args) if fn_args else TOOL_MAP[fn_name]()
                
                # Feed tool execution output back to Nemotron
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_str
                })
            else:
                print(f"❌ Unknown tool: {fn_name}")
    else:
        # No tool call; Nemotron has finished reasoning and provided the final response
        print(f"\n✅ Diagnostic & Remediation Complete ({latency:.2f} ms)\n")
        print("-" * 80)
        print("🧠 [NEMOTRON INCIDENT REPORT & RESOLUTION SUMMARY]")
        print("-" * 80)
        print(msg.content)
        break

print("\n" + "=" * 80)
print("🏁 SCARS_LAB AUTONOMOUS TRIAGE AGENT EXECUTION COMPLETE")
print("=" * 80)