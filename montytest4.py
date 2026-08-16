import os
import sys
import time
import json
import traceback
from typing import Dict, Any

# Ensure line-buffered output globally
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import pydantic_monty as monty
    HAS_MONTY = True
except ImportError:
    HAS_MONTY = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


def initialize_gemini_client():
    """
    Explicitly maps `google_api_key` from .env to standard Google/LangChain env vars.
    """
    api_key = os.getenv("google_api_key") or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ Warning: `google_api_key` not found in environment.", flush=True)
        return None

    os.environ["GOOGLE_API_KEY"] = api_key
    os.environ["GEMINI_API_KEY"] = api_key
    print("✅ Gemini API Key mapped and bound to runtime environment.", flush=True)
    return api_key


def run_verified_benchmark(iterations: int = 1_000_000) -> Dict[str, Any]:
    """
    Executes sandboxed evaluations using the verified Pydantic-Monty pool context.
    """
    print("=" * 80, flush=True)
    print(f"🔥 VERIFIED MONTY SCALE BENCHMARK ({iterations:,} ITERATIONS)", flush=True)
    print("=" * 80, flush=True)

    test_code = "1024 * 2048 // 42"
    successes = 0
    failures = 0

    if not HAS_MONTY:
        print("❌ `pydantic_monty` not found in current venv.", flush=True)
        sys.exit(1)

    start_time_ns = time.perf_counter_ns()

    # 1. ENTER WORKER POOL CONTEXT
    with monty.Monty() as pool:
        # 2. CHECK OUT WORKER SESSION
        with pool.checkout() as session:
            for i in range(1, iterations + 1):
                try:
                    res = session.feed_run(test_code)
                    successes += 1
                except Exception as err:
                    failures += 1
                    if failures <= 3:
                        print(f"⚠️ [FAULT AT {i}]: {err}", flush=True)

                if i % 100_000 == 0 or i == iterations:
                    elapsed_sec = (time.perf_counter_ns() - start_time_ns) / 1_000_000_000.0
                    ops_sec = i / elapsed_sec
                    print(
                        f"  ├─ Iteration {i:>9,d}/{iterations:,d} | "
                        f"Successes: {successes:>9,d} | "
                        f"Throughput: {ops_sec:>10,.0f} ops/sec",
                        flush=True
                    )

    total_ns = time.perf_counter_ns() - start_time_ns
    total_ms = total_ns / 1_000_000.0
    avg_us = (total_ns / iterations) / 1_000.0
    throughput = iterations / (total_ns / 1_000_000_000.0)

    return {
        "benchmark": "Verified Pydantic-Monty Pool Worker Sandbox",
        "total_iterations": iterations,
        "successful_passes": successes,
        "failed_passes": failures,
        "pass_rate_percent": round((successes / iterations) * 100, 2),
        "total_time_ms": round(total_ms, 3),
        "avg_time_per_op_us": round(avg_us, 4),
        "ops_per_second": round(throughput, 2)
    }


def confirm_metrics_with_nemotron(metrics: Dict[str, Any]) -> None:
    """
    Pipes telemetry to Nemotron via local LM Studio instance on port 1234.
    """
    if not HAS_OPENAI:
        print("⚠️ OpenAI package not installed; skipping LM Studio dispatch.", flush=True)
        return

    print("\n" + "=" * 80, flush=True)
    print("📡 PIPING VERIFIED TELEMETRY TO NEMOTRON VIA LM STUDIO...", flush=True)
    print("=" * 80, flush=True)

    try:
        client = OpenAI(
            base_url="http://127.0.0.1:1234/v1",
            api_key="lm-studio"
        )

        prompt = f"""
You are the Lead System Architect for the ACP Control Plane.
Below is the raw telemetry from our verified Pydantic-Monty sandbox test:

{json.dumps(metrics, indent=2)}

Task:
1. Confirm pass_rate_percent is 100% and failures are 0.
2. Evaluate if the latency ({metrics['avg_time_per_op_us']} µs) and throughput ({metrics['ops_per_second']:,.0f} ops/sec) meet production control plane requirements.
3. Keep response concise, technical, and actionable.
"""

        start_llm = time.perf_counter()
        response = client.chat.completions.create(
            model="nvidia/nemotron-3-nano-4b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        elapsed_llm = (time.perf_counter() - start_llm) * 1000

        print(f"\n✅ [NEMOTRON RESPONDED IN {elapsed_llm:.2f} ms]:", flush=True)
        print("-" * 80, flush=True)
        print(response.choices[0].message.content, flush=True)
        print("-" * 80, flush=True)

    except Exception as exc:
        print(f"\n❌ Could not reach LM Studio on port 1234: {exc}", flush=True)


if __name__ == "__main__":
    try:
        # 1. Bind environment keys
        initialize_gemini_client()

        # 2. Run 1,000,000 iteration test with live flushing (logs every 100k passes)
        results = run_verified_benchmark(iterations=1_000_000)

        print("\n" + "=" * 80, flush=True)
        print("📊 VERIFIED TELEMETRY PAYLOAD", flush=True)
        print("=" * 80, flush=True)
        print(json.dumps(results, indent=2), flush=True)

        # 3. Pipe results to local Nemotron model
        confirm_metrics_with_nemotron(results)

    except Exception as e:
        traceback.print_exc()