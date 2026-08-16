import duckdb
import json
import torch
import numpy as np
import sys
import os

sys.path.insert(0, r"C:\WEB CASE STUDY")
sys.stdout.reconfigure(encoding="utf-8")

from sovereign_vision_bridge import SovereignVisionBrain, generate_visual_prompt

DB_PATH = r"C:\WEB CASE STUDY\web_intel_sonicdb.duckdb"
WEIGHTS_PATH = r"C:\WEB CASE STUDY\sovereign_vision_brain.pth"
CONFIG_PATH = r"C:\WEB CASE STUDY\bridge_config.json"

def main():
    print("=" * 80)
    print(" REAL DUCKDB AUDIO TRACKS ➔ SOVEREIGN VISION BRAIN PROMPTS ")
    print("=" * 80)
    
    con = duckdb.connect(DB_PATH, read_only=True)
    df = con.execute("SELECT * FROM audio_features LIMIT 5").fetchdf()
    
    brain = SovereignVisionBrain(41, 12)
    brain.load_state_dict(torch.load(WEIGHTS_PATH))
    brain.eval()
    
    config = json.load(open(CONFIG_PATH))
    anchors = {int(k): v for k, v in config["semantic_anchors"].items()}
    
    for idx, row in df.iterrows():
        # Construct 41-dim vector from track stats
        vec = np.zeros(41, dtype=np.float32)
        rms = float(row["rms_db"])
        crest = float(row["crest_factor"])
        sub = float(row["sub_bass_energy"]) if "sub_bass_energy" in row and not np.isnan(row["sub_bass_energy"]) else 10.0
        
        vec[0] = rms
        vec[1] = crest
        vec[2] = sub
        
        prompt, latency = generate_visual_prompt(brain, config, anchors, vec)
        
        track_name = row["filename"] if "filename" in row else f"Track_{idx}"
        tempo = row.get("tempo", 124.0)
        key = row.get("key", "C")
        
        print(f"\n[{idx+1}] TRACK: {track_name}")
        print(f"    - Key: {key} | Tempo: {tempo:.1f} BPM")
        print(f"    - RMS Loudness: {rms:.2f} dB | Crest Factor: {crest:.2f}")
        print(f"    - Vision Inference Latency: {latency:.2f} ms")
        print(f"    ➔ DYNAMIC VISION PROMPT:\n      \"{prompt}\"")
        print("-" * 80)

if __name__ == "__main__":
    main()
