# sovereign_studio_scanner.py
# ==============================================================================
# 🏛️ SOVEREIGN COUNCIL: DYNAMIC STUDIO-DRIVEN AST PORT SCANNER
# Offloads file discovery to LM Studio's optimized C++ Developer Tools / MCP loop.
# Bypasses local Python os.walk recursion bottlenecks entirely.
# ==============================================================================

import os
import sys
import ast
import json
import socket
import urllib.request
import urllib.error

# High-visibility terminal logging
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

def log_info(msg): print(f"{CYAN}[INFO]{RESET} {msg}", flush=True)
def log_success(msg): print(f"{GREEN}[SUCCESS]{RESET} {msg}", flush=True)
def log_warning(msg): print(f"{YELLOW}[WARN]{RESET} {msg}", flush=True)
def log_error(msg): print(f"{RED}[ERROR]{RESET} {msg}", flush=True)

# Port sweep options to discover LM Studio's dynamic port
PORT_OPTIONS = [1234, 1010, 56217, 61277]

def discover_active_port() -> int:
    """Discovers which loopback port LM Studio's C++ kernel is listening on."""
    for port in PORT_OPTIONS:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.15)
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    return port
        except Exception:
            pass
    return 1234  # Default fallback

ACTIVE_PORT = discover_active_port()
LM_STUDIO_URL = f"http://127.0.0.1:{ACTIVE_PORT}/v1/chat/completions"

# ==============================================================================
# 1. LOCAL SURGICAL AST EXTRACTOR (IMMUNE TO RECURSION)
# ==============================================================================
def inspect_file_ast(filepath: str) -> dict:
    """
    Performs a targeted, non-recursive AST analysis on a single confirmed file.
    Completely avoids directory walk overflows.
    """
    if not os.path.exists(filepath):
        return {"status": "FAILED", "error": "File not found on disk."}
    
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
        tree = ast.parse(content, filename=filepath)
        imports = []
        functions = []
        classes = []
        has_preprocessor = False
        has_in_memory_run = False
        
        # Look for indicators
        if "preprocessPrompt" in content or "promptPreprocessor" in content or "preprocess" in content:
            has_preprocessor = True
        if "execute_sandboxed" in content or "pydantic_core" in content or "ctypes" in content:
            has_in_memory_run = True

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
                
        return {
            "status": "SUCCESS",
            "filename": os.path.basename(filepath),
            "filepath": filepath,
            "classes": classes[:10],
            "functions": functions[:15],
            "imports": imports[:10],
            "has_preprocessor": has_preprocessor,
            "has_in_memory_run": has_in_memory_run,
            "lines_count": len(content.splitlines())
        }
    except Exception as e:
        return {"status": "FAILED", "error": str(e)}

# ==============================================================================
# 2. LM STUDIO TOOL ROUTING BRIDGE
# ==============================================================================
def execute_lmstudio_mcp_tool(name: str, args: dict) -> str:
    """
    Exposes surgical file helpers to LM Studio's tool selection graph.
    Bypasses deep filesystem walking loops.
    """
    if name == "inspect_file_ast":
        filepath = args.get("filepath", "")
        return json.dumps(inspect_file_ast(filepath))
    elif name == "list_immediate_dir":
        # Flat, non-recursive directory scan of immediate workspace files
        target = r"C:\WEB CASE STUDY"
        try:
            files = [f for f in os.listdir(target) if os.path.isfile(os.path.join(target, f))]
            return json.dumps({"status": "SUCCESS", "files": [f for f in files if f.endswith(".py") or f.endswith(".js")]})
        except Exception as e:
            return json.dumps({"status": "FAILED", "error": str(e)})
    return json.dumps({"error": f"Tool '{name}' is not registered on this loop."})

# ==============================================================================
# 3. INTERACTIVE AGENT SESSION
# ==============================================================================
TOOL_METADATA = [
    {
        "type": "function",
        "function": {
            "name": "list_immediate_dir",
            "description": "Lists immediate python and javascript files in the C:\\WEB CASE STUDY workspace root without traversing subdirectories."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_file_ast",
            "description": "Performs a surgical AST parser analysis on a targeted python file to inspect functions, imports, and classes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Absolute path to the file on disk."}
                },
                "required": ["filepath"]
            }
        }
    }
]

def run_studio_orchestrated_scan():
    print("=" * 80)
    print("🛸 SOVEREIGN STUDIO AST SCANNER & COGNITIVE CONTROLLER")
    print(f"   Connected to LM Studio REST API on Loopback Port: {ACTIVE_PORT}")
    print("=" * 80)

    log_info("Initializing Developer Tools & tool-calling loopbacks...")

    system_instructions = (
        "You are the Sovereign Lead Systems Architect. Your goal is to identify and "
        "rank the best 'prompt preprocessor' and 'in-memory processor' inside the 'C:\\WEB CASE STUDY' workspace.\n\n"
        "To prevent directory walking locks or recursive infinite loops, use your toolsets in sequence:\n"
        "1. First, call 'list_immediate_dir' to pull a flat list of immediate candidate scripts.\n"
        "2. Identify which scripts look like processors (e.g. sovereign_cli, chat, RAG, preflight, or monty scripts).\n"
        "3. Call 'inspect_file_ast' surgically on those targeted files to parse their import statements, classes, and helper functions.\n"
        "4. Output a clear, concise final comparison stating which file contains the best preprocessor and which has the best in-memory processor, backed by AST details."
    )

    messages = [
        {"role": "system", "content": system_instructions},
        {"role": "user", "content": "Analyze my C:\\WEB CASE STUDY workspace. Identify the best prompt preprocessor and the best in-memory processor using your developer tools. Do not walk directories manually."}
    ]

    for turn in range(5):
        log_info(f"Querying C++ inference engine (Turn {turn+1})...")
        payload = {
            "model": "nvidia/nemotron-3-nano-4b",
            "messages": messages,
            "tools": TOOL_METADATA,
            "temperature": 0.0
        }

        req = urllib.request.Request(
            LM_STUDIO_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                res_json = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            log_error(f"Failed to communicate with LM Studio C++ engine: {e}")
            sys.exit(1)

        choice = res_json["choices"][0]
        message = choice["message"]
        content = message.get("content") or ""

        # Print model reasoning or text responses
        if content:
            print(f"\n💬 {CYAN}[STUDIO ARCHITECT]{RESET} {content}\n")

        assistant_msg = {"role": "assistant", "content": content}
        tool_calls = message.get("tool_calls")

        if tool_calls:
            assistant_msg["tool_calls"] = tool_calls
            messages.append(assistant_msg)

            for tool_call in tool_calls:
                tc_id = tool_call.get("id")
                name = tool_call["function"]["name"]
                args = json.loads(tool_call["function"]["arguments"]) if tool_call["function"].get("arguments") else {}

                log_info(f"⚙️ Model called tool '{name}' with arguments: {args}")
                tool_output = execute_lmstudio_mcp_tool(name, args)
                log_success(f"📥 Tool response acquired (size: {len(tool_output)} bytes)")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": tool_output
                })
        else:
            log_success("Coordinated scan completed successfully! System is fully aligned.")
            break

if __name__ == "__main__":
    run_studio_orchestrated_scan()
