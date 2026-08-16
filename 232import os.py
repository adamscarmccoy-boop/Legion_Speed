import os
import sys
import time
import json
import traceback
from typing import Dict, Any

try:
    import pydantic_monty as monty
    HAS_MONTY = True
except ImportError:
    HAS_MONTY = False

def run_real_scale_test(iterations: int = 1_000_000) -> Dict[str, Any]:
    print("=" * 80)
    print(f"🔥 INITIATING REAL SCALE FIRE TEST ({iterations:,} ITERATIONS)")
    print("=" * 80, flush=True)
    
    if not HAS_MONTY:
        print("❌ Cannot run test without pydantic_monty.")
        return {}
        
    test_code = "1024 * 2048 // 42"
    successes = 0
    failures = 0
    
    start_time_ns = time.perf_counter_ns()
    
    # 1. Safely open the pool
    with monty.Monty() as pool:
        # 2. Check out the dedicated session
        with pool.checkout() as session:
            for i in range(1, iterations + 1):
                try:
                    # 3. Removed .output - Monty natively unwraps primitive returns!
                    res = session.feed_run(test_code)
                    successes += 1
                except Exception as err:
                    failures += 1
                    if failures <= 3:
                        print(f"⚠️ [FAULT AT {i}]: {err}", flush=True)
                    
                    # Prevent lockups if the worker dies
                    if isinstance(err, getattr(monty, 'MontyCrashedError', Exception)):
                        break
                    
                # Print live updates every 100k passes so Windows doesn't look frozen
                if i % 100_000 == 0 or i == iterations:
                    elapsed_sec = (time.perf_counter_ns() - start_time_ns) / 1_000_000_000.0
                    ops_sec = i / elapsed_sec if elapsed_sec > 0 else 0
                    print(f"  ├─ Iteration {i:>9,d} | Successes: {successes:>9,d} | Throughput: {ops_sec:>10,.0f} ops/sec", flush=True)

    total_ns = time.perf_counter_ns() - start_time_ns
    total_ms = total_ns / 1_000_000.0
    avg_us = (total_ns / iterations) / 1_000.0
    throughput = iterations / (total_ns / 1_000_000_000.0)

    results = {
        "benchmark": "Pydantic-Monty Production Scale Test",
        "total_iterations": iterations,
        "successful_passes": successes,
        "failed_passes": failures,
        "pass_rate_percent": round((successes / iterations) * 100, 2),
        "total_time_ms": round(total_ms, 3),
        "avg_time_per_op_us": round(avg_us, 4),
        "ops_per_second": round(throughput, 2)
    }
    
    print("\n" + "=" * 80)
    print("📊 VERIFIED TELEMETRY PAYLOAD")
    print("=" * 80)
    print(json.dumps(results, indent=2), flush=True)
    return results

if __name__ == "__main__":
    try:
        run_real_scale_test(1_000_000)
    except Exception as e:
        traceback.print_exc()