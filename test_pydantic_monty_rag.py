# ============================================================================
# SOVEREIGN RAG-V1 + PYDANTIC-MONTY (C++/RUST SANDBOX) INTEGRATION TEST
# Runs Sub-Millisecond Vector Retrieval + Pydantic-Monty Rust Isolation
# ============================================================================

import sys
import time
import numpy as np

# Force UTF-8 stdout
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from pydantic_monty import Monty, ResourceLimits

print("========================================================================")
print("SOVEREIGN ENGINE: RAG-V1 + PYDANTIC-MONTY (RUST/C++ SANDBOX) TEST")
print("========================================================================")

# 1. Initialize Vector Data Index (Sub-Millisecond Vector Memory RAG)
documents = [
    {
        "id": 101,
        "title": "DSP Audio Gain Modulator",
        "code": "def process(val):\n    return val * 1.5",
        "vec": np.sin(np.arange(128) * 0.1, dtype=np.float32)
    },
    {
        "id": 102,
        "title": "FMA Latent Tensor Transformation",
        "code": "def fma_transform(x):\n    return x * 2.8934 + 1.0\nresult = fma_transform(10.0)",
        "vec": np.cos(np.arange(128) * 0.1, dtype=np.float32)
    },
    {
        "id": 103,
        "title": "Pydantic Monty State Verifier",
        "code": "data = [1, 2, 3, 4]\nresult = sum(data)",
        "vec": np.sin(np.arange(128) * 0.3, dtype=np.float32)
    }
]

# 2. Vector Search (Simulating C++ Cosine Matrix Match)
query_vec = np.cos(np.arange(128) * 0.1, dtype=np.float32)

t0 = time.perf_counter()
scores = [np.dot(query_vec, doc["vec"]) / (np.linalg.norm(query_vec) * np.linalg.norm(doc["vec"])) for doc in documents]
best_idx = int(np.argmax(scores))
t1 = time.perf_counter()

rag_latency_us = (t1 - t0) * 1_000_000

matched_doc = documents[best_idx]
print(f"[RAG-V1] Vector Match in {rag_latency_us:.2f} us ({rag_latency_us/1000:.4f} ms):")
print(f"   Doc ID:       {matched_doc['id']}")
print(f"   Title:        {matched_doc['title']}")
print(f"   Cosine Sim:   {scores[best_idx]:.4f}")
print(f"   Code Payload:\n{matched_doc['code']}")
print("------------------------------------------------------------------------")

# 3. Feed Payload directly into Pydantic-Monty C++/Rust Sandbox Pool
print("[MONTY] Launching Pydantic-Monty (C++/Rust Native Bytecode Sandbox Pool)...")

t2 = time.perf_counter()
with Monty() as pool:
    with pool.checkout() as session:
        res = session.feed_run(matched_doc["code"])
t3 = time.perf_counter()

monty_latency_us = (t3 - t2) * 1_000_000

print(f"[MONTY] Execution Complete in {monty_latency_us:.2f} us ({monty_latency_us/1000:.4f} ms)!")
print(f"   Return Value: {res}")
print("------------------------------------------------------------------------")
print(f"[SUCCESS] TOTAL RAG-V1 + PYDANTIC-MONTY LATENCY: {(rag_latency_us + monty_latency_us):.2f} us ({(rag_latency_us + monty_latency_us)/1000:.4f} ms)")
print("========================================================================")
