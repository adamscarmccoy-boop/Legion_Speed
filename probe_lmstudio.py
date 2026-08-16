import requests
import json

BASE = "http://127.0.0.1:1234"

print("=" * 60)
print("LM STUDIO — LIVE MODEL INVENTORY")
print("=" * 60)

# 1. List all models
try:
    r = requests.get(f"{BASE}/v1/models", timeout=5)
    data = r.json()
    models = data.get("data", [])
    print(f"\nTotal models loaded: {len(models)}\n")
    for m in models:
        print(f"  MODEL ID   : {m['id']}")
        print(f"  Object     : {m.get('object')}")
        print(f"  Owned By   : {m.get('owned_by')}")
        print()
except Exception as e:
    print(f"[ERROR] /v1/models failed: {e}")
    models = []

print("=" * 60)
print("EMBEDDING DIMENSION PROBES")
print("=" * 60)

# 2. Try each model for embedding dims
test_models = [m["id"] for m in models]
# Also try common aliases LM Studio accepts
test_models += [
    "nomic-ai/nomic-embed-text-v1.5-GGUF",
    "nomic-embed-text-v1.5.Q4_K_M",
    "text-embedding-nomic-embed-text-v1.5",
    "text-embedding-snowflake-arctic-embed-l-v2.0",
    "text-embedding-snowflake-arctic-embed-l-v2.0",
]

seen = set()
for model_id in test_models:
    if model_id in seen:
        continue
    seen.add(model_id)
    try:
        r2 = requests.post(
            f"{BASE}/v1/embeddings",
            json={"input": "dimension probe", "model": model_id},
            timeout=10
        )
        if r2.status_code == 200:
            d2 = r2.json()
            vec = d2["data"][0]["embedding"]
            returned_model = d2.get("model", "unknown")
            print(f"\n  REQUEST model : {model_id}")
            print(f"  RETURNED model: {returned_model}")
            print(f"  DIMENSIONS    : {len(vec)}")
            print(f"  First 3 vals  : {vec[:3]}")
        else:
            print(f"\n  [{r2.status_code}] {model_id} -> {r2.text[:100]}")
    except Exception as e:
        print(f"\n  [ERROR] {model_id} -> {e}")

print("\n" + "=" * 60)
print("WHAT YOUR CODE HARDCODES vs WHAT LM STUDIO SERVES")
print("=" * 60)
print("  Your code sends  : 'text-embedding-snowflake-arctic-embed-l-v2.0'")
print("  LM Studio serves : whatever is currently LOADED (ignores the name)")
print("  LanceDB expects  : 1024-D text_vector column")
print("=" * 60)
