import sys
sys.stdout.reconfigure(encoding="utf-8")
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


def verify_legion_connection():
    print("Attempting to handshake with Sovereign Ray Cluster...")
    try:
        # 'auto' tells Ray to look for an existing cluster on the local node
        # If you have ray start --head running, this is the ONLY way to find it.
        ray.init(address='auto', ignore_reinit_error=True)
        
        # If we reach here, we are connected. Now let's probe the cluster.
        nodes = ray.nodes()
        print(f"✅ HANDSHAKE SUCCESSFUL")
        print(f"🌐 Connected to cluster with {len(nodes)} node(s).")
        
        # Test the actual compute pipeline: Deploy a tiny remote function
        @ray.remote
        def ping():
            return "PONG from the Cluster"
        
        result = ray.get(ping.remote())
        print(f"🚀 COMPUTE VERIFIED: {result}")
        
    except Exception as e:
        print(f"❌ CONNECTION FAILED")
        print(f"Diagnostic Error: {str(e)}")
        print("\n--- Potential Root Causes ---")
        print("1. Is Terminal 1 actually running 'ray start --head'?")
        print("2. Is there still a space in your path (C:\\WEB CASE STUDY vs C:\\WEB_CASE_STUDY)?")
        print("3. Is Windows Firewall blocking port 6379?")

if __name__ == "__main__":
    verify_legion_connection()