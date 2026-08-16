"""
Ask Antigravity Legion DSP (New Updated Script)
==============================================
Uploads your ACTUAL hand-written codebase files:
- Untitled-1.py (Fused Dataset, FretFlowEngine, Omni-Vectors)
- ray_arrow_swarm.py (Raw Swarm)
- dynamic_segment_master.py
- essentia_wsl_bridge.py
- sonic_dna_engine/generate_mastering_playbooks.py
- legion_sonic_engine_actors.py
- schemas.py
"""
import os, sys, json
from google import genai
from google.genai import types
from dotenv import load_dotenv

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

load_dotenv()
client = genai.Client()

contents_to_send = []

# 1. Upload Context Documents
context_docs = [
    (r"C:\WEB CASE STUDY\current_session_chat.md", "Session Chat"),
    (r"C:\WEB CASE STUDY\AI_MODE.md", "AI Engine Spec")
]

for path, label in context_docs:
    if os.path.exists(path):
        print(f"Uploading {label} ({os.path.basename(path)})...")
        uploaded = client.files.upload(
            file=path,
            config=types.UploadFileConfig(mime_type="text/plain", display_name=os.path.basename(path))
        )
        contents_to_send.append(uploaded)
    else:
        print(f"⚠️ Warning: Context file not found at {path}")

# 2. Upload Your Actual Codebase Files (Including Untitled-1.py and Ray Arrow Swarm)
audio_codebase = [
    r"C:\WEB CASE STUDY\Untitled-155.py",
    r"C:\WEB CASE STUDY\ray_arrow_swarm.py",
    r"C:\WEB CASE STUDY\dynamic_segment_master.py",
    r"C:\WEB CASE STUDY\essentia_wsl_bridge.py",
    r"C:\WEB CASE STUDY\sonic_dna_engine\generate_mastering_playbooks.py",
    r"C:\WEB CASE STUDY\legion_sonic_engine_actors.py",
    r"C:\WEB CASE STUDY\schemas.py"
]

print("\nUploading your real Audio/DSP codebase files...")
for path in audio_codebase:
    if os.path.exists(path):
        try:
            uploaded = client.files.upload(
                file=path,
                config=types.UploadFileConfig(mime_type="text/plain", display_name=os.path.basename(path))
            )
            contents_to_send.append(uploaded)
            print(f"  -> Uploaded real codebase file: {os.path.basename(path)}")
        except Exception as e:
            print(f"  -> Failed to upload {os.path.basename(path)}: {e}")
    else:
        print(f"  ⚠️ Warning: File not found at {path}")

prompt = """
You are a senior technical architect and lead DSP audio engineer. I have uploaded our actual codebase files, including `Untitled-1.py` (FretFlowEngine, Omni-Vectors, fused dataset) and `ray_arrow_swarm.py` (raw swarm).

Look at our ACTUAL audio codebase.

Your task:
Analyze our handwritten scripts and generate clean, production-ready, zero-boilerplate Python code to extend our codebase with the following enhancements:

1. **Omni-Vector Fusion & FretFlow Ingestion:**
   - Integrate `Untitled-1.py` FretFlowEngine latent representations with Ray Arrow Swarm data ingestion.

2. **LUFS, LRA & Spectral Brightness:**
   - Integrate `pyloudnorm.Meter` and `librosa.feature.spectral_centroid` directly into our segment analysis logic.

3. **Persistent Ingestion to LanceDB:**
   - Ingest metrics and embeddings into active LanceDB tables.

4. **Continuous Mastering Integration:**
   - Process stereo audio chunk-by-chunk using a persistent `Pedalboard` object (with `reset=False`) without clicks or phase issues.

Make sure your code is complete, matches our hand-written code style (using soundfile, pedalboard, scipy, ray, and lancedb), contains no '...' placeholders, and is ready to integrate directly!
"""
contents_to_send.append(prompt)

base_out_file = r"C:\WEB CASE STUDY\antigravity_legion_dsp_output.md"
out_file = base_out_file
if os.path.exists(out_file):
    base, ext = os.path.splitext(base_out_file)
    i = 1
    while os.path.exists(f"{base}_{i}{ext}"):
        i += 1
    out_file = f"{base}_{i}{ext}"

print(f"\nCreated new script target: {out_file}")

print("\nInitializing stateful chat session (model: gemini-2.5-flash)...")
chat = client.chats.create(model="gemini-2.5-flash")

print(f"Streaming Gemini response (saving to: {os.path.basename(out_file)})...\n" + "="*70)

with open(out_file, "w", encoding="utf-8") as out:
    try:
        response = chat.send_message_stream(contents_to_send)
        for chunk in response:
            text = chunk.text or ""
            print(text, end="", flush=True)
            out.write(text)
    except Exception as e:
        print(f"\nError: {e}")

print("\n" + "="*70)
print(f"Saved complete code output to {out_file}")
