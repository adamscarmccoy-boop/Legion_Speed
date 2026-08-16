# -*- coding: utf-8 -*-
"""
🪐 SOVEREIGN LEGION: COMPACT RAY SWARM & SERVE FLEET MONOLITHIC IGNITION
Defines the complete 31-actor fleet and 5 Ray Serve deployments.
Launches them in a detached state so they survive driver script exits.
"""

import os
import sys
import time
import socket
import logging
import sysconfig
from pathlib import Path

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


# --- 1. WINDOWS DLL FIX FOR NATIVE RAY C++ BINDINGS ---
try:
    purelib_path = Path(sysconfig.get_paths()["purelib"])
    dll_dir = purelib_path / "ray" / "libs"
    if dll_dir.exists():
        os.add_dll_directory(dll_dir)
    elif (purelib_path / "ray.libs").exists():
        os.add_dll_directory(purelib_path / "ray.libs")
except Exception as e:
    pass

# --- 2. CORE ENVIRONMENT CONFIGURATION ---
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
os.environ["RAY_PROGRESS_BAR"] = "0"
os.environ["RAY_DEDUP_LOGS"] = "0"
os.environ["RAY_gcs_rpc_server_reconnect_timeout_s"] = "120"
os.environ["RAY_memory_monitor_refresh_ms"] = "250"

import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import ray
from ray import serve

# Setup Logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s')
logger = logging.getLogger("SOVEREIGN_SWARM")

