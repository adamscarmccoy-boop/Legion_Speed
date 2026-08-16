import os
import torch
import torch.nn as nn
import numpy as np
import json
import time
import requests
from datetime import datetime
from pydantic import BaseModel
from typing import List, Dict, Any

# ─── ARCHITECTURE (Kept for dimension validation) ───
class SovereignVisionBrain(nn.Module):
    def __init__(self, input_dim: int, output_dim: int = 12):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, output_dim),
            nn.Softmax(dim=1)
        )
    def forward(self, x): return self.net(x)

# ─── PRODUCTION CLIENT ───
class SovereignDNAClient:
    def __init__(self, endpoint_url: str = "http://localhost:8000/sovereign-brain"):
        self.endpoint_url = endpoint_url

    def get_dna(self, file_path: str) -> np.ndarray:
        """Queries the Sovereign Sieve (Ray Serve) for the true 41-dim DNA vector."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        payload = {"file_path": os.path.abspath(file_path)}
        
        try:
            response = requests.post(self.endpoint_url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if "error" in data:
                raise Exception(f"Sovereign Engine Error: {data['error']}")
            
            # Expecting {'dna_vector': [...]}
            dna_list = data["dna_vector"]
            dna_array = np.array(dna_list, dtype=np.float32)
            
            if dna_array.shape[0] != 41:
                raise ValueError(f"Dimension Mismatch! Engine returned {dna_array.shape[0]} dims, expected 41.")
            
            return dna_array

        except requests.exceptions.RequestException as e:
            raise Exception(f"Connection to Sovereign Sieve failed: {e}")

# ─── LOGGING ───
LOG_DIR = r"C:\WEB CASE STUDY\sovereign_production\08_logs"
SPEED_LOG = os.path.join(LOG_DIR, "vision_bridge_speed.log")
METRICS_LOG = os.path.join(LOG_DIR, "metrics.prom")

def log_performance(filename, latency_ms):
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = int(time.time() * 1000)
    
    # Human-readable log
    with open(SPEED_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] {filename} | Latency: {latency_ms:.2f}ms\n")
    
    # Prometheus metric: vision_bridge_latency_ms <value> <timestamp>
    with open(METRICS_LOG, "a", encoding="utf-8") as f:
        f.write(f"vision_bridge_latency_ms {latency_ms:.2f} {timestamp}\n")

# ─── LOGIC ───
def generate_visual_prompt(brain, config, semantic_anchors, dna_vector):
    start_time = time.perf_counter()
    
    # Ensure vector is 2D for PyTorch: (1, 41)
    input_vec = torch.from_numpy(dna_vector).float().unsqueeze(0)
    
    with torch.no_grad():
        activations = brain(input_vec).squeeze(0).numpy()
    
    top_indices = np.argsort(activations)[-3:]
    selected_aesthetics = [semantic_anchors[idx][0] for idx in top_indices]
    all_textures = []
    for idx in top_indices:
        all_textures.extend(semantic_anchors[idx][1])
    
    dark_score = activations[6]
    palette = config['palette_map']['dark_palette'] if dark_score > 0.3 else config['palette_map']['light_palette']
    
    prompt = f"A {', '.join(selected_aesthetics)} masterpiece, {', '.join(list(set(all_textures))[:4])}, intricate architectural detail, ray-traced shadows, lighting: {'volumetric' if activations[3] > 0.2 else 'high-contrast'}."
    
    end_time = time.perf_counter()
    latency_ms = (end_time - start_time) * 1000
    
    return prompt, latency_ms

def run_production_benchmark(audio_file: str):
    print("\nSOVEREIGN BRIDGE PRODUCTION BENCHMARK\n" + "="*50)
    
    CONFIG_PATH = r"C:\WEB CASE STUDY\bridge_config.json"
    WEIGHTS_PATH = r"C:\WEB CASE STUDY\sovereign_vision_brain.pth"
    
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        client = SovereignDNAClient()
        
        # 1. FETCH REAL DNA FROM ENGINE
        print(f"[*] Querying Sovereign Sieve for: {os.path.basename(audio_file)}...")
        real_dna = client.get_dna(audio_file)
        print(f"[+] DNA Received. Dimension: {real_dna.shape}")
        
        # 2. LOAD LOCAL VISION BRAIN
        brain = SovereignVisionBrain(input_dim=41, output_dim=12)
        if os.path.exists(WEIGHTS_PATH):
            brain.load_state_dict(torch.load(WEIGHTS_PATH))
            brain.eval()
            print("[+] Vision Weights Loaded.")
        else:
            print("[!] Warning: Weights not found. Using random initialization for test.")
            brain.eval()
        
        semantic_anchors = {int(k): v for k, v in config['semantic_anchors'].items()}
        print("System Online. Engine Connected.\n")
        
    except Exception as e:
        print(f"System Error: {e}")
        return

    # Test the single real file
    prompt, latency = generate_visual_prompt(brain, config, semantic_anchors, real_dna)
    log_performance(os.path.basename(audio_file), latency)
    
    print(f"{'Target File':<20} | {'Latency':<12} | {'Prompt'}")
    print("-" * 80)
    print(f"{os.path.basename(audio_file):<20} | {latency:>8.2f} ms | {prompt[:50]}...")
    print("-" * 80)
    print("="*50)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python sovereign_vision_bridge.py <path_to_audio_file>")
        sys.exit(1)
    
    target_audio = sys.argv[1]
    run_production_benchmark(target_audio)
