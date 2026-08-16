import os
import sys
import json
import urllib.request
import time
from dotenv import load_dotenv

# Ensure robust UTF-8 output on Windows terminal
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# -----------------------------------------------------------------------------
# 1. LOAD CONFIG & API KEYS
# -----------------------------------------------------------------------------
for env_path in [r"C:\WEB CASE STUDY\.env", r"C:\STUDIES_BACKUP\.env"]:
    if os.path.exists(env_path):
        load_dotenv(env_path)

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "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")

LM_STUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"
LM_STUDIO_MODEL = "nvidia/nemotron-3-nano-4b"

NIM_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NIM_MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1"

# -----------------------------------------------------------------------------
# 2. INGEST ALL CLI SCRIPTS & CHAT CONTEXT
# -----------------------------------------------------------------------------
cli_files = [
    r"C:\WEB CASE STUDY\adamscarmccoy-rag-v2\ask_antigravity.py",
    r"C:\WEB CASE STUDY\adamscarmccoy-rag-v2\ask_antigravity_langgraph_audit.py",
    r"C:\WEB CASE STUDY\run_legion_graph_test.py",
    r"C:\WEB CASE STUDY\acp_control_plane.py"
]

aggregated_cli_code = {}
print("Ingesting all CLI scripts and chat tools across the workspace...")
for path in cli_files:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            aggregated_cli_code[os.path.basename(path)] = content
            print(f"  -> Ingested {os.path.basename(path)} ({len(content):,} chars)")

# -----------------------------------------------------------------------------
# HELPER: CALL NVIDIA NIM CLOUD (SUPER NEMOTRON 49B)
# -----------------------------------------------------------------------------
def call_nim_cloud(prompt, system_prompt="You are High Council Member: NVIDIA Super Nemotron 49B."):
    req_body = {
        "model": NIM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 2500,
        "stream": True
    }
    req = urllib.request.Request(
        NIM_URL,
        data=json.dumps(req_body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {NVIDIA_API_KEY}"
        }
    )
    output = []
    with urllib.request.urlopen(req, timeout=90) as resp:
        for line in resp:
            line_str = line.decode("utf-8").strip()
            if line_str.startswith("data: ") and line_str != "data: [DONE]":
                try:
                    chunk = json.loads(line_str[6:])
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    if delta:
                        print(delta, end="", flush=True)
                        output.append(delta)
                except Exception:
                    pass
    return "".join(output)