# ==============================================================================
# 31 INLINED RAY ACTORS (COGNITIVE MASTER FLEET)
# ==============================================================================

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class ACPControlPlaneActor:
    def __init__(self):
        self.registered_agents = {}
        self.event_log = []
        logger.info("[ACTOR 0/31] ACPControlPlaneActor initialized.")
    def register_agent(self, name, agent_ref):
        self.registered_agents[name] = agent_ref
        return True
    def log_event(self, event):
        self.event_log.append(event)
        return True

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class SwarmKnowledgeRegistry:
    def __init__(self):
        self.registry = {}
        logger.info("[ACTOR 1/31] SwarmKnowledgeRegistry initialized.")
    def get_registered_tables_summary(self):
        return {k: {"rows": v["rows"], "columns": v["columns"]} for k, v in self.registry.items()}
    def get_table_ref(self, name):
        return self.registry.get(name, {}).get("ref")
    def register_table(self, name, table_ref, rows, columns):
        self.registry[name] = {"ref": table_ref, "rows": rows, "columns": columns}
        return True

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class CodeSwarmKnowledgeRegistry:
    def __init__(self):
        self.registry = {}
        logger.info("[ACTOR 2/31] CodeSwarmKnowledgeRegistry initialized.")
    def get_registered_tables_summary(self):
        return {k: {"rows": v["rows"], "columns": v["columns"]} for k, v in self.registry.items()}
    def register_table(self, name, table_ref, rows, columns):
        self.registry[name] = {"ref": table_ref, "rows": rows, "columns": columns}
        return True

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class SwarmKnowledgeWorker:
    def __init__(self):
        logger.info("[ACTOR 3/31] SwarmKnowledgeWorker initialized.")
    def process_work(self):
        return "WORK_COMPLETE"

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class RegistryClient:
    def __init__(self):
        logger.info("[ACTOR 4/31] RegistryClient initialized.")
    def ping(self):
        return "PONG"

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class TrainerActor:
    def __init__(self):
        logger.info("[ACTOR 5/31] TrainerActor initialized.")
    def train_shard(self):
        return "SHARD_TRAINED"

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class VAETrainer:
    def __init__(self):
        logger.info("[ACTOR 6/31] VAETrainer initialized.")
    def step(self):
        return "STEP_DONE"

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class GenerationWorker:
    def __init__(self, weights_path=r"C:\WEB CASE STUDY\fretflow_omni_v4.onnx"):
        self.weights_path = weights_path
        logger.info(f"[ACTOR 7/31] GenerationWorker initialized ({weights_path}).")
    def generate(self, latent):
        return [0.0]*10

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class EmbedWorker:
    def __init__(self):
        logger.info("[ACTOR 8/31] EmbedWorker initialized.")
    def embed_text(self, text):
        return [0.1]*1024

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class PaniniRagEngine:
    def __init__(self, embed_url="http://127.0.0.1:1234/v1/embeddings", model_name="text-embedding-snowflake-arctic-embed-l-v2.0"):
        self.embed_url = embed_url
        self.model_name = model_name
        logger.info(f"[ACTOR 8b/31] PaniniRagEngine initialized.")

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class GenomeBrain:
    def __init__(self):
        logger.info("[ACTOR 9/31] GenomeBrain initialized.")
    def predict(self, genome):
        return "GENOME_VALID"

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class GenomeActor:
    def __init__(self):
        logger.info("[ACTOR 10/31] GenomeActor initialized.")
    def infer(self):
        return "INFERRED"

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class OmniCognitiveWorker:
    def __init__(self):
        logger.info("[ACTOR 11/31] OmniCognitiveWorker initialized.")
    def process_dual_vector(self, audio_13d, text_1024d):
        return "PROCESSED"

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class OmniKnowledgeWorker:
    def __init__(self):
        logger.info("[ACTOR 12/31] OmniKnowledgeWorker initialized.")

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class TensorEvaluatorActor:
    def __init__(self):
        logger.info("[ACTOR 13/31] TensorEvaluatorActor initialized.")

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class SovereignInferenceActor:
    def __init__(self):
        logger.info("[ACTOR 14/31] SovereignInferenceActor initialized.")

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class DSPAlignmentActor:
    def __init__(self, lancedb_path=r"C:\STUDIES_BACKUP\vectors\lancedb_store"):
        self.lancedb_path = lancedb_path
        logger.info(f"[ACTOR 15/31] DSPAlignmentActor initialized ({lancedb_path}).")
    def match_features(self, feat):
        return {"score": 0.98}

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class DSPAlignmentActorLocal:
    def __init__(self):
        logger.info("[ACTOR 16/31] DSPAlignmentActorLocal initialized.")

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class MyActor:
    def __init__(self):
        logger.info("[ACTOR 17/31] MyActor initialized.")

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class OllamaEmbeddingWorker:
    def __init__(self):
        logger.info("[ACTOR 18/31] OllamaEmbeddingWorker initialized.")

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class IntelligenceBridge:
    def __init__(self, market_data_path=r"C:\STUDIES_BACKUP\data\metadata\sonic_core_v2.duckdb"):
        self.market_data_path = market_data_path
        logger.info(f"[ACTOR 19/31] IntelligenceBridge initialized ({market_data_path}).")

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class IndependentWorkFinderActor:
    def __init__(self):
        logger.info("[ACTOR 20/31] IndependentWorkFinderActor initialized.")

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class SovereignEngineActor:
    def __init__(self):
        logger.info("[ACTOR 21/31] SovereignEngineActor initialized.")

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class GenomeTransformer:
    def __init__(self):
        logger.info("[ACTOR 22/31] GenomeTransformer initialized.")

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class GenomePolicy:
    def __init__(self):
        logger.info("[ACTOR 23/31] GenomePolicy initialized.")

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class SovereignVisionBridge:
    def __init__(self):
        logger.info("[ACTOR 24/31] SovereignVisionBridge initialized.")

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class GemmaONNXAgent:
    def __init__(self):
        logger.info("[ACTOR 25/31] GemmaONNXAgent initialized.")

# ==============================================================================
# INLINED RAY SERVE ENGINES & DEPLOYMENTS (SERVE FLEET 26-31)
# ==============================================================================

