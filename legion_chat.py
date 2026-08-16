import os
import sys
import json
import re
import subprocess
import time
import asyncio
from datetime import datetime

# Reconfigure stdout to prevent CP1252 character map crashes on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# ── 1. THE SURGICAL ATTACHMENT (FUSING PATHS) ────────────────
EXTERNAL_ORGANS = [
    r"C:\Users\adams\AppData\Local\uv\cache\sdists-v9\pypi\audiocraft\1.3.0\8Pk7rIvMKZ5m6QGGp4Xqh\src",
    r"C:\Users\adams\AppData\Roaming\Python\Python314\site-packages",
]

print("\n" + "="*50)
print("   🦅 LEGION V8 (UNIFIED INTEGRATION + MCP PREPROCESSOR)")
print("   💉 Injecting External Libraries...")

SUCCESSFUL_MOUNTS = 0
for path in EXTERNAL_ORGANS:
    if os.path.exists(path):
        if path not in sys.path:
            sys.path.append(path)
            print(f"   ✅ ATTACHED: {os.path.basename(path)}")
            SUCCESSFUL_MOUNTS += 1

print(f"   [SYSTEM STATUS] {SUCCESSFUL_MOUNTS} Alien Cores Active.")
print("="*50 + "\n")

# ── 2. AUTO-INSTALL MEMORY DEPS ─────────────────────────────
def _ensure(pkg, import_name=None):
    try:
        __import__(import_name or pkg)
    except ImportError:
        try:
            print(f"\033[93m[System] Installing {pkg}...\033[0m")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])
        except Exception as e:
            print(f"\033[91m[System] Auto-install failed for {pkg}: {e}\033[0m")

_ensure("lancedb")
_ensure("pyarrow")
_ensure("duckdb")
_ensure("sentence-transformers", "sentence_transformers")
_ensure("httpx")
_ensure("mcp")

# Import modular workers
try:
    from memory_worker import MemoryBank
    from execution_worker import ExecutionEngine
except Exception as e:
    print(f"\033[91m[System] Failed to import modular workers: {e}\033[0m")
    sys.exit(1)

# Import custom LM Studio Client for model checking
try:
    from lmstudio_integration import LMStudioClient
except Exception as e:
    print(f"\033[93m[System] LMStudioClient SDK import skipped: {e}\033[0m")
    LMStudioClient = None

# ── 3. STITCH UI (PHOENIX TELEMETRY) ─────────────────────────
try:
    import phoenix as px
    from openinference.instrumentation.openai import OpenAIInstrumentor
    session = px.launch_app()
    print(f"👁️  STITCH UI ONLINE: {session.url}")
    OpenAIInstrumentor().instrument()
except ImportError:
    pass

# ── 4. CONFIG ──────────────────────────────────────────────
LM_STUDIO_URL = "http://127.0.0.1:1234/v1"
DEFAULT_MODEL = "nvidia/nemotron-3-nano-4b"
current_model = DEFAULT_MODEL
SESSION_DEPTH = 3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "sovereign_data")
MEDIA_DIR = os.path.join(DATA_DIR, "media")
DUCKDB_PATH = os.path.join(DATA_DIR, "sovereign.duckdb")
LANCEDB_PATH = os.path.join(DATA_DIR, "lancedb_store")

os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

SYSTEM_PROMPT = """You are Legion V8. Expert Architect. 
Use Vector Memory context for technical facts.
PROTOCOL: <<<FILE: path>>>...<<<END>>> | <<<EXECUTE: cmd>>>.
Be concise. Execute immediately when asked.
To generate music, just output <<<AUDIO: prompt>>>."""

# ── COLORS ──────────────────────────────────────────────
C_RESET  = "\033[0m"
C_USER   = "\033[92m"  # Green
C_AI     = "\033[96m"  # Cyan
C_SYS    = "\033[93m"  # Yellow
C_MEM    = "\033[90m"  # Dark grey
C_ERR    = "\033[91m"  # Red
C_FILE   = "\033[95m"  # Magenta

