import requests
import json
import sys
import os

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

url = "http://127.0.0.1:1234/v1/chat/completions"

ray_worker_hpp_path = r"c:\WEB CASE STUDY\ray_cpp_engine\ray_worker.hpp"
ray_worker_cpp_path = r"c:\WEB CASE STUDY\ray_cpp_engine\ray_worker.cpp"
lms_router_ts_path = r"c:\WEB CASE STUDY\rag-v2\src\services\LMStudioRouter.ts"
prompt_prep_ts_path = r"c:\WEB CASE STUDY\rag-v2\src\promptPreprocessor.ts"

with open(ray_worker_hpp_path, 'r', encoding='utf-8') as f:
    hpp_content = f.read()

with open(ray_worker_cpp_path, 'r', encoding='utf-8') as f:
    cpp_content = f.read()

with open(lms_router_ts_path, 'r', encoding='utf-8') as f:
    ts_router_content = f.read()

with open(prompt_prep_ts_path, 'r', encoding='utf-8') as f:
    ts_prep_content = f.read()

system_msg = "You are the Senior Core System Architect evaluating the Sovereign C++ and LM Studio SDK integration."

user_prompt = f"""
Please inspect and confirm the following code files for our zero-copy C++ Ray Worker and LM Studio SDK RAG plugin:

### FILE 1: `ray_cpp_engine/ray_worker.hpp` (C++20 Header & CUDA IPC struct)
```cpp
{hpp_content}
```

### FILE 2: `ray_cpp_engine/ray_worker.cpp` (CUDA VRAM Allocation, cudaIpcGetMemHandle, PyBind11)
```cpp
{cpp_content}
```

### FILE 3: `rag-v2/src/services/LMStudioRouter.ts` (Dynamic 1024-D / 768-D Dimension Router)
```typescript
{ts_router_content}
```

### FILE 4: `rag-v2/src/promptPreprocessor.ts` (LM Studio In-Process Hook, LanceDB & DuckDB)
```typescript
{ts_prep_content[:1500]}
```

Provide your technical confirmation:
1. Is the CUDA IPC zero-copy memory transfer struct and VRAM allocation properly structured for bare-metal C++?
2. Does the LM Studio TypeScript SDK router correctly handle the 1024-D Snowflake and 768-D Nomic embeddings without Python in the loop?
3. How should the user trigger the 3-line SDK in LM Studio?
"""

payload = {
    "model": "nvidia/nemotron-3-nano-4b",
    "messages": [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_prompt}
    ],
    "temperature": 0.1,
    "max_tokens": 1024
}

print("🚀 Dispatching C++ and TypeScript SDK files directly to LM Studio for confirmation...")
try:
    resp = requests.post(url, json=payload, timeout=180)
    if resp.status_code == 200:
        content = resp.json()["choices"][0]["message"]["content"]
        print("\n" + "=" * 70)
        print("🏛️ LM STUDIO ARCHITECT CONFIRMATION REPORT")
        print("=" * 70)
        print(content)
    else:
        print(f"HTTP Error {resp.status_code}: {resp.text}")
except Exception as e:
    print("Error communicating with LM Studio:", e)
