import ray
from ray.data import from_items

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


# Initialize Ray with custom resources and dashboard enabled
try:
    ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
    print("Connected to existing Ray cluster.")
except ConnectionError:
    print("No running Ray cluster found. Starting new local instance...")
    ray.init(num_cpus=8, num_gpus=1, resources={"special_hardware": 1}, dashboard_host="0.0.0.0", ignore_reinit_error=True)

# Define a resource-constrained actor
@ray.remote(num_cpus=2, num_gpus=1, resources={"special_hardware": 1})
class MyActor:
    def compute(self, x):
        return x * 2

# Create actors
actors = [MyActor.remote() for _ in range(1)]

# Define a resource-constrained task
@ray.remote(num_cpus=1)
def process(x):
    return x + 1

# Use Ray Data for distributed processing
ds = from_items([{"value": i} for i in range(100)])
ds = ds.map_batches(lambda batch: [{"value": x["value"] * 10} for x in batch])

# Submit jobs to actors and tasks
results = ray.get([actor.compute.remote(i) for i, actor in enumerate(actors)])
task_results = ray.get([process.remote(i) for i in range(10)])

# Monitor via Ray Dashboard at http://localhost:8265
print("Actor results:", results)
print("Task results:", task_results)
print("Ray Data sample:", ds.take(5))

ray.shutdown()