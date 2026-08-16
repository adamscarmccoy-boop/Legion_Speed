import os
import sys
import json
from openai import OpenAI

# 1. Initialize official OpenAI SDK client targeting LM Studio on port 1234
client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

# 2. Source codes to merge
v1_path = r"C:\AI_Logs\Legion-Jacked-Pipeline\legion_chat.py"
v7_path = r"C:\AI_Logs\Legion-Jacked-Pipeline\legion_chat_v7.py"

with open(v1_path, "r", encoding="utf-8") as f:
    v1_code = f.read()

with open(v7_path, "r", encoding="utf-8") as f:
    v7_code = f.read()

# 3. Tool definition for direct file writing
def write_file(path, content):
    try:
        workspace_root = r"C:\WEB CASE STUDY"
        full_path = os.path.join(workspace_root, path) if not os.path.isabs(path) else path
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[SUCCESS] Wrote {len(content)} characters to {full_path}")
        return json.dumps({"status": "OK", "path": full_path})
    except Exception as e:
        print(f"[ERROR] Failed to write: {e}")
        return json.dumps({"status": "ERROR", "error": str(e)})

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Writes the unified legion_chat.py code directly to the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The destination path, e.g. 'legion_chat.py'"},
                    "content": {"type": "string", "description": "The merged, final Python code"}
                },
                "required": ["path", "content"]
            }
        }
    }
]

system_prompt = """You are the Sovereign Rebuild Agent.
Your job is to generate a new unified `legion_chat.py` in the workspace using the `write_file` tool.
Do NOT output conversational text or stream the code blocks to the terminal. Just invoke the tool directly.

Combine the features of:
1. `legion_chat.py` (V1): LanceDB MemoryBank, ExecutionEngine auto-feedback loops, and terminal chat commands (/reset, /file, etc).
2. `legion_chat_v7.py` (V7): DuckDB interaction logging, Phoenix OpenTelemetry UI tracing, and direct Audiocraft music tensor generation.

Key Updates to Apply:
- LM Studio URL must be `http://127.0.0.1:1234/v1` (with `/v1`).
- All LanceDB and DuckDB paths must be placed inside `C:\\WEB CASE STUDY\\sovereign_data`.
- Keep the `external_organs` path additions for the UV cache.
- Print "LEGION V8" on startup.

Invoke the tool immediately to write the code into `legion_chat.py`."""

def run():
    print("Initiating direct rebuild via local model (no console streaming)...")
    prompt = f"Merge these files and write them to legion_chat.py using the tool. Do not chat.\n\n=== V1 ===\n{v1_code}\n\n=== V7 ===\n{v7_code}"
    
    try:
        response = client.chat.completions.create(
            model="nvidia/nemotron-3-nano-4b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            tools=TOOL_SCHEMAS,
            tool_choice="required",
            temperature=0.2
        )
        
        # Execute tool call
        tool_calls = response.choices[0].message.tool_calls
        if tool_calls:
            for tc in tool_calls:
                args = json.loads(tc.function.arguments)
                write_file(args["path"], args["content"])
        else:
            print("[WARN] Model did not call the write_file tool.")
            
    except Exception as e:
        print(f"[FATAL] Rebuild failed: {e}")

if __name__ == "__main__":
    run()
