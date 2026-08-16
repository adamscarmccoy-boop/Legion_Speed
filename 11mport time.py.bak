import os
import sys
import time
import traceback
import ray

# ==============================================================================
# SOVEREIGN LIFE-CYCLE STABILIZER (AUTO-INJECTED)
# Prevents dangling stdout/stdio pipes and GCS registry locks on Windows exit
# ==============================================================================
import atexit
import signal

def clean_exit_handler(*args, **kwargs):
    import sys
    sys.stderr.write("\n[LMS LIFECYCLE] Exit triggered. Flushing system streams...\n")
    sys.stderr.flush()
    try:
        import ray
        if ray.is_initialized():
            sys.stderr.write("[LMS LIFECYCLE] Active Ray session detected. Disconnecting...\n")
            ray.shutdown()
    except Exception:
        pass
    sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================


try:
    import pydantic_monty as monty
    HAS_MONTY = True
except ImportError:
    HAS_MONTY = False

def run_self_healing_benchmark(iterations: int = 1_000_000):
    print("=" * 80)
    print(f"🔥 INITIATING SELF-HEALING FIRE TEST ({iterations:,} ITERATIONS)")
    print("=" * 80, flush=True)
    
    if not HAS_MONTY:
        print("❌ Cannot run test without pydantic_monty.")
        return
        
    test_code = "1024 * 2048 // 42"
    successes = 0
    failures = 0
    
    start_time_ns = time.perf_counter_ns()
    
    # THE SELF-HEALING OUTER LOOP
    # Keeps running until we hit the target iterations, even if workers die
    while successes + failures < iterations:
        try:
            # 1. Safely open the pool
            with monty.Monty() as pool:
                # 2. Check out the dedicated session
                with pool.checkout() as session:
                    while successes + failures < iterations:
                        i = successes + failures + 1
                        try:
                            # 3. Execute in Rust VM
                            res = session.feed_run(test_code)
                            successes += 1
                        except Exception as err:
                            failures += 1
                            if failures <= 3:
                                print(f"⚠️ [FAULT AT {i}]: {err}", flush=True)
                            
                            # 4. THE CIRCUIT BREAKER:
                            # If the worker dies, break the inner loop. 
                            # The outer `while` loop will instantly check out a fresh worker!
                            if isinstance(err, getattr(monty, 'MontyCrashedError', Exception)):
                                print("🔄 [SELF-HEALING]: Dead pipe detected. Spawning fresh worker...", flush=True)
                                break
                                
                        # Print live updates without terminal lockup
                        if (successes + failures) % 100_000 == 0 or (successes + failures) == iterations:
                            elapsed_sec = (time.perf_counter_ns() - start_time_ns) / 1_000_000_000.0
                            ops_sec = (successes + failures) / elapsed_sec if elapsed_sec > 0 else 0
                            print(f"  ├─ Passes {successes + failures:>9,d} | Throughput: {ops_sec:>10,.0f} ops/sec", flush=True)
                            
        except Exception as e:
            print(f"❌ Critical Pool Error: {e}")
            break

    print("\n" + "=" * 80)
    print("✅ LOOP COMPLETE!")
    print(f"Successes: {successes:,} | Failures: {failures:,}")
    print("=" * 80)

if __name__ == "__main__":
    try:
        # Ignore re-init errors so Ray doesn't throw split-brain assertions on old sessions
        ray.init(ignore_reinit_error=True)
        run_self_healing_benchmark()
    except Exception as e:
        traceback.print_exc()