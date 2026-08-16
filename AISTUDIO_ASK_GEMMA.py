import os
import sys
import json
import asyncio
import subprocess

# --- AUTO-INSTALL DEPENDENCIES ---
try:
    from google import genai
    from google.genai import types
    from jinja2 import Template
except ImportError:
    print("📦 Missing modules found. Installing 'google-genai' and 'jinja2'...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "google-genai", "jinja2"])
    from google import genai
    from google.genai import types
    from jinja2 import Template

from dotenv import load_dotenv

# ----------------------------------------------------------------
# 1. API AUTHENTICATION
# ----------------------------------------------------------------
load_dotenv()
api_key = os.getenv("AISTUDIO_API_KEY") or os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: API key not found in .env")
    sys.exit(1)

# LangSmith / LangChain configuration (use exact manifest values)
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "legion-starter")
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "true")
# Export into environment for any LangChain / LangSmith client that reads them
os.environ["LANGSMITH_ENDPOINT"] = LANGSMITH_ENDPOINT
os.environ["LANGSMITH_PROJECT"] = LANGSMITH_PROJECT
os.environ["LANGSMITH_TRACING"] = LANGSMITH_TRACING

client = genai.Client(api_key=api_key)
contents_to_send = []

# Append a short manifest block so downstream models/runs are grounded with LangSmith metadata
langsmith_block = (
    f"LANGSMITH_ENDPOINT={LANGSMITH_ENDPOINT}\n"
    f"LANGSMITH_PROJECT={LANGSMITH_PROJECT}\n"
    f"LANGSMITH_TRACING={LANGSMITH_TRACING}\n"
    f"ls_run_depth={os.getenv('ls_run_depth','0')}\n"
)
contents_to_send.append(langsmith_block)

# Persist LangSmith metadata for external ingestion
try:
    out_dir = os.path.join(os.path.dirname(__file__), "out")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "langsmith_meta.json"), "w", encoding="utf-8") as mf:
        json.dump({
            "endpoint": LANGSMITH_ENDPOINT,
            "project": LANGSMITH_PROJECT,
            "tracing": LANGSMITH_TRACING,
            "ls_run_depth": int(os.getenv('ls_run_depth','0'))
        }, mf, indent=2)
    print(f"[+] LangSmith metadata written to {os.path.join(out_dir, 'langsmith_meta.json')}")
except Exception as e:
    print(f"[!] Failed to write LangSmith metadata: {e}")

