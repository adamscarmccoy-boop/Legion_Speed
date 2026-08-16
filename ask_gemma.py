import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

error_message = """
2026-07-09 22:59:21,707 - httpx - INFO - HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 404 Not Found"
2026-07-09 22:59:21,709 - api_bridge - ERROR - Error during chat: Error code: 404 - {'error': {'message': 'No endpoints found for google/gemma-2-9b-it.', 'code': 404}, 'user_id': 'user_3DAw8py0oHLgLUzqeS0bOpSIqRW'}
Traceback (most recent call last):
  ...
openai.NotFoundError: Error code: 404 - {'error': {'message': 'No endpoints found for google/gemma-2-9b-it.', 'code': 404}, 'user_id': 'user_3DAw8py0oHLgLUzqeS0bOpSIqRW'}
"""

file_path = r"C:\Users\adams\.vscode\extensions\legion.antigravity-swarm-1.0.0\backend\legion_langgraph_brain.py"
with open(file_path, 'r', encoding='utf-8') as f:
    code = f.read()

prompt = f"""
I am getting this 404 error when running my LangGraph agent:
{error_message}

Here is my code for `legion_langgraph_brain.py`. How do I fix the model endpoint error so it uses the Gemma 4 31B model directly from Google AI Studio instead of OpenRouter?

```python
{code}
```
"""

model_name = "gemma-4-31b-it"
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

payload = {
    "contents": [{"parts": [{"text": prompt}]}]
}

print("Asking Gemma 4 31B directly for the fix...")
try:
    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
    if response.status_code == 200:
        data = response.json()
        reply = data['candidates'][0]['content']['parts'][0]['text']
        print("\n--- GEMMA'S RESPONSE ---\n")
        print(reply)
        
        # Save Gemma's response to a markdown file for the user to read easily
        with open("GEMMA_FIX.md", "w", encoding="utf-8") as f:
            f.write(reply)
        print("\n(Saved Gemma's response to GEMMA_FIX.md)")
    else:
        print(f"FAILED with status {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
