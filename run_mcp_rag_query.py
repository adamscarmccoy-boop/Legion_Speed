import time
import json
import asyncio
import os
import sys

# Force UTF-8 stdout
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

async def main():
    query_str = "code genome brain"
    print(f"=== SOVEREIGN RAG BENCHMARK QUERY: '{query_str}' ===")
    t0 = time.perf_counter_ns()

    # Query RAG Engine
    sys.path.insert(0, r"C:\WEB CASE STUDY")
    from mcp_rag_server import semantic_code_search
    results = semantic_code_search(query_str, limit=3)
    t1 = time.perf_counter_ns()

    elapsed_ms = (t1 - t0) / 1_000_000.0
    elapsed_us = (t1 - t0) / 1_000.0

    print(f"\n[BENCHMARK] Retrieval Latency: {elapsed_ms:.3f} ms ({elapsed_us:.1f} μs)")
    print("\n=== EXTRACTED RAG DATA: CODE GENOME BRAIN ===")
    print(results)

    # Log telemetry evidence packet (Mandate: GEMINI.md)
    log_dir = r"C:\WEB CASE STUDY\logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"rag_query_genome_brain_{int(time.time())}.log")
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"Query: {query_str}\n")
        f.write(f"Latency: {elapsed_ms:.3f} ms ({elapsed_us:.1f} us)\n")
        f.write("Results:\n")
        f.write(str(results))

    print(f"\n[TELEMETRY] Evidence Packet Logged -> {log_file}")

if __name__ == "__main__":
    asyncio.run(main())
