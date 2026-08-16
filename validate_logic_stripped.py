import os
import torch
import torch.nn as nn
import numpy as np
import json
from pydantic import BaseModel
from typing import List, Dict, Any

# ─── STRIPPED NEURAL ARCHITECTURE (For Validation) ───
class SovereignVisionBrain(nn.Module):
    def __init__(self, input_dim: int, output_dim: int = 12):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, output_dim),
            nn.Softmax(dim=1)
        )
    def forward(self, x): return self.net(x)

class VibeProfile(BaseModel):
    primary_aesthetic: str
    texture_descriptors: List[str]
    lighting_mood: str
    color_palette: List[str]
    motion_character: str

class BridgePrompt(BaseModel):
    raw_tags: str
    llm_expanded_prompt: str
    metadata: Dict[str, Any]

class SonicToVisualBridgeLogic:
    def __init__(self, pth_path: str = r"C:\WEB CASE STUDY\sovereign_vision_brain.pth", config_path: str = r"C:\WEB CASE STUDY\bridge_config.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.brain = SovereignVisionBrain(
            input_dim=self.config['input_dim'], 
            output_dim=self.config['output_dim']
        )
        
        if os.path.exists(pth_path):
            self.brain.load_state_dict(torch.load(pth_path))
            self.brain.eval()

        self.semantic_anchors = {int(k): v for k, v in self.config['semantic_anchors'].items()}

    def _decode_dna_to_profile(self, dna_vector: np.ndarray) -> VibeProfile:
        input_vec = torch.from_numpy(dna_vector[:self.config['input_dim']]).float().unsqueeze(0)
        with torch.no_grad():
            activations = self.brain(input_vec).squeeze(0).numpy()
        
        top_indices = np.argsort(activations)[-3:]
        selected_aesthetics = []
        all_textures = []
        for idx in top_indices:
            concept, descriptors = self.semantic_anchors[idx]
            selected_aesthetics.append(concept)
            all_textures.extend(descriptors)
            
        dark_score = activations[6]
        palette = self.config['palette_map']['dark_palette'] if dark_score > 0.3 else self.config['palette_map']['light_palette']
        
        return VibeProfile(
            primary_aesthetic=", ".join(selected_aesthetics),
            texture_descriptors=list(set(all_textures))[:4],
            lighting_mood="volumetric" if activations[3] > 0.2 else "high-contrast",
            color_palette=palette,
            motion_character="glitchy" if activations[4] > 0.2 else "smooth"
        )

    def bridge_dna_to_prompt(self, dna_vector: np.ndarray) -> BridgePrompt:
        if dna_vector is None or dna_vector.shape[0] < self.config['input_dim']:
            raise ValueError(f"Invalid DNA vector shape. Expected at least {self.config['input_dim']} dimensions.")
        
        profile = self._decode_dna_to_profile(dna_vector)
        generative_modifiers = "intricate architectural detail, ray-traced shadows, monolithic 3D geometry, hyper-realistic textures, depth of field, unreal engine 5 render style"
        expanded_prompt = f"A {profile.primary_aesthetic} masterpiece, {', '.join(profile.texture_descriptors)}, {generative_modifiers}, lighting: {profile.lighting_mood}."
        
        return BridgePrompt(
            raw_tags=str(profile.dict()),
            llm_expanded_prompt=expanded_prompt,
            metadata={"dna_hash": hash(dna_vector.tobytes()), "is_generative": True, "structure_weight": 1.5}
        )

def run_tests():
    print("Sovereign Bridge Logic Unit Test\n" + "="*30)
    
    try:
        bridge = SonicToVisualBridgeLogic()
        print("SUCCESS: Config and Weights loaded.")
    except Exception as e:
        print(f"FAIL: Init failed: {e}")
        return

    # Test 1: Valid
    valid_dna = np.random.rand(41).astype(np.float32)
    try:
        res = bridge.bridge_dna_to_prompt(valid_dna)
        print(f"SUCCESS: Valid DNA generated prompt: {res.llm_expanded_prompt[:60]}...")
    except Exception as e:
        print(f"FAIL: Valid DNA failed: {e}")

    # Test 2: Too Short
    short_dna = np.random.rand(10).astype(np.float32)
    try:
        bridge.bridge_dna_to_prompt(short_dna)
        print("FAIL: Short DNA should have raised ValueError.")
    except ValueError as e:
        print(f"SUCCESS: Correctly caught short vector: {e}")

    # Test 3: None
    try:
        bridge.bridge_dna_to_prompt(None)
        print("FAIL: None input should have raised ValueError.")
    except ValueError as e:
        print(f"SUCCESS: Correctly caught None input: {e}")

if __name__ == "__main__":
    run_tests()
