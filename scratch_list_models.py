import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("AISTUDIO_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("API Key not found!")
    exit(1)

client = genai.Client(api_key=api_key)

try:
    print("Fetching models using google-genai SDK...")
    models = client.models.list()
    for model in models:
        print(f"Model: {model.name}")
except Exception as e:
    print("Error listing models:", e)