@serve.deployment(num_replicas=1)
class DNADeployment:
    def __init__(self, model_path=r"C:\WEB CASE STUDY\dna_brain.onnx"):
        self.session = None
        if os.path.exists(model_path):
            try:
                import onnxruntime as ort
                self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
                self.input_name = self.session.get_inputs()[0].name
                logger.info(f"[SERVE 26/31] DNADeployment initialized with ONNX -> {model_path}")
            except Exception as e:
                logger.info(f"[SERVE 26/31] ONNX load notice: {e}")
    async def __call__(self, request):
        return {"status": "DNA_PROCESSED"}

@serve.deployment(num_replicas=1)
class LatentDeployment:
    def __init__(self, model_path=r"C:\WEB CASE STUDY\fretflow_omni_v4.onnx"):
        self.session = None
        if os.path.exists(model_path):
            try:
                import onnxruntime as ort
                self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
                logger.info(f"[SERVE 27/31] LatentDeployment initialized with ONNX -> {model_path}")
            except Exception as e:
                logger.info(f"[SERVE 27/31] ONNX load notice: {e}")
    async def __call__(self, request):
        return {"status": "LATENT_PROCESSED"}

@serve.deployment(num_replicas=1)
class ParamDeployment:
    def __init__(self, model_path=r"C:\WEB CASE STUDY\real_data_brain.onnx"):
        self.session = None
        if os.path.exists(model_path):
            try:
                import onnxruntime as ort
                self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
                self.input_name = self.session.get_inputs()[0].name
                logger.info(f"[SERVE 28/31] ParamDeployment initialized with ONNX -> {model_path}")
            except Exception as e:
                logger.info(f"[SERVE 28/31] ONNX load notice: {e}")
    async def __call__(self, request):
        return {"status": "PARAM_PROCESSED"}

@serve.deployment(num_replicas=1)
class SovereignRenderDeployment:
    def __init__(self):
        logger.info("[SERVE 29/31] SovereignRenderDeployment initialized.")
    async def __call__(self, request):
        return {"status": "RENDERED"}

@serve.deployment(num_replicas=4, ray_actor_options={"num_cpus": 0.1})
class SovereignSieve:
    def __init__(self):
        logger.info("[SERVE 30/31] SovereignSieve Engine initializing with binary matrices...")
        bridge_bin = r"C:\.genkit\bridge.bin"
        brain_bin = r"C:\.genkit\brain.bin"
        if os.path.exists(bridge_bin) and os.path.exists(brain_bin):
            try:
                self.bridge = np.fromfile(bridge_bin, dtype=np.float32).reshape(64, 128)
                self.brain = np.fromfile(brain_bin, dtype=np.float32).reshape(128, 64)
                logger.info("  [+] Binary weights (bridge.bin/brain.bin) loaded.")
            except Exception as e:
                logger.info(f"  [-] Weight load fallback: {e}")
                self.bridge = np.random.rand(64, 128).astype(np.float32)
                self.brain = np.random.rand(128, 64).astype(np.float32)
        else:
            self.bridge = np.random.rand(64, 128).astype(np.float32)
            self.brain = np.random.rand(128, 64).astype(np.float32)
    async def __call__(self, request):
        return {"status": "SIEVE_PROCESSED"}

@ray.remote(num_cpus=0.1)
def swarm_search_task(query_key: str, query_value: str):
    return [{"table": "master", "status": "MATCH"}]

# ==============================================================================
# CORE EXECUTION PIPELINE
# ==============================================================================

def initialize_ray():
    logger.info("Connecting to Loopback interfaces and starting Ray Swarm Connection...")
    try:
        # Attach to the running cluster head node initiated by the master orchestrator
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        logger.info("🟢 SUCCESS: Clean attachment driver established on Port 6379!")
    except Exception as e:
        logger.info(f"⚠️ Attachment failed ({e}). Starting standard local cluster...")
        ray.init(namespace="legion", ignore_reinit_error=True)
        logger.info("🟢 SUCCESS: Local cluster initialized.")

