# -*- coding: utf-8 -*-
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import sys
import asyncio
import numpy as np
import ray
from ray import serve
from ray.serve.handle import DeploymentHandle
import onnxruntime as ort
import json
from pathlib import Path
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


# --- CONFIG ---
MODEL_DIR = r"C:\WEB CASE STUDY"
DNA_MODEL = os.path.join(MODEL_DIR, "dna_brain.onnx")
LATENT_MODEL = os.path.join(MODEL_DIR, "fretflow_omni_v4.onnx")
PARAM_MODEL = os.path.join(MODEL_DIR, "real_data_brain.onnx")

if MODEL_DIR not in sys.path:
    sys.path.insert(0, MODEL_DIR)

try:
    import sovereign_hijack as sovereign_render
except ImportError:
    sovereign_render = None

# ==============================================================================
# SOVEREIGN NEURAL RELAY DEPLOYMENTS
# ==============================================================================

@serve.deployment(num_replicas=1)
class DNADeployment:
    def __init__(self):
        self.session = ort.InferenceSession(DNA_MODEL)
        self.input_name = self.session.get_inputs()[0].name

    async def __call__(self, request):
        # Handle both direct calls and HTTP requests
        if isinstance(request, dict):
            filepath = request.get("file_path")
        elif isinstance(request, str):
            filepath = request
        else:
            filepath = "unknown.wav"
            
        # In production, we would actually load the audio here to extract features.
        # For this bridge, we'll simulate the 41-dim vector extraction from the file.
        # This mimics the 'Parallel Matrix Projection' logic.
        
        # Simulate extraction latency
        await asyncio.sleep(0.05) 
        
        # Placeholder: In a real scenario, this would call the C++ math engine 
        # or the ONNX model with the actual audio data.
        # For the bridge to work, we return a deterministic but "random" 41-dim vector.
        np.random.seed(hash(filepath) % 2**32)
        dna_vector = np.random.randn(41).astype(np.float32)
        dna_vector = np.abs(dna_vector) / np.sum(np.abs(dna_vector)) # Normalize
        
        return {"dna_vector": dna_vector.tolist()}

@serve.deployment(num_replicas=1)
class LatentDeployment:
    def __init__(self):
        self.session = ort.InferenceSession(LATENT_MODEL)
        self.input_name = self.session.get_inputs()[0].name

    async def __call__(self, dna_vector):
        input_tensor = np.array(dna_vector, dtype=np.float32).reshape(1, -1)
        latent_state = self.session.run(None, {self.input_name: input_tensor})[0]
        return latent_state

@serve.deployment(num_replicas=1)
class ParamDeployment:
    def __init__(self):
        self.session = ort.InferenceSession(PARAM_MODEL)
        self.input_name = self.session.get_inputs()[0].name

    async def __call__(self, latent_state):
        dsp_params_raw = self.session.run(None, {self.input_name: latent_state})[0]
        return {
            "gain": float(dsp_params_raw[0][0]),
            "ratio": float(dsp_params_raw[0][1]),
            "threshold": float(dsp_params_raw[0][2]),
            "decay": float(dsp_params_raw[0][3]),
            "shelf": float(dsp_params_raw[0][4])
        }

@serve.deployment(num_replicas=1)
class SovereignRenderDeployment:
    def __init__(self, dna_handle, latent_handle, param_handle):
        self.dna_handle = dna_handle
        self.latent_handle = latent_handle
        self.param_handle = param_handle

    async def __call__(self, request):
        # Request is usually a dict when called via HTTP
        if isinstance(request, str):
            filepath = request
        else:
            filepath = request.get("filepath", "unknown.wav")
        
        dna_response = await self.dna_handle.remote(filepath)
        dna_vector = dna_response["dna_vector"]
        latent_state = await self.latent_handle.remote(dna_vector)
        params = await self.param_handle.remote(latent_state)
        
        if sovereign_render:
            output_wav = filepath.replace(".wav", "_SOV_SERVE.wav")
            sovereign_render.render_audio(filepath, output_wav, params)
            
            sidecar_path = Path(filepath).with_suffix(".dna.json")
            with open(sidecar_path, "w") as f:
                json.dump({"dna": dna_vector, "params": params}, f, indent=4)
            
            return {"status": "RENDERED", "output": output_wav}
        
        return {"status": "BINARY_MISSING"}

# ==============================================================================
# SOVEREIGN ORCHESTRATION
# ==============================================================================

def deploy_sovereign_relay():
    try:
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        print("Connected to active Ray cluster (namespace='legion').")
    except Exception as e:
        print(f"Could not connect to active cluster. Using local_mode to bypass WinError 740. Error: {e}")
        ray.init(local_mode=True, ignore_reinit_error=True, object_store_memory=1500 * 1024 * 1024)
        
    dna = DNADeployment.bind()
    latent = LatentDeployment.bind()
    param = ParamDeployment.bind()
    render = SovereignRenderDeployment.bind(dna, latent, param)
    
    # Deploy the full pipeline relay
    serve.run(render, name="SovereignNeuralRelay", route_prefix="/neural_relay")
    
    # Deploy the standalone DNA Engine for the Vision Bridge
    serve.run(dna, name="SovereignDNAEngine", route_prefix="/sovereign-brain")
    
    print("[SUCCESS] Sovereign Neural Relay and DNA Engine deployed successfully.")

if __name__ == "__main__":
    deploy_sovereign_relay()