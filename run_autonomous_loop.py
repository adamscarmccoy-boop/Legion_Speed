import os
import re
import sys
import json
import socket
import requests
import traceback
from pathlib import Path
from openai import OpenAI

# Try importing pydantic_monty if available
try:
    import pydantic_monty as monty
    HAS_MONTY = True
except ImportError:
    HAS_MONTY = False

# --- CONFIGURATION & PATH RESOLUTION ---
TARGET_DIR = r"C:\WEB CASE STUDY"
if not os.path.exists(TARGET_DIR):
    TARGET_DIR = os.getcwd()

PORT_OPTIONS = [1234, 1010, 56217, 61277]

# LM Studio Standard Configuration Files (User's Workspace Paths)
USER_HOME = str(Path.home())
LM_STUDIO_INTERNAL_DIR = os.path.join(USER_HOME, ".lmstudio", ".internal")
LM_STUDIO_LOG_DIR = os.path.join(USER_HOME, ".lmstudio", "logs")
HARDWARE_CONFIG_PATH = os.path.join(LM_STUDIO_INTERNAL_DIR, "hardware-config.json")
LM_STUDIO_MAIN_LOG = os.path.join(LM_STUDIO_LOG_DIR, "main.log")

MCP_CONFIG_PATHS = [
    os.path.join(r"C:\STUDIES", "mcp_config_lmstudio.json"),
    os.path.join(r"C:\STUDIES", "mcp.json"),
    os.path.join(r"C:\STUDIES", ".roo", "mcp.json"),
    os.path.join(USER_HOME, "AppData", "Roaming", "Code", "User", "globalStorage", 
                 "rooveterinaryinc.roo-cline", "settings", "mcp_settings.json")
]

# Ensure terminal uses UTF-8 to prevent console decoding crashes on Windows 11 GGUF logs
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def discover_active_port() -> int:
    """Tries to connect to model server ports to find the active llama_server instance."""
    for port in PORT_OPTIONS:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.2)
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    url = f"http://127.0.0.1:{port}/v1/models"
                    res = requests.get(url, timeout=0.5)
                    if res.status_code == 200:
                        return port
        except Exception:
            pass
    return 1234  # Fallback standard

ACTIVE_PORT = discover_active_port()
LM_STUDIO_URL = f"http://127.0.0.1:{ACTIVE_PORT}/v1"
LLM_MODEL = "nvidia/nemotron-3-nano-4b"

print(f"📡 [BOUND] Connecting to Active C++ Inference Engine on Port {ACTIVE_PORT}...")

try:
    client = OpenAI(base_url=LM_STUDIO_URL, api_key="lm-studio")
except Exception as e:
    print(f"[-] Warn: OpenAI client initialization failed: {e}")
    sys.exit(1)


# =============================================================================
# 1. PURE IN-PROCESS DEVTOOLS & FILE SENSORY HARDWARE BINDINGS
# =============================================================================

def read_lmstudio_logs(lines: int = 50) -> str:
    """Tails local LM Studio C++ log output to diagnose connection/OOM/context errors."""
    print(f"📖 [LOG DIAGNOSTIC] Reading LM Studio main log tail ({lines} lines)...")
    if not os.path.exists(LM_STUDIO_MAIN_LOG):
        return json.dumps({"status": "FAILED", "error": f"LM Studio log not found: {LM_STUDIO_MAIN_LOG}"})
    try:
        with open(LM_STUDIO_MAIN_LOG, "r", encoding="utf-8", errors="ignore") as f:
            content_lines = f.readlines()
        tail = content_lines[-min(len(content_lines), lines):]
        return json.dumps({
            "status": "SUCCESS",
            "log_path": LM_STUDIO_MAIN_LOG,
            "total_lines": len(content_lines),
            "tail": "".join(tail)
        })
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": str(e)})

