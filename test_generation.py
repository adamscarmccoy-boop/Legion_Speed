import os
import numpy as np
import torch
import json
from sonic_to_visual_bridge import SonicToVisualBridgeActor

def simulate_generation():
    print("SOVEREIGN GENERATION SIMULATION\n" + "="*40)
    
    from validate_logic_stripped import SonicToVisualBridgeLogic
    
    try:
        bridge = SonicToVisualBridgeLogic()
        print("Sovereign Brain Online.")
    except Exception as e:
        print(f"Brain Offline: {e}")
        return

    test_cases = {
        "Cyber-Industrial": np.random.rand(41).astype(np.float32) * 0.5,
        "High-Energy Club": np.random.rand(41).astype(np.float32) * 2.0,
        "Dark Ambient": np.random.rand(41).astype(np.float32) * 0.2
    }

    for name, dna in test_cases.items():
        print(f"\nGenerating for: [{name}]")
        try:
            prompt = bridge.bridge_dna_to_prompt(dna)
            print(f"Visual Prompt: {prompt.llm_expanded_prompt}")
            print(f"Metadata: {prompt.metadata}")
        except Exception as e:
            print(f"Generation failed: {e}")

    print("\n" + "="*40 + "\nSimulation Complete.")

if __name__ == "__main__":
    simulate_generation()
