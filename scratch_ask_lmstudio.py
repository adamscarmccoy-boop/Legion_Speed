import urllib.request
import urllib.error
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = 'http://localhost:1234/v1/chat/completions'
headers = {'Content-Type': 'application/json'}
data = {
    'model': 'local-model',
    'messages': [
        {'role': 'system', 'content': 'You are an AI assistant connected via LM Studio with access to tools (like Monty and Legion Graph) and the local filesystem.'},
        {'role': 'user', 'content': 'Find the hardcoded .venv files (specifically those referencing E:\\WEB CASE STUDY) and tell us how to switch them, then run the code to fix it and run it in monty.'}
    ],
    'temperature': 0.7
}

try:
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        print(result['choices'][0]['message']['content'])
except urllib.error.URLError as e:
    print(f'Error connecting to LM Studio: {e}')
