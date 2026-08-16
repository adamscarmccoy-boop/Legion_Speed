# -*- coding: utf-8 -*-
"""
Audio LLM — RAY SERVE DEPLOYMENT
Serves the `audio_llm_v1.onnx` at C++ speeds using ONNX Runtime.
"""
import os, sys, json
import numpy as np
import ray
from ray import serve
import onnxruntime as ort
from pydantic import BaseModel

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


try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ONNX_PATH = r"C:\WEB CASE STUDY\sonic_dna_engine\audio_llm_v1.onnx"
SIDECAR_PATH = ONNX_PATH + ".meta.json"

class AudioLLMRequest(BaseModel):
    kick_dna: list[float]  # The input DNA vector of the Kick (length = in_dim)

@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 1})
class AudioLLMDeployment:
    def __init__(self):
        print("[AudioLLM] Booting ONNX C++ Runtime Engine...")
        self.session = ort.InferenceSession(ONNX_PATH, providers=['CPUExecutionProvider'])
        self.input_name = self.session.get_inputs()[0].name
        
        with open(SIDECAR_PATH, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
            
        self.in_dim = self.metadata["in_dim"]
        self.dsp_cols = self.metadata["dsp_cols"]
        print(f"[AudioLLM] Ready. Expecting vectors of size {self.in_dim}")

    def __call__(self, request: AudioLLMRequest) -> dict:
        vec = np.array(request.kick_dna, dtype=np.float32)
        if len(vec) != self.in_dim:
            return {"error": f"Expected vector of length {self.in_dim}, got {len(vec)}"}
            
        # Inference entirely in C++
        out = self.session.run(None, {self.input_name: vec.reshape(1, self.in_dim)})[0][0]
        
        # Format the hallucinated bass vector
        hallucinated = {col: float(val) for col, val in zip(self.dsp_cols, out)}
        return {"hallucinated_bass": hallucinated}

# ==============================================================================
# MAIN — Spin up Ray Serve and Deploy
# ==============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  AUDIO LLM: RAY SERVE (C++ ONNX ENGINE)")
    print("=" * 60)
    
    try:
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
    except Exception:
        print("Starting fresh Ray cluster in LOCAL MODE to bypass WinError 740...")
        ray.init(local_mode=True, ignore_reinit_error=True, object_store_memory=1500 * 1024 * 1024)
    serve.start(detached=True)
    
    print("Deploying AudioLLM...")
    AudioLLMDeployment.deploy()
    print("✅ Deployment successful. Available via Ray Serve!")