import os
import time
import typing
import pyarrow as pa
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


os.environ["RAY_DISABLE_VERSION_CHECK"] = "1"
os.environ["RAY_ACCEL_ENV_VAR_OVERRIDE_ON_ZERO"] = "0"

ray.init(address="auto", namespace="legion", ignore_reinit_error=True)

print("=" * 70)
print("🚀 SCARS_LAB DISTRIBUTED PIPELINE ENGINE INITIALIZED")
print("=" * 70)

# -------------------------------------------------------------------
# 1. PANINI RAG ENGINE (BATCH INGESTION ACTOR)
# -------------------------------------------------------------------
@ray.remote
class PaniniRagEngineActor:
    def __init__(self, batch_size: int = 500):
        self.batch_size = batch_size
        self.buffer = []
        self.total_ingested = 0

    def ingest_row(self, row: dict) -> typing.Optional[ray.ObjectRef]:
        self.buffer.append(row)
        if len(self.buffer) >= self.batch_size:
            return self.flush_batch()
        return None

    def flush_batch(self) -> typing.Optional[ray.ObjectRef]:
        if not self.buffer:
            return None
        
        ids = [r.get("id", 0) for r in self.buffer]
        contents = [r.get("content", "") for r in self.buffer]
        
        arrow_table = pa.table({
            "id": ids,
            "content": contents
        })
        
        table_ref = ray.put(arrow_table)
        self.total_ingested += len(self.buffer)
        print(f"📦 [PaniniRagEngine] Flushed batch of {len(self.buffer)} rows to Shared Memory.")
        
        self.buffer = []
        return table_ref

# -------------------------------------------------------------------
# 2. SOVEREIGN SIEVE AGENT (BATCH PROCESSING ACTOR)
# -------------------------------------------------------------------
@ray.remote
class SovereignSieveAgentActor:
    def __init__(self, partition_count: int = 32):
        self.partition_count = partition_count

    def process_partitioned_batch(self, table_or_ref: typing.Union[pa.Table, ray.ObjectRef]) -> dict:
        start_time = time.time()
        
        if isinstance(table_or_ref, ray.ObjectRef):
            arrow_table = ray.get(table_or_ref)
        else:
            arrow_table = table_or_ref
        
        # Convert PyArrow to partitioned Ray Dataset
        ds = ray.data.from_arrow(arrow_table)
        
        # Fixed split call for Ray Data API:
        shards = ds.split(n=self.partition_count, equal=True)
        
        processed_count = arrow_table.num_rows
        latency_ms = (time.time() - start_time) * 1000
        
        print(f"⚡ [SovereignSieve] Processed {processed_count} rows across {len(shards)} shards in {latency_ms:.2f}ms.")
        return {
            "status": "SUCCESS",
            "rows_processed": processed_count,
            "latency_ms": latency_ms
        }

# -------------------------------------------------------------------
# 3. PIPELINE ORCHESTRATION
# -------------------------------------------------------------------
def run_pipeline():
    print("\n1. Instantiating Actor Handles...")
    panini_actor = PaniniRagEngineActor.remote(batch_size=500)
    sieve_actor = SovereignSieveAgentActor.remote(partition_count=32)
    
    try:
        acp = ray.get_actor("ACPControlPlane", namespace="legion")
        acp.register_agent.remote(
            agent_id="panini_ingest_01",
            agent_name="PaniniRagEngineActor",
            capabilities=["batch_ingest", "plasma_push"],
            endpoint_uri="127.0.0.1:8265"
        )
        print("✅ Registered PaniniRagEngineActor with ACPControlPlane.")
    except Exception as e:
        print(f"⚠️ ACP Registration notice: {e}")

    print("\n2. Executing 1,000 Row Micro-Batch Ingestion Test...")
    
    active_batch = None
    for i in range(1000):
        ref_future = panini_actor.ingest_row.remote({"id": i, "content": f"telemetry_payload_node_{i}"})
        batch_res = ray.get(ref_future)
        if batch_res is not None:
            active_batch = batch_res

    if active_batch is None:
        active_batch = ray.get(panini_actor.flush_batch.remote())

    print("\n3. Triggering SovereignSieve Processing across Shared Memory...")
    if active_batch is not None:
        sieve_future = sieve_actor.process_partitioned_batch.remote(active_batch)
        metrics = ray.get(sieve_future)
        print(f"\n📊 Final Pipeline Metrics: {metrics}")
    else:
        print("❌ No batch object reference created.")

if __name__ == "__main__":
    try:
        run_pipeline()
    finally:
        ray.shutdown()
        print("\nPipeline execution complete. Ray session detached cleanly.")