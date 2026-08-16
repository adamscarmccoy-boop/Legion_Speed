import os
import sys
import time
import ray
from pydantic_monty import Monty

# Force UTF-8 stdout
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

@ray.remote(num_cpus=1)
class RayMontyWorker:
    def __init__(self, worker_id):
        self.worker_id = worker_id

    def verify_file_chunk(self, file_paths):
        results = []
        with Monty() as pool:
            for filepath in file_paths:
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        code = f.read()
                    with pool.checkout() as session:
                        session.feed_run(code)
                    results.append((filepath, True, len(code), None))
                except Exception as e:
                    results.append((filepath, False, len(code), str(e)))
        return results

def run_ray_monty_sweep(target_dir=r"C:\WEB CASE STUDY"):
    print("=== RAY-PARALLEL PYDANTIC-MONTY RUST SANDBOX SWEEP ===")
    print("Initializing / Connecting to Ray Cluster...")

    ray.init(
        address="auto", 
        namespace="legion", 
        ignore_reinit_error=True,
        runtime_env={
            "env_vars": {
                "PYTHONPATH": r"C:\WEB CASE STUDY\.venv\Lib\site-packages;C:\WEB CASE STUDY\.venv\Lib\site-packages"
            }
        }
    )
    print("Successfully locked onto Ray Cluster!\n")

    skip_dirs = {, ".venv", "site-packages", "__pycache__", ".git", "node_modules", "prometheus", "dist", "build"}
    py_files = []
    for root, dirs, files in os.walk(target_dir):
        # Exclude directories in-place
        dirs[:] = [d for d in dirs if d.lower() not in skip_dirs and not d.startswith(".")]
        for file in files:
            if file.endswith(".py") and not file.startswith("."):
                py_files.append(os.path.join(root, file))

    num_files = len(py_files)
    num_workers = min(8, max(2, os.cpu_count() or 4))
    print(f"Found {num_files} Python source files. Partitioning across {num_workers} Ray Monty Workers...")

    # Partition file paths evenly across workers
    chunk_size = (num_files + num_workers - 1) // num_workers
    chunks = [py_files[i:i + chunk_size] for i in range(0, num_files, chunk_size)]

    t0 = time.perf_counter()

    workers = [RayMontyWorker.remote(i) for i in range(len(chunks))]
    futures = [workers[i].verify_file_chunk.remote(chunks[i]) for i in range(len(chunks))]

    raw_results = ray.get(futures)

    t1 = time.perf_counter()

    all_results = [item for sublist in raw_results for item in sublist]
    verified = sum(1 for r in all_results if r[1])
    failed = sum(1 for r in all_results if not r[1])
    total_bytes = sum(r[2] for r in all_results)

    elapsed_ms = (t1 - t0) * 1000.0
    avg_file_us = (elapsed_ms * 1000.0) / num_files if num_files else 0.0

    print("\n========================================================================")
    print("      RAY + PYDANTIC-MONTY RUST PARALLEL SWEEP COMPLETE RESULTS        ")
    print("========================================================================")
    print(f"  Ray Cluster Workers Used : {len(chunks)}")
    print(f"  Total Source Files Parsed: {num_files}")
    print(f"  Total Code Bytes Read    : {total_bytes / (1024*1024):.2f} MB")
    print(f"  Clean / Verified ASTs    : {verified}")
    print(f"  Failed / Unsafe ASTs     : {failed}")
    print(f"  Total Parallel Latency   : {elapsed_ms:.2f} ms")
    print(f"  Average Per-File Speed   : {avg_file_us:.2f} μs")
    print("========================================================================")

if __name__ == "__main__":
    run_ray_monty_sweep()
