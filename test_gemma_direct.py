import os
import requests
import json
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("ERROR: GOOGLE_API_KEY is not set in your .env file.")
    exit(1)

# Direct Google AI Studio Endpoint for Gemma 4 31B
model_name = "gemma-4-31b-it"
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

payload = {
    "contents": [{
        "parts": [{"text": "Hello from the raw API! Are you online and working?"}]
    }]
}

print(f"Sending direct raw HTTP request to Google AI Studio ({model_name})...")
print("-" * 50)

try:
    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        data = response.json()
        reply = data['candidates'][0]['content']['parts'][0]['text']
        print("SUCCESS! Response from Gemma:\n")
        print(reply)
    else:
        print(f"FAILED with status {response.status_code}")
        print("Error Details:")
        print(json.dumps(response.json(), indent=2))
        
except Exception as e:
    print(f"CRITICAL ERROR connecting to API: {e}")
