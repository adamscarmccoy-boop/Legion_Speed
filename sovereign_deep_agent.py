"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  SOVEREIGN DEEP AGENT v2 — Monty Sandbox + Jinja2 + Streaming              ║
║  LLM is the BRAIN. Tools are the HANDS. Monty is the SANDBOX.              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import time
import sys
import os
import importlib
import platform
import traceback
from pathlib import Path

from openai import OpenAI
from jinja2 import Environment, BaseLoader
from pydantic_monty import Monty, CollectString, MountDir, MontyError, ResourceLimits

# ═══════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════
VENV_ROOT       = r"C:\WEB CASE STUDY\.venv"
SITE_PACKAGES   = os.path.join(VENV_ROOT, "Lib", "site-packages")
WORKSPACE       = r"C:\WEB CASE STUDY"
TOKEN_BUDGET    = 50000
APPROX_CHARS_PER_TOKEN = 4
MAX_TURNS       = 20
MAX_TOOL_RESPONSE_CHARS = 4000  # cap tool output to prevent budget blowout

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)
LLM_MODEL = "nvidia/nemotron-3-nano-4b"

# ═══════════════════════════════════════════════════════════════════════════
# MONTY SANDBOX — subprocess-isolated Python execution
# ═══════════════════════════════════════════════════════════════════════════
monty_pool = None

def init_monty():
    global monty_pool
    monty_pool = Monty(
        min_processes=1,
        max_processes=2,
        request_timeout=30.0,
    )
    monty_pool.__enter__()
    return monty_pool

def shutdown_monty():
    global monty_pool
    if monty_pool:
        monty_pool.__exit__(None, None, None)
        monty_pool = None

