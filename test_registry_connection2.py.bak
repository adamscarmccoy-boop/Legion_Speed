import ray
import psutil

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


ray.init(address="auto", ignore_reinit_error=True)

try:
    daemon = ray.get_actor("SwarmKnowledgeWorker")
    status = ray.get(daemon.sync_from_disk.remote()) # Trigger a test sync
    print(f"--- DAEMON HEARTBEAT: {status} ---")
except Exception as e:
    print(f"--- DAEMON IS GHOSTED: {str(e)} ---")

# Check the Page File / RAM ratio
mem = psutil.virtual_memory()
swap = psutil.swap_memory()

print(f"\n--- HARDWARE TELEMETRY ---")
print(f"Physical RAM: {mem.percent}% used ({mem.used / 1e9:.2f} GB / {mem.total / 1e9:.2f} GB)")
print(f"Page File (Swap): {swap.percent}% used ({swap.used / 1e9:.2f} GB / {swap.total / 1e9:.2f} GB)")

if swap.percent > 80:
    print("\nCRITICAL: SYSTEM IS THRASHING. Page file is full.")
    print("ACTION: Reduce Ray --object-store-memory or prune the SwarmKnowledgeRegistry.")