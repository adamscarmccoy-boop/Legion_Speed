import os
import sys
import time
import typing
import ray
from ray import data
import ray as ray_state
import ray  as ray_worker

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
    # Avoid raising SystemExit inside an atexit callback (which causes RuntimeWarnings)
    if args and isinstance(args[0], int):
        sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================


# ------------------------------------------------------------------------------
# 1. CLUSTER ATTACHMENT & LEGION NAMESPACE INITIALIZATION
# ------------------------------------------------------------------------------
# Latch directly into the local active GCS head node (127.0.0.1:6379 / auto)
# bound to the target 'legion' namespace without re-initializing the process.
if not ray.is_initialized():
    ray.init(
        address="auto",
        namespace="legion",
        ignore_reinit_error=True,
        logging_level="info"
    )

print(f"[LEGION_RAY_CORE] Attached to Cluster Session: {ray.get_runtime_context().get_job_id()}")
print(f"[LEGION_RAY_CORE] Current Namespace: {ray.get_runtime_context().namespace}")
print(f"[LEGION_RAY_CORE] Available Resources: {ray.cluster_resources()}")

# ------------------------------------------------------------------------------
# 2. INTERNAL WORKER & NODE TELEMETRY EXTRACTION (ray/python/ray/_private/)
# ------------------------------------------------------------------------------
def fetch_legion_cluster_telemetry() -> dict:
    """
    Extracts core worker states, node manager configurations, and registered
    actors directly from the local GCS state table.
    """
    worker_instance = ray_worker.global_worker
    worker_instance.check_connected()
    
    active_nodes = ray.nodes()
    live_actors = ray_state.state.summarize_actors()
    named_actors = ray.util.list_named_actors(all_namespaces=True)
    
    telemetry_payload = {
        "node_count": len(active_nodes),
        "nodes": [
            {
                "node_id": n.get("NodeID"),
                "ip": n.get("NodeManagerAddress"),
                "status": "ALIVE" if n.get("Alive") else "DEAD",
                "resources": n.get("Resources", {})
            }
            for n in active_nodes
        ],
        "named_actors": named_actors,
        "raw_actor_summary": live_actors
    }
    return telemetry_payload

# ------------------------------------------------------------------------------
# 3. RAY WORKER TASK EXECUTION & RAY DATA PIPELINE
# ------------------------------------------------------------------------------
@ray.remote(num_cpus=1)
class LegionWorkerProcess:
    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.pid = os.getpid()

    def process_payload(self, batch: dict) -> dict:
        """Process incoming data batches on worker process."""
        items = batch.get("id", [])
        computed = [x * 2 for x in items]
        return {"id": items, "computed": computed, "worker_pid": [self.pid] * len(items)}

def execute_ray_data_pipeline():
    """
    Constructs a Ray Data Dataset using block execution and transforms it across
    distributed worker tasks.
    """
    print("[LEGION_DATA] Constructing Ray Data Dataset stream...")
    
    # Generate in-memory dataset via Ray Data
    ds = data.range(1000)
    
    # Apply batch transformations across worker resources
    transformed_ds = ds.map_batches(
        lambda batch: {"id": batch["id"], "value": [x ** 2 for x in batch["id"]]},
        batch_format="numpy"
    )
    
    # Filter dataset
    filtered_ds = transformed_ds.filter(lambda row: row["value"] % 2 == 0)
    
    # Materialize and extract telemetry from dataset memory blocks
    stats = filtered_ds.stats()
    sample_take = filtered_ds.take(10)
    
    print(f"[LEGION_DATA] Execution Stats:\n{stats}")
    print(f"[LEGION_DATA] Sample Output: {sample_take[:3]}")
    return stats

# ------------------------------------------------------------------------------
# 4. MAIN EXECUTION PIPELINE
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 80)
    print("LEGION SYSTEM TELEMETRY & RAY DATA PIPELINE EXECUTION")
    print("=" * 80)
    
    # 1. Audit Active Cluster Telemetry
    telemetry = fetch_legion_cluster_telemetry()
    print(f"[TELEMETRY] Detected Nodes: {telemetry['node_count']}")
    print(f"[TELEMETRY] Named Actors in Cluster: {telemetry['named_actors']}")
    
    # 2. Instantiate Legion Worker Process Actor
    worker_actor = LegionWorkerProcess.remote(worker_id="legion_node_01")
    print(f"[WORKER] Spawned LegionWorkerProcess handle: {worker_actor}")
    
    # 3. Run Ray Data Pipeline
    execute_ray_data_pipeline()
    
    print("=" * 80)
    print("EXECUTION COMPLETE: All worker and data handles integrated successfully.")
    print("=" * 80)