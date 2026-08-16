import os
import json
import time
from openai import OpenAI

try:
    import pydantic_monty as monty
    HAS_MONTY = True
except ImportError:
    HAS_MONTY = False

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

LLM_MODEL = "nvidia/nemotron-3-nano-4b"
TARGET_DIR = r"C:\WEB CASE STUDY"
os.makedirs(TARGET_DIR, exist_ok=True)

print("=" * 75)
print("🛠️ EXECUTING PRE-FLIGHT AUTO-CODER LOOP WITH NEMOTRON-3-NANO")
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
    },
    {
        "type": "function",
        "function": {
            "name": "write_verified_code",
            "description": "Writes Python code to a file ONLY IF it passes AST and syntax verification.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Name of the .py file (e.g., system_monitor.py)"},
                    "code_content": {"type": "string", "description": "The complete, executable Python code to write."}
                },
                "required": ["filename", "code_content"]
            }
        }
    }
]

# 2. LOCAL SIMULATED FUNCTIONS
def query_ray_cluster_status(namespace="legion", include_actors=True):
    return json.dumps({
        "status": "HEALTHY",
        "namespace": namespace,
        "active_actors": 39,
        "key_components": ["PaniniRagEngine", "SovereignSieve", "ACPControlPlane"],
        "shared_memory_type": "PyArrow Zero-Copy Plasma Store",
        "embedding_model": "text-embedding-snowflake-arctic-embed-l-v2.0 (1024-D)"
    })

def execute_preflight_and_write(filename="unknown.py", code_content=""):
    print(f"\n🔍 [PRE-FLIGHT] Verifying '{filename}' in Monty Rust VM...")
    if not HAS_MONTY:
        return json.dumps({"status": "FAILED", "error": "Pydantic-Monty is not installed."})

    try:
        with monty.Monty() as pool:
            with pool.checkout() as session:
                session.feed_run(code_content)
                
        filepath = os.path.join(TARGET_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code_content)
            
        print(f"✅ [SUCCESS] File written to: {filepath}")
        return json.dumps({"status": "SUCCESS", "message": f"File flawlessly compiled and written to {filepath}"})
        
    except Exception as e:
        print(f"❌ [PRE-FLIGHT FAILED] Intercepted Fault: {e}")
        return json.dumps({
            "status": "REJECTED_BY_PREFLIGHT",
            "error_message": f"Code failed pre-flight verification: {str(e)}. Please fix the syntax errors and invoke the tool again."
        })

# 3. INITIAL MESSAGES
messages = [
    {
        "role": "user",
        "content": "Inspect the 'legion' cluster namespace, then outline what expert-level AI sub-systems you can help us design for this SCARS_LAB cluster. Finally, use the write_verified_code tool to output the Python script for the first subsystem."
    }
]

print("\n📡 Step 1: Sending prompt and tool definitions to Nemotron...")
start_time = time.time()

# 4. THE AUTONOMOUS LOOP
for turn in range(5):
    print(f"\n📡 Turn {turn+1}: Waiting for Nemotron's response...")
    
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        tools=tools_schema,
        tool_choice="auto",
        temperature=0.0
    )
    
    # 🚨 FIX 1: BYPASSING THE MARKDOWN BUG
    # Using .pop() completely avoids the square brackets syntax that your UI keeps eating!
    first_choice = response.choices.pop(0)
    message = first_choice.message
    
    # 🚨 FIX 2: THE SAFE DICT CONSTRUCTOR 
    # Strips out 'reasoning_content' so LM Studio doesn't throw a 400 Bad Request on Turn 2
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
            fn_args = json.loads(tool_call.function.arguments)
            
            print(f"🎯 [TOOL CALL DETECTED]: {fn_name}")
            
            tool_result = ""
            if fn_name == "query_ray_cluster_status":
                tool_result = query_ray_cluster_status(**fn_args)
                print("⚡ [EXECUTED]: Retrieved Ray Cluster State.")
            elif fn_name == "write_verified_code":
                tool_result = execute_preflight_and_write(**fn_args)
                
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })
    else:
        latency = (time.time() - start_time) * 1000
        print(f"\n✅ FINAL OUTPUT RECEIVED ({latency:.2f} ms total)")
        print("-" * 75)
        print(message.content)
        break

print("\n" + "=" * 75)
print("🏁 FULL AGENTIC LOOP COMPLETE")
print("=" * 75)