def read_hardware_config() -> str:
    """Reads LM Studio internal hardware-config.json specifying GPU offloads and memory configs."""
    print(f"🔍 [HARDWARE CONFIG] Reading internal configuration: {HARDWARE_CONFIG_PATH}")
    if not os.path.exists(HARDWARE_CONFIG_PATH):
        return json.dumps({"status": "FAILED", "error": "hardware-config.json does not exist. Server is using system defaults."})
    try:
        with open(HARDWARE_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return json.dumps({"status": "SUCCESS", "path": HARDWARE_CONFIG_PATH, "config": data})
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": str(e)})

def write_hardware_config(config_content: str) -> str:
    """Safely validates JSON syntax and overwrites LM Studio internal hardware-config.json."""
    print(f"💾 [HARDWARE CONFIG] Overwriting internal configuration: {HARDWARE_CONFIG_PATH}")
    try:
        parsed_json = json.loads(config_content)
        os.makedirs(LM_STUDIO_INTERNAL_DIR, exist_ok=True)
        with open(HARDWARE_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(parsed_json, f, indent=2)
        return json.dumps({"status": "SUCCESS", "message": f"Successfully updated hardware config at {HARDWARE_CONFIG_PATH}"})
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": f"JSON syntax error or file write failure: {str(e)}"})

def read_mcp_configs() -> str:
    """Searches and aggregates all available local MCP settings and configurations."""
    print("📁 [MCP CONFIG] Scanning known folders for active MCP configs...")
    configs = {}
    for path in MCP_CONFIG_PATHS:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    configs[path] = json.load(f)
            except Exception as e:
                configs[path] = {"error": f"Read/Parse failure: {str(e)}"}
    if not configs:
        return json.dumps({"status": "FAILED", "message": "No active MCP configuration files found on disk."})
    return json.dumps({"status": "SUCCESS", "configs_found": list(configs.keys()), "data": configs})

def write_mcp_config(target_path: str, config_content: str) -> str:
    """Validates JSON structure and writes back corrected settings for active MCP servers."""
    print(f"💾 [MCP CONFIG] Writing validated settings to: {target_path}")
    try:
        parsed_json = json.loads(config_content)
        parent_dir = os.path.dirname(target_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(parsed_json, f, indent=2)
        return json.dumps({"status": "SUCCESS", "message": f"MCP configuration safely written to {target_path}"})
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": f"Invalid JSON format or write permission failure: {str(e)}"})

def safe_list_directory(path: str = "") -> str:
    """Safely lists files and folders in the target workspace to prevent directory loops."""
    target_path = os.path.join(TARGET_DIR, path) if path else TARGET_DIR
    if not os.path.exists(target_path):
        return json.dumps({"status": "FAILED", "error": f"Path '{path}' not found."})
    if not os.path.isdir(target_path):
        return json.dumps({"status": "FAILED", "error": f"'{path}' is a file, not a directory."})
    try:
        items = os.listdir(target_path)
        details = []
        for item in items:
            item_full_path = os.path.join(target_path, item)
            is_dir = os.path.isdir(item_full_path)
            details.append({
                "name": item,
                "type": "directory" if is_dir else "file",
                "size_bytes": os.path.getsize(item_full_path) if not is_dir else 0
            })
        return json.dumps({"status": "SUCCESS", "current_dir": path, "contents": details}, indent=2)
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": str(e)})

def safe_read_file(filepath: str) -> str:
    """Reads file content but checks for directory state first to eliminate EISDIR errors."""
    target_path = os.path.join(TARGET_DIR, filepath) if not os.path.isabs(filepath) else filepath
    if not os.path.exists(target_path):
        return json.dumps({"status": "FAILED", "error": f"File '{filepath}' not found."})
    if os.path.isdir(target_path):
        return json.dumps({
            "status": "FAILED", 
            "error": f"'{filepath}' is a directory. Use list_directory to see its contents instead of read_file."
        })
    try:
        with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return json.dumps({"status": "SUCCESS", "filepath": filepath, "content": content})
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": str(e)})

def execute_preflight_and_write(filename: str, code_content: str) -> str:
    """AST compile validation with auto-repair of Markdown dunder bolding."""
    print(f"\n🔍 [PRE-FLIGHT] Verifying script '{filename}'...")
    
    # Auto-Heal markdown Bold manglings (e.g. **name** -> __name__, **main** -> __main__)
    repaired_code = re.sub(r'\*+([a-zA-Z0-9_]+)\*+', r'__\1__', code_content)
    repaired_code = repaired_code.replace("**name**", "__name__").replace("**main**", "__main__")
    
    if repaired_code != code_content:
        print("⚡ [AUTO-HEALER] Repaired Markdown dunder bold-mangling successfully!")

    if not HAS_MONTY:
        filepath = os.path.join(TARGET_DIR, filename) if not os.path.isabs(filename) else filename
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
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
                
        filepath = os.path.join(TARGET_DIR, filename) if not os.path.isabs(filename) else filename
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
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

def safe_find_files(pattern: str, search_path: str = "") -> str:
    """Finds files matching a regex pattern, fully resolving paths to prevent string errors."""
    base_path = os.path.join(TARGET_DIR, search_path) if search_path else TARGET_DIR
    if not os.path.exists(base_path):
        return json.dumps({"status": "FAILED", "error": f"Search path '{search_path}' not found."})
    
    matches = []
    try:
        regex = re.compile(pattern, re.IGNORECASE)
        for root, dirs, files in os.walk(base_path):
            dirs[:] = [d for d in dirs if d.lower() not in [".venv", "node_modules", ".git", "venv", "__pycache__"]]
            for file in files:
                if regex.search(file):
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, TARGET_DIR)
                    matches.append({
                        "name": file,
                        "relative_path": rel_p,
                        "size_bytes": os.path.getsize(full_p)
                    })
        return json.dumps({"status": "SUCCESS", "matches": matches}, indent=2)
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": str(e)})


# =============================================================================
# 2. OPENAI-COMPATIBLE TOOL SCHEMA & DISPATCH ROUTER
# =============================================================================

TOOL_METADATA = [
    {
        "type": "function",
        "function": {
            "name": "safe_list_directory",
            "description": "Lists contents of a folder in your workspace safely. Use this to find available folders/files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from workspace root. Defaults to empty (root)."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "safe_read_file",
            "description": "Reads raw contents of a target file. DO NOT call on directories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Relative path of the target file."}
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_verified_code",
            "description": "Writes code safely to disk, auto-creating nested folders and running pre-flight verification inside Monty VM.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Relative path of file to create/overwrite."},
                    "code_content": {"type": "string", "description": "The raw code block to write."}
                },
                "required": ["filename", "code_content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "safe_find_files",
            "description": "Searches the directory tree for files matching a specific text pattern/name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Search pattern (regex/substring) for filename."},
                    "search_path": {"type": "string", "description": "Folder to search in. Defaults to workspace root."}
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_mcp_configs",
            "description": "Locates and reads all local and AppData MCP configuration files (mcp.json) on disk."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_mcp_config",
            "description": "Writes a clean, validated JSON config file back to any specified target MCP path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_path": {"type": "string", "description": "Absolute destination path for the MCP config."},
                    "config_content": {"type": "string", "description": "Validated JSON configuration string."}
                },
                "required": ["target_path", "config_content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_hardware_config",
            "description": "Reads LM Studio's active internal hardware configurations (GPU layers, VRAM cap, KV offload)."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_lmstudio_logs",
            "description": "Tails the main C++ engine log to inspect memory errors, context bounds, or engine failures.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lines": {"type": "integer", "description": "Number of lines of tail log.", "default": 50}
                }
            }
        }
    }
]

