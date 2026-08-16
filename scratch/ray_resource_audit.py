import sys, json, time
sys.stdout.reconfigure(encoding='utf-8')
import requests

print("=" * 60, flush=True)
print("  RAY CLUSTER RESOURCE & PROCESS AUDIT", flush=True)
print("=" * 60, flush=True)

# 1. Node resources
print("\n--- NODE RESOURCES ---", flush=True)
try:
    r = requests.get("http://127.0.0.1:8265/api/v0/nodes", timeout=5)
    data = r.json().get("data", {}).get("summary", [])
    for node in data:
        print(f"  Node: {node.get('nodeId','?')[:12]}", flush=True)
        print(f"    CPU: {node.get('cpuCount',0)}  GPU: {node.get('gpuCount',0)}", flush=True)
        mem = node.get('mem', [0,0,0])
        print(f"    RAM used: {mem[0]/1e9:.1f} GB / {mem[1]/1e9:.1f} GB ({mem[2]:.0f}%)" if isinstance(mem, list) and len(mem) >= 3 else f"    RAM: {mem}", flush=True)
        obj = node.get('objectStoreUsedMemory', 0)
        obj_avail = node.get('objectStoreAvailableMemory', 0)
        print(f"    Object Store: {obj/1e6:.0f} MB used / {(obj+obj_avail)/1e6:.0f} MB total", flush=True)
except Exception as e:
    print(f"  Error: {e}", flush=True)

# 2. Actors
print("\n--- LIVE ACTORS ---", flush=True)
try:
    r = requests.get("http://127.0.0.1:8265/api/v0/actors?limit=100", timeout=5)
    actors = r.json().get("data", {}).get("actors", {})
    if not actors:
        print("  No actors found", flush=True)
    for aid, a in actors.items():
        name = a.get("name", "unnamed")
        state = a.get("state", "?")
        cls = a.get("className", "?")
        pid = a.get("pid", "?")
        print(f"  [{state:10s}] {name:40s} class={cls} pid={pid}", flush=True)
except Exception as e:
    print(f"  Error: {e}", flush=True)

# 3. Serve deployments  
print("\n--- RAY SERVE DEPLOYMENTS ---", flush=True)
try:
    r = requests.get("http://127.0.0.1:8265/api/serve/deployments/", timeout=5)
    deployments = r.json().get("deployments", {})
    for name, d in deployments.items():
        status = d.get("status", "?")
        replicas = d.get("replicas", [])
        print(f"  [{status:10s}] {name} ({len(replicas)} replicas)", flush=True)
except Exception as e:
    print(f"  Error: {e}", flush=True)

# 4. Running/pending tasks
print("\n--- RUNNING TASKS (top 20) ---", flush=True)
try:
    r = requests.get("http://127.0.0.1:8265/api/v0/tasks?limit=20&filter_keys=state&filter_values=RUNNING", timeout=5)
    tasks = r.json().get("data", {}).get("result", [])
    if not tasks:
        print("  No running tasks", flush=True)
    for t in tasks:
        name = t.get("name", t.get("func_or_class_name", "?"))
        state = t.get("state", "?")
        task_type = t.get("type", "?")
        print(f"  [{state}] {name} type={task_type}", flush=True)
except Exception as e:
    print(f"  Error: {e}", flush=True)

# 5. Jobs
print("\n--- RAY JOBS ---", flush=True)
try:
    r = requests.get("http://127.0.0.1:8265/api/v0/jobs/", timeout=5)
    jobs = r.json()
    if isinstance(jobs, list):
        for j in jobs[:10]:
            jid = j.get("job_id", "?")
            status = j.get("status", "?")
            pid = j.get("driver_pid", "?")
            print(f"  [{status:10s}] job={jid} driver_pid={pid}", flush=True)
    else:
        print(f"  Response: {str(jobs)[:300]}", flush=True)
except Exception as e:
    print(f"  Error: {e}", flush=True)

# 6. Check Windows processes hogging Python/Ray
print("\n--- PYTHON PROCESSES (Windows) ---", flush=True)
import subprocess
result = subprocess.run(
    ["powershell", "-Command", "Get-Process python*, ray* -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, CPU, WorkingSet64 | Format-Table -AutoSize"],
    capture_output=True, text=True, timeout=10
)
print(result.stdout if result.stdout.strip() else "  No python/ray processes found", flush=True)

print("\n" + "=" * 60, flush=True)
print("  AUDIT COMPLETE", flush=True)
print("=" * 60, flush=True)
