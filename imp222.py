import os
import json
import asyncio
import httpx

# ============================================================================
# ⚙️ CONFIGURATION & VARIABLE DECLARATIONS
# ============================================================================
TARGET_FILE_PATH = r"C:\WEB CASE STUDY\autoscale2.py"
STUDIO_ENDPOINT = "http://127.0.0.1:1234/v1/chat/completions"  # Local Studio Port
MODEL_NAME = "nvidia/nemotron-3-nano-4b"
MAX_TURNS = 5  # Maximum execution rounds for the multi-turn loop
MAX_TOKENS_BUDGET = 2048
TEMPERATURE_SETTING = 0.0

SYSTEM_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_swarm_memory",
            "description": "Queries Ray Arrow Swarm PyArrow shared memory tables for latent deployments.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query target across memory tables."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_verified_code",
            "description": "Surgically updates a target file at a specific line number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_file": {"type": "string"},
                    "line_number": {"type": "integer"},
                    "code_to_insert": {"type": "string"}
                },
                "required": ["target_file", "line_number", "code_to_insert"]
            }
        }
    }
]

# ============================================================================
# 🛠️ LOCAL TOOL IMPLEMENTATIONS (MOCK / LIVE SWARM HANDLERS)
# ============================================================================
async def execute_local_tool(function_name: str, args: dict) -> str:
    """Dispatches intercepted tool calls to local Ray Swarm / File system handlers."""
    if function_name == "search_swarm_memory":
        target_query = args.get("query", "")
        # Return simulated/live memory lookup result to pass back to model in Turn 2
        return json.dumps({
            "status": "SUCCESS",
            "table_found": "active_swarm_registry",
            "query": target_query,
            "matches": [
                {"line": 28, "class": "LatentDeployment", "issue": "Missing __call__ async request handler"}
            ]
        })
    elif function_name == "write_verified_code":
        return json.dumps({
            "status": "APPLIED",
            "file": args.get("target_file"),
            "line": args.get("line_number")
        })
    return json.dumps({"status": "ERROR", "message": f"Unknown tool: {function_name}"})

# ============================================================================
# 🚀 AGENTIC MULTI-TURN EXECUTION LOOP
# ============================================================================
async def run_multi_turn_studio_session():
    print("=" * 80)
    print(f"🔄 STARTING MULTI-TURN TOOL LOOP WITH LM STUDIO AT: {STUDIO_ENDPOINT}")
    print("=" * 80)

    if not os.path.exists(TARGET_FILE_PATH):
        print(f"[-] File not found: {TARGET_FILE_PATH}")
        return

    with open(TARGET_FILE_PATH, "r", encoding="utf-8") as f:
        code_lines = f.readlines()
    enumerated_code = "\n".join([f"Line {i+1}: {l.rstrip()}" for i, l in enumerate(code_lines)])

    # Initialize Message History
    messages = [
        {
            "role": "system", 
            "content": "You are a Ray Swarm engineer. Analyze code and execute tools (`search_swarm_memory`, `write_verified_code`) to report fixes."
        },
        {
            "role": "user", 
            "content": f"Inspect `{TARGET_FILE_PATH}` below. Query swarm memory for `LatentDeployment` and tell us what line number to update.\n\n{enumerated_code}"
        }
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        turn_counter = 1
        
        while turn_counter <= MAX_TURNS:
            print(f"\n📡 [TURN {turn_counter}] Sending request payload to LM Studio...")
            payload = {
                "model": MODEL_NAME,
                "messages": messages,
                "tools": SYSTEM_TOOLS,
                "tool_choice": "auto",
                "temperature": TEMPERATURE_SETTING,
                "max_tokens": MAX_TOKENS_BUDGET
            }

            response = await client.post(STUDIO_ENDPOINT, json=payload)
            choice = response.json()["choices"][0]["message"]

            # Append Assistant Message to History
            messages.append(choice)

            content = choice.get("content", "")
            tool_calls = choice.get("tool_calls", [])

            if content:
                print(f"\n💬 Assistant Response:\n{content}")

            if not tool_calls:
                print("\n✅ Multi-turn cycle complete. Model finished tool execution.")
                break

            # Execute Each Tool Call and Append Output with role="tool"
            for tool_call in tool_calls:
                call_id = tool_call["id"]
                fn_name = tool_call["function"]["name"]
                fn_args = json.loads(tool_call["function"]["arguments"])

                print(f"🛠️ [TURN {turn_counter} EXECUTION] Invoking: {fn_name}({fn_args})")
                tool_result_str = await execute_local_tool(fn_name, fn_args)

                # Feed the result back as role="tool"
                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": tool_result_str
                })

            turn_counter += 1

if __name__ == "__main__":
    asyncio.run(run_multi_turn_studio_session())