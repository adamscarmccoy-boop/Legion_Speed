import os
import sys
from dotenv import load_dotenv

# 1. Install/Import the NEW official Google SDK
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Installing the new google-genai SDK...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "google-genai"])
    from google import genai
    from google.genai import types

# Load your AI Studio API Key from .env
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("❌ ERROR: GEMINI_API_KEY not found in .env file.")
    sys.exit(1)

# 2. Initialize the exact same AI Studio connection
client = genai.Client(api_key=API_KEY)

# We use the massive 27B open-weights model hosted on AI Studio
MODEL_ID = "gemma-2-27b-it"

print("=========================================================")
print(f"🎙️ AI STUDIO TERMINAL REPLACEMENT ({MODEL_ID})")
print("=========================================================")
print("Type 'exit' to quit.\n")

# Start an infinite chat loop just like the old CLI!
chat = client.chats.create(model=MODEL_ID)

while True:
    user_input = input("You: ")
    if user_input.lower() in ['exit', 'quit']:
        break
        
    print("\nGemma is thinking...")
    
    # Send the message to Google's cloud
    response = chat.send_message(user_input)
    
    # Print the response back to your terminal
    print(f"\nGemma: {response.text}\n")
    print("-" * 50)
