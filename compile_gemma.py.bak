import os
import sys
import time
from pathlib import Path
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


@ray.remote(num_cpus=2)
def compile_gemma_to_onnx_task(model_id, output_dir):
    """
    Executes the Optimum compiler inside an isolated Ray worker to protect
    the main system memory and avoid total freezes.
    """
    print("=" * 80)
    print(f"[*] INITIALIZING RAY-MANAGED GRAPH COMPILATION FOR: {model_id}")
    print("=" * 80)
    
    start_time = time.perf_counter()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Task 'causal-lm-with-past' triggers KV-Caching natively within the ONNX engine
    # Updated to opset 18 per warning logs for gemma2
    compilation_cmd = (
        f"optimum-cli export onnx "
        f"--model {model_id} "
        f"--task causal-lm-with-past "
        f"--device cpu "
        f"--opset 18 " 
        f'"{output_dir}"'
    )
    
    print(f"[*] Spawning compiler pipeline inside Ray worker...")
    print(f"[*] Command: {compilation_cmd}\n")
    
    exit_code = os.system(compilation_cmd)
    
    print("-" * 80)
    if exit_code == 0:
        elapsed = time.perf_counter() - start_time
        print(f"[+] COMPILATION SUCCESSFUL | Latency: {elapsed:.2f} seconds")
        print(f"[+] Clean, serialized model layers generated inside: {output_dir}")
        for file in os.listdir(output_dir):
            if file.endswith(('.onnx', '.json')):
                size_mb = os.path.getsize(os.path.join(output_dir, file)) / (1024 * 1024)
                print(f"    -> {file} ({size_mb:.2f} MB)")
        return True
    else:
        print(f"[-] Critical Error: Compiler engine threw an unexpected exit code: {exit_code}")
        return False

def main():
    print("[*] Initializing Ray connection to manage compilation resources safely...")
    # Follow the rules: hard cap object store memory to 1.5GB to avoid starving the 16GB system
    import os
    if "RAY_ADDRESS" in os.environ:
        del os.environ["RAY_ADDRESS"]
    try:
        ray.init(address="local", namespace="legion", object_store_memory=1500 * 1024 * 1024, ignore_reinit_error=True)
    except Exception as e:
        print(f"[*] Ray init exception: {e}")
        
    model_id = "google/gemma-2-2b-it"
    output_dir = r"C:\WEB CASE STUDY\gemma_onnx"
    
    print(f"[*] Dispatching ONNX compilation for {model_id} to Ray cluster...")
    future = compile_gemma_to_onnx_task.remote(model_id, output_dir)
    success = ray.get(future)
    
    if success:
        print("[+] Ray task completed successfully.")
    else:
        print("[-] Ray task failed.")

if __name__ == "__main__":
    main()