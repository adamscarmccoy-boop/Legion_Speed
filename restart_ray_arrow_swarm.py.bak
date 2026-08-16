import os
import sys
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


sys.stdout.reconfigure(encoding='utf-8')

print("==================================================================")
print("     RESTARTING RAY ARROW SWARM WITH OPTIMIZED MEMORY             ")
print("==================================================================")

try:
    if ray.is_initialized():
        ray.shutdown()
    
    # Initialize Ray with explicit object store memory limit (2GB shared RAM)
    ray.init(object_store_memory=2 * 1024 * 1024 * 1024, ignore_reinit_error=True)
    print("✅ Ray Swarm restarted successfully with 2GB Object Store Memory!")
except Exception as e:
    print(f"⚠️ Ray Swarm restart note: {e}")

print("==================================================================")