import os
import sys
import httpx
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

# Force UTF-8 output
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# --- LangGraph Verification State ---
class SwarmVerificationState(TypedDict):
    edge_status: str
    local_api_status: str
    ray_serve_status: str
    logs: List[str]

def check_edge_agent(state: SwarmVerificationState) -> SwarmVerificationState:
    print("[1/3] Verifying Cloudflare Edge Worker & Frontend...")
    try:
        res = httpx.get("http://127.0.0.1:8787/health", timeout=5.0)
        state["edge_status"] = f"ONLINE (HTTP {res.status_code})" if res.status_code == 200 else f"RESPONSE {res.status_code}"
    except Exception as e:
        state["edge_status"] = f"OFFLINE ({e})"
    state["logs"].append(f"Edge Worker Status: {state['edge_status']}")
    return state

def check_local_api(state: SwarmVerificationState) -> SwarmVerificationState:
    print("[2/3] Verifying Local Onyx API (Port 8001)...")
    try:
        res = httpx.get("http://127.0.0.1:8001/docs", timeout=5.0)
        state["local_api_status"] = "HEALTHY (OpenAPI Active)" if res.status_code == 200 else f"STATUS {res.status_code}"
    except Exception as e:
        state["local_api_status"] = f"UNREACHABLE ({e})"
    state["logs"].append(f"Local Onyx API (8001): {state['local_api_status']}")
    return state

def check_ray_serve(state: SwarmVerificationState) -> SwarmVerificationState:
    print("[3/3] Verifying Ray Serve Engine & ONNX Models (Port 8000)...")
    try:
        res = httpx.get("http://127.0.0.1:8000/sovereign-brain", timeout=5.0)
        state["ray_serve_status"] = "ACTIVE (Sovereign Engine Ready)" if res.status_code == 200 else f"STATUS {res.status_code}"
    except Exception as e:
        state["ray_serve_status"] = f"UNREACHABLE ({e})"
    state["logs"].append(f"Ray Serve Engine (8000): {state['ray_serve_status']}")
    return state

# --- Build LangGraph Pipeline ---
builder = StateGraph(SwarmVerificationState)
builder.add_node("check_edge", check_edge_agent)
builder.add_node("check_api", check_local_api)
builder.add_node("check_ray", check_ray_serve)

builder.set_entry_point("check_edge")
builder.add_edge("check_edge", "check_api")
builder.add_edge("check_api", "check_ray")
builder.add_edge("check_ray", END)

verifier_graph = builder.compile()

if __name__ == "__main__":
    initial_state = {
        "edge_status": "UNKNOWN",
        "local_api_status": "UNKNOWN",
        "ray_serve_status": "UNKNOWN",
        "logs": []
    }
    final_state = verifier_graph.invoke(initial_state)

    print("\n" + "=" * 65)
    print("      NVIDIA LANGGRAPH FULL SYSTEM VERIFICATION SUMMARY")
    print("=" * 65)
    for log in final_state["logs"]:
        print(f"  ✔ {log}")
    print("=" * 65)
