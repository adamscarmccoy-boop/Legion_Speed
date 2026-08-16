import os
import sys
import json
import urllib.request
from dotenv import load_dotenv

# Ensure robust UTF-8 console output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# -----------------------------------------------------------------------------
# 1. LOAD CREDENTIALS
# -----------------------------------------------------------------------------
for env_path in [r"C:\WEB CASE STUDY\.env", r"C:\STUDIES_BACKUP\.env"]:
    if os.path.exists(env_path):
        load_dotenv(env_path)

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "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")
NVIDIA_BIG_MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1"

# -----------------------------------------------------------------------------
# 2. COLLECT LANGGRAPH, LANGCHAIN & MONTY SANDBOX FILES
# -----------------------------------------------------------------------------
files_to_audit = [
    r"C:\WEB CASE STUDY\legion_graph.py",
    r"C:\WEB CASE STUDY\build_legion_graph.py",
    r"C:\WEB CASE STUDY\qc_langgraph_engine.py",
    r"C:\WEB CASE STUDY\run_pydantic_core_monty.py",
    r"C:\WEB CASE STUDY\acp_control_plane.py",
    r"C:\WEB CASE STUDY\sonic_dna_engine\SovereignOrtBinding.hpp"
]

file_contents = {}
print("Loading core LangGraph, Tool, and Sandbox files for 49B Nemotron Audit...")
for path in files_to_audit:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                # Take full content or large representative chunk
                file_contents[os.path.basename(path)] = content[:15000]
                print(f"  -> Loaded {os.path.basename(path)} ({len(file_contents[os.path.basename(path)]):,} chars)")
        except Exception as e:
            print(f"  -> Error reading {path}: {e}")
    else:
        print(f"  -> ⚠️ Warning: {path} not found.")

prompt = """
You are the Chief AI Systems Architect and Lead Distributed Graph Engineer for NVIDIA & LangChain.
Analyze our production LangGraph state machines, tools, and Pydantic-Monty / C++ execution sandboxes.

Files uploaded:
1. `legion_graph.py` (Core LangGraph StateGraph with DuckDB, Parquet, and LanceDB tools)
2. `build_legion_graph.py` (Graph builder, edge compiler, and execution loop)
3. `qc_langgraph_engine.py` (3-try closed-loop VLM Quality Control StateGraph)
4. `run_pydantic_core_monty.py` (Pydantic-Monty Rust VM sandbox & bytecode validator)
5. `acp_control_plane.py` (Agent-to-Agent ACP protocol control plane)
6. `SovereignOrtBinding.hpp` (Zero-allocation AOT C++ ONNX audio DSP runtime)

Your Deliverable:
Provide a rigorous, master-level architecture report containing:

1. **Tool Status & Health Audit:**
   - Detailed status check on every tool (`query_sonic_core`, `analyze_parquet_data`, `search_similar_audio_vibes`, `decide_route`).
   - Identify schema drift, hardcoded paths, and potential failure modes.

2. **Execution Sandbox Analysis:**
   - How the Pydantic-Monty Rust VM and C++ execution sandboxes isolate untrusted agent bytecode and ensure zero host contamination.
   - Verification of the 3-try error-recovery loop.

3. **High-Impact Architectural Improvements:**
   - Specific, high-impact code optimizations to accelerate StateGraph node transitions (e.g. from 5ms down to <1ms).
   - Upgrades for zero-copy memory passing between Python LangGraph and C++ AOT DSP engines.

Make your report extremely structured, actionable, and authoritative.
"""

full_prompt = prompt + "\n\n" + "="*50 + "\nATTACHED PRODUCTION CODEBASE FILES:\n" + "="*50 + "\n"
for fname, content in file_contents.items():
    full_prompt += f"\n--- FILE: {fname} ---\n```\n{content}\n```\n"

# -----------------------------------------------------------------------------
# 3. DISPATCH LIVE TO NVIDIA FLAGSHIP SUPER NEMOTRON 49B
# -----------------------------------------------------------------------------
print(f"\n==========================================================================")
print(f" DISPATCHING LANGGRAPH & SANDBOX AUDIT TO: {NVIDIA_BIG_MODEL}")
print(f"==========================================================================")

out_file = r"C:\WEB CASE STUDY\langgraph_tools_and_sandbox_super_nemotron_report.md"
print(f"\n[NVIDIA NIM CLOUD] Streaming live architectural audit...\n" + "-"*70 + "\n")

req_body = {
    "model": NVIDIA_BIG_MODEL,
    "messages": [
        {"role": "system", "content": "You are a master distributed AI systems architect, LangGraph core engineer, and low-latency C++/Python performance authority."},
        {"role": "user", "content": full_prompt}
    ],
    "temperature": 0.2,
    "max_tokens": 3000,
    "stream": True
}

req = urllib.request.Request(
    "https://integrate.api.nvidia.com/v1/chat/completions",
    data=json.dumps(req_body).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {NVIDIA_API_KEY}"
    }
)

with open(out_file, "w", encoding="utf-8") as out:
    out.write(f"# Sovereign LangGraph, Tools & Sandbox Master Audit\n")
    out.write(f"**Evaluated by:** `{NVIDIA_BIG_MODEL}`\n\n")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            for line in resp:
                line_str = line.decode("utf-8").strip()
                if line_str.startswith("data: ") and line_str != "data: [DONE]":
                    try:
                        chunk = json.loads(line_str[6:])
                        delta = chunk["choices"][0]["delta"].get("content", "")
                        print(delta, end="", flush=True)
                        out.write(delta)
                    except Exception:
                        pass
        print(f"\n\n" + "-"*70)
        print(f"[NVIDIA PASS] Master audit saved to: {out_file}")
    except Exception as e:
        print(f"\n[NVIDIA ERROR] {e}")

print("="*70)