# ----------------------------------------------------------------
# LANGCHAIN / LANGSMITH PRESENCE CHECK
# Ensure a LangChain runtime is available and record metadata so runs are traced
# ----------------------------------------------------------------
USING_LANGCHAIN = False
try:
    try:
        import langchain
    except ImportError:
        print("📦 LangChain not found in environment — installing 'langchain' and 'langchain-core'...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "langchain", "langchain-core"], stdout=subprocess.DEVNULL)
        import langchain
    USING_LANGCHAIN = True
    lc_ver = getattr(langchain, "__version__", "unknown")
    # Emit a runtime marker file that other tools can read to confirm LangChain usage
    try:
        lc_meta = {"langchain_installed": True, "version": lc_ver, "project": LANGSMITH_PROJECT}
        with open(os.path.join(out_dir, "langchain_meta.json"), "w", encoding="utf-8") as lf:
            json.dump(lc_meta, lf, indent=2)
        print(f"[+] LangChain available (version: {lc_ver}). Metadata written to out/langchain_meta.json")
    except Exception as e:
        print(f"[!] Could not write LangChain metadata: {e}")
except Exception as e:
    USING_LANGCHAIN = False
    print(f"[!] LangChain check/installation failed: {e}")

# ----------------------------------------------------------------
# 2. LANGGRAPH NODE PLACEHOLDERS (Hijack Logic)
# ----------------------------------------------------------------
async def dna_extractor_node(state):
    print("🧪 [Node] Extracting DNA from Ray Swarm...")
    # Simulated fetch from Ray Actor
    return {"dna": [0.1, 0.4, -0.2, 0.8], "filename": "PG_808_Hijack.wav"}

async def sieve_classifier_node(state):
    print("🧬 [Node] Sieve Classifier analyzing DNA...")
    return {"match_info": {"winner": "Chris Lake Baseline", "confidence": 0.94}}

async def hijacking_node(state):
    print("🏴‍☠️ [Node] Hijacking Code Structure Tokens...")
    return {"code_structure": "[[HIJACKED_STRUCTURE]]\nTokens: [142, 54, 991]"}

# ----------------------------------------------------------------
# 3. UPLOAD SEQUENCE (Like ask_gemini_codegen.py)
# ----------------------------------------------------------------
print("\n📡 Uploading Context Files to AI Studio...")

uploads = [
    (r"C:\WEB CASE STUDY\mastering_swarm_summary.json", "mastering_swarm_summary.json — Swarm Math Summary"),
    (r"C:\WEB CASE STUDY\mastering_playbooks.json", "mastering_playbooks.json — Generated Playbooks"),
    (r"C:\.genkit\sovereign_langgraph_hijack.py", "sovereign_langgraph_hijack.py — Langgraph Orchestrator"),
]

for path, label in uploads:
    if os.path.exists(path):
        print(f"  ⬆️ Uploading: {label}")
        f = client.files.upload(
            file=path,
            config=types.UploadFileConfig(mime_type="text/plain", display_name=label)
        )
        contents_to_send.append(f)
    else:
        print(f"  ⚠️ SKIP (not found): {path}")

# ----------------------------------------------------------------
# 4. ASYNC STATE EXECUTION & JINJA RENDERING
# ----------------------------------------------------------------
async def main():
    # Execute the mock nodes to build the state
    state = {}
    state.update(await dna_extractor_node(state))
    state.update(await sieve_classifier_node(state))
    state.update(await hijacking_node(state))
    
    JINJA_PROMPT = """
You are a Staff Audio Engineer and Antigravity Expert.
We are configuring our mastering agents based on recent swarm API data.

I have uploaded several files to your context:
- mastering_swarm_summary.json
- mastering_playbooks.json
- sovereign_langgraph_hijack.py

### Current LangGraph Hijack State:
- **Target File:** {{ state.filename }}
- **Extracted DNA Vector (partial):** {{ state.dna }}
- **Sieve Classification Winner:** {{ state.match_info.winner }} ({{ state.match_info.confidence * 100 }}% match)
- **Hijacked Tokens:** {{ state.code_structure }}

### TASK:
Analyze the uploaded JSON configurations and the current Hijack state. 
Please outline the exact python code to connect the `council_reasoner_node` directly to the `Gemma 4 26B` endpoint using this exact data.
"""

    print("\n⚙️ Compiling prompt via Jinja template...")
    jinja_compiler = Template(JINJA_PROMPT)
    fully_rendered_prompt = jinja_compiler.render(state=state)
    
    contents_to_send.append(fully_rendered_prompt)

    # ----------------------------------------------------------------
    # 5. STREAM RESPONSE
    # ----------------------------------------------------------------
    out_path = r"C:\WEB CASE STUDY\gemma_hijack_codegen.md"
    print("\n🧠 Consulting Antigravity Brain (Gemma 4 26B) with Thinking ON...\n" + "="*70)

    with open(out_path, "w", encoding="utf-8") as out:
        try:
            response = client.models.generate_content_stream(
                model="models/gemma-4-26b-a4b-it",
                contents=contents_to_send,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(include_thoughts=True)
                )
            )
            for chunk in response:
                text = chunk.text or ""
                print(text, end="", flush=True)
                out.write(text)
        except Exception as e:
            print(f"\n❌ Error during generation: {e}")

    print("\n" + "="*70)
    print(f"💾 Advice saved to {out_path}")

if __name__ == "__main__":
    asyncio.run(main())