# ── 5. MEMORY INITIALIZATION ────────────────────────────────
try:
    memory_bank = MemoryBank(db_path=LANCEDB_PATH)
except Exception as e:
    print(f"{C_ERR}[Memory Bank Initialization Failed] {e}{C_RESET}")
    memory_bank = None

executor = ExecutionEngine()

def query_memory(user_input):
    if memory_bank:
        return memory_bank.query_context(user_input)
    return ""

def save_to_memory(user_input, response):
    if memory_bank:
        try:
            memory_bank.save_interaction(user_input, response)
        except Exception as e:
            print(f"{C_ERR}⚠️ LanceDB save error: {e}{C_RESET}")
            
    # DuckDB Logging
    try:
        import duckdb
        conn = duckdb.connect(DUCKDB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS interaction_logs 
            (timestamp TIMESTAMP, user_input TEXT, ai_response TEXT, action TEXT)
        """)
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute("INSERT INTO interaction_logs VALUES (?, ?, ?, ?)", 
                    (ts, user_input, response, "chat"))
        conn.close()
    except Exception as e:
        print(f"{C_ERR}⚠️ DuckDB log error: {e}{C_RESET}")

def read_file_content(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"[Error reading file: {e}]"

def get_audio_processing_status():
    try:
        if not os.path.exists("check_audio_processing.py"):
            return "check_audio_processing.py script not found."
            
        result = subprocess.run(
            [sys.executable, "check_audio_processing.py"],
            capture_output=True,
            text=True,
            timeout=5
        )
        output = result.stdout.strip()
        if result.stderr:
            output += "\n" + result.stderr.strip()
        return output
    except Exception as e:
        return f"Error executing check_audio_processing.py: {str(e)}"

# ── 6. MCP RAG PREPROCESSOR ─────────────────────────────────
async def query_mcp_rag(query: str, limit: int = 3) -> str:
    """Connects to the MCP RAG server on port 8005 and triggers parallel searches."""
    from mcp import ClientSession
    from mcp.client.sse import sse_client
    
    mcp_context = ""
    try:
        async with asyncio.timeout(6.0):  # Bounded execution window
            async with sse_client("http://127.0.0.1:8005/sse") as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    tasks = [
                        session.call_tool("semantic_code_search", arguments={"query": query, "limit": limit}),
                        session.call_tool("swarm_code_search", arguments={"search_term": query, "limit": max(1, limit // 2)}),
                        session.call_tool("swarm_intelligence_search", arguments={"search_term": query, "limit": max(1, limit // 2)})
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for res in results:
                        if isinstance(res, Exception) or not res:
                            continue
                        if hasattr(res, "content") and res.content and len(res.content) > 0:
                            mcp_context += res.content[0].text + "\n\n"
    except Exception:
        # Silently bypass if MCP server is offline/slow to prevent blocking loops
        pass
    return mcp_context

# ── 7. MUSCLE (AUDIO GENERATION) ────────────────────────────
def engage_music_core(prompt, duration=10):
    print(f"\n{C_AI}⚡ [VRAM SWITCH] ENGAGING AUDIOCRAFT: '{prompt}'{C_RESET}")
    try:
        import torch
        from audiocraft.models import MusicGen
        from audiocraft.data.audio import audio_write
        
        model = MusicGen.get_pretrained('facebook/musicgen-small')
        model.set_generation_params(duration=duration)
        wav = model.generate([prompt])
        
        filename = f"legion_beat_{int(time.time())}"
        path = os.path.join(MEDIA_DIR, filename)
        audio_write(path, wav[0].cpu(), model.sample_rate, strategy="loudness")
        del model
        torch.cuda.empty_cache()
        print(f"{C_USER}✅ AUDIO SAVED: {path}.wav{C_RESET}")
        return f"AUDIO SAVED: {path}.wav"
    except Exception as e:
        err = f"GENERATION FAIL: {e}"
        print(f"{C_ERR}❌ {err}{C_RESET}")
        return err

# ── 8. THE CONSTRUCTOR PROTOCOL ─────────────────────────────
def parse_and_write(full_response):
    """Scans response for <<<FILE>>> and <<<AUDIO>>> tags."""
    
    # Process Audio Generation
    audio_pattern = r"<<<AUDIO:\s*(.*?)>>>"
    audio_matches = re.findall(audio_pattern, full_response)
    for prompt in audio_matches:
        engage_music_core(prompt)

    # Process File Generation
    file_pattern = r"<<<FILE:\s*(.*?)>>>\n?(.*?)<<<END>>>"
    matches = re.findall(file_pattern, full_response, re.DOTALL)

    if not matches: return

    print(f"\n{C_FILE}=== CONSTRUCTOR PROTOCOL DETECTED ==={C_RESET}")
    for filepath, content in matches:
        filepath = filepath.strip()
        
        if ".." in filepath or os.path.isabs(filepath) or filepath.startswith("/"):
            print(f"{C_ERR}[SECURITY BLOCKED] Attempted write to unsafe path: {filepath}{C_RESET}")
            continue

        print(f"{C_FILE}Target: {filepath} ({len(content)} bytes){C_RESET}")
        confirm = input(f"{C_SYS}Write to disk? [y/N]: {C_RESET}").strip().lower()
        
        if confirm == 'y':
            try:
                dir_name = os.path.dirname(filepath)
                if dir_name:
                    os.makedirs(dir_name, exist_ok=True)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content.strip())
                print(f"{C_USER}[SUCCESS] Wrote {filepath}{C_RESET}")
            except Exception as e:
                print(f"{C_ERR}[FAILED] {e}{C_RESET}")
        else:
            print(f"{C_SYS}[SKIPPED]{C_RESET}")

def parse_and_execute(full_response):
    try:
        return executor.parse_and_execute(full_response)
    except Exception as e:
        print(f"{C_ERR}⚠️ Sandbox execute loop crashed: {e}{C_RESET}")
        return f"Sandbox execution crash: {e}"

# ── 9. LM STUDIO STREAMING CLIENT (HTTPX BASED) ──────────────
async def stream_chat(client: "httpx.AsyncClient", messages):
    url = f"{LM_STUDIO_URL}/chat/completions"
    payload = {
        "model": current_model,
        "messages": messages,
        "stream": True,
        "temperature": 0.3
    }
    
    print(f"{C_AI}Legion: {C_RESET}", end="", flush=True)
    full_response = ""
    
    try:
        async with client.stream("POST", url, json=payload, timeout=60.0) as response:
            if response.status_code != 200:
                print(f"\n{C_ERR}[ERROR] API returned status code {response.status_code}{C_RESET}")
                return None
                
            async for line in response.aiter_lines():
                line = line.strip()
                if line.startswith("data: ") and line != "data: [DONE]":
                    try:
                        chunk = json.loads(line[6:])
                        delta = chunk["choices"][0]["delta"].get("content", "")
                        if delta:
                            print(delta, end="", flush=True)
                            full_response += delta
                    except Exception:
                        pass
        print()
        
        parse_and_write(full_response)
        return full_response
        
    except Exception as e:
        print(f"\n{C_ERR}[CONNECTION ERROR] Cannot reach LM Studio: {e}{C_RESET}")
        print(f"{C_ERR}Ensure LM Studio server is running on port 1234 and CORS is enabled.{C_RESET}")
        return None

# ── 10. MAIN LOOP ────────────────────────────────────────────
async def main():
    global current_model
    os.system("cls" if os.name == "nt" else "clear")
    
    mem_count = memory_bank.get_count() if memory_bank else 0
    
    # Check connected model using the integration SDK if present
    connected = False
    if LMStudioClient:
        try:
            sdk_client = LMStudioClient(api_base=LM_STUDIO_URL)
            models = await sdk_client.list_models()
            if models:
                current_model = models[0].get("id", "local-model")
                connected = True
            await sdk_client.close()
        except Exception:
            pass
            
    print(f"{C_SYS}=== LEGION V8 UPLINK ESTABLISHED ==={C_RESET}")
    print(f"{C_SYS}Brain: LanceDB ({mem_count} memories) & DuckDB Logs | Model: {current_model}{C_RESET}")
    print(f"{C_FILE}Features: Auto-Write (<<<FILE>>>), Execute (<<<EXECUTE>>>), Audio (<<<AUDIO>>>){C_RESET}")
    print(f"{C_SYS}Commands: /file <path>, /reset, /memory, /exit{C_RESET}\n")

    session_history = []  

    # Initialize shared AsyncClient
    import httpx
    async with httpx.AsyncClient(timeout=60.0) as client:
        while True:
            try:
                user_input = input(f"{C_USER}You: {C_RESET}").strip()
                if not user_input: continue

                if user_input.lower() in ["/exit", "/quit"]:
                    mc = memory_bank.get_count() if memory_bank else 0
                    print(f"{C_SYS}Severing link... ({mc} memories saved){C_RESET}")
                    break

                if user_input.lower() == "/reset":
                    session_history.clear()
                    print(f"{C_SYS}[Session cleared. Long-term memory intact.]{C_RESET}")
                    continue

                if user_input.lower() == "/memory":
                    mc = memory_bank.get_count() if memory_bank else 0
                    print(f"{C_SYS}[LanceDB: {mc} interactions stored in {LANCEDB_PATH}]{C_RESET}")
                    continue

                if user_input.startswith("/file "):
                    fpath = user_input.split(" ", 1)[1].strip()
                    content = read_file_content(fpath)
                    print(f"{C_SYS}[Loaded {len(content)} chars from {fpath}]{C_RESET}")
                    session_history.append({"role": "user", "content": f"File '{fpath}':\n\n{content}\n\n(Awaiting your question)"})
                    print(f"{C_SYS}[Context buffered. Ask your question.]{C_RESET}")
                    continue

                # Run checking status background audio
                audio_status = get_audio_processing_status()
                dynamic_system_prompt = SYSTEM_PROMPT + "\n\n=== CURRENT AUDIO DB STATUS ===\n" + audio_status

                # ── INGEST SWARM RAG CONTEXT (MCP PREPROCESSOR) ──
                print(f"{C_SYS}[System] Fetching Swarm RAG context from MCP...{C_RESET}")
                mcp_context = await query_mcp_rag(user_input, limit=SESSION_DEPTH)
                if mcp_context.strip():
                    print(f"{C_MEM}[Swarm hit: Injected RAG Context]{C_RESET}")
                    dynamic_system_prompt += "\n\n=== RELEVANT SWARM RAG CONTEXT ===\n" + mcp_context

                # Load memory context
                past_context = query_memory(user_input)
                if past_context:
                    print(f"{C_MEM}[Memory hit: Injected Conversation History]{C_RESET}", flush=True)
                    dynamic_system_prompt += "\n\n=== RELEVANT LONG TERM MEMORY ===\n" + past_context

                messages = [{"role": "system", "content": dynamic_system_prompt}]
                messages += session_history[-SESSION_DEPTH:]
                messages.append({"role": "user", "content": user_input})

                response_text = await stream_chat(client, messages)

                if response_text:
                    session_history.append({"role": "user", "content": user_input})
                    session_history.append({"role": "assistant", "content": response_text})
                    save_to_memory(user_input, response_text)
                    
                    execution_feedback = parse_and_execute(response_text)
                    
                    while execution_feedback:
                        print(f"\n{C_SYS}[Auto-feeding terminal output back to Legion...]{C_RESET}")
                        messages.append({"role": "assistant", "content": response_text})
                        messages.append({"role": "user", "content": execution_feedback})
                        
                        session_history.append({"role": "user", "content": execution_feedback})
                        
                        response_text = await stream_chat(client, messages)
                        
                        if response_text:
                            session_history.append({"role": "assistant", "content": response_text})
                            save_to_memory("Auto-Execution Feedback", response_text)
                            execution_feedback = parse_and_execute(response_text)
                        else:
                            break

            except KeyboardInterrupt:
                mc = memory_bank.get_count() if memory_bank else 0
                print(f"\n{C_SYS}[Interrupt — {mc} memories saved]{C_RESET}")
                break

if __name__ == "__main__":
    asyncio.run(main())