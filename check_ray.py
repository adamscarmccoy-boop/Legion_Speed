import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

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


ray.init(address="auto", namespace="legion")

print("=" * 60)
print("RAY CLUSTER STATUS")
print("=" * 60)
print("Cluster Resources:", ray.cluster_resources())

nodes = ray.nodes()
print(f"\nNodes: {len(nodes)}")
for n in nodes:
    nid = n["NodeID"][:8]
    alive = n["Alive"]
    res = n.get("Resources", {})
    print(f"  Node {nid}: alive={alive}, CPU={res.get('CPU', 0)}, GPU={res.get('GPU', 0)}, ObjStore={res.get('object_store_memory', 0) / 1e9:.2f}GB")

actors = ray.util.list_named_actors(all_namespaces=True)
print(f"\nLive Named Actors ({len(actors)}):")
for a in actors:
    print(f"  - {a}")

print("\n" + "=" * 60)
print("HEAD NODE IS LIVE" if nodes else "NO NODES FOUND")
print("=" * 60)