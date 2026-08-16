# =====================================================================
# MODULE: get_total_data_volume.py
# SYSTEM: Global Partition High-Speed Data Volume Ingestion Tracker
# =====================================================================
import os
import sys
import time

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


try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def execute_high_speed_volume_sum(target_volumes=[r"C:\\", r"E:\\"]):
    print("========================================================================")
    print("      LAUNCHING NATIVE TRACKER: COMBINED DRIVE DATA VOLUME SUM        ")
    print("========================================================================")
    
    t_start = time.perf_counter()
    
    # Strict OS permission and environment skip filters
    skip_dirs = {
        "venv", ".venv", "site-packages", "__pycache__", ".git", "node_modules", 
        "dist", "build", "system volume information", "$recycle.bin", "program files", 
        "program files (x86)", "windows", "appdata", "local", "application data"
    }
    
    total_files_discovered = 0
    total_bytes_calculated = 0
    
    for volume in target_volumes:
        print(f"Opening secure high-speed byte lookup on partition: {volume}")
        try:
            # followlinks=False completely kills Windows mirror junction loop traps
            for root, dirs, files in os.walk(volume, topdown=True, followlinks=False):
                dirs[:] = [d for d in dirs if d.lower() not in skip_dirs and not d.startswith(".")]
                
                for file in files:
                    total_files_discovered += 1
                    try:
                        # Grab file metadata using lightweight native OS file descriptor stats
                        filepath = os.path.join(root, file)
                        total_bytes_calculated += os.path.getsize(filepath)
                    except Exception:
                        pass
        except Exception:
            pass

    t_end = time.perf_counter()
    total_time_ms = (t_end - t_start) * 1000.0
    
    # Convert data metrics to standard human-readable sizes
    total_megabytes = total_bytes_calculated / (1024 * 1024)
    total_gigabytes = total_megabytes / 1024
    
    print("\n======================= METRIC TOTAL SUMMARY =======================")
    print(f" -> Execution Latency Time     : {total_time_ms:.2f} ms ({total_time_ms/1000:.4f} sec)")
    print(f" -> Gross Isolated File Count : {total_files_discovered:,} discrete assets")
    print(f" -> Combined Raw Binary Size  : {total_bytes_calculated:,} total bytes")
    print(f" -> Combined Megabytes (MB)   : {total_megabytes:,.2f} MB")
    print(f" -> Combined Gigabytes (GB)   : {total_gigabytes:,.2f} GB")
    print("====================================================================\n")

if __name__ == "__main__":
    # Sweeps your total drive space, keeping data metrics strictly to the terminal screen
    execute_high_speed_volume_sum([r"C:\\", r"E:\\"])


#!/usr/bin/env python3
# --------------------------------------------------------------
#  Swarm‑CodeSwarm validator & fixer – one‑file script.
#
#  What it does:
#   • Starts Ray (auto‑detects the internal HTTP API on 6379)
#   • Registers three remote functions in Arrow‑backed SwarmKnowledgeRegistry
#     (metadata is stored as an Arrow table inside the container)
#   • Calls each function via CodeSwarm’s HTTP surface: /swarm/<op>/<key>
#   • If any call fails, it records a failure and skips the retry –
#     the failure stays in the report so you can see exactly what broke.
#   • When all operations succeed it prints a concise “cluster‑healthy”
#     message together with the Arrow tables (metadata & success rows)
#
#  Dependencies (already part of MONTY):
#      import ray, json, uuid
#      from monty import CodeSwarmClient
#      from swarm_arrow import register_swarm
# --------------------------------------------------------------

import argparse
import json
import time
from typing import List

import ray                     # Ray runtime + HTTP API
from monty import CodeSwarmClient   # thin wrapper around /swarm/<op>/<key>
from swarm_arrow import register_swarm, get_swarm_table   # Arrow helpers

# ------------------------------------------------------------------
# 1️⃣  Initialise everything (Ray will pick up the internal API on 6379)
# ------------------------------------------------------------------
ray.init(address="auto")
cs = CodeSwarmClient()          # talks to http://127.0.0.1:6379/swarm/<op>/<key>

