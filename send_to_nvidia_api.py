import os
import sys
from openai import OpenAI

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

api_key = "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"
base_url = "https://integrate.api.nvidia.com/v1"

client = OpenAI(
    base_url=base_url,
    api_key=api_key
)

prompt = """
You are an expert NVIDIA HPC & Ray Architecture Engineer.

The user is running a system on Windows with Ray Arrow Swarm (`ray_arrow_swarm.py`).
Here is the git diff of the changes made to add error handling across the boot sequence:

```diff
--- ray_arrow_swarm_orig.py
+++ ray_arrow_swarm.py
@@ -289,14 +289,20 @@
     print("\\n--- Booting Code Swarm Registry ---")
+    try:
         import ray_code_swarm
         ray_code_swarm.main(keep_alive=False)
         print("--- Code Swarm Boot Complete ---\\n")
+    except Exception as e:
+        print(f"[WARNING] Code Swarm Boot failed/skipped: {e}\\n")
     
     print("\\n--- Booting Sovereign Neural Relay (Ray Serve) ---")
+    try:
         import sovereign_serve_app
         sovereign_serve_app.deploy_sovereign_relay()
         print("--- Sovereign Neural Relay Boot Complete ---\\n")
+    except Exception as e:
+        print(f"[WARNING] Sovereign Neural Relay Boot failed/skipped: {e}\\n")
     
     print("\\n--- Booting MCP Servers ---")
     import subprocess
     import sys
     
+    try:
         print("Starting MCP RAG Server (LegionLakehouse_RAG) on port 8003...")
         subprocess.Popen([sys.executable, "mcp_rag_server.py", "--sse"], cwd=r"C:\\WEB CASE STUDY")
+    except Exception as e:
+        print(f"[WARNING] Failed to start MCP RAG Server: {e}")
         
+    try:
         print("Starting MCP API Server (Legion Unified Onyx) on port 8001...")
         subprocess.Popen([sys.executable, "-m", "uvicorn", "mcp_api_server:app", "--port", "8001", "--host", "127.0.0.1"], cwd=r"C:\\WEB CASE STUDY")
+    except Exception as e:
+        print(f"[WARNING] Failed to start MCP API Server: {e}")
```

User Question:
"How can I offload models or actors with fewer serve applications in Ray so memory/OOM crashes don't happen on Windows?"

Provide a concise, direct, expert response.
"""

print("📡 Sending original code diff directly to NVIDIA API endpoint (meta/llama-3.1-70b-instruct)...")

try:
    completion = client.chat.completions.create(
        model="meta/llama-3.1-70b-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1024
    )
    
    response_text = completion.choices[0].message.content
    print("\n=================== NVIDIA API RESPONSE ===================")
    print(response_text)
    print("===========================================================")
except Exception as e:
    print(f"Error querying NVIDIA API: {e}")
