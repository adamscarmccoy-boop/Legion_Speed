import sys
import os
import json
import torch
import numpy as np

sys.path.insert(0, r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline")
sys.path.insert(0, r"C:\WEB CASE STUDY")
sys.stdout.reconfigure(encoding="utf-8")

from sovereign_intelligence import SovereignIntelligencePipeline
from sovereign_vision_bridge import SovereignVisionBrain, generate_visual_prompt

def main():
    print("=" * 70)
    print(" SOVEREIGN INTELLIGENCE ➔ VISION BRAIN INTEGRATION ")
    print("=" * 70)
    
    # 1. Load Sovereign Intelligence catalog
    pipe = SovereignIntelligencePipeline()
    records = pipe.dsp_lookup.get_full_catalog()[:5]
    
    # 2. Load Vision Brain model & prompt configuration
    weights_path = r"C:\WEB CASE STUDY\sovereign_vision_brain.pth"
    config_path = r"C:\WEB CASE STUDY\bridge_config.json"
    
    brain = SovereignVisionBrain(input_dim=41, output_dim=12)
    if os.path.exists(weights_path):
        brain.load_state_dict(torch.load(weights_path))
        brain.eval()
        print("[+] Sovereign Vision Brain weights loaded.")
        
    config = json.load(open(config_path))
    semantic_anchors = {int(k): v for k, v in config["semantic_anchors"].items()}
    
    print("\n[*] Processing Sovereign Catalog tracks through Vision Brain...\n")
    print(f"{'Track Filename':<40} | {'RMS (dB)':<10} | {'Crest':<8} | {'Generated Vision Prompt'}")
    print("-" * 110)
    
    for r in records:
        # Construct 41-dim feature vector from track DSP stats
        feat_vec = np.zeros(41, dtype=np.float32)
        rms = getattr(r, 'rms_db', -12.0)
        crest = getattr(r, 'crest_factor', 4.0)
        feat_vec[0] = rms
        feat_vec[1] = crest
        
        prompt, latency = generate_visual_prompt(brain, config, semantic_anchors, feat_vec)
        track_name = getattr(r, 'filename', getattr(r, 'filepath', 'Track_Catalog_Item'))
        
        print(f"{str(track_name)[:38]:<40} | {rms:>9.2f} | {crest:>7.2f} | {prompt}")
        print("-" * 110)
        
    print("=" * 70)

if __name__ == "__main__":
    main()