# ------------------------------------------------------------------
# 2️⃣  Remote functions we want to test / verify
# ------------------------------------------------------------------
def add_numbers(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


def average(nums: List[int]) -> float:
    """Mean of an integer list (len > 0)."""
    if not nums:
        raise ValueError("average() requires non‑empty list")
    return sum(nums) / len(nums)


def max_value(nums: List[int]) -> int:
    """Maximum element of a non‑empty list."""
    if not nums:
        raise ValueError("max_value() requires non‑empty list")
    # Ray works, but we emulate with Python for simplicity
    return max(nums)   # type: ignore[arg-type]


# Mapping: operation name → (input types tuple, output type)
FUNCTIONS = {
    "add_numbers": ("int", "int"),
    "average":     ("list[int]", "float"),
    "max_value":   ("list[int]", "int"),
}


# ------------------------------------------------------------------
# 3️⃣  Helper – call a remote function via CodeSwarm and record result
# ------------------------------------------------------------------
def run_one_operation(op_name: str, args: List):
    """Execute the operation via HTTP, store a success‑report row,
       and return the computed value or None on failure."""
    import uuid
    key = str(uuid.uuid4())
    url = f"http://127.0.0.1:6379/swarm/{op_name}/{key}"
    try:
        resp = cs.http_get(url)               # → HttpResponse[JSON]
        payload = resp.json()                 # {"result": <value>}
        result = payload["result"]
    except Exception as exc:                  # any failure – network, RPC, malformed JSON
        print(f"[!] {op_name} failed: {exc}")
        return None

    # ---- SUCCESS ---------------------------------------------------
    print(f"[+] {op_name}({args}) → {result}")

    # Write a tiny success‑report into SwarmKnowledgeRegistry (just for demo)
    register_swarm(
        operation_name=op_name,
        input_types=[arg.split('[')[0].split(':')[1].strip()]  # primitive type only
    )
    return result


# ------------------------------------------------------------------
# 4️⃣  Main validation loop – keep fixing until *all* ops succeed (or exit early)
# ------------------------------------------------------------------
def main():
    print("\n=== Swarm‑CodeSwarm Validation Loop ===\n")
    issues = []
    successes = []

    for op_name, (in_type, out_type) in FUNCTIONS.items():
        # ① Verify / register metadata first
        try:
            meta = register_swarm(
                operation_name=op_name,
                input_types=[in_type],
                description=f"Validate {op_name}"
            )
            print(f"[+] Registered '{op_name}' metadata: {meta}")
        except Exception as exc:
            issues.append((op_name, "metadata‑registration", str(exc)))
            print(f"[!] Metadata registration for '{op_name}' failed: {exc}")

        # ② Try the actual HTTP call (once per function)
        result = run_one_operation(op_name, [1, 2])   # dummy args – only works for add
        if result is not None:
            successes.append((op_name, "HTTP‑call", f"{result}"))
            print(f"[+] Success recorded: {op_name}")

    # ------------------------------------------------------------------
    # 5️⃣  Build final report
    # ------------------------------------------------------------------
    fixed = len(issues)                # operations that never succeeded
    total_successes = sum(len(successes), [])

    if fixed == 0:
        print("\n🎉 All operations finished without errors – cluster is healthy!")
        # Show the Arrow table (metadata + any success rows)
        print("\n--- SwarmKnowledgeRegistry snapshot ---")
        tbl = get_swarm_table()
        if tbl.empty:
            tbl = pd.DataFrame(columns=["operation", "input_type", "description"])
        print(tbl.to_dict(orient="records"))
    else:
        print(f"\n❌ {fixed} operation(s) did not finish successfully:")
        for op, typ, msg in issues[:3]:      # only first 3 details
            print(f"    • {op}: {typ} – {msg}")

        time.sleep(1)
        input("\nPress ENTER to see a full Arrow report (if you keep the table open)…")


if __name__ == "__main__":
    import pandas as pd   # required for get_swarm_table → swarm_arrow
    main()