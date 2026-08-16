import sys
import json
import requests
from openai import OpenAI

# Connect to LM Studio's local server (Default port is 1234)
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

print("📡 Searching for local AI on port 1234...")

try:
    models = client.models.list()
    current_model = models.data[0].id
    print(f"✅ Connected to: {current_model}")
except Exception as e:
    print("\n❌ FAILED TO CONNECT TO LM STUDIO!")
    print("Please make sure LM Studio is open, a model is loaded, and the Local Server is started.")
    sys.exit(1)

# Define the tools available to LM Studio (The Swarm Gateway)
swarm_tools = [
    {
        "type": "function",
        "function": {
            "name": "delegate_to_swarm",
            "description": "Delegate a complex task to the Legion Swarm Orchestrator. The swarm can write files, run commands, analyze data, and execute workflows.",
            "parameters": {
                "type": "object",
                "properties": {
                    "instruction": {
                        "type": "string",
                        "description": "A natural language instruction describing exactly what the swarm should do."
                    }
                },
                "required": ["instruction"]
            }
        }
    }
]

def execute_swarm_tool(instruction: str) -> str:
    print(f"\n[⚡ EXECUTING SWARM TOOL]: {instruction}")
    try:
        payload = {
            "tool_name": "chat_v4",
            "parameters": {"message": instruction}
        }
        # Hit the actual swarm gateway backend
        response = requests.post(
            "http://127.0.0.1:8001/tools/execute",
            json=payload,
            timeout=180
        )
        if response.status_code == 200:
            return json.dumps(response.json())
        else:
            return f"Swarm API Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"Failed to connect to Swarm: {str(e)}"

print("\n💬 Chat initialized with Swarm Tools enabled. Type 'exit' to quit.\n")

chat_history = [
    {"role": "system", "content": "You are a helpful AI assistant connected to a powerful Swarm Orchestrator. If the user asks you to perform complex actions, write files, or query data, use the `delegate_to_swarm` tool."}
]

while True:
    try:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            break
        if not user_input.strip():
            continue
            
        chat_history.append({"role": "user", "content": user_input})
        
        # Send to LM Studio WITH tools
        response = client.chat.completions.create(
            model=current_model,
            messages=chat_history,
            temperature=0.7,
            tools=swarm_tools,
            tool_choice="auto",
            stream=False # Non-streaming is usually more reliable for tool calling in LM Studio
        )
        
        response_message = response.choices[0].message
        chat_history.append(response_message)
        
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                if tool_call.function.name == "delegate_to_swarm":
                    args = json.loads(tool_call.function.arguments)
                    result = execute_swarm_tool(args.get("instruction", ""))
                    
                    # Feed tool result back to the model
                    chat_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })
            
            # Get the final answer from the model after tool execution
            final_response = client.chat.completions.create(
                model=current_model,
                messages=chat_history,
                temperature=0.7
            )
            final_text = final_response.choices[0].message.content
            print(f"\nAgent: {final_text}\n")
            chat_history.append({"role": "assistant", "content": final_text})
        else:
            print(f"\nAgent: {response_message.content}\n")
            
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"\n[!] Error: {str(e)}\n")
