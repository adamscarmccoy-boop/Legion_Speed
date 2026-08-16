import os
import sys
import time
from pydantic_monty import Monty

# Force UTF-8 stdout
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def parse_codebase(target_dir=r"C:\WEB CASE STUDY"):
    print(f"=== PYDANTIC-MONTY (RUST SANDBOX) CODEBASE SWEEP ===")
    print(f"Scanning target directory: {target_dir}")

    py_files = []
    for root, _, files in os.walk(target_dir):
        # Exclude virtual environments and hidden directories
        if ".venv" in root or "__pycache__" in root or ".git" in root or "node_modules" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))

    print(f"Found {len(py_files)} Python source files.")
    print("Launching Pydantic-Monty Rust Bytecode Sandbox Pool...\n")

    verified_count = 0
    failed_count = 0
    total_bytes = 0

    t_start = time.perf_counter()

    with Monty() as pool:
        for filepath in py_files:
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    code_content = f.read()
                
                total_bytes += len(code_content.encode("utf-8"))
                
                with pool.checkout() as session:
                    session.feed_run(code_content)
                verified_count += 1
            except Exception as e:
                failed_count += 1

    t_end = time.perf_counter()

    total_time_ms = (t_end - t_start) * 1000.0
    avg_per_file_ms = total_time_ms / len(py_files) if py_files else 0.0

    print("========================================================================")
    print("           PYDANTIC-MONTY RUST SANDBOX SWEEP RESULTS                    ")
    print("========================================================================")
    print(f"  Total Source Files Parsed : {len(py_files)}")
    print(f"  Total Code Bytes Read     : {total_bytes / (1024*1024):.2f} MB")
    print(f"  Clean / Verified ASTs     : {verified_count}")
    print(f"  Failed / Unsafe ASTs      : {failed_count}")
    print(f"  Total Sweep Latency       : {total_time_ms:.2f} ms")
    print(f"  Average Per-File Latency  : {avg_per_file_ms:.4f} ms ({avg_per_file_ms*1000:.1f} μs)")
    print("========================================================================")

if __name__ == "__main__":
    parse_codebase()
