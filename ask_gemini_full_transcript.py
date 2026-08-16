"""
Ask Gemini Full Transcript Help
===============================
1. Exports the entire conversation transcript to Markdown.
2. Uploads the transcript file via Google GenAI SDK.
3. Asks Gemini: "please help me do what i have been asking for this entire time"
"""
import os, sys, json
from google import genai
from google.genai import types
from dotenv import load_dotenv

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

load_dotenv()

# Step 1: Export Conversation Transcript to Markdown
log_path = r"C:\Users\adams\.gemini\antigravity-ide\brain\c4fe5f1e-faae-49b3-9d6d-54afc1c21b7c\.system_generated\logs\transcript.jsonl"
md_out_path = r"C:\WEB CASE STUDY\entire_conversation_history.md"

md_lines = ["# FULL CONVERSATION TRANSCRIPT\n"]
if os.path.exists(log_path):
    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                data = json.loads(line)
                step_type = data.get("type", "ACTION")
                content = data.get("content", "")
                if content:
                    md_lines.append(f"### [{step_type}]\n{content}\n")
            except Exception:
                pass

with open(md_out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines))

print(f"✅ Exported full conversation transcript ({len(md_lines)} blocks) to: {md_out_path}")

# Step 2: Upload to Gemini via SDK
client = genai.Client()

print(f"Uploading transcript file ({os.path.basename(md_out_path)})...")
uploaded_file = client.files.upload(
    file=md_out_path,
    config=types.UploadFileConfig(mime_type="text/plain", display_name="entire_conversation_history.md")
)
print(f"✅ Uploaded file: {uploaded_file.name}")

# Step 3: Exact Prompt
user_prompt = "please help me do what i have been asking for this entire time"

print(f"\nSending prompt: '{user_prompt}'")
response_file = r"C:\WEB CASE STUDY\gemini_transcript_help_response.md"

with open(response_file, "w", encoding="utf-8") as out_f:
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[uploaded_file, user_prompt]
        )
        res_text = response.text or ""
        print("\n" + "="*70 + "\n=== GEMINI RESPONSE ===\n" + "="*70 + "\n")
        print(res_text)
        out_f.write(res_text)
    except Exception as e:
        print(f"\nAPI Error: {e}")

print("\n" + "="*70)
print(f"✅ Saved response to: {response_file}")
