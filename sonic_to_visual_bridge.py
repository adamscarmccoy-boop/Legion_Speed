import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import re
import torch
import numpy as np
import ray
from pydantic import BaseModel, Field
from typing import List, Dict, Any

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


# ─── SCHEMA: THE SEMANTIC CONTRACT ───

class VibeProfile(BaseModel):
    """The Pydantic bridge between Audio Math and Visual Language."""
    primary_aesthetic: str = Field(..., description="The core visual style (e.g., Cyberpunk, Baroque, Minimalist)")
    texture_descriptors: List[str] = Field(..., description="Surface qualities (e.g., chrome, grainy, liquid)")
    lighting_mood: str = Field(..., description="Atmospheric lighting (e.g., neon, volumetric, chiaroscuro)")
    color_palette: List[str] = Field(..., description="Dominant color tones")
    motion_character: str = Field(..., description="Visual energy (e.g., glitchy, fluid, sweeping)")

class BridgePrompt(BaseModel):
    """The final payload ready for clip_generative_art.py."""
    raw_tags: str
    llm_expanded_prompt: str
    metadata: Dict[str, Any]

# ─── THE ACTOR: SONIC-TO-VISUAL BRIDGE ───

@ray.remote
class SonicToVisualBridgeActor:
    """
    A Ray Actor that performs 'Semantic Projection'.
    It maps 64-D audio vectors into a multi-dimensional semantic space.
    """
    def __init__(self, llm_endpoint: str = "http://localhost:11434"):
        self.llm_endpoint = llm_endpoint
        
        # Heuristic Projection Matrix (DNA_DIM (64) -> SEMANTIC_DIM (12))
        self.projection_matrix = torch.randn(64, 12)
        
        # Semantic Anchor Map: Connects the 12 projected dimensions to human concepts
        self.semantic_anchors = {
            0: ("Cybernetic", ["neon", "chrome", "circuitry", "mechanical"]),
            1: ("Organic", ["fluid", "biological", "growth", "veins"]),
            2: ("Brutalist", ["concrete", "monolithic", "heavy", "industrial"]),
            3: ("Ethereal", ["mist", "glow", "translucent", "dreamlike"]),
            4: ("Glitch", ["digital noise", "pixelated", "fragmented", "stutter"]),
            5: ("High-Energy", ["explosive", "vibrant", "sharp", "kinetic"]),
            6: ("Dark", ["void", "shadow", "obsidian", "noir"]),
            7: ("Retro-Futurism", ["analog", "synthwave", "VHS", "warm"]),
            8: ("Luxury", ["gold", "silk", "polished", "refined"]),
            9: ("Chaos", ["turbulent", "abstract", "distorted", "unstable"]),
            10: ("Minimal", ["clean", "geometric", "white-space", "stark"]),
            11: ("Surreal", ["impossible", "melting", "gravity-defying", "strange"])
        }

    def decode_dna_to_profile(self, dna_vector: np.ndarray) -> VibeProfile:
        """Maps the math to the Pydantic VibeProfile."""
        tensor_vec = torch.from_numpy(dna_vector).float().unsqueeze(0)
        
        # Project DNA -> Semantic Space
        projection = torch.matmul(tensor_vec, self.projection_matrix).squeeze(0)
        
        # Softmax to get 'activation' of each semantic anchor
        activations = torch.softmax(projection, dim=-1).numpy()
        
        # Find top 3 active semantic dimensions
        top_indices = np.argsort(activations)[-3:]
        
        selected_aesthetics = []
        all_textures = []
        
        for idx in top_indices:
            concept, descriptors = self.semantic_anchors[idx]
            selected_aesthetics.append(concept)
            all_textures.extend(descriptors)
            
        palette = ["deep obsidian", "midnight blue", "charcoal"] if activations[6] > 0.3 else ["vibrant cyan", "electric violet", "acid green"]

        return VibeProfile(
            primary_aesthetic=", ".join(selected_aesthetics),
            texture_descriptors=list(set(all_textures))[:4],
            lighting_mood="volumetric and cinematic" if activations[3] > 0.2 else "high-contrast",
            color_palette=palette,
            motion_character="glitchy and rapid" if activations[4] > 0.2 else "smooth and flowing"
        )

    def expand_with_llm(self, profile: VibeProfile) -> str:
        """Connects to local LLM via GemmaONNXAgent logic."""
        # Simulated/Fallback LLM expansion
        simulated_response = (
            f"{profile.primary_aesthetic} digital art, featuring {', '.join(profile.texture_descriptors)}, "
            f"set in a {profile.lighting_mood} environment with a {profile.color_palette[0]} and "
            f"{profile.color_palette[1]} color scheme. The composition is {profile.motion_character}. "
            f"8k resolution, highly detailed, masterpiece."
        )
        return simulated_response

    def bridge_dna_to_prompt(self, dna_vector: np.ndarray) -> BridgePrompt:
        """Primary entry point for the Ray Swarm."""
        profile = self.decode_dna_to_profile(dna_vector)
        expanded_prompt = self.expand_with_llm(profile)
        return BridgePrompt(
            raw_tags=str(profile.dict()),
            llm_expanded_prompt=expanded_prompt,
            metadata={"dna_hash": hash(dna_vector.tobytes())}
        )

# ─── TEST RUNNER ───

if __name__ == "__main__":
    import os
    if "RAY_ADDRESS" in os.environ:
        del os.environ["RAY_ADDRESS"]
    if not ray.is_initialized():
        ray.init(namespace="legion", object_store_memory=1500 * 1024 * 1024)

    # Spawn the Actor
    bridge_actor = SonicToVisualBridgeActor.options(name="SonicToVisualBridge", lifetime="detached", get_if_exists=True).remote()

    import librosa
    audio_path = r"C:\WEB CASE STUDY\sovereign_capture.wav"
    if os.path.exists(audio_path):
        y, sr = librosa.load(audio_path, sr=22050, duration=10.0)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=64)
        real_dna = np.mean(mfcc, axis=1)
    else:
        real_dna = np.zeros(64, dtype=np.float32)
    result_ref = bridge_actor.bridge_dna_to_prompt.remote(real_dna)
    final_payload = ray.get(result_ref)