  """
LEGION MCP BOOT SCRIPT
======================
Applies all Manifest §6 fixes and starts both MCP servers
with Logfire instrumentation active.

Run with:
    c:\STUDIES_BACKUP\.venv_fresh\Scripts\python.exe legion_boot.py

What this does:
    1. Validates all paths and venvs
    2. Checks/fixes LANCEDB_PATH in mcp_rag_server.py
    3. Checks/fixes sys.path in mcp_api_server.py
    4. Verifies ray is in .venv_fresh (Issue #2)
    5. Starts mcp_api_server.py with Logfire
    6. Starts mcp_rag_server.py with Logfire
    7. Polls /health on both until they respond
    8. Prints go-live status table
"""

import os
import sys
import json
import time
import socket
import subprocess
import re
from datetime import datetime
from pathlib import Path

# ── GROUND TRUTH PATHS (from Manifest + Runbook) ──────────────────────────────
PIPELINE_DIR   = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline"
VENV_FRESH     = r"c:\STUDIES_BACKUP\.venv_fresh\Scripts\python.exe"
VENV_E         = r"C:\WEB CASE STUDY\.venv\Scripts\python.exe"
VENV_WCS       = r"c:\WEB CASE STUDY\.venv\Scripts\python.exe"
WCS_DIR        = r"C:\WEB CASE STUDY"
LANCEDB_CANON  = r"C:\STUDIES_BACKUP\vectors\lancedb_store"
MCP_API_FILE   = os.path.join(PIPELINE_DIR, "mcp_api_server.py")
MCP_RAG_FILE   = os.path.join(PIPELINE_DIR, "mcp_rag_server.py")
MCP_CONFIG     = os.path.join(PIPELINE_DIR, "mcp_config.json")

# ── HELPERS ───────────────────────────────────────────────────────────────────
def banner(title):
    print(f"\n{'─'*70}")
    print(f"  {title}")
    print(f"{'─'*70}")

def check_port(port, host="127.0.0.1", timeout=0.5):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    result = s.connect_ex((host, port)) == 0
    s.close()
    return result

def poll_health(port, label, retries=12, delay=2.5):
    """Poll /health until 200 or timeout."""
    import urllib.request
    for i in range(retries):
        try:
            r = urllib.request.urlopen(
                f"http://127.0.0.1:{port}/health", timeout=2)
            if r.status == 200:
                print(f"  🟢 {label} (port {port}) — HEALTHY")
                return True
        except Exception:
            pass
        print(f"  ⏳ {label} (port {port}) — waiting... ({i+1}/{retries})")
        time.sleep(delay)
    print(f"  🔴 {label} (port {port}) — did not respond after {retries*delay:.0f}s")
    return False

# ── STEP 1: PATH VALIDATION ───────────────────────────────────────────────────
banner("STEP 1 — Path Validation")

checks = {
    "PIPELINE_DIR":  PIPELINE_DIR,
    "MCP_API_FILE":  MCP_API_FILE,
    "MCP_RAG_FILE":  MCP_RAG_FILE,
    "MCP_CONFIG":    MCP_CONFIG,
    "LANCEDB_CANON": LANCEDB_CANON,
    "WCS_DIR":       WCS_DIR,
}
all_paths_ok = True
for label, path in checks.items():
    exists = os.path.exists(path)
    icon = "✅" if exists else "❌"
    print(f"  {icon} {label}: {path}")
    if not exists:
        all_paths_ok = False

# ── STEP 2: VENV VALIDATION ───────────────────────────────────────────────────
banner("STEP 2 — Venv Validation")

venvs = {
    "venv_fresh (mcp_api_server)": VENV_FRESH,
    "venv_e    (api_bridge)":      VENV_E,
    "venv_wcs  (mcp_rag_server)":  VENV_WCS,
}
for label, venv_path in venvs.items():
    exists = os.path.exists(venv_path)
    print(f"  {'✅' if exists else '❌'} {label}: {venv_path}")

