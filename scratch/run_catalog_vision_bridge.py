import sys
import os
import json
import torch
import numpy as np

sys.path.insert(0, r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline")
sys.path.insert(0, r"C:\WEB CASE STUDY")
sys.stdout.reconfigure(encoding="utf-8")

from sovereign_intelligence import DSPFeatureLookup
from sovereign_vision_bridge import SovereignVisionBrain, generate_visual_prompt

def main():
    print("=" * 75)
    print(" REAL SOVEREIGN DUCKDB CATALOG ➔ VISION BRAIN PROMPT GENERATION ")
    print("=" * 75)
    
    dsp = DSPFeatureLookup()
    recs = dsp.get_full_catalog()[:5]
    
    brain = SovereignVisionBrain(41, 12)
    brain.load_state_dict(torch.load(r"C:\WEB CASE STUDY\sovereign_vision_brain.pth"))
    brain.eval()
    
    config = json.load(open(r"C:\WEB CASE STUDY\bridge_config.json"))
    anchors = {int(k): v for k, v in config["semantic_anchors"].items()}
    
    for i, r in enumerate(recs, 1):
        # Build 41-dim vector from track stats
        vec = np.zeros(41, dtype=np.float32)
        vec[0] = r.rms_db
        vec[1] = r.crest_factor
        vec[2] = r.sub_bass_energy if hasattr(r, 'sub_bass_energy') and r.sub_bass_energy is not None else 10.0
        
        prompt, latency = generate_visual_prompt(brain, config, anchors, vec)
        
        print(f"\n[{i}] TRACK: {r.filename}")
        print(f"    - Key: {r.key} | Tempo: {r.tempo:.1f} BPM")
        print(f"    - RMS: {r.rms_db:.2f} dB | Crest Factor: {r.crest_factor:.2f}")
        print(f"    - Latency: {latency:.2f} ms")
        print(f"    ➔ GENERATED VISION PROMPT:\n      \"{prompt}\"")
        print("-" * 75)

if __name__ == "__main__":
    main()