def dispatch_tool(name: str, arguments: dict) -> str:
    try:
        if name == "safe_list_directory":
            return safe_list_directory(arguments.get("path", ""))
        elif name == "safe_read_file":
            return safe_read_file(arguments["filepath"])
        elif name == "write_verified_code":
            return execute_preflight_and_write(arguments["filename"], arguments["code_content"])
        elif name == "safe_find_files":
            return safe_find_files(arguments["pattern"], arguments.get("search_path", ""))
        elif name == "read_mcp_configs":
            return read_mcp_configs()
        elif name == "write_mcp_config":
            return write_mcp_config(arguments["target_path"], arguments["config_content"])
        elif name == "read_hardware_config":
            return read_hardware_config()
        elif name == "read_lmstudio_logs":
            return read_lmstudio_logs(arguments.get("lines", 50))
        else:
            return json.dumps({"error": f"Unknown tool '{name}'"})
    except Exception as e:
        return json.dumps({"error": str(e)})


# =============================================================================
# 3. INTERACTIVE AUTONOMOUS CONTROL LOOP
# =============================================================================

# The strict output instruction for the local model
AUTONOMOUS_TASK_PROMPT = """
TASK: Autonomously audit the workstation environment, verify active database tables, and write/compile the zero-dependency RAG-v2 JavaScript extension files.

CRITICAL OPERATIONAL FLOW:
1. Scan loopback sockets and active processes to confirm Port 8001 is listening.
2. Interrogate the relational DuckDB store schemas and LanceDB vector table row counts.
3. Read the existing entrypoint script at 'rag-v2/index.js' to identify any lingering native imports.
4. Replace native database imports with HTTP loopback fetches pushing to Port 8001.
5. Save and compile-verify the finalized JavaScript code inside the Monty Rust VM.

STRICT OUTPUT CONSTRAINTS (CODE & CONFIRMATIONS ONLY):
- Do NOT provide conversational preambles, introductory summaries, or meta-commentary.
- Do NOT write general explanations of how the code works.
- Output ONLY:
  1. A Markdown table of active ports and processes.
  2. A Markdown table of confirmed DuckDB and LanceDB schemas.
  3. The final, syntax-verified JavaScript code blocks for 'DuckDBService.js' and 'index.js'.
  4. The exact '[SUCCESS]' compiler and pre-flight validation status from Monty.
"""

