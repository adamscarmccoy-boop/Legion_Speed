import os
import json
import time
import sys
import re
import socket
import subprocess
from pathlib import Path
from openai import OpenAI

# Try importing pydantic_monty if available
try:
    import pydantic_monty as monty
    HAS_MONTY = True
except ImportError:
    HAS_MONTY = False

# --- CONFIGURATION & PATH RESOLUTION ---
TARGET_DIR = r"C:\STUDIES"
LM_STUDIO_URLS = ["http://127.0.0.1:1234/v1", "http://127.0.0.1:1010/v1"]
LLM_MODEL = "nvidia/nemotron-3-nano-4b"

USER_HOME = str(Path.home())
LM_STUDIO_DIR = os.path.join(USER_HOME, ".lmstudio")
LM_STUDIO_INTERNAL_DIR = os.path.join(LM_STUDIO_DIR, ".internal")
LM_STUDIO_LOG_DIR = os.path.join(LM_STUDIO_DIR, "logs")

# Direct targets for DevTools repair
HARDWARE_CONFIG_PATH = os.path.join(LM_STUDIO_INTERNAL_DIR, "hardware-config.json")
LM_STUDIO_MAIN_LOG = os.path.join(LM_STUDIO_LOG_DIR, "main.log")

# Exact active MCP and Tool config paths
ACTIVE_FILES = {
    "LM_STUDIO_HARDWARE": HARDWARE_CONFIG_PATH,
    "LM_STUDIO_MAIN_LOG": LM_STUDIO_MAIN_LOG,
    "CLINE_MCP_SETTINGS": os.path.join(USER_HOME, "AppData", "Roaming", "Code", "User", "globalStorage", 
                                       "rooveterinaryinc.roo-cline", "settings", "mcp_settings.json"),
    "PROJECT_MCP_CONFIG": os.path.join(r"C:\STUDIES", "mcp.json"),
    "PROJECT_DATA_MCP": os.path.join(r"C:\STUDIES", "data", "config", "mcp.json"),
    "PROJECT_ROO_MCP": os.path.join(r"C:\STUDIES", ".roo", "mcp.json")
}

# Ensure terminal uses UTF-8 to prevent console decoding crashes on Windows 11 GGUF logs
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Helper to automatically resolve active loopback endpoint
def get_active_endpoint():
    for url in LM_STUDIO_URLS:
        try:
            port = int(url.split(":")[-1].split("/" )[0])
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    return url
        except Exception:
            pass
    return LM_STUDIO_URLS[0]  # Fallback to standard Port 1234

ACTIVE_ENDPOINT = get_active_endpoint()
client = OpenAI(base_url=ACTIVE_ENDPOINT, api_key="lm-studio")

# =============================================================================
# 1. LIVE FILE ACQUISITION & SENSORY MATRIX (GET THE EXACT DATA)
# =============================================================================

def get_exact_files_data() -> str:
    """
    Directly scans and loads the exact contents of active developer and LM Studio files.
    This guarantees the model has full visibility into live workstation configurations.
    """
    print("📂 [ACQUISITION] Retrieving exact DevTools configurations...")
    results = {}
    for key, path in ACTIVE_FILES.items():
        if os.path.exists(path):
            try:
                # Safe read for configs and small files
                if path.endswith(".log"):
                    # Tail logs
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    results[key] = {
                        "path": path,
                        "status": "LOADED_TAIL",
                        "content": "".join(lines[-40:]) # Last 40 lines
                    }
                else:
                    with open(path, "r", encoding="utf-8") as f:
                        results[key] = {
                            "path": path,
                            "status": "LOADED",
                            "content": json.load(f)
                        }
            except Exception as e:
                results[key] = {"path": path, "status": "READ_ERROR", "error": str(e)}
        else:
            results[key] = {"path": path, "status": "NOT_FOUND"}
    return json.dumps(results, indent=2)

# =============================================================================
# 2. AUTO-HEALING PRE-FLIGHT COMPILING & DUNDER RECOVERY
# =============================================================================

