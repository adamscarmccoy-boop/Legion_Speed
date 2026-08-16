"""
Ask Gemini for Notebook Cells
=============================
Uploads:
1. recent_conversation_history.md
2. gemini_transcript_help_response.md 
3. MUSIC_AND_VIDEO.html
And asks for the exact 5-7 notebook cells required by the user.
"""
import os, sys
from google import genai
from google.genai import types
from dotenv import load_dotenv

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

load_dotenv()
client = genai.Client()

files_to_upload = [
    r"C:\WEB CASE STUDY\recent_conversation_history.md",
    r"C:\WEB CASE STUDY\gemini_transcript_help_response.md",
    r"C:\WEB CASE STUDY\MUSIC_AND_VIDEO.html"
]

uploaded_files = []
for p in files_to_upload:
    if os.path.exists(p):
        print(f"Uploading {os.path.basename(p)}...")
        mime_type = 'text/html' if p.endswith('.html') else 'text/markdown'
        uploaded_file = client.files.upload(
            file=p,
            config=types.UploadFileConfig(mime_type=mime_type, display_name=os.path.basename(p))
        )
        uploaded_files.append(uploaded_file)
        print(f"✅ Uploaded file: {uploaded_file.name}")
    else:
        print(f"⚠️ File not found: {p}")

user_prompt = '''i need the next 5-7 cells to connect the marketing tables to the vision and music/social media content/ and i need it error handled, using ray, validated with pydantics, and all assumptions or MOCK PATHs to be mentioned at the top of each cell. with these cells, they need to be raw visually new creations, i have enough ray cpu to do REAL GENERATION. DO NOT TOUCH MY PICTURES, use my logo at most, AND make sure my marketing tables have a new ingestion cell that is verified and ran deep into the already good scraper code i have'''

print(f"\nSending prompt: '{user_prompt}'")
response_file = r"C:\WEB CASE STUDY\gemini_cells_response.md"

with open(response_file, "w", encoding="utf-8") as out_f:
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=uploaded_files + [user_prompt]
        )
        res_text = response.text or ""
        print("\n" + "="*70 + "\n=== GEMINI RESPONSE ===\n" + "="*70 + "\n")
        print(res_text)
        out_f.write(res_text)
    except Exception as e:
        print(f"\nAPI Error: {e}")

print("\n" + "="*70)
print(f"✅ Saved response to: {response_file}")
