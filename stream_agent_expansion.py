import json
import time
import sys
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

LLM_MODEL = "nvidia/nemotron-3-nano-4b"

print("=" * 80)
print("🛠️ EXECUTING CAPACITY PLANNING AGENT LOOP WITH NEMOTRON-3-NANO (STREAMING)")
print("=" * 80)

# 1. TOOL SCHEMAS
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_active_runners",
            "description": "Returns a list of currently active runners/workers in the Ray cluster and their memory usage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "namespace": {"type": "string", "description": "The cluster namespace (e.g. 'legion')"}
                },
                "required": ["namespace"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_cluster_capacity",
            "description": "Returns the current hardware capacity and utilization metrics for the Ray cluster.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

# 2. LOCAL SIMULATED FUNCTIONS (Represents your Ray Cluster state)
def get_active_runners(namespace="legion"):
    return json.dumps({
        "namespace": namespace,
        "runners": [
            {"type": "PaniniRagEngine", "status": "WORKING", "memory_usage_gb": 4.5, "compute_type": "CPU/RAM"},
            {"type": "SnowflakeArcticEmbed_L_v2", "status": "WORKING", "memory_usage_gb": 6.2, "compute_type": "GPU/VRAM"},
            {"type": "SovereignSieve", "status": "WORKING", "memory_usage_gb": 2.1, "compute_type": "CPU/RAM"},
            {"type": "ACPControlPlane", "status": "WORKING", "memory_usage_gb": 1.0, "compute_type": "CPU/RAM"}
        ],
        "total_runner_memory_gb": 13.8
    })

def get_cluster_capacity():
    return json.dumps({
        "total_memory_gb": 15.0,
        "used_memory_gb": 14.2,
        "available_memory_gb": 0.8,
        "status": "CRITICAL_WARNING_MAXED_OUT",
        "bottleneck": "Memory (RAM/VRAM)",
        "ray_system_overhead_gb": 0.4
    })

# 3. INITIAL MESSAGES
messages = [
    {
        "role": "user",
        "content": "Check what runners are currently working in the 'legion' cluster and analyze our cluster capacity using Ray data. Our cluster is maxed out at 15GB and we need to make it bigger. Give us a detailed hardware expansion plan based on the current runner workloads."
    }
]

print("\n📡 Step 1: Sending prompt and tool definitions to Nemotron...")
start_time = time.time()

# TURN 1: Model issues the tool call (Streaming)
response = client.chat.completions.create(
    model=LLM_MODEL,
    messages=messages,
    tools=tools_schema,
    tool_choice="auto",
    temperature=0.2,
    stream=True
)

print("\n🤖 Thinking & Generating Tool Calls: ", end="", flush=True)

tool_calls = []
content = ""

for chunk in response:
    delta = chunk.choices[0].delta
    
    # Stream content if any
    if delta.content:
        print(delta.content, end="", flush=True)
        content += delta.content
        
    # Accumulate tool calls
    if delta.tool_calls:
        for tc_chunk in delta.tool_calls:
            while len(tool_calls) <= tc_chunk.index:
                tool_calls.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
            
            tc = tool_calls[tc_chunk.index]
            if tc_chunk.id:
                tc["id"] += tc_chunk.id
            if tc_chunk.function.name:
                tc["function"]["name"] += tc_chunk.function.name
            if tc_chunk.function.arguments:
                tc["function"]["arguments"] += tc_chunk.function.arguments

# Reconstruct message to append to history
assistant_message = {"role": "assistant"}
if content:
    assistant_message["content"] = content
if tool_calls:
    assistant_message["tool_calls"] = tool_calls
    if "content" not in assistant_message:
        assistant_message["content"] = None
        
messages.append(assistant_message)

if tool_calls:
    print("\n")
    for tool_call in tool_calls:
        fn_name = tool_call["function"]["name"]
        fn_args_str = tool_call["function"]["arguments"]
        
        try:
            fn_args = json.loads(fn_args_str) if fn_args_str else {}
        except json.JSONDecodeError:
            fn_args = fn_args_str
            
        print(f"\n🎯 [TOOL CALL DETECTED]: {fn_name}({fn_args})")
        
        # Step 2: Execute local code based on tool call
        tool_result = ""
        if fn_name == "get_active_runners":
            tool_result = get_active_runners(**(fn_args if isinstance(fn_args, dict) else {}))
            print(f"⚡ [EXECUTED LOCAL TOOL]: Retrieved Active Runners.")
        elif fn_name == "get_cluster_capacity":
            tool_result = get_cluster_capacity()
            print(f"⚡ [EXECUTED LOCAL TOOL]: Retrieved Cluster Capacity.")
            
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": tool_result
        })

    # TURN 2: Send tool output back to Nemotron for final reasoning
    print("\n📡 Step 2: Returning cluster telemetry back to Nemotron for capacity planning...\n")
    
    second_response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.3,
        stream=True
    )
    
    print("🤖 Expansion Plan Analysis: \n")
    for chunk in second_response:
        delta = chunk.choices[0].delta
        if delta.content:
            print(delta.content, end="", flush=True)
            
    print()

latency = (time.time() - start_time) * 1000
print(f"\n✅ FULL PROCESS COMPLETED ({latency:.2f} ms total)")

print("\n" + "=" * 80)
print("🏁 CAPACITY PLANNING AGENT LOOP COMPLETE")
print("=" * 80)
