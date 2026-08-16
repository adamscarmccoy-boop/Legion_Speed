import os
import torch
import torch.nn as nn
import numpy as np
import json
import time
from pydantic import BaseModel
from typing import List, Dict, Any

# ─── ARCHITECTURE ───
class SovereignVisionBrain(nn.Module):
    def __init__(self, input_dim: int, output_dim: int = 12):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, output_dim),
            nn.Softmax(dim=1)
        )
    def forward(self, x): return self.net(x)

# ─── LOGIC ───
def generate_visual_prompt(brain, config, semantic_anchors, dna_vector):
    start_time = time.perf_counter()
    
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

def run_benchmark():
    print("SOVEREIGN BRIDGE SPEED & DATA BENCHMARK\n" + "="*50)
    
    CONFIG_PATH = r"C:\WEB CASE STUDY\bridge_config.json"
    WEIGHTS_PATH = r"C:\WEB CASE STUDY\sovereign_vision_brain.pth"
    
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        brain = SovereignVisionBrain(input_dim=config['input_dim'], output_dim=config['output_dim'])
        if os.path.exists(WEIGHTS_PATH):
            brain.load_state_dict(torch.load(WEIGHTS_PATH))
            brain.eval()
        
        semantic_anchors = {int(k): v for k, v in config['semantic_anchors'].items()}
        print("System Online. Weights Loaded.\n")
    except Exception as e:
        print(f"System Error: {e}")
        return

    test_cases = {
        "Cyber-Industrial": np.random.rand(41).astype(np.float32),
        "High-Energy Club": np.random.rand(41).astype(np.float32),
        "Dark Ambient": np.random.rand(41).astype(np.float32)
    }

    total_latency = 0
    print(f"{'Profile':<20} | {'Latency':<12} | {'Prompt'}")
    print("-" * 80)

    for name, dna in test_cases.items():
        prompt, latency = generate_visual_prompt(brain, config, semantic_anchors, dna)
        total_latency += latency
        print(f"{name:<20} | {latency:>8.2f} ms | {prompt[:50]}...")

    avg_latency = total_latency / len(test_cases)
    print("-" * 80)
    print(f"AVERAGE INFERENCE SPEED: {avg_latency:.2f} ms per prompt")
    print(f"THROUGHPUT: {1000/avg_latency:.2f} prompts/sec")
    print("="*50)

if __name__ == "__main__":
    run_benchmark()