def run_in_monty(code_str):
    """Execute code in the Monty sandbox with read-only access to site-packages."""
    collector = CollectString()
    
    mounts = [
        MountDir(
            host_path=SITE_PACKAGES,
            virtual_path="/site-packages",
            mode="read-only",
        ),
        MountDir(
            host_path=WORKSPACE,
            virtual_path="/workspace",
            mode="read-only",
        ),
    ]
    
    limits = ResourceLimits(
        max_duration_secs=15.0,
        max_memory=256 * 1024 * 1024,  # 256MB
        max_recursion_depth=100,
    )
    
    try:
        with monty_pool.checkout(limits=limits) as session:
            result = session.feed_run(
                code_str,
                print_callback=collector,
                mount=mounts,
            )
            return json.dumps({
                "status": "SUCCESS",
                "output": collector.output,
                "return_value": repr(result) if result is not None else None,
            }, indent=2)
    except MontyError as e:
        return json.dumps({
            "status": "ERROR",
            "error_type": type(e).__name__,
            "error": str(e),
            "output": collector.output,
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "CRASH",
            "error_type": type(e).__name__,
            "error": str(e),
        }, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
# JINJA2 PROMPT TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════
jinja_env = Environment(loader=BaseLoader(), trim_blocks=True, lstrip_blocks=True)

SYSTEM_TEMPLATE = jinja_env.from_string("""
You are SOVEREIGN ANALYST — a diagnostic intelligence connected to a live Python environment via external service endpoints.

You DO NOT execute code yourself. You REQUEST information from external diagnostic services, and they return real results from the live environment.

## YOUR ENVIRONMENT
- Python {{ python_version }} on {{ platform_name }}
- Virtual environment: {{ venv_root }}
- Site-packages: {{ site_packages }}
- Workspace: {{ workspace }}

## YOUR MISSION
The user has reported that **lancedb** and **duckdb** have issues in this environment.
Your job:
1. Query the diagnostic services to inspect these packages
2. Check what versions are installed, whether they import cleanly, and what errors occur
3. Run diagnostic code through the sandbox service to test specific hypotheses
4. Check for ghost files, corrupt installs, version conflicts
5. Produce a REPAIR PLAN with exact pip commands

## AVAILABLE SERVICES
You have access to these external diagnostic endpoints. Use them systematically:
- `check_module_health` — Tests if a Python module imports successfully
- `inspect_directory` — Lists files inside a package folder on disk
- `get_package_metadata` — Reads pip dist-info for version, deps
- `find_ghost_files` — Compares RECORD manifest vs actual files on disk
- `scan_corrupt_dirs` — Finds tilde-prefixed (~) leftover directories
- `get_system_info` — Reports RAM, CPU, disk, Python version
- `run_diagnostic_code` — Executes Python code in an isolated sandbox and returns output
- `write_report` — Writes your final findings to DIAGNOSTIC_REPORT.md

## RULES
- Call services one at a time. Wait for results before deciding next step.
- Start with check_module_health on duckdb and lancedb.
- Use run_diagnostic_code to test specific imports and operations.
- When done, call write_report with your complete findings and repair steps.
- End your final message with SOVEREIGN_COMPLETE.
""")

REFLECTION_TEMPLATE = jinja_env.from_string("""
Turn {{ turn }}/{{ max_turns }} | ~{{ tokens_used }}/{{ token_budget }} tokens used.
Services called: {{ tools_called | join(', ') }}
Keep investigating or call write_report if you have enough data.
""")

# ═══════════════════════════════════════════════════════════════════════════
# REAL DIAGNOSTIC TOOLS
# ═══════════════════════════════════════════════════════════════════════════

def check_module_health(module_name):
    result = {"module": module_name}
    try:
        mod = importlib.import_module(module_name)
        result["status"] = "HEALTHY"
        result["location"] = getattr(mod, "__file__", "built-in")
        result["version"] = getattr(mod, "__version__", "unknown")
        attrs = [a for a in dir(mod) if not a.startswith("__")]
        result["public_attributes"] = len(attrs)
        result["sample_attrs"] = attrs[:15]
    except Exception as e:
        result["status"] = "BROKEN"
        result["error_type"] = type(e).__name__
        result["error"] = str(e)
        tb = traceback.format_exc()
        result["traceback_tail"] = tb.strip().split("\n")[-5:]
    return json.dumps(result, indent=2)


def inspect_directory(path, max_depth=2):
    result = {"path": path, "entries": []}
    try:
        p = Path(path)
        if not p.exists():
            result["status"] = "NOT_FOUND"
            return json.dumps(result, indent=2)
        result["status"] = "EXISTS"
        items = sorted(p.iterdir())
        result["total_items"] = len(items)
        for item in items[:80]:  # cap at 80 entries to avoid blowout
            entry = {"name": item.name, "type": "DIR" if item.is_dir() else "FILE"}
            if item.is_file():
                entry["size_bytes"] = item.stat().st_size
            elif item.is_dir() and max_depth > 1:
                children = list(item.iterdir())
                entry["child_count"] = len(children)
                entry["children_sample"] = [c.name for c in sorted(children)[:10]]
            result["entries"].append(entry)
    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = str(e)
    return json.dumps(result, indent=2)


def get_package_metadata(package_name):
    result = {"package": package_name}
    try:
        from importlib.metadata import metadata as get_metadata
        meta = get_metadata(package_name)
        result["status"] = "INSTALLED"
        result["version"] = meta["Version"]
        result["summary"] = meta.get("Summary", "N/A")
        result["requires_python"] = meta.get("Requires-Python", "N/A")
        requires = meta.get_all("Requires-Dist") or []
        result["dependencies"] = requires[:20]
    except Exception as e:
        result["status"] = "NOT_FOUND"
        result["error"] = str(e)
    return json.dumps(result, indent=2)


def find_ghost_files(package_name):
    pkg_dir = os.path.join(SITE_PACKAGES, package_name)
    dist_dirs = [d for d in os.listdir(SITE_PACKAGES)
                 if d.startswith(f"{package_name}-") and d.endswith(".dist-info")]
    result = {"package": package_name, "dist_info_dirs": dist_dirs}

    if not dist_dirs:
        result["status"] = "NO_DIST_INFO"
        return json.dumps(result, indent=2)

    record_path = os.path.join(SITE_PACKAGES, dist_dirs[0], "RECORD")
    if not os.path.exists(record_path):
        result["status"] = "NO_RECORD"
        return json.dumps(result, indent=2)

    with open(record_path, "r", encoding="utf-8", errors="replace") as f:
        record_files = set()
        for line in f:
            parts = line.strip().split(",")
            if parts:
                record_files.add(parts[0].replace("/", os.sep))

    actual_files = set()
    if os.path.isdir(pkg_dir):
        for root, dirs, files in os.walk(pkg_dir):
            for fn in files:
                rel = os.path.relpath(os.path.join(root, fn), SITE_PACKAGES)
                actual_files.add(rel)

    ghosts = actual_files - record_files
    missing = set()
    for rf in record_files:
        if rf.startswith(package_name + os.sep):
            if not os.path.exists(os.path.join(SITE_PACKAGES, rf)):
                missing.add(rf)

    result["status"] = "SCANNED"
    result["record_count"] = len(record_files)
    result["actual_count"] = len(actual_files)
    result["ghost_files"] = sorted(list(ghosts))[:25]
    result["ghost_count"] = len(ghosts)
    result["missing_files"] = sorted(list(missing))[:25]
    result["missing_count"] = len(missing)
    return json.dumps(result, indent=2)


def scan_corrupt_dirs():
    corrupt = []
    for entry in os.listdir(SITE_PACKAGES):
        if entry.startswith("~"):
            full = os.path.join(SITE_PACKAGES, entry)
            size = sum(f.stat().st_size for f in Path(full).rglob("*") if f.is_file())
            corrupt.append({"name": entry, "size_bytes": size})
    return json.dumps({"corrupt_dirs": corrupt, "count": len(corrupt)}, indent=2)


def get_system_info():
    import psutil
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage(WORKSPACE)
    return json.dumps({
        "ram_total_gb": round(mem.total / (1024**3), 2),
        "ram_available_gb": round(mem.available / (1024**3), 2),
        "ram_percent": mem.percent,
        "cpu_cores": psutil.cpu_count(logical=True),
        "disk_free_gb": round(disk.free / (1024**3), 2),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "executable": sys.executable,
    }, indent=2)


def write_report(title, findings, repair_steps):
    report_path = os.path.join(WORKSPACE, "DIAGNOSTIC_REPORT.md")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    report = f"# {title}\n**Generated:** {timestamp}\n\n---\n\n## Findings\n\n{findings}\n\n---\n\n## Repair Plan\n\n{repair_steps}\n"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    return json.dumps({"status": "WRITTEN", "path": report_path}, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
# TOOL REGISTRY
# ═══════════════════════════════════════════════════════════════════════════

TOOL_FUNCTIONS = {
    "check_module_health": lambda **kw: check_module_health(kw["module_name"]),
    "inspect_directory": lambda **kw: inspect_directory(kw["path"], kw.get("max_depth", 2)),
    "get_package_metadata": lambda **kw: get_package_metadata(kw["package_name"]),
    "find_ghost_files": lambda **kw: find_ghost_files(kw["package_name"]),
    "scan_corrupt_dirs": lambda **kw: scan_corrupt_dirs(),
    "get_system_info": lambda **kw: get_system_info(),
    "run_diagnostic_code": lambda **kw: run_in_monty(kw["code"]),
    "write_report": lambda **kw: write_report(kw["title"], kw["findings"], kw["repair_steps"]),
}

TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "check_module_health",
        "description": "Tests if a Python module imports successfully. Returns version, location, errors, traceback.",
        "parameters": {"type": "object", "properties": {
            "module_name": {"type": "string", "description": "e.g. 'duckdb', 'lancedb', 'ray._common'"}
        }, "required": ["module_name"]}
    }},
    {"type": "function", "function": {
        "name": "inspect_directory",
        "description": "Lists files and subdirectories at a filesystem path inside the environment.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Absolute path to inspect"},
            "max_depth": {"type": "integer", "description": "Depth (default 2)"}
        }, "required": ["path"]}
    }},
    {"type": "function", "function": {
        "name": "get_package_metadata",
        "description": "Reads pip dist-info metadata: version, dependencies, requires-python.",
        "parameters": {"type": "object", "properties": {
            "package_name": {"type": "string", "description": "Package name as in pip, e.g. 'duckdb'"}
        }, "required": ["package_name"]}
    }},
    {"type": "function", "function": {
        "name": "find_ghost_files",
        "description": "Compares RECORD manifest vs actual files on disk to find ghost/missing files.",
        "parameters": {"type": "object", "properties": {
            "package_name": {"type": "string", "description": "Package dir name in site-packages"}
        }, "required": ["package_name"]}
    }},
    {"type": "function", "function": {
        "name": "scan_corrupt_dirs",
        "description": "Finds tilde-prefixed (~) leftover directories from failed pip installs.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }},
    {"type": "function", "function": {
        "name": "get_system_info",
        "description": "Reports RAM, CPU, disk, Python version.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }},
    {"type": "function", "function": {
        "name": "run_diagnostic_code",
        "description": "Executes Python code in an isolated Monty sandbox. Use print() for output. Has read-only access to /site-packages and /workspace.",
        "parameters": {"type": "object", "properties": {
            "code": {"type": "string", "description": "Python code to execute"}
        }, "required": ["code"]}
    }},
    {"type": "function", "function": {
        "name": "write_report",
        "description": "Writes final diagnostic report to DIAGNOSTIC_REPORT.md.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"},
            "findings": {"type": "string", "description": "Markdown findings"},
            "repair_steps": {"type": "string", "description": "Markdown repair plan with pip commands"}
        }, "required": ["title", "findings", "repair_steps"]}
    }},
]


