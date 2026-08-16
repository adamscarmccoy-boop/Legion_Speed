#!/usr/bin/env python3
import os
import sys
import argparse
import socket
import queue
import threading
import time
from openai import OpenAI

# ----------------------------------------------------------------------
# HIGH-PERFORMANCE STATIC EXCLUSIONS & CONFIG
# ----------------------------------------------------------------------
DEFAULT_PORTS = [1234, 1010, 56217, 61277]
EXCLUDE_DIRS = {
    '.git', '.venv', '.venv_314', 'node_modules', '__pycache__', 
    'artifacts', 'scratch', 'out', '.metadata', 'build', 'dist'
}
CODE_EXTENSIONS = {
    '.py', '.js', '.cpp', '.hpp', '.h', '.sh', '.json', '.md', '.sql', '.html', '.css'
}

# Ray integration check
try:
    import ray
    HAS_RAY = True
except ImportError:
    HAS_RAY = False

# ----------------------------------------------------------------------
# 1. ATOMIC SCANNING UNIT
# ----------------------------------------------------------------------
def scan_directory_single(dir_path, code_extensions, exclude_dirs):
    """Scans a single directory level using os.scandir (avoiding heavy os.walk overhead)."""
    local_files = []
    subdirs_to_queue = []
    
    try:
        with os.scandir(dir_path) as it:
            for entry in it:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        if entry.name not in exclude_dirs:
                            subdirs_to_queue.append(entry.path)
                    elif entry.is_file(follow_symlinks=False):
                        ext = os.path.splitext(entry.name)[1].lower()
                        if ext in code_extensions:
                            # Fast size check
                            size_bytes = entry.stat().st_size
                            
                            # Fast line-counting stream
                            line_count = 0
                            try:
                                with open(entry.path, "rb") as f:
                                    # Read in 64KB blocks for blazingly fast physical disk reads
                                    for chunk in iter(lambda: f.read(65536), b""):
                                        line_count += chunk.count(b'\n')
                            except OSError:
                                pass
                                
                            local_files.append({
                                "path": entry.path,
                                "ext": ext,
                                "size": size_bytes,
                                "lines": line_count
                            })
                except (OSError, PermissionError):
                    continue  # Silently bypass locked/permission-denied entities
    except (OSError, PermissionError):
        pass
        
    return local_files, subdirs_to_queue

# ----------------------------------------------------------------------
# 2. QUEUE-BASED PARALLEL TRAVERSAL (Consumes 0% idle CPU)
# ----------------------------------------------------------------------
def parallel_scan_queue(root_dir=".", max_workers=16, code_extensions=CODE_EXTENSIONS, exclude_dirs=EXCLUDE_DIRS):
    """
    Coordinates a high-speed multi-threaded directory crawl.
    Uses a thread-safe Queue and worker pool. This completely eliminates
    main-thread CPU spinning and avoids the overhead of managing dynamic lists of futures.
    """
    root_dir = os.path.abspath(root_dir)
    all_files = []
    
    q = queue.Queue()
    q.put(root_dir)
    
    lock = threading.Lock()
    active_workers = 0
    cv = threading.Condition()
    
    def worker():
        nonlocal active_workers
        while True:
            with cv:
                # Wait while queue is empty but other workers are still running
                while q.empty() and active_workers > 0:
                    cv.wait()
                
                # If queue is empty and no workers are running, we are fully done
                if q.empty() and active_workers == 0:
                    cv.notify_all()
                    return
                
                try:
                    dir_path = q.get_nowait()
                except queue.Empty:
                    continue
                
                active_workers += 1
            
            # Execute directory I/O outside of the monitor lock to allow concurrency
            files_found, subdirs_found = scan_directory_single(dir_path, code_extensions, exclude_dirs)
            
            with lock:
                all_files.extend(files_found)
                
            with cv:
                for subdir in subdirs_found:
                    q.put(subdir)
                active_workers -= 1
                q.task_done()
                cv.notify_all()
                
    threads = []
    for _ in range(max_workers):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)
        
    for t in threads:
        t.join()
        
    # Standardize absolute paths to relative paths
    total_lines = 0
    total_size = 0
    for f in all_files:
        f["path"] = os.path.relpath(f["path"], root_dir)
        total_lines += f["lines"]
        total_size += f["size"]
        
    return all_files, total_lines, total_size

# ----------------------------------------------------------------------
# 3. RAY-BASED PARALLEL CRAWLER (Optional distributed backend)
# ----------------------------------------------------------------------
if HAS_RAY:
    @ray.remote
    def ray_scan_dir_task(dir_path, code_extensions, exclude_dirs):
        return scan_directory_single(dir_path, code_extensions, exclude_dirs)

