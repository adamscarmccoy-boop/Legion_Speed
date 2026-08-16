"""
Ask Antigravity Real DSP
========================
Uploads ONLY your actual, hand-written audio and DSP codebase files,
along with context documents, and streams the response from the same Gemini
model to generate clean, high-signal, zero-boilerplate DSP code.
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
    (r"C:\Users\adams\.gemini\antigravity-ide\brain\806438d3-d535-4108-8401-4321fa6a9f89\walkthrough.md", "Walkthrough"),
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

# 2. Upload ONLY Your Actual Audio/DSP Codebase Files
audio_codebase = [
    r"C:\WEB CASE STUDY\dynamic_segment_master.py",
    r"C:\WEB CASE STUDY\mix_audit_agent.py",
    r"C:\WEB CASE STUDY\generate_mastering_playbooks.py",
    r"C:\WEB CASE STUDY\essentia_wsl_bridge.py",
    r"C:\WEB CASE STUDY\fire_test_visual.py",
    r"C:\WEB CASE STUDY\ray_arrow_swarm.py",
    r"C:\.genkit\run_mastering_and_package.py"
]

print("\nUploading your hand-written Audio/DSP codebase...")
for path in audio_codebase:
    if os.path.exists(path):
        try:
            uploaded = client.files.upload(
                file=path,
                config=types.UploadFileConfig(mime_type="text/plain", display_name=os.path.basename(path))
            )
            contents_to_send.append(uploaded)
            print(f"  -> Uploaded real DSP file: {os.path.basename(path)}")
        except Exception as e:
            print(f"  -> Failed to upload {os.path.basename(path)}: {e}")
    else:
        print(f"  ⚠️ Warning: DSP file not found at {path}")

prompt = """
You are a senior technical architect and lead DSP audio engineer. I have uploaded our actual, hand-written audio/DSP codebase files, along with our walkthrough and session design documents.

Look at our ACTUAL audio codebase (specifically `dynamic_segment_master.py`, `mix_audit_agent.py`, `generate_mastering_playbooks.py`, and `fire_test_visual.py`).

Your task:
Analyze our handwritten scripts and generate clean, production-ready, zero-boilerplate Python code to extend our codebase with the following enhancements:

1. **LUFS & LRA Loudness Logging:**
   - Integrate `pyloudnorm.Meter` calculations directly into our segment analysis logic to track Integrated LUFS and Loudness Range (LRA).

2. **Spectral Centroid Brightness:**
   - Integrate `librosa.feature.spectral_centroid` into our segment analysis to track brightness over time.

3. **Persistent Segment Ingestion to LanceDB:**
   - Write a clean script or class to directly ingest our segment metrics (RMS, Crest, LUFS, LRA, Band Energies, Spectral Centroid, and a 128-dimensional MFCC embedding) into our active `"omni_semantic_baselines"` LanceDB table.

4. **Continuous Mastering Integration:**
   - Show how we can orchestrate these calculations and query closest baseline segments to dynamically update dynamic compressor/gain settings on a single, persistent `Pedalboard` object (with `reset=False`) to process stereo audio chunk-by-chunk without clicks or phase issues.

Make sure your code is complete, matches our hand-written code style (using soundfile, pedalboard, scipy, and lancedb), contains no '...' placeholders, and is ready to integrate directly!
"""
contents_to_send.append(prompt)

# Initialize a stateful, persistent chat session using the SDK
print("\nInitializing stateful chat session (model: gemini-2.5-flash)...")
chat = client.chats.create(model="gemini-2.5-flash")

# Determine a unique output filename that won't overwrite existing reports
base_out_file = r"C:\WEB CASE STUDY\antigravity_real_dsp_output.md"
out_file = base_out_file
if os.path.exists(out_file):
    base, ext = os.path.splitext(base_out_file)
    i = 1
    while os.path.exists(f"{base}_{i}{ext}"):
        i += 1
    out_file = f"{base}_{i}{ext}"

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
