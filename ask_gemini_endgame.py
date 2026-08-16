import os
import sys
from google import genai
from google.genai import types
from dotenv import load_dotenv

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

load_dotenv()
api_key = os.getenv("AISTUDIO_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ Error: API key not found in .env")
    sys.exit(1)

client = genai.Client(api_key=api_key)

contents_to_send = []

# ----------------------------------------------------------------
# 1. Upload context files
# ----------------------------------------------------------------
uploads = [
    (r"C:\WEB CASE STUDY\LEGION_MANIFEST.md", "LEGION_MANIFEST.md"),
    (r"C:\WEB CASE STUDY\conversation_history.md", "conversation_history.md"),
    (r"C:\WEB CASE STUDY\mcp_rag_server.py", "mcp_rag_server.py"),
    (r"C:\WEB CASE STUDY\ray_arrow_swarm.py", "ray_arrow_swarm.py"),
    (r"C:\Users\adams\.gemini\antigravity-ide\brain\861ee326-6442-4397-ae7f-b35fcbd4ddb2\scratch\run_100_mcp_monty_benchmark.py", "run_100_mcp_monty_benchmark.py"),
    (r"C:\Users\adams\.gemini\antigravity-ide\brain\861ee326-6442-4397-ae7f-b35fcbd4ddb2\scratch\test_mcp_rag_monty_prometheus.py", "test_mcp_rag_monty_prometheus.py"),
    (r"C:\Users\adams\.gemini\antigravity-ide\brain\861ee326-6442-4397-ae7f-b35fcbd4ddb2\scratch\monty_prometheus_trace_log.json", "monty_prometheus_trace_log.json"),
]

uploaded_files = {}

for path, label in uploads:
    if os.path.exists(path):
        print(f"Uploading: {label}")
        f = client.files.upload(
            file=path,
            config=types.UploadFileConfig(mime_type="text/plain", display_name=label)
        )
        contents_to_send.append(f)
        uploaded_files[label] = f.name
    else:
        print(f"  SKIP (not found): {path}")

# ----------------------------------------------------------------
# 2. The Prompt with variables
# ----------------------------------------------------------------
manifest_file = uploaded_files.get("LEGION_MANIFEST.md", "LEGION_MANIFEST.md")
timeline_file = uploaded_files.get("conversation_history.md", "conversation_history.md")
mcp_file = uploaded_files.get("mcp_rag_server.py", "mcp_rag_server.py")
swarm_file = uploaded_files.get("ray_arrow_swarm.py", "ray_arrow_swarm.py")
bench_file = uploaded_files.get("run_100_mcp_monty_benchmark.py", "run_100_mcp_monty_benchmark.py")
prometheus_file = uploaded_files.get("test_mcp_rag_monty_prometheus.py", "test_mcp_rag_monty_prometheus.py")
trace_log_file = uploaded_files.get("monty_prometheus_trace_log.json", "monty_prometheus_trace_log.json")

prompt = f"""
You are the lead architect and C++/Rust/Node.js Native integration expert for the Sovereign Audio Intelligence system.

I have uploaded the following files. You must use them in this exact order to understand the context:
1. The {manifest_file} is the current state of the system.
2. The {timeline_file} contains the timeline reference of our conversation and proves exactly what we already successfully ran and built.
3. Here are the actual files that it talks about:
   - {mcp_file}
   - {swarm_file}
   - {bench_file}
   - {prometheus_file}
   - {trace_log_file}

## YOUR TASK:
I need you to act as a parsing tool like Monty. Take all the `.py` code I just uploaded, list them, and use the timing references in {timeline_file} to understand exactly how we got the Monty sandbox working in Python. 

Then, I need you to translate that EXACT working logic (from {bench_file} and {prometheus_file}) into the native C++/Node.js LM Studio Plugin architecture we discussed. 
Do not guess or make it "conceptual." Port the actual logic that we proved works in the benchmark traces into the native Node.js / Rust FFI architecture.

Output the complete, updated architecture and native code implementation based on the actual verified python logic.
"""

contents_to_send.append(prompt)

# ----------------------------------------------------------------
# 3. Stream response
# ----------------------------------------------------------------
print("\nInitializing session (model: gemini-2.5-flash)...")
chat = client.chats.create(model="gemini-2.5-flash")

out_file = r"C:\WEB CASE STUDY\gemini_endgame_architecture.md"

print(f"Streaming Response (saving code to: {os.path.basename(out_file)})...\n" + "="*70)

with open(out_file, "w", encoding="utf-8") as out:
    try:
        response = chat.send_message_stream(contents_to_send)
        for chunk in response:
            text = chunk.text or ""
            print(text, end="", flush=True)
            out.write(text)
    except Exception as e:
        print(f"\nError: {e}")

print("\n" + "="*70)
print(f"Full response saved to: {out_file}")
