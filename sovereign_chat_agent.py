import os
import sys
import json
import time
import socket
import logging
import traceback
from pathlib import Path

# ==============================================================================
# 1. CORE SYSTEM ENVIRONMENT STABILIZERS
# ==============================================================================
os.environ["RAY_gcs_rpc_server_reconnect_timeout_s"] = "120"
os.environ["RAY_memory_monitor_refresh_ms"] = "250"
os.environ["RAY_DEDUP_LOGS"] = "0"
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

# Set up logging to output cleanly to the console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("SovereignClient")

# Try to resolve OpenAI SDK
try:
    from openai import OpenAI
except ImportError:
    log.error("[-] Please run 'pip install openai' to enable LM Studio communication.")
    sys.exit(1)

# ==============================================================================
# 2. DEFINING THE LEAN TOOL REPERTOIRE (NO BLOAT, NO TIMEOUTS)
# ==============================================================================
def check_port_status(port: int) -> dict:
    """Verifies if a local TCP port is open."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        try:
            s.connect(("127.0.0.1", port))
            return {"port": port, "status": "ONLINE", "message": "Successfully connected"}
        except Exception as e:
            return {"port": port, "status": "OFFLINE", "message": str(e)}

def read_file(filepath: str) -> dict:
    """Safely reads the contents of a specific file."""
    path = Path(filepath)
    if not path.exists():
        return {"status": "FAILED", "error": f"File '{filepath}' not found on disk."}
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        # Truncate to protect context limits
        if len(content) > 10000:
            content = content[:10000] + "\n... [TRUNCATED BY WARDEN TO PREVENT CHOKE] ..."
        return {"status": "SUCCESS", "filepath": str(path.resolve()), "content": content}
    except Exception as e:
        return {"status": "FAILED", "error": str(e)}

def write_verified_code(filepath: str, code_content: str) -> dict:
    """Performs compile verification and commits code back to Windows."""
    path = Path(filepath)
    try:
        # Pre-flight syntax compile check
        compile(code_content, str(path), "exec")
    except SyntaxError as syntax_err:
        return {
            "status": "COMPILATION_FAILED",
            "error": "Python syntax validation rejected the code block.",
            "traceback": str(syntax_err)
        }
    
    # Save code to disk
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code_content, encoding="utf-8")
        # Trigger Notepad to verify visually
        if os.name == "nt":
            import subprocess
            subprocess.Popen(["notepad.exe", str(path.resolve())])
        return {"status": "SUCCESS", "filepath": str(path.resolve()), "message": "Written and opened in notepad"}
    except Exception as e:
        return {"status": "FAILED", "error": f"Write failed: {str(e)}"}

# Map of tool names to local execution functions
TOOL_MAP = {
    "check_port_status": check_port_status,
    "read_file": read_file,
    "write_verified_code": write_verified_code
}

# Declarations matching OpenAI format
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "check_port_status",
            "description": "Verifies if a local TCP port is open. Use to check 1234 (LM Studio), 6379 (Ray GCS), or 8001 (Gateway).",
            "parameters": {
                "type": "object",
                "properties": {
                    "port": {"type": "integer", "description": "The target TCP port number."}
                },
                "required": ["port"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Loads a script's raw code into context for analysis. Protects against context-bloat.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Absolute file path (e.g. C:\\WEB CASE STUDY\\mcp_swarm_gateway.py)"}
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_verified_code",
            "description": "Saves code back to Windows ONLY IF it passes pre-flight AST syntax compilation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Target output path on Windows."},
                    "code_content": {"type": "string", "description": "Raw, unformatted Python code string."}
                },
                "required": ["filepath", "code_content"]
            }
        }
    }
]

SYSTEM_PROMPT = """You are an expert autonomic system architect. You are running inside a multi-turn, tool-calling client.
OPERATIONAL CORE:
1. Use check_port_status to verify cluster ports, read_file to inspect codes, and write_verified_code to apply syntax-safe patches.
2. If tool executions fail or return errors, analyze the output, adjust parameters, and retry immediately.
3. Keep payloads clean and focus ONLY on files specified by the user. Do not crawl directories blindly.
"""

# ==============================================================================
# 3. CHAT ORCHESTRATION WITH STREAMING & RECURSIVE TOOL CALLS
# ==============================================================================
def run_streaming_tool_loop(prompt: str, max_turns: int = 10):
    client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")
    
    # Initialize message history
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]
    
    turn = 1
    while turn <= max_turns:
        log.info(f"📡 [TURN {turn}/{max_turns}] Dispatching conversation context to LM Studio...")
        
        # We request chat completions from Port 1234
        try:
            response = client.chat.completions.create(
                model="nvidia/nemotron-3-nano-4b",
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
                temperature=0.0,
                stream=True  # Force Token-by-Token Streaming!
            )
        except Exception as conn_err:
            log.error(f"❌ Failed to reach LM Studio on port 1234. Is your server running?")
            log.error(str(conn_err))
            break

        current_role = "assistant"
        assistant_content = ""
        tool_calls_buffer = {}

        print("\n🤖 [LM STUDIO STREAMING]: ", end="", flush=True)
        
        # Iterate over stream chunks
        for chunk in response:
            delta = chunk.choices[0].delta
            
            # Handle standard text streaming
            if delta.content:
                assistant_content += delta.content
                print(delta.content, end="", flush=True)
                
            # Accumulate structured tool calls from stream chunks
            if delta.tool_calls:
                for tool_call_delta in delta.tool_calls:
                    index = tool_call_delta.index
                    if index not in tool_calls_buffer:
                        tool_calls_buffer[index] = {
                            "id": tool_call_delta.id,
                            "type": "function",
                            "function": {"name": "", "arguments": ""}
                        }
                    
                    tc = tool_calls_buffer[index]
                    if tool_call_delta.id:
                        tc["id"] = tool_call_delta.id
                    if tool_call_delta.function.name:
                        tc["function"]["name"] += tool_call_delta.function.name
                    if tool_call_delta.function.arguments:
                        tc["function"]["arguments"] += tool_call_delta.function.arguments
        
        print("\n") # New line after stream ends

        # Prepare assistant message representation to add back to history
        assistant_msg = {"role": "assistant"}
        if assistant_content:
            assistant_msg["content"] = assistant_content
            
        if tool_calls_buffer:
            # Parse buffered tool calls into schema list
            tool_calls = list(tool_calls_buffer.values())
            assistant_msg["tool_calls"] = tool_calls
            messages.append(assistant_msg)
            
            log.info(f"🔨 Model initiated {len(tool_calls)} parallel tool calls.")
            
            # Execute tool calls and append feedback
            for tc in tool_calls:
                fn_name = tc["function"]["name"]
                raw_args = tc["function"]["arguments"]
                call_id = tc["id"]
                
                try:
                    args = json.loads(raw_args) if raw_args else {}
                except json.JSONDecodeError:
                    log.warning(f"[!] Could not decode JSON arguments: {raw_args}. Attempting evaluation...")
                    args = {}
                
                if fn_name in TOOL_MAP:
                    log.info(f"⚙️ Running local function: '{fn_name}' with args: {args}")
                    tool_result = TOOL_MAP[fn_name](**args)
                    log.info(f"📥 Tool Execution Complete.")
                else:
                    tool_result = {"status": "ERROR", "error": f"Tool '{fn_name}' is not registered."}
                
                # Append tool response
                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": fn_name,
                    "content": json.dumps(tool_result)
                })
            
            # Loop back to next turn with the results fed to the model
            turn += 1
            continue
        else:
            # No tool calls made; model returned standard chat text. We are done!
            log.info("✅ Final answer received. Ending orchestration loop cleanly.")
            messages.append(assistant_msg)
            break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sovereign_chat_agent.py \"<PROMPT>\"")
        print("Example: python sovereign_chat_agent.py \"Verify if Ray GCS is up and read C:\\WEB CASE STUDY\\mcp_swarm_gateway.py\"")
        sys.exit(1)
        
    user_prompt = " ".join(sys.argv[1:])
    run_streaming_tool_loop(user_prompt)
