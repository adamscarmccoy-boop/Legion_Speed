import sys
import time
import json
import traceback

# Force unbuffered output globally so prints show immediately
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)

print("=" * 80, flush=True)
print("🔍 MONTY RUNTIME DIAGNOSTIC INSPECTOR", flush=True)
print("=" * 80, flush=True)

# 1. IMPORTS
print("1. Testing Imports...", end=" ", flush=True)
try:
    import pydantic_monty as monty
    print("✅ pydantic_monty imported successfully.", flush=True)
except Exception as e:
    print(f"❌ Failed to import pydantic_monty: {e}", flush=True)
    sys.exit(1)

# 2. POOL INITIALIZATION
print("2. Initializing Worker Pool...", end=" ", flush=True)
try:
    start_pool = time.perf_counter()
    pool = monty.Monty()
    pool.__enter__()
    print(f"✅ Worker pool online in {(time.perf_counter() - start_pool)*1000:.2f} ms.", flush=True)
except Exception as e:
    print(f"❌ Pool initialization failed: {e}", flush=True)
    sys.exit(1)

# 3. WORKER CHECKOUT
print("3. Checking out session from worker pool...", end=" ", flush=True)
try:
    start_checkout = time.perf_counter()
    session = pool.checkout().__enter__()
    print(f"✅ Session acquired in {(time.perf_counter() - start_checkout)*1000:.2f} ms.", flush=True)
except Exception as e:
    print(f"❌ Session checkout failed: {e}", flush=True)
    pool.__exit__(None, None, None)
    sys.exit(1)

# 4. SMALL BATCH BENCHMARK (1,000 ITERATIONS WITH FLUSHED LOGS)
print("\n4. Running 1,000-pass probe with forced unbuffered output...", flush=True)

test_code = "1024 * 2048 // 42"
successes = 0
failures = 0

start_loop = time.perf_counter_ns()

for i in range(1, 1001):
    try:
        res = session.feed_run(test_code)
        successes += 1
    except Exception as exc:
        failures += 1
        if failures <= 3:
            print(f"\n⚠️ Exception on pass {i}: {exc}", flush=True)

    if i % 100 == 0:
        elapsed_ms = (time.perf_counter_ns() - start_loop) / 1_000_000.0
        print(f"  ├─ Pass {i:>4d}/1000 | Successes: {successes} | Failures: {failures} | Elapsed: {elapsed_ms:.2f} ms", flush=True)

total_ns = time.perf_counter_ns() - start_loop
total_ms = total_ns / 1_000_000.0
avg_us = (total_ns / 1000) / 1_000.0
throughput = 1000 / (total_ns / 1_000_000_000.0)

print("\n" + "=" * 80, flush=True)
print("📊 PROBE RESULTS", flush=True)
print("=" * 80, flush=True)
print(f"  • Total Time:   {total_ms:.3f} ms", flush=True)
print(f"  • Avg Latency:  {avg_us:.4f} µs/op", flush=True)
print(f"  • Throughput:   {throughput:,.2f} ops/sec", flush=True)

# CLEANUP
print("\n5. Cleaning up worker session and pool...", end=" ", flush=True)
session.__exit__(None, None, None)
pool.__exit__(None, None, None)
print("✅ Clean shutdown complete.", flush=True)