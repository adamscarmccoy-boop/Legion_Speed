"""
SOVEREIGN EXECUTION AGENT — Legion Chat Recovery & Update
"""

import json
import time
import sys
import os
import subprocess
from pathlib import Path

from openai import OpenAI

# ═══════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════
WORKSPACE       = r"C:\WEB CASE STUDY"
VENV_ROOT       = os.path.join(WORKSPACE, ".venv")
VENV_PYTHON     = os.path.join(VENV_ROOT, "Scripts", "python.exe")
MAX_TURNS       = 5

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)
LLM_MODEL = "nvidia/nemotron-3-nano-4b"

# ═══════════════════════════════════════════════════════════════════════════
# TOOLS
# ═══════════════════════════════════════════════════════════════════════════
def write_file(path, content):
    """Write or overwrite a file."""
    try:
        full = os.path.join(WORKSPACE, path) if not os.path.isabs(path) else path
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        return json.dumps({"status": "OK", "path": full})
    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})

TOOL_FUNCTIONS = {
    "write_file": lambda **kw: write_file(kw["path"], kw["content"]),
}

TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "write_file",
        "description": "Write new content to a file, replacing what was there.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "File path"},
            "content": {"type": "string", "description": "Full new file content"}
        }, "required": ["path", "content"]}
    }},
]

# ═══════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════════════════
ORIGINAL_CHAT_CODE = '''import sys
import time
import json
import os
import subprocess
import duckdb
from openai import OpenAI
from datetime import datetime

# --- 1. THE SURGICAL ATTACHMENT (FUSING PATHS) ---
EXTERNAL_ORGANS = [
    r"C:\\Users\\adams\\AppData\\Local\\uv\\cache\\sdists-v9\\pypi\\audiocraft\\1.3.0\\8Pk7rIvMKZ5m6QGGp4Xqh\\src",
    r"C:\\Users\\adams\\AppData\\Roaming\\Python\\Python314\\site-packages",
]

print("\\n" + "="*50)
print("   🦅 LEGION V7 (PRECISION LINK)")
print("   💉 Injecting External Libraries...")

SUCCESSFUL_MOUNTS = 0
for path in EXTERNAL_ORGANS:
    if os.path.exists(path):
        if path not in sys.path:
            sys.path.append(path)
            print(f"   ✅ ATTACHED: {os.path.basename(path)}")
            SUCCESSFUL_MOUNTS += 1

print(f"   [SYSTEM STATUS] {SUCCESSFUL_MOUNTS} Alien Cores Active.")
print("="*50 + "\\n")

# --- 2. STITCH UI (PHOENIX) ---
try:
    import phoenix as px
    from openinference.instrumentation.openai import OpenAIInstrumentor
    session = px.launch_app()
    print(f"👁️  STITCH UI ONLINE: {session.url}")
    OpenAIInstrumentor().instrument()
except ImportError:
    pass

# --- 3. CONFIGURATION ---
LM_STUDIO_URL = "http://localhost:1010/v1"
MODEL_ID = "local-model"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.join(BASE_DIR, "AI_WORKSPACE")
MEDIA_DIR = os.path.join(WORKSPACE_DIR, "media")
DB_PATH = os.path.join(WORKSPACE_DIR, "logic_registry.duckdb")

os.makedirs(MEDIA_DIR, exist_ok=True)

# --- 4. MEMORY (DUCKDB) ---
def log_interaction(user_text, ai_text, action_type):
    try:
        conn = duckdb.connect(DB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS interaction_logs 
            (timestamp TIMESTAMP, user_input TEXT, ai_response TEXT, action TEXT)
        """)
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute("INSERT INTO interaction_logs VALUES (?, ?, ?, ?)", 
                    (ts, user_text, ai_text, action_type))
        conn.close()
    except Exception as e:
        print(f"⚠️ LOG ERROR: {e}")

# --- 5. MUSCLE (AUDIO GENERATION) ---
def engage_music_core(prompt, duration=10):
    print(f"\\n⚡ [VRAM SWITCH] ENGAGING AUDIOCRAFT: '{prompt}'")
    start_time = time.time()
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
        return f"✅ AUDIO SAVED: {path}.wav"
    except Exception as e:
        return f"❌ GENERATION FAIL: {e}"

# --- 6. HANDS (CODE & FILES) ---
def execute_python(code):
    try:
        temp_script = os.path.join(WORKSPACE_DIR, "temp_exec.py")
        with open(temp_script, "w", encoding='utf-8') as f:
            f.write(code)
        result = subprocess.run([sys.executable, temp_script], capture_output=True, text=True)
        return f"🖥️ OUTPUT:\\n{result.stdout + result.stderr}"
    except Exception as e:
        return f"❌ EXEC ERROR: {e}"

# --- 7. MAIN BRAIN ---
def main():
    client = OpenAI(base_url=LM_STUDIO_URL, api_key="lm-studio")
    system_context = """You are LEGION (V8). Tool protocol:
    1. MUSIC: { "tool": "music", "prompt": "techno 140bpm" }
    2. EXEC:  { "tool": "exec", "code": "print('hello')" }"""
    
    print("🦅 LEGION ARCHITECT V8\\nWaiting for input...")
    history = [{"role": "system", "content": system_context}]

    while True:
        try:
            user_input = input("\\n👤 USER: ")
            if user_input.lower() in ['exit', 'quit']: break
            history.append({"role": "user", "content": user_input})
            
            completion = client.chat.completions.create(
                model=MODEL_ID, messages=history, temperature=0.6, stream=True
            )
            
            full_response = ""
            print("🤖 LEGION: ", end="")
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    c = chunk.choices[0].delta.content
                    print(c, end="", flush=True)
                    full_response += c
            print()
            
            # Simple JSON Tool Parse
            if "{" in full_response and "}" in full_response:
                start = full_response.find("{")
                end = full_response.rfind("}") + 1
                try:
                    data = json.loads(full_response[start:end])
                    if data.get("tool") == "music":
                        res = engage_music_core(data["prompt"])
                        print(res)
                    elif data.get("tool") == "exec":
                        res = execute_python(data["code"])
                        print(res)
                except:
                    pass
                    
            history.append({"role": "assistant", "content": full_response})
            log_interaction(user_input, full_response, "chat")
        except Exception as e:
            print(f"\\n❌ ERROR: {e}")

if __name__ == "__main__":
    main()
'''

