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
# 1. LOAD CREDENTIALS (NVIDIA NIM & GOOGLE GEMINI)
# -----------------------------------------------------------------------------
for env_path in [r"C:\WEB CASE STUDY\.env", r"C:\STUDIES_BACKUP\.env"]:
    if os.path.exists(env_path):
        load_dotenv(env_path)

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "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")
os.environ["NVIDIA_API_KEY"] = NVIDIA_API_KEY

# -----------------------------------------------------------------------------
# 2. SELECT FLAGSHIP BIG MODEL FOR NVIDIA NIM
# -----------------------------------------------------------------------------
# Flagship Big Models:
# - "nvidia/llama-3.3-nemotron-super-49b-v1" (NVIDIA Flagship Super Nemotron)
# - "meta/llama-3.3-70b-instruct" (Llama 3.3 70B Titan)
NVIDIA_BIG_MODEL = sys.argv[1] if len(sys.argv) > 1 and "/" in sys.argv[1] else "nvidia/llama-3.3-nemotron-super-49b-v1"

# -----------------------------------------------------------------------------
# 3. COLLECT FILES TO ANALYZE
# -----------------------------------------------------------------------------
app_dir = r"C:\WEB CASE STUDY\Snoop_Stylizer_App"
files_to_analyze = [
    "README.md",
    "snoop_voice_app.py",
    "install_mac.command",
    "snoop_voice_engine_run.py",
    "run_dolly_test.py",
    "run_snoop_test.py"
]

file_contents = {}
print(f"Reading target files from {app_dir}...")
for filename in files_to_analyze:
    path = os.path.join(app_dir, filename)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                file_contents[filename] = f.read()
            print(f"  -> Loaded {filename} ({len(file_contents[filename]):,} chars)")
        except Exception as e:
            print(f"  -> Error reading {filename}: {e}")
    else:
        print(f"  -> ⚠️ Warning: {filename} not found.")

prompt_core = """
You are an expert Python developer, DSP audio engineer, and macOS deployment specialist. 
My user is building this application (`Snoop_Stylizer_App`) as a birthday present for his girlfriend. 
It needs to run seamlessly when sent to her Mac desktop.

I have included the core scripts and the Mac installation command (`install_mac.command`).

Please analyze these files with the following goals:
1. **Mac Compatibility:** Are there any hardcoded Windows paths, incompatible libraries, or platform-specific issues that will break on macOS?
2. **Ease of Use:** As a birthday present, it needs to be foolproof. Will `install_mac.command` work flawlessly for a non-technical Mac user?
3. **Actionable Fixes:** Provide the exact code changes or instructions needed to ensure it works perfectly on her Mac desktop out of the box.

Make your response extremely clear, encouraging, and focused on making this a perfect birthday gift!
"""

full_prompt = prompt_core + "\n\n" + "="*50 + "\nATTACHED SOURCE CODE FILES:\n" + "="*50 + "\n"
for fname, content in file_contents.items():
    full_prompt += f"\n--- FILE: {fname} ---\n```\n{content}\n```\n"

# -----------------------------------------------------------------------------
# 4. STREAMING INFERENCE FROM NVIDIA BIG MODEL
# -----------------------------------------------------------------------------
print(f"\n==========================================================================")
print(f" DISPATCHING TO NVIDIA BIG FLAGSHIP MODEL: {NVIDIA_BIG_MODEL}")
print(f"==========================================================================")

base_out_file = r"C:\WEB CASE STUDY\Mac_Birthday_Present_Analysis.md"
out_file = base_out_file
if os.path.exists(out_file):
    base, ext = os.path.splitext(base_out_file)
    i = 1
    while os.path.exists(f"{base}_{i}{ext}"):
        i += 1
    out_file = f"{base}_{i}{ext}"

nv_out_file = out_file.replace(".md", "_nemotron_super_49b.md")
print(f"\n[NVIDIA NIM CLOUD] Streaming live from {NVIDIA_BIG_MODEL}...\n" + "-"*70 + "\n")

req_body = {
    "model": NVIDIA_BIG_MODEL,
    "messages": [
        {"role": "system", "content": "You are a master Python software engineer, DSP audio architect, and macOS deployment authority."},
        {"role": "user", "content": full_prompt}
    ],
    "temperature": 0.2,
    "max_tokens": 2048,
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

with open(nv_out_file, "w", encoding="utf-8") as out:
    out.write(f"# Analysis via NVIDIA Big Flagship Model ({NVIDIA_BIG_MODEL})\n\n")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
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
        print(f"[NVIDIA PASS] Complete Big Model analysis saved to: {nv_out_file}")
    except Exception as e:
        print(f"\n[NVIDIA ERROR] {e}")

print("="*70)