def parallel_scan_ray(root_dir=".", code_extensions=CODE_EXTENSIONS, exclude_dirs=EXCLUDE_DIRS):
    """
    Crawls your workspace using your active local or distributed Ray cluster.
    """
    if not HAS_RAY:
        print("❌ Ray Error: Ray is not installed or loaded in this virtual env.", file=sys.stderr)
        sys.exit(1)
        
    if not ray.is_initialized():
        print("📡 Connecting to your local Ray Cluster...")
        ray.init(ignore_reinit_error=True)
        
    root_dir = os.path.abspath(root_dir)
    all_files = []
    
    # We maintain a dynamic pool of object references (futures) in Ray
    pending_ids = [ray_scan_dir_task.remote(root_dir, code_extensions, exclude_dirs)]
    
    while pending_ids:
        # wait blocks until at least one object reference is ready
        ready_ids, pending_ids = ray.wait(pending_ids, num_returns=1)
        
        for obj_id in ready_ids:
            try:
                files_found, subdirs_found = ray.get(obj_id)
                all_files.extend(files_found)
                
                # Launch remote Ray tasks for each discovered subdirectory
                for subdir in subdirs_found:
                    pending_ids.append(
                        ray_scan_dir_task.remote(subdir, code_extensions, exclude_dirs)
                    )
            except Exception as e:
                print(f"⚠️ Ray Task Warning: {e}", file=sys.stderr)
                
    # Compile metrics
    total_lines = 0
    total_size = 0
    for f in all_files:
        f["path"] = os.path.relpath(f["path"], root_dir)
        total_lines += f["lines"]
        total_size += f["size"]
        
    return all_files, total_lines, total_size

# ----------------------------------------------------------------------
# 4. PORT DISCOVERY
# ----------------------------------------------------------------------
def find_active_inference_port(ports=DEFAULT_PORTS):
    """Scans loopback ports to locate where LM Studio or the local server is listening."""
    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.1)
            result = s.connect_ex(('127.0.0.1', port))
            if result == 0:
                return port
    return None

# ----------------------------------------------------------------------
# 5. STREAMING INFERENCE CONTROLLER
# ----------------------------------------------------------------------
def execute_query(prompt, port, model_name="nvidia/nemotron-3-nano-4b"):
    """Binds to the local OpenAI-compatible endpoint and streams response to stdout."""
    try:
        client = OpenAI(
            base_url=f"http://127.0.0.1:{port}/v1",
            api_key="lm-studio"
        )
        
        stream = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )
        
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                print(content, end="", flush=True)
        print()
        
    except Exception as e:
        print(f"\n❌ Inference Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

# ----------------------------------------------------------------------
# MAIN CLI CONTROLLER
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Forest CLI v4: High-performance parallel codebase auditor (Queue & Ray options)."
    )
    parser.add_argument(
        "query", 
        nargs="?", 
        default=None, 
        help="Custom instruction or query to run against your scanned code files."
    )
    parser.add_argument(
        "--path", \
        default=".", \
        help="Root directory path to scan (default: current directory)."
    )
    parser.add_argument(
        "--threads", \
        type=int, \
        default=16, \
        help="Number of concurrent crawler threads (default: 16)."
    )
    parser.add_argument(
        "--use-ray", \
        action="store_true", \
        help="Use local or distributed Ray cluster instead of threads."
    )
    parser.add_argument(
        "--port", \
        type=int, \
        default=None, \
        help="Force a specific loopback port instead of running dynamic auto-discovery."
    )
    parser.add_argument(
        "--model", \
        default="nvidia/nemotron-3-nano-4b", \
        help="Local target model identifier loaded in LM Studio."
    )
    
    args = parser.parse_args()
    
    # Port Detection
    target_port = args.port
    if not target_port:
        target_port = find_active_inference_port()
        if not target_port:
            print("❌ Port Error: Could not find an active local server on ports: " + ", ".join(map(str, DEFAULT_PORTS)), file=sys.stderr)
            sys.exit(1)
            
    # Executing the fast parallel scan
    if args.use_ray:
        if not HAS_RAY:
            print("❌ Ray module not installed or importable in this environment.", file=sys.stderr)
            sys.exit(1)
        files, total_lines, total_size = parallel_scan_ray(args.path, CODE_EXTENSIONS, EXCLUDE_DIRS)
    else:
        files, total_lines, total_size = parallel_scan_queue(args.path, args.threads, CODE_EXTENSIONS, EXCLUDE_DIRS)
    
    if not files:
        print(f"⚠️ No active code files found in '{args.path}'.", file=sys.stderr)
        sys.exit(0)
        
    # Format the prompt context
    file_list_str = "\n".join(
        [f"- {f['path']} ({f['lines']} lines, {f['size']} bytes)" for f in files]
    )
    
    preprompt = (
        f"You are a local workstation assistant auditing the physical codebase.\n"
        f"Below is the current structure and physical metrics of active code files:\n\n"
        f"--- WORKSPACE METRICS ---\n"
        f"Total Files Scanned: {len(files)}\n"
        f"Total Line Count: {total_lines}\n"
        f"Total Code Footprint: {total_size} bytes\n\n"
        f"--- ACTIVE CODE FILES ---\n"
        f"{file_list_str}\n"
        f"-------------------------\n\n"
    )
    
    if args.query:
        final_prompt = preprompt + f"User CLI Directive: {args.query}\n\nPlease answer based on the metrics above."
    else:
        final_prompt = preprompt + "Please provide a quick, high-level terminal-ready diagnostic summary of this codebase structure."

    execute_query(final_prompt, target_port, args.model)

if __name__ == "__main__":
    main()
