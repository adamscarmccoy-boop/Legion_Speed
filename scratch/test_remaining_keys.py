import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests

print("Testing OpenRouter...")
r = requests.get(
    "https://openrouter.ai/api/v1/models",
    headers={"Authorization": "Bearer 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"},
    timeout=8,
)
print(f"  OpenRouter: {r.status_code}")

print("Testing HuggingFace...")
r2 = requests.get(
    "https://huggingface.co/api/whoami-v2",
    headers={"Authorization": "Bearer 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"},
    timeout=8,
)
if r2.status_code == 200:
    print(f"  HuggingFace: {r2.status_code} -> user: {r2.json().get('name', '?')}")
else:
    print(f"  HuggingFace: {r2.status_code} REJECTED")
