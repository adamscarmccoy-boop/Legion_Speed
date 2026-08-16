"""
=== SOVEREIGN REAL STRUCTURAL VISION GENERATOR ===
Generates a brand-new image with actual macro geometric shape mutations 
using PyTorch backpropagation on pixel logits guided by CLIP multi-scale crops.
"""
import sys
from unittest.mock import MagicMock
sys.modules["torchaudio"] = MagicMock()
sys.stdout.reconfigure(encoding="utf-8")

import os
import time
import re
import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

# ─── CONFIGURATION ───
PROMPT = os.getenv(
    "CLIP_PROMPT",
    "cyberpunk mechanical dragon with intricate glowing neon red wings and metallic chrome scales, hyperdetailed 3d unreal engine render, cinematic lighting"
)
STEPS = 250
LEARNING_RATE = 0.08  # Higher LR for strong geometric structural mutations

clean_prompt = re.sub(r'[^a-zA-Z0-9]', '_', PROMPT[:30]).strip('_').lower()
timestamp = time.strftime("%Y%m%d_%H%M%S")
filename = f"real_vision_generation_{clean_prompt}_{timestamp}.png"

OUTPUT_DIR = "mastered_output"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── SETUP DEVICE & MODELS ───
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🚀 Using Device: {device}")
print("📦 Loading CLIP model (openai/clip-vit-base-patch32)...")
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32", use_safetensors=True).to(device)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32", use_safetensors=True)

# Freeze CLIP parameters
for param in model.parameters():
    param.requires_grad = False

# ─── ENCODE TEXT PROMPT ───
print(f"📝 Encoding target prompt: '{PROMPT}'")
inputs = processor(text=[PROMPT], return_tensors="pt", padding=True)
with torch.no_grad():
    text_outputs = model.text_model(
        input_ids=inputs['input_ids'].to(device), 
        attention_mask=inputs['attention_mask'].to(device)
    )
    text_features = model.text_projection(text_outputs[1]) # pooler_output
    text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)

# ─── INITIALIZE LEARNABLE CANVAS ───
canvas_size = 448
BASE_IMAGE_PATH = r"C:\Users\adams\Downloads\9282d86a-5060-4796-bbc2-854322ae252c.jpg"

if os.path.exists(BASE_IMAGE_PATH):
    print(f"🖼️ Loading base image for initial seed: {os.path.basename(BASE_IMAGE_PATH)}")
    base_pil = Image.open(BASE_IMAGE_PATH).convert("RGB").resize((canvas_size, canvas_size), Image.Resampling.BILINEAR)
    base_tensor = torch.from_numpy(np.array(base_pil)).permute(2, 0, 1).float() / 255.0
    base_tensor = base_tensor.unsqueeze(0).to(device)
    
    eps = 1e-6
    raw_canvas = torch.log(base_tensor.clamp(eps, 1.0 - eps) / (1.0 - base_tensor.clamp(eps, 1.0 - eps)))
    raw_canvas.requires_grad = True
else:
    print("⚠️ Base image not found! Initializing random noise canvas for structural evolution.")
    raw_canvas = torch.randn(1, 3, canvas_size, canvas_size, device=device) * 0.1
    raw_canvas.requires_grad = True

optimizer = torch.optim.Adam([raw_canvas], lr=LEARNING_RATE)

# CLIP normalization constants
CLIP_MEAN = torch.tensor([0.48145466, 0.4578275, 0.40821073], device=device).view(1, 3, 1, 1)
CLIP_STD = torch.tensor([0.26862954, 0.26130258, 0.27577711], device=device).view(1, 3, 1, 1)

print("\n🎨 Commencing Structural Vision Generation Loop (Macro Geometry & Shape Mutation)...")
t0 = time.perf_counter()

# Multi-scale crops force CLIP to generate coherent macro objects + fine micro details
CROP_SIZES = [224, 192, 160, 128]

for step in range(1, STEPS + 1):
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
        
        vision_outputs = model.vision_model(pixel_values=clip_input_normalized)
        image_features = model.visual_projection(vision_outputs[1])
        image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
        
        sim = torch.cosine_similarity(text_features, image_features)
        clip_losses.append(1.0 - sim.mean())
    
    clip_loss = torch.stack(clip_losses).mean()
    similarity = 1.0 - clip_loss

    # Total Variation Loss (smooths spatial noise while allowing sharp macro edges)
    tv_loss = torch.sum(torch.abs(img_tensor[:, :, :, :-1] - img_tensor[:, :, :, 1:])) + \
              torch.sum(torch.abs(img_tensor[:, :, :-1, :] - img_tensor[:, :, 1:, :]))
    tv_normalized = tv_loss / (canvas_size * canvas_size)

    # Ultra-low anchor weight (0.002) so geometry can mutate freely into new objects
    if os.path.exists(BASE_IMAGE_PATH):
        anchor_loss = F.mse_loss(img_tensor, base_tensor.detach())
    else:
        anchor_loss = torch.tensor(0.0, device=device)

    total_loss = clip_loss + 0.02 * tv_normalized + 0.002 * anchor_loss
    
    total_loss.backward()
    optimizer.step()
    
    if step % 25 == 0 or step == 1:
        print(f"   Step {step:03d}/{STEPS} | Cosine Sim: {similarity.item():.4f} | TV: {tv_normalized.item():.4f} | Total Loss: {total_loss.item():.4f}")

t_opt = time.perf_counter() - t0
print(f"\n✅ Structural Vision Generation complete in {t_opt:.2f} seconds.")

# ─── EXPORT RESULT ───
with torch.no_grad():
    final_img = torch.sigmoid(raw_canvas).squeeze(0).permute(1, 2, 0).cpu().numpy()
    final_img = (final_img * 255.0).astype(np.uint8)
    
    pil_img = Image.fromarray(final_img)
    pil_img.save(OUTPUT_PATH)
    print(f"📁 Real Generative Artwork saved to: {os.path.abspath(OUTPUT_PATH)}")