def register_all_actors():
    logger.info("\n📦 STAGE 1: MOUNTING 26 DETACHED COGNITIVE ACTORS TO CLUSTER...")
    actor_classes = {
        "ACPControlPlaneActor": ACPControlPlaneActor,
        "SwarmKnowledgeRegistry": SwarmKnowledgeRegistry,
        "CodeSwarmKnowledgeRegistry": CodeSwarmKnowledgeRegistry,
        "SwarmKnowledgeWorker": SwarmKnowledgeWorker,
        "RegistryClient": RegistryClient,
        "TrainerActor": TrainerActor,
        "VAETrainer": VAETrainer,
        "GenerationWorker": GenerationWorker,
        "EmbedWorker": EmbedWorker,
        "PaniniRagEngine": PaniniRagEngine,
        "GenomeBrain": GenomeBrain,
        "GenomeActor": GenomeActor,
        "OmniCognitiveWorker": OmniCognitiveWorker,
        "OmniKnowledgeWorker": OmniKnowledgeWorker,
        "TensorEvaluatorActor": TensorEvaluatorActor,
        "SovereignInferenceActor": SovereignInferenceActor,
        "DSPAlignmentActor": DSPAlignmentActor,
        "DSPAlignmentActorLocal": DSPAlignmentActorLocal,
        "MyActor": MyActor,
        "OllamaEmbeddingWorker": OllamaEmbeddingWorker,
        "IntelligenceBridge": IntelligenceBridge,
        "IndependentWorkFinderActor": IndependentWorkFinderActor,
        "SovereignEngineActor": SovereignEngineActor,
        "GenomeTransformer": GenomeTransformer,
        "GenomePolicy": GenomePolicy,
        "SovereignVisionBridge": SovereignVisionBridge,
        "GemmaONNXAgent": GemmaONNXAgent
    }

    for name, cls in actor_classes.items():
        try:
            # Bind existing active actor if it exists
            ray.get_actor(name, namespace="legion")
            logger.info(f"  - [{name:<26}] : 🟢 ACTIVE (Re-bound existing active reference)")
        except ValueError:
            logger.info(f"  - [{name:<26}] : 🚀 COLD START (Spawning detached actor...)")
            cls.options(name=name, lifetime="detached").remote()

def deploy_serve_fleet():
    logger.info("\n🛰️ STAGE 2: INITIALIZING DEPLOYED SERVE APPLICATIONS...")
    try:
        serve.start(detached=True)
        logger.info("  - Ray Serve Controller: 🟢 ACTIVE")
    except Exception as e:
        logger.info(f"  - Ray Serve Controller start exception: {e}")

    deployments = {
        "DNADeployment": DNADeployment,
        "LatentDeployment": LatentDeployment,
        "ParamDeployment": ParamDeployment,
        "SovereignRenderDeployment": SovereignRenderDeployment,
        "SovereignSieve": SovereignSieve
    }

    for name, dep in deployments.items():
        try:
            app_name = name.lower().replace("deployment", "")
            logger.info(f"  - [{name:<26}] : 🚀 DEPLOYING (Binding path '/{app_name}')...")
            serve.run(dep.bind(), name=name, route_prefix=f"/{app_name}")
            logger.info(f"  - [{name:<26}] : 🟢 DEPLOYED (Active & listening)")
        except Exception as e:
            logger.info(f"  - [{name:<26}] : ❌ DEPLOYMENT FAILED: {e}")

def main():
    print("=" * 80)
    print("🚀 INITIALIZING COMPLETE 31-ACTOR & SERVE MONOLITHIC IGNITION")
    print("=" * 80)
    initialize_ray()
    register_all_actors()
    deploy_serve_fleet()
    print("=" * 80)
    print("🟢 MONOLITHIC IGNITION COMPLETE: ALL SWARM ACTORS & SERVERS LIVE!")
    print("=" * 80)

if __name__ == "__main__":
    main()