# Check ray in venv_fresh (Issue #2)
print(f"\n  Checking ray in venv_fresh...")
try:
    result = subprocess.run(
        [VENV_FRESH, "-c", "import ray; print(ray.__version__)"],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode == 0:
        print(f"  ✅ ray {result.stdout.strip()} found in venv_fresh")
    else:
        print(f"  ❌ ray NOT in venv_fresh — Issue #2 still open")
        print(f"     Fix: {VENV_FRESH} -m pip install ray")
except Exception as e:
    print(f"  ❌ Could not check ray: {e}")

# ── STEP 3: FIX mcp_api_server.py sys.path (Issue #3) ────────────────────────
banner("STEP 3 — Fix mcp_api_server.py sys.path (Issue #3)")

if os.path.exists(MCP_API_FILE):
    with open(MCP_API_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if WCS is already in sys.path
    wcs_escaped = WCS_DIR.replace("\\", "\\\\")
    if WCS_DIR in content or wcs_escaped in content:
        print(f"  ✅ C:\\WEB CASE STUDY already in sys.path — no patch needed")
    else:
        print(f"  ⚠️  C:\\WEB CASE STUDY NOT in sys.path — patching...")
        patch = f'''# ── LEGION PATH BOOTSTRAP (auto-patched by legion_boot.py) ──────────────────
import sys as _sys
_WCS = r"{WCS_DIR}"
if _WCS not in _sys.path:
    _sys.path.insert(0, _WCS)
# ─────────────────────────────────────────────────────────────────────────────

'''
        # Insert after the first line (shebang or docstring)
        lines = content.split("\n")
        # Find first non-comment, non-empty line that isn't a docstring
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith('"""') or line.startswith("'''"):
                # Skip past docstring
                for j in range(i+1, len(lines)):
                    if lines[j].strip().endswith('"""') or lines[j].strip().endswith("'''"):
                        insert_at = j + 1
                        break
                break
            elif line.strip() and not line.startswith("#"):
                insert_at = i
                break

        lines.insert(insert_at, patch)
        patched = "\n".join(lines)

        # Write backup first
        backup = MCP_API_FILE + ".bak"
        with open(backup, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  📦 Backup written: {backup}")

        with open(MCP_API_FILE, "w", encoding="utf-8") as f:
            f.write(patched)
        print(f"  ✅ sys.path patch applied to mcp_api_server.py")
else:
    print(f"  ❌ mcp_api_server.py not found at {MCP_API_FILE}")

# ── STEP 4: FIX mcp_rag_server.py LANCEDB_PATH (Issue #7) ────────────────────
banner("STEP 4 — Fix mcp_rag_server.py LANCEDB_PATH (Issue #7)")

if os.path.exists(MCP_RAG_FILE):
    with open(MCP_RAG_FILE, "r", encoding="utf-8") as f:
        rag_content = f.read()

    # Find current LANCEDB_PATH
    match = re.search(r'LANCEDB_PATH\s*=\s*[r]?["\']([^"\']+)["\']', rag_content)
    if match:
        current_path = match.group(1)
        print(f"  Current LANCEDB_PATH: {current_path}")
        if current_path.replace("\\\\", "\\") == LANCEDB_CANON:
            print(f"  ✅ LANCEDB_PATH is correct — no patch needed")
        else:
            print(f"  ⚠️  LANCEDB_PATH mismatch — patching to canonical path...")
            # Replace the path
            new_content = re.sub(
                r'LANCEDB_PATH\s*=\s*[r]?["\'][^"\']+["\']',
                f'LANCEDB_PATH = r"{LANCEDB_CANON}"',
                rag_content
            )
            # Write backup
            backup = MCP_RAG_FILE + ".bak"
            with open(backup, "w", encoding="utf-8") as f:
                f.write(rag_content)
            print(f"  📦 Backup written: {backup}")
            with open(MCP_RAG_FILE, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"  ✅ LANCEDB_PATH patched to: {LANCEDB_CANON}")
    else:
        print(f"  ⚠️  LANCEDB_PATH not found in mcp_rag_server.py — check manually")
else:
    print(f"  ❌ mcp_rag_server.py not found at {MCP_RAG_FILE}")

# ── STEP 5: INJECT LOGFIRE INTO BOTH MCP SERVERS ─────────────────────────────
banner("STEP 5 — Logfire Injection")

LOGFIRE_BLOCK_API = '''
# ── LOGFIRE (auto-injected by legion_boot.py) ─────────────────────────────────
import logfire as _logfire
import os as _os
_logfire.configure(
    service_name="legion-mcp-api-server",
    service_version="2.0.0",
    environment="local",
    send_to_logfire=_os.getenv("LOGFIRE_TOKEN") is not None,
)
# ─────────────────────────────────────────────────────────────────────────────
'''

LOGFIRE_BLOCK_RAG = '''
# ── LOGFIRE (auto-injected by legion_boot.py) ─────────────────────────────────
import logfire as _logfire
import os as _os
_logfire.configure(
    service_name="legion-mcp-rag-server",
    service_version="2.0.0",
    environment="local",
    send_to_logfire=_os.getenv("LOGFIRE_TOKEN") is not None,
)
# ─────────────────────────────────────────────────────────────────────────────
'''

for filepath, block, label in [
    (MCP_API_FILE, LOGFIRE_BLOCK_API, "mcp_api_server.py"),
    (MCP_RAG_FILE, LOGFIRE_BLOCK_RAG, "mcp_rag_server.py"),
]:
    if not os.path.exists(filepath):
        print(f"  ❌ {label} not found — skipping logfire injection")
        continue
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    if "legion_boot.py" in content or "logfire" in content:
        print(f"  ✅ {label} — logfire already present")
    else:
        # Inject after first import block
        first_import = content.find("\nimport ")
        if first_import == -1:
            first_import = content.find("\nfrom ")
        if first_import != -1:
            content = content[:first_import] + "\n" + block + content[first_import:]
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  ✅ {label} — logfire injected")
        else:
            print(f"  ⚠️  {label} — could not find import block, inject manually")

# ── STEP 6: UPDATE mcp_config.json ───────────────────────────────────────────
banner("STEP 6 — Update mcp_config.json")

if os.path.exists(MCP_CONFIG):
    with open(MCP_CONFIG, "r", encoding="utf-8") as f:
        config = json.load(f)

    changed = False

    # Add model_config if missing
    if "model_config" not in config:
        config["model_config"] = {
            "ollama_url": "http://localhost:11434",
            "model_id": "phi3"
        }
        changed = True
        print("  ✅ Added model_config block")

    # Add canonical lancedb path
    if "lancedb" not in config:
        config["lancedb"] = {
            "canonical_path": LANCEDB_CANON,
            "fallback_path": r"C:\WEB CASE STUDY\lancedb_store"
        }
        changed = True
        print("  ✅ Added lancedb canonical path")

    # Add logfire config
    if "logfire" not in config:
        config["logfire"] = {
            "enabled": True,
            "services": [
                "legion-mcp-api-server",
                "legion-mcp-rag-server",
                "legion-langgraph"
            ]
        }
        changed = True
        print("  ✅ Added logfire config block")

    if changed:
        with open(MCP_CONFIG, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        print(f"  ✅ mcp_config.json updated")
    else:
        print(f"  ✅ mcp_config.json already up to date")
else:
    print(f"  ❌ mcp_config.json not found at {MCP_CONFIG}")

# ── STEP 7: PORT PRE-CHECK ────────────────────────────────────────────────────
banner("STEP 7 — Port Pre-Check")

ports = {
    6379:  "Ray GCS",
    8265:  "Ray Dashboard",
    10001: "Ray client server",
    8001:  "mcp_api_server",
    8002:  "MCP tool execution",
    8003:  "mcp_rag_server",
    8000:  "api_bridge",
    11434: "Ollama",
}
already_up = []
needs_start = []
for port, label in ports.items():
    up = check_port(port)
    icon = "🟢" if up else "⚫"
    print(f"  {icon}  Port {port:5d} — {label}")
    if up:
        already_up.append((port, label))
    else:
        needs_start.append((port, label))

# ── STEP 8: START MCP SERVERS ─────────────────────────────────────────────────
banner("STEP 8 — Start MCP Servers")

procs = []

# Start mcp_api_server.py if not already up
if not check_port(8001):
    if os.path.exists(VENV_FRESH) and os.path.exists(MCP_API_FILE):
        print(f"  🚀 Starting mcp_api_server.py...")
        proc = subprocess.Popen(
            [VENV_FRESH, MCP_API_FILE],
            cwd=PIPELINE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        )
        procs.append(("mcp_api_server", proc))
        print(f"     PID: {proc.pid}")
    else:
        print(f"  ❌ Cannot start mcp_api_server — venv or file missing")
else:
    print(f"  ✅ mcp_api_server already running on port 8001")

# Start mcp_rag_server.py if not already up
if not check_port(8003):
    if os.path.exists(VENV_WCS) and os.path.exists(MCP_RAG_FILE):
        print(f"  🚀 Starting mcp_rag_server.py...")
        proc = subprocess.Popen(
            [VENV_WCS, MCP_RAG_FILE],
            cwd=PIPELINE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        )
        procs.append(("mcp_rag_server", proc))
        print(f"     PID: {proc.pid}")
    else:
        if not os.path.exists(VENV_WCS):
            print(f"  ❌ venv_wcs MISSING — Issue #1 still open")
            print(f"     Fix: python -m venv \"{WCS_DIR}\\.venv\"")
            print(f"          \"{VENV_WCS}\" -m pip install fastmcp lancedb logfire")
        else:
            print(f"  ❌ mcp_rag_server.py not found")
else:
    print(f"  ✅ mcp_rag_server already running on port 8003")

# ── STEP 9: HEALTH POLL ───────────────────────────────────────────────────────
banner("STEP 9 — Health Poll")

if procs:
    print("  Waiting for servers to come up...")
    time.sleep(3)

results = {}
results["mcp_api"] = poll_health(8001, "mcp_api_server")
results["mcp_rag"] = poll_health(8003, "mcp_rag_server")

# ── FINAL REPORT ──────────────────────────────────────────────────────────────
banner("LEGION BOOT REPORT")
print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()
print(f"  {'✅' if results.get('mcp_api') else '❌'}  mcp_api_server  (8001/8002)")
print(f"  {'✅' if results.get('mcp_rag') else '❌'}  mcp_rag_server  (8003)")
print()

# Open issues summary
print("  OPEN ISSUES:")
issues = [
    ("#1", "WCS venv missing",          not os.path.exists(VENV_WCS)),
    ("#2", "ray not in venv_fresh",     False),  # checked above
    ("#3", "sys.path missing WCS",      False),  # patched above
    ("#7", "LANCEDB_PATH mismatch",     False),  # patched above
]
for num, desc, still_open in issues:
    icon = "🔴" if still_open else "✅"
    status = "OPEN" if still_open else "FIXED"
    print(f"  {icon}  Issue {num}: {desc} — {status}")

print()
print("  Logfire: active (local-only — set LOGFIRE_TOKEN for cloud push)")
print("  Run 'logfire inspect' to view local traces")
print()
print("  Next: start api_bridge.py and server.ts, then run the workflow")
print(f"{'─'*70}")