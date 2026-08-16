import json
from legion_kernel_bridge import LlamaKernelBridge

print("CONNECTING TO LM STUDIO TO VERIFY REGISTERED TOOLS...")
bridge = LlamaKernelBridge()

# Query chat completion endpoint with a test prompt asking for tool definitions
try:
    headers = bridge.get_headers()
    url = f"http://{bridge.host}:{bridge.port}/v1/models"
    
    import requests
    models_resp = requests.get(url, headers=headers)
    print("\nActive Models Loaded in LM Studio:")
    for model in models_resp.json().get("data", []):
        print(f" - {model['id']}")
        
    print("\nChecking if native tools are visible to the model:")
    # Send a prompt to test if the model sees the newly registered rag-v2 ToolsProvider
    resp = bridge.chat(
        messages=[
            {"role": "system", "content": "You are verifying registered ToolsProvider tools. Confirm the name of the tools available to you."},
            {"role": "user", "content": "What tools can you call?"}
        ],
        max_tokens=100
    )
    print("\nModel Response:")
    print(resp["choices"][0]["message"]["content"])
    print(f"\nThroughput verification: Latency {resp['_latency_ms']:.2f}ms on Port {resp['_kernel_port']}")
except Exception as e:
    print(f"Error querying active tools: {e}")
