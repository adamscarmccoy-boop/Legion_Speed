"""
=== RAY SWARM STRUCTURAL VISION GENERATOR ===
Executes CLIP multi-crop structural backprop vision generation 
directly on the active Ray Swarm Cluster (namespace='legion').
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import os
import time
import re
import ray
import torch
import torch.nn as nn
import torch.nn.functional as F

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

import numpy as np
from PIL import Image

# ─── CONNECT TO RAY CLUSTER ───
print("📡 Connecting to active Ray Swarm Cluster (namespace='legion')...")
ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
print("✅ Connected to Ray Cluster!")

PROMPT = "cyberpunk mechanical dragon with glowing neon red wings and metallic chrome scales, 3d unreal engine render"
STEPS = 250
LEARNING_RATE = 0.08

clean_prompt = re.sub(r'[^a-zA-Z0-9]', '_', PROMPT[:30]).strip('_').lower()
timestamp = time.strftime("%Y%m%d_%H%M%S")
filename = f"real_ray_vision_{clean_prompt}_{timestamp}.png"

OUTPUT_DIR = "mastered_output"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── DEFINE RAY VISION ACTOR ───
@ray.remote
class RayVisionWorker:
    def __init__(self, prompt: str, steps: int, lr: float):
        self.prompt = prompt
        self.steps = steps
        self.lr = lr
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🤖 [RayVisionWorker] Initialized on device: {self.device}")

        # Load vision backbone via open_clip or torchvision / pure pytorch
        import open_clip
        self.model, _, self.preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k')
        self.model = self.model.to(self.device).eval()
        self.tokenizer = open_clip.get_tokenizer('ViT-B-32')

        for param in self.model.parameters():
            param.requires_grad = False

        text_tokens = self.tokenizer([self.prompt]).to(self.device)
        with torch.no_grad():
            self.text_features = self.model.encode_text(text_tokens)
            self.text_features /= self.text_features.norm(dim=-1, keepdim=True)

    def generate_image(self, canvas_size=448):
        print(f"🎨 [RayVisionWorker] Starting Ray Swarm Optimization for '{self.prompt}'...")
        
        BASE_IMAGE_PATH = r"C:\Users\adams\Downloads\9282d86a-5060-4796-bbc2-854322ae252c.jpg"
        if os.path.exists(BASE_IMAGE_PATH):
            base_pil = Image.open(BASE_IMAGE_PATH).convert("RGB").resize((canvas_size, canvas_size), Image.Resampling.BILINEAR)
            base_tensor = torch.from_numpy(np.array(base_pil)).permute(2, 0, 1).float() / 255.0
            base_tensor = base_tensor.unsqueeze(0).to(self.device)
            eps = 1e-6
            raw_canvas = torch.log(base_tensor.clamp(eps, 1.0 - eps) / (1.0 - base_tensor.clamp(eps, 1.0 - eps)))
            raw_canvas.requires_grad = True
        else:
            raw_canvas = torch.randn(1, 3, canvas_size, canvas_size, device=self.device) * 0.1
            raw_canvas.requires_grad = True

        optimizer = torch.optim.Adam([raw_canvas], lr=self.lr)
        
        # OpenCLIP normalization constants
        CLIP_MEAN = torch.tensor([0.48145466, 0.4578275, 0.40821073], device=self.device).view(1, 3, 1, 1)
        CLIP_STD = torch.tensor([0.26862954, 0.26130258, 0.27577711], device=self.device).view(1, 3, 1, 1)

        CROP_SIZES = [224, 192, 160, 128]

        for step in range(1, self.steps + 1):
            optimizer.zero_grad()
            img_tensor = torch.sigmoid(raw_canvas)

            clip_losses = []
            for crop_size in CROP_SIZES:
                max_offset = canvas_size - crop_size
                oy = torch.randint(0, max(1, max_offset), (1,)).item()
                ox = torch.randint(0, max(1, max_offset), (1,)).item()
                crop = img_tensor[:, :, oy:oy+crop_size, ox:ox+crop_size]

                clip_input = F.interpolate(crop, size=(224, 224), mode='bilinear', align_corners=False)
                clip_input_normalized = (clip_input - CLIP_MEAN) / CLIP_STD

                image_features = self.model.encode_image(clip_input_normalized)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)

                sim = torch.cosine_similarity(self.text_features, image_features)
                clip_losses.append(1.0 - sim.mean())

            clip_loss = torch.stack(clip_losses).mean()
            similarity = 1.0 - clip_loss

            tv_loss = torch.sum(torch.abs(img_tensor[:, :, :, :-1] - img_tensor[:, :, :, 1:])) + \
                      torch.sum(torch.abs(img_tensor[:, :, :-1, :] - img_tensor[:, :, 1:, :]))
            tv_normalized = tv_loss / (canvas_size * canvas_size)

            total_loss = clip_loss + 0.02 * tv_normalized
            total_loss.backward()
            optimizer.step()

            if step % 25 == 0 or step == 1:
                print(f"   [Ray Worker Step {step:03d}/{self.steps}] Cosine Sim: {similarity.item():.4f} | Loss: {total_loss.item():.4f}")

        with torch.no_grad():
            final_img = torch.sigmoid(raw_canvas).squeeze(0).permute(1, 2, 0).cpu().numpy()
            return (final_img * 255.0).astype(np.uint8)

def main():
    worker = RayVisionWorker.remote(PROMPT, STEPS, LEARNING_RATE)
    img_array = ray.get(worker.generate_image.remote())

    pil_img = Image.fromarray(img_array)
    pil_img.save(OUTPUT_PATH)
    print(f"\n🎉 [Ray Swarm Complete] Real structural vision artwork saved to:\n  👉 {os.path.abspath(OUTPUT_PATH)}")

if __name__ == "__main__":
    main()