import ray
import time

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
    ray.init(address='auto', ignore_reinit_error=True)
    print("✅ Connected to Control Plane.")

    # TEST 1: CPU-Only Task (Tests Plasma Store/Shared Memory)
    @ray.remote(num_gpus=0) # Explicitly tell Ray NOT to touch the GPU
    def cpu_ping():
        return "CPU-PONG"

    print("🛰️ Testing CPU Data Plane...")
    start = time.time()
    print(f"🚀 Result: {ray.get(cpu_ping.remote())} (Time: {time.time()-start:.2f}s)")
    print("✅ CPU Data Plane is HEALTHY.")

    # TEST 2: GPU Task (Tests VRAM Availability)
    @ray.remote(num_gpus=0.1) # Request a tiny sliver of GPU
    def gpu_ping():
        return "GPU-PONG"

    print("\n🛰️ Testing GPU Data Plane...")
    start = time.time()
    print(f"🚀 Result: {ray.get(gpu_ping.remote())} (Time: {time.time()-start:.2f}s)")
    print("✅ GPU Data Plane is HEALTHY.")

except Exception as e:
    print(f"❌ Failed: {e}")