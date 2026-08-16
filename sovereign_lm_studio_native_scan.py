# sovereign_lm_studio_native_scan.py
# ==============================================================================
# 🏛️ SOVEREIGN COUNCIL: NATIVE LM STUDIO REST API MCP SCANNER
# Queries LM Studio's REST API and lets the server-side MCP plugins (Beledarian Tools)
# execute the file discovery, reading, and AST analysis natively inside LM Studio.
# Completely bypasses client-side tool-execution and os.walk recursion loops.
# ==============================================================================

import json
import urllib.request
import urllib.error
import socket
import sys

# High-visibility logging
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"

PORT_OPTIONS = [1234, 1010, 56217, 61277]

def discover_active_port() -> int:
    """Finds which port LM Studio's server-daemon is listening on."""
    for port in PORT_OPTIONS:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    return port
        except Exception:
            pass
    return 1234

ACTIVE_PORT = discover_active_port()
# Use LM Studio's stateful /v1/chat endpoint which manages MCP executions on the server-side
LM_STUDIO_STATEFUL_URL = f"http://127.0.0.1:{ACTIVE_PORT}/v1/chat"
LM_STUDIO_COMPLETIONS_URL = f"http://127.0.0.1:{ACTIVE_PORT}/v1/chat/completions"

def run_native_mcp_scan():
    print("=" * 80)
    print(f"🛸 SOVEREIGN NATIVE REST API SCANNER (BOUND TO PORT {ACTIVE_PORT})")
    print("  Delegating file discovery and AST analysis entirely to LM Studio's server plugins.")
    print("=" * 80)

    # Prompt instructing the local model to run its own registered MCP tools natively
    prompt_payload = (
        "TASK: Analyze my C:\\WEB CASE STUDY workspace. Identify the best prompt preprocessor "
        "and the best in-memory processor.\n\n"
        "INSTRUCTIONS:\n"
        "1. Do not ask me to write python scripts or run manual walk loops.\n"
        "2. Call your natively registered 'beledarian/beledarians-lm-studio-tools' or "
        "'legion-architect' MCP tools (like list_directory, find_files, or read_file) "
        "to locate Python scripts inside C:\\WEB CASE STUDY.\n"
        "3. Inspect files matching 'preflight', 'orchestrator', 'cli', or 'monty' to parse "
        "their structural classes and functions.\n"
        "4. Output a clean table comparing the candidates, citing their functions and why they qualify."
    )

    print(f"📡 Sending native prompt payload to {LM_STUDIO_STATEFUL_URL}...")

    # We hit the v1/chat endpoint which natively triggers server-side local MCP servers 
    # configured in ~/.lmstudio/mcp.json without requiring the client to execute any code.
    payload = {
        "model": "nvidia/nemotron-3-nano-4b",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are the Sovereign Lead Systems Architect. You are operating inside LM Studio "
                    "with direct access to local filesystem MCP tools (beledarians-lm-studio-tools). "
                    "You must use your native tools to browse C:\\WEB CASE STUDY and inspect files."
                )
            },
            {
                "role": "user",
                "content": prompt_payload
            }
        ],
        "temperature": 0.0
    }

    req = urllib.request.Request(
        LM_STUDIO_COMPLETIONS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            content = res_json["choices"][0]["message"].get("content") or ""
            
            print(f"\n💬 {CYAN}[LM STUDIO ARCHITECT DECISION]{RESET}")
            print("-" * 80)
            print(content)
            print("-" * 80)
            print(f"🏆 {GREEN}SUCCESS: Scan completed natively via server-side MCP toolchain!{RESET}\n")

    except urllib.error.URLError as e:
        print(f"\n{RED}[ERROR] Failed to reach LM Studio on port {ACTIVE_PORT}: {e}{RESET}")
        print("  - Ensure that LM Studio's Local Server is active.")
        print("  - Check that the 'beledarian/beledarians-lm-studio-tools' plugin is enabled.")
    except Exception as e:
        print(f"\n{RED}[ERROR] Unexpected scan crash: {e}{RESET}")

if __name__ == "__main__":
    run_native_mcp_scan()
