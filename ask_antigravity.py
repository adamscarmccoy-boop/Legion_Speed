import os, sys
from google import genai
from google.genai import types
from dotenv import load_dotenv

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

load_dotenv()
client = genai.Client()

contents_to_send = []
app_dir = r"C:\WEB CASE STUDY\Snoop_Stylizer_App"

files_to_analyze = [
    "README.md",
    "snoop_voice_app.py",
    "install_mac.command",
    "snoop_voice_engine_run.py",
    "run_dolly_test.py",
    "run_snoop_test.py"
]

print(f"Uploading files from {app_dir} for Mac compatibility analysis...")

for filename in files_to_analyze:
    path = os.path.join(app_dir, filename)
    if os.path.exists(path):
        try:
            uploaded_file = client.files.upload(
                file=path,
                config=types.UploadFileConfig(mime_type="text/plain", display_name=filename)
            )
            contents_to_send.append(uploaded_file)
            print(f"  -> Uploaded {filename}")
        except Exception as e:
            print(f"  -> Failed to upload {filename}: {e}")
    else:
        print(f"  -> ⚠️ Warning: {filename} not found.")

prompt = """
You are an expert Python developer and macOS deployment specialist. 
My user is building this application (`Snoop_Stylizer_App`) as a birthday present for his girlfriend. 
It needs to run seamlessly when sent to her Mac desktop.

I have uploaded the core scripts and the Mac installation command (`install_mac.command`).

Please analyze these files with the following goals:
1. **Mac Compatibility:** Are there any hardcoded Windows paths, incompatible libraries, or platform-specific issues that will break on macOS?
2. **Ease of Use:** As a birthday present, it needs to be foolproof. Will `install_mac.command` work flawlessly for a non-technical Mac user?
3. **Actionable Fixes:** Provide the exact code changes or instructions needed to ensure it works perfectly on her Mac desktop out of the box.

Make your response extremely clear, encouraging, and focused on making this a perfect birthday gift!
"""
contents_to_send.append(prompt)

print("\nInitializing stateful chat session (model: gemini-2.5-flash)...")
chat = client.chats.create(model="gemini-2.5-flash")

base_out_file = r"C:\WEB CASE STUDY\Mac_Birthday_Present_Analysis.md"
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
print(f"Saved to {out_file}")