# -----------------------------------------------------------------------------
# HELPER: CALL LM STUDIO (LOCAL)
# -----------------------------------------------------------------------------
def call_lm_studio(prompt, system_prompt="You are Local Council Member: Nemotron Nano 4B."):
    req_body = {
        "model": LM_STUDIO_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 600,
        "stream": True
    }
    req = urllib.request.Request(
        LM_STUDIO_URL,
        data=json.dumps(req_body).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    output = []
    with urllib.request.urlopen(req, timeout=30) as resp:
        for line in resp:
            line_str = line.decode("utf-8").strip()
            if line_str.startswith("data: ") and line_str != "data: [DONE]":
                try:
                    chunk = json.loads(line_str[6:])
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    if delta:
                        print(delta, end="", flush=True)
                        output.append(delta)
                except Exception:
                    pass
    return "".join(output)

# -----------------------------------------------------------------------------
# COUNCIL DELIBERATION
# -----------------------------------------------------------------------------
council_report_path = r"C:\WEB CASE STUDY\council_master_cli_synthesis_report.md"

code_block = ""
for fname, code in aggregated_cli_code.items():
    code_block += f"\n--- SCRIPT: {fname} ---\n```python\n{code}\n```\n"

print("\n" + "="*80)
print(" 🏛️  SOVEREIGN COUNCIL: FULL CLI AUDIT & SYNTHESIS DEBATE")
print(f" Council Members: Cloud [{NIM_MODEL}]  <--->  Local [{LM_STUDIO_MODEL}]")
print("="*80)

with open(council_report_path, "w", encoding="utf-8") as out:
    out.write("# Sovereign Council: Master CLI Audit & Synthesis Report\n\n")
    out.write(f"**Council Members:** `{NIM_MODEL}` (Cloud Titan) & `{LM_STUDIO_MODEL}` (Local Edge)\n\n---\n\n")

    # -------------------------------------------------------------------------
    # ROUND 1: CLOUD NIM SUPER NEMOTRON 49B DEEP INGESTION & AUDIT
    # -------------------------------------------------------------------------
    print("\n🟢 [COUNCIL ROUND 1: NVIDIA Super Nemotron 49B Comprehensive Audit]\n" + "-"*70 + "\n")
    out.write("## 🟢 Round 1: Cloud Titan Audit (NVIDIA Super Nemotron 49B)\n\n")
    
    r1_prompt = f"""
You are the High Systems Architect and Lead Cloud Engineer (NVIDIA Super Nemotron 49B).
Inspect all 4 CLI scripts currently in the workspace:
{code_block}

Your Tasks:
1. **Redundancy & Overlap Analysis:** How `ask_antigravity.py`, `ask_antigravity_langgraph_audit.py`, and `run_legion_graph_test.py` duplicate logic.
2. **Protocol & Architectural Hygiene:** Evaluate A2A control plane compatibility, error handling, and streaming.
3. **Master Architecture Specification:** Outline how all 4 tools should merge into a single unified CLI (`sovereign_cli.py`).
"""
    r1_review = call_nim_cloud(r1_prompt)
    out.write(r1_review + "\n\n---\n\n")

    # -------------------------------------------------------------------------
    # ROUND 2: LOCAL LM STUDIO EDGE PERSPECTIVE & CRITIQUE
    # -------------------------------------------------------------------------
    print("\n\n🔵 [COUNCIL ROUND 2: Local LM Studio Edge Critique & Constraints]\n" + "-"*70 + "\n")
    out.write("## 🔵 Round 2: Local Edge Review (LM Studio Nemotron Nano 4B)\n\n")
    
    r2_prompt = f"""
You are the Local Edge Engineer (Nemotron Nano 4B).
Review the Cloud Architect's Round 1 Audit:
{r1_review[:1500]}...

State your local constraints:
1. Ensuring offline execution when internet/API keys are unavailable.
2. Zero-allocation memory passing and sub-millisecond local routing.
3. State whether you endorse the Cloud Architect's unified CLI design.
"""
    r2_review = call_lm_studio(r2_prompt)
    out.write(r2_review + "\n\n---\n\n")

    # -------------------------------------------------------------------------
    # ROUND 3: FINAL UNIFIED MASTER CLI CODE IMPLEMENTATION
    # -------------------------------------------------------------------------
    print("\n\n🏆 [COUNCIL ROUND 3: Unanimous Synthesis & Unified CLI Implementation]\n" + "-"*70 + "\n")
    out.write("## 🏆 Round 3: Unanimous Consensus & Master CLI Code (`sovereign_cli.py`)\n\n")
    
    r3_prompt = f"""
As the Lead Architect of the Sovereign Council, synthesize Round 1 and Round 2:
- Cloud Specification: {r1_review[:800]}...
- Local Edge Constraints: {r2_review[:800]}...

Generate the complete, production-ready, beautiful Python script: `sovereign_cli.py`.
It must include:
1. Subcommands: `ask` (multi-model streaming), `audit` (codebase review), `graph` (LangGraph state engine), and `acp` (A2A zero-copy envelope check).
2. Fallback routing: Defaults to local LM Studio if NVIDIA API is unavailable.
3. Clean CLI formatting and argument parsing.
"""
    r3_code = call_nim_cloud(r3_prompt)
    out.write(r3_code + "\n\n")

print("\n\n" + "="*80)
print(f"🏛️ Council Deliberation Complete! Master Synthesis saved to: {council_report_path}")
print("="*80)
