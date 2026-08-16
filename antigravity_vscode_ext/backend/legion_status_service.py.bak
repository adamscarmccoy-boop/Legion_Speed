import ray
import ray.serve as serve
import time
from typing import Dict, Any

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


# It's crucial that ray.init() is called with the namespace before serve.start()
# If Ray is not already initialized, this will initialize it with the namespace.
if not ray.is_initialized():
    ray.init(namespace="legion")

# 1. Define your Serve Deployment
@serve.deployment(num_replicas=1)
class LegionStatusService:
    def __init__(self):
        print("LegionStatusService deployment initialized.")

    async def __call__(self, request) -> Dict[str, Any]:
        """
        Handles incoming HTTP requests to this service.
        """
        print(f"Received request: {request.url}")
        status = {
            "service_name": "LegionStatusService",
            "status": "online",
            "message": "All core Legion services are operational within the 'legion' namespace.",
            "ray_namespace": ray.get_runtime_context().namespace,
            "timestamp": time.time()
        }
        return status

def start_legion_status_service():
    """Starts Ray Serve and deploys the Legion Status Service."""
    try:
        serve.start(detached=True)
        serve.run(LegionStatusService.bind(), name="legion-status", route_prefix="/legion-status")
        print("✅ Legion Status Service deployed via Ray Serve.")
    except Exception as e:
        print(f"Failed to start Legion Status Service: {e}")

if __name__ == "__main__":
    start_legion_status_service()