#!/usr/bin/env python3
"""
LEGION RAY C++ JIT ORCHESTRATOR
Compiles native C++/CUDA Ray actors on the fly using PyTorch JIT without CMake,
and wraps them in @ray.remote actors for zero-copy execution across the cluster.
"""

import os
import sys
import struct
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
    # Avoid raising SystemExit inside an atexit callback (which causes RuntimeWarnings)
    if args and isinstance(args[0], int):
        sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================


try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from torch.utils.cpp_extension import load

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CPP_SOURCE = os.path.join(CURRENT_DIR, "ray_worker.cpp")

print("=" * 65)
print("COMPILING / LOADING C++ RAY WORKER VIA PYTORCH JIT")
print("=" * 65)
print(f"Source: {CPP_SOURCE}")

# 1. On-the-fly PyTorch JIT Compilation (Cached at ~/.cache/torch_extensions/)
ray_cpp_module = load(
    name="ray_core_worker_jit",
    sources=[CPP_SOURCE],
    extra_cflags=["-O3", "-std=c++17"],
    verbose=True,
)
print("✨ [SUCCESS] C++ Module compiled & loaded into Python process memory!")


# 2. Ray Remote Actor Wrapping the JIT-Compiled C++ Module
@ray.remote(num_cpus=1)
class RayCppJitActor:
    def __init__(self, worker_id: int, gpu_id: int = 0, buffer_size_bytes: int = 1024 * 1024 * 4):
        self.worker_id = worker_id
        self.gpu_id = gpu_id
        self.buffer_size_bytes = buffer_size_bytes

        # Instantiate native C++ class compiled by PyTorch JIT
        self.cpp_worker = ray_cpp_module.RayCoreWorkerActor(
            worker_id, gpu_id, buffer_size_bytes
        )
        self.initialized = self.cpp_worker.initialize_core()
        print(f"[Worker {worker_id}] Status: {self.cpp_worker.get_status()}")

    def execute_subtask(self, action_vector: list[float]) -> dict:
        # Executes native C++ task & returns zero-copy byte payload
        payload_bytes = bytes(self.cpp_worker.execute_task_and_get_ipc_handle(action_vector))
        
        # Unpack header
        worker_id, buffer_size = struct.unpack("II", payload_bytes[:8])
        handle_bytes = payload_bytes[8:]
        return {
            "worker_id": worker_id,
            "buffer_size_bytes": buffer_size,
            "handle_len": len(handle_bytes),
            "status": self.cpp_worker.get_status()
        }

    def get_status(self) -> str:
        return self.cpp_worker.get_status()


# 3. Cluster Launcher
def launch_jit_cluster():
    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True)

    print(f"\n📡 Ray Cluster Resources: {ray.cluster_resources()}")
    
    # Spawn 4 parallel C++ Ray remote actors
    num_actors = 4
    actors = [
        RayCppJitActor.remote(worker_id=i, gpu_id=0, buffer_size_bytes=1024 * 1024)
        for i in range(num_actors)
    ]
    print(f"🚀 Spawned {len(actors)} parallel C++ Ray JIT Actors.")

    # Dispatch tasks in parallel
    test_vectors = [
        [0.1 * i, 0.2 * i, 0.3 * i, 128.0, -13.9, 5.69]
        for i in range(num_actors)
    ]

    futures = [actor.execute_subtask.remote(vec) for actor, vec in zip(actors, test_vectors)]
    results = ray.get(futures)

    print("\n" + "=" * 65)
    print("C++ RAY JIT EXECUTION RESULTS")
    print("=" * 65)
    for res in results:
        print(f"  Worker #{res['worker_id']}: Status={res['status']} | Buffer={res['buffer_size_bytes']} bytes | IPC Handle={res['handle_len']} bytes")

if __name__ == "__main__":
    launch_jit_cluster()