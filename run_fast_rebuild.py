import asyncio
import os
import sys
import json
from lmstudio_integration import LMStudioClient

# 1. Define the write tool for the agent
def write_workspace_file(path: str, content: str) -> str:
    """Writes content to a file in the workspace."""
    try:
        # Resolve path
        workspace_root = r"C:\WEB CASE STUDY"
        full_path = os.path.join(workspace_root, path) if not os.path.isabs(path) else path
        
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to {full_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

# 2. Get original source codes
v1_path = r"C:\AI_Logs\Legion-Jacked-Pipeline\legion_chat.py"
v7_path = r"C:\AI_Logs\Legion-Jacked-Pipeline\legion_chat_v7.py"

with open(v1_path, "r", encoding="utf-8") as f:
    v1_code = f.read()

with open(v7_path, "r", encoding="utf-8") as f:
    v7_code = f.read()

system_prompt = """You are the Sovereign Rebuild Agent.
Your task is to generate a new unified `legion_chat.py` in the workspace using the `write_workspace_file` tool.
Do NOT write long text or stream the code in your conversational response. Just call the tool.

Combine the features of:
1. `legion_chat.py` (V1): LanceDB MemoryBank, ExecutionEngine auto-feedback loops, and terminal chat commands (/reset, /file, etc).
2. `legion_chat_v7.py` (V7): DuckDB interaction logging, Phoenix OpenTelemetry UI tracing, and direct Audiocraft music tensor generation.

Key Updates to Apply:
- LM Studio URL must be `http://127.0.0.1:1234/v1` (with `/v1`).
- All LanceDB and DuckDB paths must be placed inside `C:\\WEB CASE STUDY\\sovereign_data`.
- Keep the `external_organs` path additions for the UV cache.
- Print "LEGION V8" on startup.

Call the tool immediately to write `legion_chat.py`."""

async def main():
    # Force use of port 1234
    client = LMStudioClient(api_base="http://127.0.0.1:1234/v1")
    
    # We want it to run headlessly without streaming tokens to terminal.
    # We pass the write tool.
    tools = [write_workspace_file]
    
    print("Initiating fast rebuild via local LMStudioClient...")
    
    prompt = f"Merge the following two files into a unified `legion_chat.py` and write it to disk. Do not talk, just call the tool.\n\n=== V1 CODE ===\n{v1_code}\n\n=== V7 CODE ===\n{v7_code}"
    
    try:
        # We run the act loop to let it call the tool
        response, history = await client.act(
            prompt=prompt,
            tools=tools,
            model="nvidia/nemotron-3-nano-4b",
            system_prompt=system_prompt,
            max_iterations=3
        )
    except Exception as e:
        import traceback
        print(f"ACT FAILED WITH EXCEPTION: {e}")
        traceback.print_exc()
        response = f"Error: {e}"
    
    print("\nRebuild Loop Finished!")
    print(f"Final Agent Response: {response}")
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