# ═══════════════════════════════════════════════════════════════════════════
# TOKEN TRACKER
# ═══════════════════════════════════════════════════════════════════════════
class TokenBudget:
    def __init__(self, budget):
        self.budget = budget
        self.used = 0
    def add(self, text):
        self.used += len(str(text)) // APPROX_CHARS_PER_TOKEN
    @property
    def remaining(self):
        return max(0, self.budget - self.used)
    @property
    def exhausted(self):
        return self.used >= self.budget
    def __repr__(self):
        return f"[{self.used}/{self.budget} tokens]"


# ═══════════════════════════════════════════════════════════════════════════
# STREAMING + MULTI-TURN LOOP
# ═══════════════════════════════════════════════════════════════════════════

def stream_response(messages, use_tools=True):
    kwargs = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "stream": True,
        "max_tokens": 4096,
    }
    if use_tools:
        kwargs["tools"] = TOOL_SCHEMAS
        kwargs["tool_choice"] = "auto"

    response = client.chat.completions.create(**kwargs)
    tool_calls = []
    content = ""

    for chunk in response:
        delta = chunk.choices[0].delta
        if delta.content:
            print(delta.content, end="", flush=True)
            content += delta.content
        if delta.tool_calls:
            for tc_chunk in delta.tool_calls:
                while len(tool_calls) <= tc_chunk.index:
                    tool_calls.append({"id": "", "type": "function",
                                       "function": {"name": "", "arguments": ""}})
                tc = tool_calls[tc_chunk.index]
                if tc_chunk.id:
                    tc["id"] += tc_chunk.id
                if tc_chunk.function.name:
                    tc["function"]["name"] += tc_chunk.function.name
                if tc_chunk.function.arguments:
                    tc["function"]["arguments"] += tc_chunk.function.arguments

    return content, tool_calls


