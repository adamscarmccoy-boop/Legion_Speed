import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
try:
    with open(r'C:\gemini.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    messages = data.get('messages', [])
    for msg in messages[-25:]:
        role = msg.get('type', 'unknown')
        content_parts = msg.get('content', [])
        text_out = []
        for c in content_parts:
            if 'text' in c:
                text_out.append(c['text'])
            elif 'inlineData' in c:
                text_out.append(f"<MEDIA BLOB: {c['inlineData'].get('mimeType', 'unknown')}>")
        print(f"[{role.upper()}] {''.join(text_out)}\n")
except Exception as e:
    print(f"Error: {e}")
