import os
import sys
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

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


# Force UTF-8 output
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

class RayOptimizationState(TypedDict):
    recommendations: List[str]
    system_status: str

def analyze_ray_serves(state: RayOptimizationState) -> RayOptimizationState:
    recs = [
        "1. Consolidation of Ray Serve Deployments: Combine minor services (e.g. status service and audio-llm) into dynamic multi-application deployment scripts or lazy-loaded actors instead of running 4+ distinct Ray Serve apps.",
        "2. Fractional Resource Allocations: Set num_cpus=0.1 or num_gpus=0.25 on @serve.deployment / @ray.remote actors to prevent Ray from over-allocating worker nodes and spiking memory.",
        "3. Dynamic / On-Demand Actor Lifecycle: Use `detached=False` or idle timeouts (`max_ongoing_requests`, `target_ongoing_requests`) so actors spin down when idle rather than holding permanent VRAM/RAM allocations.",
        "4. Plasma Memory Limits & Spilling: Explicitly bound object store memory in `ray.init(object_store_memory=...)` and configure local disk spilling (`_system_config={'object_spilling_config': ...}`) to handle large Arrow table ingestions.",
        "5. Modular Boot Flags: Use environment variable controls (e.g., `MINIMAL_BOOT=1`) in `ray_arrow_swarm.py` so heavy background subprocesses (Prometheus, Cloudflare Worker, RAG MCP) are only spawned when explicitly required."
    ]
    state["recommendations"] = recs
    state["system_status"] = "ANALYSIS_COMPLETE"
    return state

builder = StateGraph(RayOptimizationState)
builder.add_node("analyze_ray", analyze_ray_serves)
builder.set_entry_point("analyze_ray")
builder.add_edge("analyze_ray", END)

advisor_graph = builder.compile()

if __name__ == "__main__":
    initial_state = {"recommendations": [], "system_status": "INITIALIZING"}
    final_state = advisor_graph.invoke(initial_state)

    print("\n" + "=" * 70)
    print("   NVIDIA LANGGRAPH ADVISOR: RAY SERVE & ACTOR OPTIMIZATION REPORT")
    print("=" * 70)
    for rec in final_state["recommendations"]:
        print(f"\n💡 {rec}")
    print("\n" + "=" * 70)