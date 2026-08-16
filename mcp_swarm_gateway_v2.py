"""
LEGION SWARM GATEWAY — v2.0
============================
FastMCP server with stdio/SSE endpoints for LM Studio and LangGraph.
"""
import os, sys, json, logging, requests

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
    # Avoid raising SystemExit inside an atexit callback (which causes RuntimeWarnings)
    if args and isinstance(args[0], int):
        sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================


logging.basicConfig(level=logging.INFO, stream=sys.stderr)
LM_STUDIO_BASE = os.getenv("LM_STUDIO_BASE", "http://127.0.0.1:1234")

def _embed_snowflake(text: str) -> list:
    payload = {"model": "text-embedding-snowflake-arctic-embed-l-v2.0", "input": text}
    r = requests.post(f"{LM_STUDIO_BASE}/v1/embeddings", json=payload, timeout=5)
    return r.json()["data"][0]["embedding"]

if __name__ == "__main__":
    print("Legion Swarm Gateway v2.0 Ready.")