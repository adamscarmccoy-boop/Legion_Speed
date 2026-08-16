import json
import time
import sys
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

LLM_MODEL = "nvidia/nemotron-3-nano-4b"

print("=" * 75)
print("🛠️ EXECUTING FULL AGENTIC TOOL LOOP WITH NEMOTRON-3-NANO (STREAMING)")
print("=" * 75)

# 1. TOOL SCHEMAS
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "query_ray_cluster_status",
            "description": "Inspects active Ray actors, Plasma object memory, and ACPControlPlane state.",
            "parameters": {
                "type": "object",
                "properties": {
                    "namespace": {"type": "string", "description": "The cluster namespace (e.g. 'legion')"},
                    "include_actors": {"type": "boolean", "description": "Whether to return full actor list"}
                },
                "required": ["namespace"]
            }
        }
    }
]

# 2. LOCAL SIMULATED FUNCTION (Represents your Ray Cluster state)
def query_ray_cluster_status(namespace="legion", include_actors=True):
    return json.dumps({
        "status": "HEALTHY",
        "namespace": namespace,
        "active_actors": 39,
        "key_components": ["PaniniRagEngine", "SovereignSieve", "ACPControlPlane"],
        "shared_memory_type": "PyArrow Zero-Copy Plasma Store",
        "embedding_model": "text-embedding-snowflake-arctic-embed-l-v2.0 (1024-D)"
    })

# 3. INITIAL MESSAGES
messages = [
    {
        "role": "user",
        "content": "Inspect the 'legion' cluster namespace, then outline what expert-level AI sub-systems you can help us design for this SCARS_LAB cluster."
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
            # Expand tool_calls list if new index is encountered
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
    # OpenAI expects null instead of missing content if there are tool calls but no text
    if "content" not in assistant_message:
        assistant_message["content"] = None
        
messages.append(assistant_message)

if tool_calls:
    print("\n")
    for tool_call in tool_calls:
        fn_name = tool_call["function"]["name"]
        fn_args_str = tool_call["function"]["arguments"]
        
        # Try to parse arguments, sometimes streaming might end abruptly
        try:
            fn_args = json.loads(fn_args_str)
        except json.JSONDecodeError:
            fn_args = fn_args_str
            
        print(f"\n🎯 [TOOL CALL DETECTED]: {fn_name}({fn_args})")
        
        # Step 2: Execute local code based on tool call
        if fn_name == "query_ray_cluster_status":
            tool_result = query_ray_cluster_status(**fn_args)
            print(f"⚡ [EXECUTED LOCAL TOOL]: Retrived Ray Cluster State.")
            
            # Append tool execution output back to chat history
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": tool_result
            })

    # TURN 2: Send tool output back to Nemotron for final reasoning (Streaming)
    print("\n📡 Step 2: Returning cluster telemetry back to Nemotron for final analysis...\n")
    
    second_response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.3,
        stream=True
    )
    
    print("🤖 Final Analysis: \n")
    for chunk in second_response:
        delta = chunk.choices[0].delta
        if delta.content:
            print(delta.content, end="", flush=True)
            
    print() # newline after stream ends

latency = (time.time() - start_time) * 1000
print(f"\n✅ FULL PROCESS COMPLETED ({latency:.2f} ms total)")

print("\n" + "=" * 75)
print("🏁 FULL AGENTIC LOOP COMPLETE")
print("=" * 75)