def execute_autonomous_run():
    print("=" * 80)
    print("🚀 DISPATCHING AUTONOMOUS WORKFLOW TO C++ INFERENCE KERNEL")
    print("=" * 80)

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert systems developer operating with physical workspace tools. "
                "You must execute tools in sequence to investigate, write, and verify code. "
                "Do not talk. Do not explain. Run your tools, verify compile status, and return "
                "nothing but clean Markdown tables of system state and the finalized, verified code blocks."
            )
        },
        {"role": "user", "content": AUTONOMOUS_TASK_PROMPT}
    ]

    for turn in range(8):
        print(f"\n📡 [TURN {turn+1}] Querying local model on Port {ACTIVE_PORT}...")
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                tools=TOOL_METADATA,
                temperature=0.0,
                seed=42,
                max_tokens=2500
            )
        except Exception as e:
            print(f"❌ Failed to query local model on Port {ACTIVE_PORT}: {e}")
            break

        choice = response.choices[0] if response.choices else None
        if not choice:
            break

        message = choice.message
        content = message.content or ""
        reasoning = getattr(message, "reasoning_content", "") or ""

        if reasoning:
            print(f"\n💭 [THOUGHTS] {reasoning}")
        elif content.strip():
            print(f"\n💬 [ASSISTANT]\n{content}")

        assistant_msg = {"role": "assistant", "content": content}
        if message.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in message.tool_calls
            ]
        messages.append(assistant_msg)

        if not message.tool_calls:
            print("\n🏁 [COMPLETE] Autonomous loop finalized!")
            break

        # Execute Tool Calls
        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
            
            print(f"🔨 [TOOL CALL] Executing '{name}' with args: {args}")
            tool_output = dispatch_tool(name, args)
            print(f"📥 [TOOL OUTPUT] Returned (snippet): {tool_output[:250]}...")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_output
            })

if __name__ == "__main__":
    execute_autonomous_run()
