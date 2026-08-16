import os
import sys
import subprocess

# --- AUTO-INSTALL GOOGLE-GENAI ---
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("📦 Module 'google-genai' not found. Installing now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "google-genai"])
    from google import genai
    from google.genai import types

from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("AISTUDIO_API_KEY") or os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: GEMINI_API_KEY not found in .env")
    sys.exit(1)

client = genai.Client(api_key=api_key)

walkthrough_path = r"C:\Users\adams\.gemini\antigravity-ide\brain\ab68d511-5685-4692-8293-08a6b2fa31c1\walkthrough.md"
print(f"Uploading context from {walkthrough_path}...")
walkthrough_file = client.files.upload(
    file=walkthrough_path,
    config=types.UploadFileConfig(mime_type="text/plain")
)

prompt = """
You are a Staff Audio Engineer and Antigravity Expert. 
We are building the "Sovereign Audio Link" using sounddevice and Pedalboard on Windows.

CURRENT ISSUES:
1. AUDIO QUALITY: 29% High-Frequency Noise detected. Verdict: NOISY/STATIC.
2. HARDWARE: Realtek(R) Audio via Stereo Mix.
3. ENVIRONMENT: Windows, Jupyter Notebook.

TASK:
Give us the exact 'Zero-Static' configuration. 
Should we use 44.1kHz vs 48kHz? 
What blocksize and latency settings will kill that 29% noise floor?
Provide a robust Python code snippet for the capture.
"""

print("Consulting Antigravity Brain (Gemma 4 26B)...\n" + "="*70)

try:
    response = client.models.generate_content(
        model="models/gemma-4-26b-a4b-it",
        contents=[walkthrough_file, prompt],
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(include_thoughts=True)
        )
    )
    print(response.text)
    
    with open("antigravity_advice.md", "w", encoding="utf-8") as out:
        out.write(response.text)
except Exception as e:
    print(f"\nError: {e}")

print("\n" + "="*70)
print("Advice saved to antigravity_advice.md")
