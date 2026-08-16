import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from IPython.utils import importstring
import ray
from ray import serve
import time
import pandas as pd
import numpy as np
from prometheus_client import Gauge, Counter, Histogram, CollectorRegistry
import os
import logging

from ray_code_swarm import CodeSwarmKnowledgeRegistry

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

from ray_arrow_swarm import SwarmKnowledgeRegistry
from cell_30_clean import GenomeBrain
from fretflow_ray_gen import GenerationWorker
# from run_vector_rebuild import EmbedWorker
from dsp_alignment_actor import DSPAlignmentActor
from intelligence_bridge import IntelligenceBridge
from ollama_rag_indexer import OllamaEmbeddingWorker
# from omni_vae_generator import OmniVAEGenerator
from sovereign_engine import SovereignEngine

from starlette_exporter import PrometheusMiddleware, handle_metrics

# --- Prometheus Logging Configuration ---
PROMETHEUS_LOG_PATH = r"C:\WEB CASE STUDY\sovereign_production\08_logs\metrics.prom"
os.makedirs(os.path.dirname(PROMETHEUS_LOG_PATH), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(PROMETHEUS_LOG_PATH, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("SovereignStartup")

def log_prometheus_metric(metric_name, value):
    """Writes a metric in Prometheus text format to the metrics.prom file."""
    with open(PROMETHEUS_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{metric_name} {value} {int(time.time() * 1000)}\n")

from sovereign_serve_app import deploy_sovereign_relay

# ... (rest of imports)

# 1. TACTICAL RESET
ray.init(address="auto", namespace="legion", ignore_reinit_error=True, object_store_memory=1500 * 1024 * 1024)
serve.start(detached=True)

# ... (registry and actors initialization)

# --- LAYER 4: THE MASTER ENGINE (The Sovereign) ---
# master_engine = SovereignEngine.options(name="SovereignEngine", namespace="legion", lifetime="detached").remote()

# Deploy the Ray Serve components
deploy_sovereign_relay()

logger.info("SOVEREIGN STACK INITIALIZED: ALL ACTORS AND SERVE DEPLOYMENTS DETACHED AND LIVE")
log_prometheus_metric("sovereign_startup_success", 1)

# 2. The MCP Bridge
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json

app = FastAPI()
app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics)

RAY_SERVE_URL = "http://localhost:8000"
CPP_MEMORY_URL = "http://localhost:9000" 

@app.post("/mcp")
async def mcp_endpoint(req: dict):
    method = req.get("method")
    params = req.get("params", {})
    req_id = req.get("id")

    if method == "tools/list":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {"tools": [
                {"name": "query_sovereign_brain", "description": "Call 24-replica ONNX Inference", "inputSchema": {"type": "object", "properties": {"dna": {"type": "array", "items": {"type": "number"}}}}},
                {"name": "read_swarm_memory", "description": "Read DNA from SwarmKnowledgeRegistry", "inputSchema": {"type": "object", "properties": {"key": "string"}}},
                {"name": "trigger_remaster", "description": "Fire the 42-track parallel Ray remaster", "inputSchema": {"type": "object", "properties": {"batch_id": {"type": "string"}}}}
            ]}
        }

    if method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})

        if tool_name == "query_sovereign_brain":
            r = requests.post(f"{RAY_SERVE_URL}/sovereign-brain", json=args)
            return _ok(req_id, r.json())

        if tool_name == "read_swarm_memory":
            registry = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
            data = ray.get(registry.get_key.remote(args["key"]))
            return _ok(req_id, {"data": data})

        if tool_name == "trigger_remaster":
            engine = ray.get_actor("SovereignEngine", namespace="legion")
            job_id = ray.get(engine.run_batch.remote(args["batch_id"]))
            return _ok(req_id, {"job_id": job_id, "status": "fanned_out_to_12_cpus"})

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}

def _ok(id_, result):
    return {"jsonrpc": "2.0", "id": id_, "result": result}

if __name__ == "__main__":
    if not ray.is_initialized():
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True, object_store_memory=1500 * 1024 * 1024)
    
    log_prometheus_metric("sovereign_system_boot", 1)
    uvicorn.run(app, host="0.0.0.0", port=8080)
m   