def run_deep_agent():
    budget = TokenBudget(TOKEN_BUDGET)
    tools_called = []

    system_prompt = SYSTEM_TEMPLATE.render(
        venv_root=VENV_ROOT,
        python_version=platform.python_version(),
        platform_name=platform.platform(),
        site_packages=SITE_PACKAGES,
        workspace=WORKSPACE,
    )
    budget.add(system_prompt)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": (
            "Diagnose what's wrong with duckdb and lancedb in this environment. "
            "Check if they import, look for ghost files, version conflicts, corrupt dirs. "
            "Run diagnostic code in the sandbox to test. Produce a repair plan."
        )}
    ]
    budget.add(messages[-1]["content"])

    # Init Monty sandbox
    print("=" * 80)
    print("🧠 SOVEREIGN DEEP AGENT v2 — Monty Sandbox + Jinja2 + Streaming")
    print("=" * 80)
    print(f"   Model:    {LLM_MODEL}")
    print(f"   Sandbox:  pydantic_monty (subprocess-isolated)")
    print(f"   Prompts:  Jinja2")
    print(f"   Budget:   {TOKEN_BUDGET} tokens")
    print(f"   Tools:    {len(TOOL_SCHEMAS)}")
    print("=" * 80)

    init_monty()
    start_time = time.time()

    try:
        for turn in range(1, MAX_TURNS + 1):
            print(f"\n{'─' * 80}")
            print(f"  ⟳ TURN {turn}/{MAX_TURNS}  |  {budget}")
            print(f"{'─' * 80}\n")

            if budget.exhausted:
                messages.append({"role": "user", "content": "Budget exhausted. Call write_report NOW."})

            print("🤖 ", end="", flush=True)
            content, tool_calls = stream_response(messages)
            print()
            budget.add(content)

            assistant_msg = {"role": "assistant"}
            if content:
                assistant_msg["content"] = content
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
                if "content" not in assistant_msg:
                    assistant_msg["content"] = None
            messages.append(assistant_msg)

            if content and "SOVEREIGN_COMPLETE" in content:
                print("\n✅ Agent signaled SOVEREIGN_COMPLETE")
                break

            if not tool_calls:
                if turn < MAX_TURNS:
                    reflection = REFLECTION_TEMPLATE.render(
                        turn=turn, max_turns=MAX_TURNS,
                        tokens_used=budget.used, token_budget=budget.budget,
                        tools_called=tools_called or ["none"],
                    )
                    messages.append({"role": "user", "content": reflection})
                    budget.add(reflection)
                    print("   💭 Reflection injected...")
                continue

            for tc in tool_calls:
                fn_name = tc["function"]["name"]
                fn_args_str = tc["function"]["arguments"]
                try:
                    fn_args = json.loads(fn_args_str) if fn_args_str else {}
                except json.JSONDecodeError:
                    fn_args = {}

                print(f"\n   🎯 SERVICE: {fn_name}")
                if fn_args:
                    display = {k: (v[:60] + "..." if isinstance(v, str) and len(v) > 60 else v)
                               for k, v in fn_args.items()}
                    print(f"      Query:  {json.dumps(display)}")

                try:
                    tool_result = TOOL_FUNCTIONS[fn_name](**fn_args)
                except Exception as e:
                    tool_result = json.dumps({"error": f"{type(e).__name__}: {e}"})

                # Cap response size to prevent token budget blowout
                if len(tool_result) > MAX_TOOL_RESPONSE_CHARS:
                    tool_result = tool_result[:MAX_TOOL_RESPONSE_CHARS] + f"\n... [TRUNCATED — {len(tool_result)} total chars]"

                tools_called.append(fn_name)
                budget.add(tool_result)

                preview = tool_result[:400]
                if len(tool_result) > 400:
                    preview += f"\n      ... ({len(tool_result)} chars)"
                print(f"   ⚡ Response: {preview}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": tool_result
                })

    finally:
        shutdown_monty()

    elapsed = time.time() - start_time
    print(f"\n{'═' * 80}")
    print(f"  🏁 SOVEREIGN DEEP AGENT COMPLETE")
    print(f"     Turns: {turn} | Tools: {len(tools_called)} | Elapsed: {elapsed:.1f}s")
    print(f"     Unique services: {', '.join(set(tools_called)) if tools_called else 'none'}")
    print(f"     {budget}")
    print(f"{'═' * 80}")


if __name__ == "__main__":
    run_deep_agent()
