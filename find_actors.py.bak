import ray
import sys

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


def scan_cluster():
    try:
        ray.init(address='auto', namespace='legion', ignore_reinit_error=True)
        print("=" * 50)
        print("  RAY CLUSTER ACTOR SCAN")
        print("=" * 50)
        
        # Access the internal Ray state to find all actors
        from ray.util.state import STATE
        state = STATE.get_state()
        actors = state.get('actors', {})
        
        if not actors:
            print("No active actors found in the cluster.")
            return

        print(f"Found {len(actors)} active actors:\n")
        for aid, info in actors.items():
            name = info.get('name', 'Unnamed')
            print(f"ID: {aid} | Name: {name}")
            
        print("=" * 50)
    except Exception as e:
        print(f"Error scanning cluster: {e}")

if __name__ == '__main__':
    scan_cluster()