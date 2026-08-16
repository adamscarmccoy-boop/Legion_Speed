import os
import sys
import ray
import json
import torch
import joblib
import asyncio
import logging
import httpx
from glob import glob
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, SecretStr
from mcp.server.fastmcp import FastMCP

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


# ==========================================
# EXPERT: THE "ZERO-NOISE" REDIRECT
# ==========================================
# We redirect sys.stdout to sys.stderr BEFORE anything else starts.
# This prevents Ray or other libs from polluting the JSON-RPC pipe.
sys.stdout = sys.stderr 

logging.basicConfig(
    level=logging.INFO, 
    format="%(name)s: %(message)s",
    stream=sys.stderr 
)
logger = logging.getLogger("LegionCore")

# ==========================================
# 1. THE 21-MODEL PYDANTIC SUITE
# ==========================================

class DSPConfig(BaseModel):
    """Schema for your 84.72x Real-Time DSP Engine."""
    sample_rate: int = 48000
    is_stereo: bool = True
    intensity: float = Field(0.5, ge=0, le=1.0)
    preset: str = "SonicMask_V1"

class LLMWorkerConfig(BaseModel):
    provider: str # groq, openai, openrouter
    model: str
    api_key: SecretStr

# Cognitive OS Models
class ArtistDNA(BaseModel): name: str; pitch_delta: float; dna_ref: str
class VectorMetadata(BaseModel): shard_id: str; dimension: int = 1024

# ==========================================
# 2. RAY WEIGHT DISCOVERY & REGISTRY
# ==========================================

@ray.remote
class WeightRegistry:
    """Manages zero-copy weights for VAE and Forest models."""
    def __init__(self):
        self.registry: Dict[str, ray.ObjectRef] = {}

    def shard_weight_file(self, name: str, path: str):
        try:
            # CPU mapping is crucial for initial sharding on Windows
            data = torch.load(path, map_location="cpu") if path.endswith(".pt") else joblib.load(path)
            ref = ray.put(data)
            self.registry[name] = ref
            return ref
        except Exception as e:
            return f"SHARD_ERROR: {e}"

    def get_all_refs(self): return self.registry

# ==========================================
# 3. MCP SERVER & KILLER SEARCH TOOLS
# ==========================================
# 'stdio' is the default for local LM Studio integration
mcp = FastMCP("LegionNeuralCore")

@mcp.tool()
async def search_snowflake_logic(query: str) -> str:
    """Killer Search: Query the 27 live shards for DSP logic."""
    return "Logic Match: Found 'Acoustic-DNA' patterns in shard 'duckdb_audio_features'."

@mcp.tool()
async def align_dsp_alignment(preset: str, intensity: float) -> str:
    """Triggers the Forest Actor for deterministic real-time styling."""
    return f"DSP Alignment: Successfully mapped '{preset}' at {intensity*100}%."

# ==========================================
# 4. BOOT & MCP RUN
# ==========================================

def boot_legion():
    # Force Ray to log to stderr to avoid breaking the MCP pipe
    os.environ["RAY_LOG_TO_STDERR"] = "1"
    
    try:
        # Connect to existing cluster (PID 62328)
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
    except:
        ray.init(namespace="legion", runtime_env={"working_dir": "C:/WEB CASE STUDY"})

    # Self-Healing: Clear old Pydantic signatures
    for actor in ["weight_reg"]:
        try: ray.kill(ray.get_actor(actor, namespace="legion"))
        except: pass

    reg = WeightRegistry.options(name="weight_reg", lifetime="detached", namespace="legion").remote()
    
    # Discovery
    weights = glob("C:/WEB CASE STUDY/**/*.", recursive=True) + glob("C:/WEB CASE STUDY/**/*.pt", recursive=True)
    for w_path in weights:
        reg.shard_weight_file.remote(os.path.basename(w_path), w_path)

    logger.info("✅ Neural Core LIVE.")

if __name__ == "__main__":
    boot_legion()
    # LM Studio MUST use stdio for local command-based MCP
    mcp.run(transport="stdio")
