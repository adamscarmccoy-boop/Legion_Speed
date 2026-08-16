import json
import time
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

LLM_MODEL = "nvidia/nemotron-3-nano-4b"

print("=" * 75)
print("🛠️ EXECUTING FULL AGENTIC TOOL LOOP WITH NEMOTRON-3-NANO")
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

# TURN 1: Model issues the tool call
response = client.chat.completions.create(
    model=LLM_MODEL,
    messages=messages,
    tools=tools_schema,
    tool_choice="auto",
    temperature=0.2
)

message = response.choices[0].message
messages.append(message) # Append assistant's tool-call response to history

if message.tool_calls:
    for tool_call in message.tool_calls:
        fn_name = tool_call.function.name
        fn_args = json.loads(tool_call.function.arguments)
        
        print(f"\n🎯 [TOOL CALL DETECTED]: {fn_name}({fn_args})")
        
        # Step 2: Execute local code based on tool call
        if fn_name == "query_ray_cluster_status":
            tool_result = query_ray_cluster_status(**fn_args)
            print(f"⚡ [EXECUTED LOCAL TOOL]: Retrived Ray Cluster State.")
            
            # Append tool execution output back to chat history
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })

    # TURN 2: Send tool output back to Nemotron for final reasoning
    print("\n📡 Step 2: Returning cluster telemetry back to Nemotron for final analysis...")
    second_response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.3
    )
    
    latency = (time.time() - start_time) * 1000
    print(f"\n✅ FINAL ANALYSIS RECEIVED ({latency:.2f} ms total)")
    print("-" * 75)
    print(second_response.choices[0].message.content)

print("\n" + "=" * 75)
print("🏁 FULL AGENTIC LOOP COMPLETE")
print("=" * 75)