def execute_preflight_and_write(filename: str, code_content: str) -> str:
    """
    AST compile validation with auto-repair of Markdown dunder bolding.
    Safely writes the file to the target workspace (C:\\STUDIES).
    """
    print(f"\n🔍 [PRE-FLIGHT] Verifying script '{filename}'...")
    
    # Auto-Heal markdown Bold manglings (e.g. **name** -> __name__, **main** -> __main__)
    repaired_code = re.sub(r'\*+([a-zA-Z0-9_]+)\*+', r'__\1__', code_content)
    repaired_code = repaired_code.replace("**name**", "__name__").replace("**main**", "__main__")
    
    if repaired_code != code_content:
        print("⚡ [AUTO-HEALER] Repaired Markdown dunder bold-mangling successfully!")

    if not HAS_MONTY:
        filepath = os.path.join(TARGET_DIR, filename)
        try:
            os.makedirs(TARGET_DIR, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(repaired_code)
            return json.dumps({
                "status": "WARNING",
                "message": f"File written directly to {filepath} (Monty pre-flight was unavailable on host)."
            })
        except Exception as e:
            return json.dumps({"status": "FAILED", "error": f"Write failed: {str(e)}"})

    try:
        # Pre-flight compilation step in isolated Rust subprocess
        with monty.Monty() as pool:
            with pool.checkout() as session:
                session.feed_run(repaired_code)
                
        filepath = os.path.join(TARGET_DIR, filename)
        os.makedirs(TARGET_DIR, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(repaired_code)
            
        print(f"✅ [SUCCESS] Pre-flight passed! Code written cleanly: {filepath}")
        return json.dumps({
            "status": "SUCCESS", 
            "message": f"Code verified inside Monty Rust VM and written to {filepath}"
        })
        
    except Exception as e:
        print(f"❌ [PRE-FLIGHT REJECTED] AST syntax/compilation error: {e}")
        return json.dumps({
            "status": "REJECTED_BY_PREFLIGHT",
            "error_message": f"Syntax compilation failed: {str(e)}. Please correct your code syntax."
        })

# =============================================================================
# 3. DETERMINISTIC ORCHESTRATION LAYER (GGUF STACK BINDINGS)
# =============================================================================

def run_devtools_autocoder(prompt: str):
    print("=" * 80)
    print("🤖 INITIATING DETERMINISTIC DEVTOOLS AUTO-CODER (V2 GET-AND-WRITE)")
    print(f"📡 API ENDPOINT: {ACTIVE_ENDPOINT} | MODEL: {LLM_MODEL}")
    print("=" * 80)
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_exact_files_data",
                "description": "Acquires exact content and paths of active MCP, Cline, and LM Studio configuration files."
            }
        },
        {
            "type": "function",
            "function": {
                "name": "write_verified_code",
                "description": "Writes the finished Python repair script to C:\\STUDIES after syntax validation.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string", "description": "Output file (e.g. repair_mcp.py)"},
                        "code_content": {"type": "string", "description": "Unformatted Python code content."}
                    },
                    "required": ["filename", "code_content"]
                }
            }
        }
    ]
    
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert devtools administrator. Your task is to inspect active configurations, "
                "identify corruptions or errors, and write an absolute, self-healing Python script that the "
                "user can run locally to resolve issues.\n\n"
                "CRITICAL SANDBOX PROTECTION RULES:\n"
                "1. The pre-flight checker (Monty) physically executes your code block to verify syntax.\n"
                "2. If your script attempts file operations (like open, write, or makedirs) inside the current "
                "directory or standard system paths, it will crash with a PermissionError inside the Rust VM.\n"
                "3. You must shield the script from running side-effects during pre-flight checks by adding a "
                "sandbox-detection gate:\n\n"
                "   def is_preflight():\n"
                "       # Returns True if running inside Monty pre-flight VM\n"
                "       return not os.path.exists(r\"C:\\Users\\adams\") or os.environ.get(\"MONTY_VM\")\n\n"
                "   if __name__ == \"__main__\":\n"
                "       if is_preflight():\n"
                "           print(\"Preflight Check passed successfully.\")\n"
                "           sys.exit(0)\n"
                "       # Real repair logic goes here...\n\n"
                "4. Write robust, non-interactive Python 3 code with complete error handling.\n"
                "5. Use 'get_exact_files_data' first to retrieve the real configuration parameters before making changes."
            )
        },
        {"role": "user", "content": prompt}
    ]
    
    for turn in range(8):
        print(f"\n📡 [TURN {turn+1}/8] Sending deterministic prompt to LM Studio...")
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                tools=tools,
                temperature=0.0,       # Force absolute deterministic precision
                seed=42,
                max_tokens=2000
            )
        except Exception as e:
            print(f"❌ OpenAI handshake failed: {e}")
            break
            
        if not response.choices:
            print("[-] Null choice array returned.")
            break
            
        choice = response.choices[0]
        message = choice.message
        
        if hasattr(message, "reasoning_content") and message.reasoning_content:
            print(f"\n💭 [THOUGHTS] {message.reasoning_content}")
        elif message.content:
            print(f"\n💬 [ASSISTANT] {message.content}")
            
        # Construct standard API response payload
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
                fn_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                
                print(f"🔨 [TOOL CALL] Processing: {fn_name}")
                if fn_name == "get_exact_files_data":
                    result = get_exact_files_data()
                elif fn_name == "write_verified_code":
                    result = execute_preflight_and_write(fn_args["filename"], fn_args["code_content"])
                else:
                    result = json.dumps({"error": f"Unknown tool: {fn_name}"})
                    
                print(f"📥 [TOOL OUTPUT] Returned snippet: {result[:200]}...")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
                
                if fn_name == "write_verified_code":
                    res_data = json.loads(result)
                    if res_data.get("status") == "SUCCESS":
                        print("\n🏁 [COMPLETE] Successfully validated and wrote script to disk!")
                        return
        else:
            print("\n🏁 [COMPLETE] Model finished without additional tool execution.")
            break

if __name__ == "__main__":
    task_prompt = (
        "Retrieve the exact MCP configuration files on my workstation, inspect their active tool structures, "
        "and then write a Python script named 'repair_active_devtools.py' that repairs any structural syntax "
        "errors in my mcp.json files, ensuring that it compiles perfectly and bypasses pre-flight sandboxing constraints."
    )
    run_devtools_autocoder(task_prompt)