SYSTEM_PROMPT = f"""You are the SOVEREIGN EXECUTION AGENT.
Your mission is to upgrade the Legion Chat agent.

INSTRUCTIONS:
1. Below is the original code for `legion_chat_v7.py`.
2. I need you to write a NEW file called `legion_chat.py` in the workspace using the `write_file` tool.
3. In the new code, you MUST make these changes:
   - Change `LM_STUDIO_URL = "http://localhost:1010/v1"` to `LM_STUDIO_URL = "http://127.0.0.1:1234/v1"`
   - Change `DB_PATH = os.path.join(WORKSPACE_DIR, "logic_registry.duckdb")` to `DB_PATH = os.path.join(WORKSPACE_DIR, "sovereign_data", "sovereign.duckdb")`
   - Update the print statements to say "LEGION V8" instead of "LEGION V7".
4. Output the `write_file` tool call immediately.
5. End your final message with EXECUTION_COMPLETE.

ORIGINAL CODE:
{ORIGINAL_CHAT_CODE}
"""

def stream_response(messages):
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        tools=TOOL_SCHEMAS,
        tool_choice="auto",
        temperature=0.2,
        stream=True,
    )
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
                    tool_calls.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                tc = tool_calls[tc_chunk.index]
                if tc_chunk.id: tc["id"] += tc_chunk.id
                if tc_chunk.function.name: tc["function"]["name"] += tc_chunk.function.name
                if tc_chunk.function.arguments: tc["function"]["arguments"] += tc_chunk.function.arguments
    return content, tool_calls

def run_agent():
    print("=" * 80)
    print("SOVEREIGN EXECUTION AGENT - CHAT RECOVERY")
    print("=" * 80)
    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "Update the chat code as instructed and write it to legion_chat.py."}]

    for turn in range(1, MAX_TURNS + 1):
        print(f"\n[Turn {turn}] LLM: ", end="", flush=True)
        content, tool_calls = stream_response(messages)
        print()

        msg = {"role": "assistant"}
        if content: msg["content"] = content
        if tool_calls: msg["tool_calls"] = tool_calls
        messages.append(msg)

        if content and "EXECUTION_COMPLETE" in content:
            print("\n[DONE]")
            break

        if not tool_calls: continue

        for tc in tool_calls:
            fn_name = tc["function"]["name"]
            try: fn_args = json.loads(tc["function"]["arguments"])
            except: fn_args = {}
            print(f"   [TOOL] {fn_name}")
            res = TOOL_FUNCTIONS[fn_name](**fn_args)
            print(f"   [DATA] {res[:200]}...")
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": res})

if __name__ == "__main__":
    run_agent()
