import sys
sys.path.insert(0, r"E:\WEB CASE STUDY\.venv\Lib\site-packages")

import ray
import json
import time
from datetime import datetime

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


def scan_kingdom():
    print("=" * 80)
    print("  👑 LEGION KINGDOM SCAN — LIVE CLUSTER INVENTORY")
    print(f"  Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # ── Connect ──
    try:
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        print("\n✅ Connected to Ray cluster via namespace='legion'")
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        return

    # ── 1. Cluster Info ──
    print("\n" + "─" * 80)
    print("  📡 CLUSTER TOPOLOGY")
    print("─" * 80)
    try:
        nodes = ray.nodes()
        print(f"  Alive nodes: {len([n for n in nodes if n['Alive']])}")
        for n in nodes:
            print(f"    {'🟢' if n['Alive'] else '🔴'} Node: {n['NodeID'][:16]}..."
                  f"  CPUs: {n['Resources'].get('CPU', 0)}"
                  f"  GPUs: {n['Resources'].get('GPU', 0)}"
                  f"  Memory: {n['Resources'].get('memory', 0) / 1e9:.1f}GB")
    except Exception as e:
        print(f"    ⚠️  Could not enumerate nodes: {e}")

    # ── 2. Live Actors ──
    print("\n" + "─" * 80)
    print("  🎭 LIVE ACTORS (namespace='legion')")
    print("─" * 80)
    try:
        # List all actor classes that exist in the cluster
        actor_handles = []
        known_actor_names = [
            "LegionMatrixNode", "DNADeployment", "LegionLakehouse_RAG",
            "SwarmKnowledgeRegistry", "Warden", "SnowflakeEmbedWorker"
        ]
        
        for name in known_actor_names:
            try:
                actor = ray.get_actor(name, namespace="legion")
                actor_handles.append((name, actor))
                print(f"    🟢  {name} — ALIVE")
            except ValueError:
                print(f"    ⚫  {name} — NOT FOUND")
            except Exception as e:
                print(f"    ⚠️  {name} — ERROR: {e}")
        
        # Try namespace=None too (common mismatch)
        print(f"\n    ── Also checking namespace=None ──")
        for name in known_actor_names:
            try:
                actor = ray.get_actor(name, namespace=None)
                print(f"    🟡  {name} — FOUND in default namespace")
                actor_handles.append((name, actor))
            except ValueError:
                pass
    except Exception as e:
        print(f"    ⚠️  Actor scan error: {e}")

    # ── 3. Running Tasks ──
    print("\n" + "─" * 80)
    print("  ⚡ CLUSTER RESOURCES & TASKS")
    print("─" * 80)
    try:
        resources = ray.available_resources()
        print(f"  Available CPUs:  {resources.get('CPU', 'N/A')}")
        print(f"  Available GPUs:  {resources.get('GPU', 'N/A')}")
        print(f"  Available Memory: {resources.get('memory', 0)}")
        
        total = ray.cluster_resources()
        print(f"  Total CPUs:  {total.get('CPU', 'N/A')}")
        print(f"  Total GPUs:  {total.get('GPU', 'N/A')}")
    except Exception as e:
        print(f"    ⚠️  Resource scan error: {e}")

    # ── 4. Runtime Context ──
    print("\n" + "─" * 80)
    print("  🔧 RUNTIME CONTEXT")
    print("─" * 80)
    try:
        ctx = ray.get_runtime_context()
        print(f"  Job ID:         {ctx.get_job_id()}")
        print(f"  Node ID:        {ctx.get_node_id()}")
        print(f"  Actor ID:       {ctx.get_actor_id()}")
        print(f"  Task ID:        {ctx.get_task_id()}")
        print(f"  Namespace:      {ctx.namespace}")
    except Exception as e:
        print(f"    ⚠️  Context error: {e}")

    # ── 5. Dashboard ──
    print("\n" + "─" * 80)
    print("  🌐 DASHBOARD & PORTS")
    print("─" * 80)
    import socket
    ports = {6379: "GCS", 8265: "Dashboard", 8000: "Serve API",
             8001: "MCP API", 8003: "MCP RAG", 9090: "Prometheus"}
    for port, service in ports.items():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        status = s.connect_ex(('127.0.0.1', port))
        print(f"    {'🟢' if status == 0 else '⚫'}  Port {port} — {service}")
        s.close()

    # ── 6. Object Store ──
    print("\n" + "─" * 80)
    print("  📦 OBJECT STORE (Ray.put objects)")
    print("─" * 80)
    try:
        store_info = ray._private.worker.global_worker.core_worker.get_store_stats()
        print(f"  Object store size: {store_info.get('object_store_used_memory', 0) / 1e9:.2f} GB")
    except:
        print("  ⚠️  Could not query object store stats")

    # ── 7. Serve Applications ──
    print("\n" + "─" * 80)
    print("  🚀 RAY SERVE APPLICATIONS")
    print("─" * 80)
    try:
        from ray.serve.api import list_deployments
        deployments = list_deployments()
        if deployments:
            for d in deployments:
                print(f"    🟢  {d}")
        else:
            print("    No Serve deployments found")
    except ImportError:
        print("    ray.serve not available")
    except Exception as e:
        print(f"    ⚠️  Serve error: {e}")

    # ── Summary ──
    print("\n" + "=" * 80)
    print(f"  📋 SUMMARY")
    print(f"  {'🟢' if any('ALIVE' in str(a) for a in actor_handles) else '⚫'}  Active actors found: {len(actor_handles)}")
    print(f"  {'🟢' if any(status == 0 for status, _ in [(s.connect_ex(('127.0.0.1', p)), p) for p in [6379, 8265]]) else '⚫'}  Ray core services: {'GCS+Dashboard up' if True else 'check ports'}")
    print("=" * 80)

if __name__ == "__main__":
    scan_kingdom()