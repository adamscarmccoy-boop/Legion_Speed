"""
Ask Antigravity Session
=======================
Demonstrates how to run a stateful, streaming multi-turn chat session with memory
using the modern google-genai SDK. It uploads files first, then initializes 
a persistent chat that retains all conversational memory.
Guarantees unique output files and never overwrites previous files.
"""
import os
import sys
from google import genai
from google.genai import types
from dotenv import load_dotenv

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

load_dotenv()
client = genai.Client()

print("=== Starting Stateful Antigravity Chat Session ===")

# 1. Upload contextual files
uploaded_files = []
files_to_upload = [
    (r"C:\WEB CASE STUDY\current_session_chat.md", "Session Chat"),
    (r"C:\WEB CASE STUDY\AI_MODE.md", "AI Engine Spec")
]

for path, display_name in files_to_upload:
    if os.path.exists(path):
        print(f"Uploading {display_name} ({os.path.basename(path)})...")
        uploaded = client.files.upload(
            file=path,
            config=types.UploadFileConfig(mime_type="text/plain", display_name=display_name)
        )
        uploaded_files.append(uploaded)
    else:
        print(f"⚠️ Warning: Context file not found at {path}")

# 2. Initialize the stateful Chat with memory
print("\nInitializing persistent chat session (model: gemini-2.5-flash)...")
chat = client.chats.create(model="gemini-2.5-flash")

# 3. Seed the chat session with the initial system context and files
initial_prompt = [
    "You are a senior technical architect and audio/DSP engineer. I have attached the following context files for our session:\n"
]
for f in uploaded_files:
    initial_prompt.append(f)

initial_prompt.append(
    "\nPlease analyze these files and acknowledge that you are ready to help me build, refine, and master our audio architecture. Keep your tone professional, concise, and focused on clean DSP code."
)

# Determine unique file name for session log
base_log_path = r"C:\WEB CASE STUDY\antigravity_session_log.md"
log_path = base_log_path
if os.path.exists(log_path):
    base, ext = os.path.splitext(base_log_path)
    i = 1
    while os.path.exists(f"{base}_{i}{ext}"):
        i += 1
    log_path = f"{base}_{i}{ext}"

print(f"Streaming initial response from Antigravity (logging to: {os.path.basename(log_path)})...\n" + "-"*50)
with open(log_path, "w", encoding="utf-8") as out_log:
    response = chat.send_message_stream(initial_prompt)
    for chunk in response:
        text = chunk.text or ""
        print(text, end="", flush=True)
        out_log.write(text)
    out_log.write("\n\n" + "="*50 + "\n\n")
print("\n" + "-"*50)

# 4. Multi-turn conversation loop (Memory is automatically preserved inside 'chat'!)
print("\nChat Session Active! You can now have a continuous conversation.")
print("Type 'exit' or 'quit' to end the session.\n")

while True:
    try:
        user_input = input("You: ")
        if user_input.strip().lower() in ["exit", "quit"]:
            print("Ending session. Goodbye!")
            break
            
        if not user_input.strip():
            continue

        print("\nAntigravity: ", end="")
        with open(log_path, "a", encoding="utf-8") as out_log:
            out_log.write(f"User: {user_input}\n\nAntigravity: ")
            stream_response = chat.send_message_stream(user_input)
            for chunk in stream_response:
                text = chunk.text or ""
                print(text, end="", flush=True)
                out_log.write(text)
            out_log.write("\n\n" + "-"*30 + "\n\n")
        print("\n")
        
    except KeyboardInterrupt:
        print("\nEnding session. Goodbye!")
        break
    except Exception as e:
        print(f"\nError: {e}\n")
