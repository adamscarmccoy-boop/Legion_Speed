import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("AISTUDIO_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemma-4-26b-a4b-it?key={api_key}"
req = urllib.request.Request(url)
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        print("Schema for gemma-4-26b-a4b-it:")
        print(json.dumps(data, indent=2))
except Exception as e:
    print("Error:", e)
