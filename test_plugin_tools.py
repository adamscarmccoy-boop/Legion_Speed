import requests
import json
from legion_kernel_bridge import LlamaKernelBridge

print("TESTING NATIVE TOOLSPROVIDER AND PROMPT PREPROCESSOR...")
bridge = LlamaKernelBridge()

try:
    headers = bridge.get_headers()
    
    # We will send a prompt that triggers RAG tools to confirm it sees the new schema context
    payload = {
        "messages": [
            {"role": "user", "content": "Run the list_available_data tool to check my active tables."}
        ],
        "temperature": 0.0,
        "max_tokens": 150,
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "list_available_data",
                    "description": "List all available tables and schemas inside DuckDB."
                }
            }
        ]
    }
    
    url = f"http://{bridge.host}:{bridge.port}/v1/chat/completions"
    print(f"Sending completion request to llama-server on Port {bridge.port}...")
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    
    print("\nAPI Response:")
    print(json.dumps(data, indent=2))
    
    # Check if the model decided to call the list_available_data tool
    choices = data.get("choices", [])
    if choices:
        message = choices[0].get("message", {})
        tool_calls = message.get("tool_calls", [])
        if tool_calls:
            print(f"\nSUCCESS: The model successfully called tool: '{tool_calls[0]['function']['name']}'!")
        else:
            print("\nWARNING: No tool calls generated. Response content:", message.get("content"))
            
except Exception as e:
    print(f"Error testing plugin: {e}")
