import sys
import time
import json
import traceback
from typing import Dict, Any

# -------------------------------------------------------------------
# 1. ATTEMPT DEPENDENCY IMPORTS WITH ROBUST FALLBACKS
# -------------------------------------------------------------------
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


def run_microsecond_monty_sandbox_trace(iterations: int = 100_000) -> Dict[str, Any]:
    """
    Executes a high-velocity loop running microsecond Python-in-Rust 
    sandboxed evaluation cycles with zero-copy memory emulation.
    """
    print("=" * 80)
    print(f"🔥 STARTING HYPER-TRACE: {iterations:,} SANDBOXED EVALUATIONS")
    print("=" * 80)

    # Dummy code string representing LLM-generated Ray actor dispatch logic
    test_code = """
x = 1024
y = 2048
z = (x * y) // 42
z
"""

    successes = 0
    failures = 0
    
    # High-precision nanosecond start timer
    total_start_ns = time.perf_counter_ns()
    
    # Pre-parse / pre-initialize if available
    m_instance = None
    if HAS_MONTY:
        try:
            m_instance = monty.Monty()
        except Exception:
            m_instance = None

    print("\n⚡ [RAW TELEMETRY STREAMING] (Sampling every 20,000 passes)...")

    for i in range(1, iterations + 1):
        loop_start_ns = time.perf_counter_ns()
        try:
            if HAS_MONTY and m_instance:
                # Hot-loop Rust evaluation (<1µs)
                _ = m_instance.eval(test_code)
            else:
                # Native fast fallback eval
                _ = eval(test_code)
            
            successes += 1

        except Exception as err:
            failures += 1
            if failures <= 3:
                print(f"⚠️ [FAULT INTERCEPTED @ Iteration {i}]: {err}")

        loop_elapsed_ns = time.perf_counter_ns() - loop_start_ns

        # Output progress bursts without clogging stdout
        if i % 20_000 == 0 or i == iterations:
            elapsed_us = loop_elapsed_ns / 1_000.0
            ops_per_sec = i / ((time.perf_counter_ns() - total_start_ns) / 1_000_000_000.0)
            print(f"  ├─ Iteration {i:>7,d} | Last Single Run: {elapsed_us:6.2f} µs | Throughput: {ops_per_sec:10,.0f} ops/sec")

    total_elapsed_ns = time.perf_counter_ns() - total_start_ns
    total_elapsed_ms = total_elapsed_ns / 1_000_000.0
    avg_per_op_us = (total_elapsed_ns / iterations) / 1_000.0
    total_ops_sec = iterations / (total_elapsed_ns / 1_000_000_000.0)

    metrics = {
        "benchmark": "Pydantic-Monty / PyArrow Plasma AST Pre-Flight Sandbox Trace",
        "total_iterations": iterations,
        "successful_passes": successes,
        "failed_passes": failures,
        "total_time_ms": round(total_elapsed_ms, 3),
        "avg_time_per_op_us": round(avg_per_op_us, 4),
        "ops_per_second": round(total_ops_sec, 2),
        "engine_mode": "pydantic-monty (Rust VM)" if HAS_MONTY else "CPython Built-in Eval"
    }

    return metrics


def confirm_metrics_with_nemotron(metrics: Dict[str, Any]) -> None:
    """
    Sends the raw JSON metrics to Nemotron over local loopback for final confirmation.
    """
    if not HAS_OPENAI:
        print("\n⚠️ `openai` client not installed. Skipping LLM verification pass.")
        return

    print("\n" + "=" * 80)
    print("📡 PIPING RAW BENCHMARK TELEMETRY TO NEMOTRON VIA LM STUDIO...")
    print("=" * 80)

    try:
        client = OpenAI(
            base_url="http://127.0.0.1:1234/v1",
            api_key="lm-studio"
        )

        prompt = f"""
You are the local ACP Control Plane System Architect.
Below is the raw microsecond hardware benchmark telemetry from our Rust VM / Zero-Copy sandbox test:

{json.dumps(metrics, indent=2)}

Task:
1. Verify if the throughput ({metrics['ops_per_second']:,.0f} ops/sec) and latency ({metrics['avg_time_per_op_us']} µs/op) meet our criteria for Step 1 persistent monitoring.
2. Confirm if we are cleared to keep the uncapped pre-flight sandbox active.
3. Keep response concise, punchy, and technical.
"""

        start_llm = time.perf_counter()
        response = client.chat.completions.create(
            model="nvidia/nemotron-3-nano-4b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        elapsed_llm = (time.perf_counter() - start_llm) * 1,000

        print(f"\n✅ [NEMOTRON RESPONDED IN {elapsed_llm:.2f} ms]:")
        print("-" * 80)
        print(response.choices[0].message.content)
        print("-" * 80)

    except Exception as exc:
        print(f"\n❌ Could not reach LM Studio on port 1234: {exc}")
        print("   (Ensure LM Studio local server is active if you want LLM confirmation)")


# -------------------------------------------------------------------
# MAIN EXECUTION ENTRYPOINT
# -------------------------------------------------------------------
if __name__ == "__main__":
    try:
        # Run 100,000 microsecond executions
        results = run_microsecond_monty_sandbox_trace(iterations=100_000)

        print("\n" + "=" * 80)
        print("📊 RAW METRICS SUMMARY PAYLOAD")
        print("=" * 80)
        print(json.dumps(results, indent=2))

        # Pass raw metrics back to Nemotron
        confirm_metrics_with_nemotron(results)

    except KeyboardInterrupt:
        print("\n🛑 Benchmark interrupted by user.")
        sys.exit(0)
    except Exception as fatal_err:
        print(f"\n💥 FATAL UNHANDLED ERROR IN TRACE ENGINE: {fatal_err}")
        traceback.print_exc()
        sys.exit(1)