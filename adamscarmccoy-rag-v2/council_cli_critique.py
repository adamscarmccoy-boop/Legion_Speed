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
# 2. SELECT RECENT CLI FILE TO REVIEW
# -----------------------------------------------------------------------------
target_file = r"C:\WEB CASE STUDY\adamscarmccoy-rag-v2\ask_antigravity.py"
if not os.path.exists(target_file):
    target_file = r"C:\WEB CASE STUDY\ask_antigravity.py"

print(f"Reading target CLI code from: {target_file}")
with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
    cli_code = f.read()

print(f"Loaded CLI code: {len(cli_code):,} chars, {len(cli_code.splitlines())} lines\n")

council_log_file = r"C:\WEB CASE STUDY\council_cli_critique_report.md"

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
        "max_tokens": 1200,
        "stream": True
    }
    req = urllib.request.Request(
        LM_STUDIO_URL,
        data=json.dumps(req_body).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    output = []
    with urllib.request.urlopen(req, timeout=40) as resp:
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
# HELPER: CALL NVIDIA NIM CLOUD (BIG 49B MODEL)
# -----------------------------------------------------------------------------
def call_nim_cloud(prompt, system_prompt="You are High Council Member: NVIDIA Super Nemotron 49B."):
    req_body = {
        "model": NIM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 2048,
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
    with urllib.request.urlopen(req, timeout=60) as resp:
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
print("="*80)
print(" 🏛️  THE SOVEREIGN COUNCIL OF AGENTS: CLI CODE REVIEW & CRITIQUE")
print(f" Target: {os.path.basename(target_file)}")
print(f" Members: [Local] {LM_STUDIO_MODEL}  vs  [Cloud] {NIM_MODEL}")
print("="*80)

with open(council_log_file, "w", encoding="utf-8") as report:
    report.write(f"# Sovereign Council Code Review Report\n\n")
    report.write(f"**Target CLI:** `{os.path.basename(target_file)}`\n")
    report.write(f"**Council Members:** `{LM_STUDIO_MODEL}` (Local Edge) & `{NIM_MODEL}` (Cloud Titan)\n\n---\n\n")

    # -------------------------------------------------------------------------
    # ROUND 1: LOCAL LM STUDIO INSPECTION
    # -------------------------------------------------------------------------
    print("\n\n🔵 [COUNCIL ROUND 1: Local LM Studio Review]\n" + "-"*70 + "\n")
    report.write("## 🔵 Round 1: Local Edge Review (LM Studio Nemotron Nano 4B)\n\n")
    
    round1_prompt = f"""
You are the Local Edge Engineer for this system.
Inspect this CLI script (`{os.path.basename(target_file)}`) for:
1. Local execution safety, file I/O efficiency, and UTF-8 handling on Windows.
2. Hardcoded fallback keys and environment variable hygiene.
3. Stream parsing resiliency (e.g. handling broken chunks or HTTP timeouts).
4. Score the code from 1 to 10 and state your top 2 concerns.

SOURCE CODE:
```python
{cli_code}
```
"""
    r1_output = call_lm_studio(round1_prompt)
    report.write(r1_output + "\n\n---\n\n")

    # -------------------------------------------------------------------------
    # ROUND 2: NIM SUPER NEMOTRON 49B COUNTER-CRITIQUE
    # -------------------------------------------------------------------------
    print("\n\n🟢 [COUNCIL ROUND 2: NVIDIA NIM Super Nemotron 49B Counter-Critique]\n" + "-"*70 + "\n")
    report.write("## 🟢 Round 2: High Council Counter-Critique (NVIDIA Super Nemotron 49B)\n\n")
    
    round2_prompt = f"""
You are the High Systems Architect and Senior Cloud Engineer (NVIDIA Super Nemotron 49B).
Review the CLI source code AND critique the feedback given by Local Council Member (Nemotron Nano 4B).

TARGET CLI CODE:
```python
{cli_code}
```

LOCAL COUNCIL MEMBER'S REVIEW:
{r1_output}

Your Task:
1. Evaluate whether the Local Member's critique is accurate or missed critical flaws.
2. Analyze advanced architecture: asynchronous streaming, argparse CLI ergonomics, exponential backoff on rate limits, and zero-allocation streaming buffers.
3. Provide your architectural rating (1 to 10) and specific counter-points.
"""
    r2_output = call_nim_cloud(round2_prompt)
    report.write(r2_output + "\n\n---\n\n")

    # -------------------------------------------------------------------------
    # ROUND 3: UNANIMOUS COUNCIL SYNTHESIS & REFACTORED CODE
    # -------------------------------------------------------------------------
    print("\n\n🏆 [COUNCIL ROUND 3: Unanimous Synthesis & Final Patched CLI]\n" + "-"*70 + "\n")
    report.write("## 🏆 Round 3: Unanimous Council Consensus & Patched Production CLI\n\n")
    
    round3_prompt = f"""
As the Lead Architect of the Council, synthesize the findings from both Council Members:
- Local Review: {r1_output[:800]}...
- Cloud Critique: {r2_output[:800]}...

Deliverables:
1. Final Consensus Score (1-10).
2. Key Consensus Upgrades Agreed Upon by both models.
3. The complete, production-ready, refactored version of the CLI script incorporating all fixes (argparse, error handling, timeout recovery, secure env fallback).
"""
    r3_output = call_nim_cloud(round3_prompt)
    report.write(r3_output + "\n\n")

print("\n\n" + "="*80)
print(f"🏛️ Council Deliberation Complete! Master Report saved to: {council_log_file}")
print("="*80)
