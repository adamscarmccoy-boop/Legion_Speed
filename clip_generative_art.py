"""
=== SOVEREIGN CLIP-GUIDED IMAGE GENERATOR ===
Generates a brand-new stylized image from scratch (using only a text prompt)
by running a PyTorch backpropagation loop on a raw pixel tensor guided by CLIP.
Uses openai/clip-vit-base-patch32 which is pre-installed in your venv.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import os
import time
import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

# ─── CONFIGURATION ───
# Accepts a dynamic prompt injected by legion_vision_orchestrator.py via env var.
# Falls back to the hardcoded default when run standalone.
PROMPT = os.getenv(
    "CLIP_PROMPT",
    "cyberpunk liquid chrome mechanical skull, neon glowing red eyes, highly detailed 3d digital art, dark moody background"
)
STEPS = 400          # More steps = more coherent structure
LEARNING_RATE = 0.04  # Conservative LR to prevent gradient explosion

# Generate dynamic name based on prompt slug and timestamp
import re
clean_prompt = re.sub(r'[^a-zA-Z0-9]', '_', PROMPT[:30]).strip('_').lower()
timestamp = time.strftime("%Y%m%d_%H%M%S")
filename = f"generated_art_{clean_prompt}_{timestamp}.png"

OUTPUT_DIR = "mastered_output"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── SETUP DEVICE & MODELS ───
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🚀 Using Device: {device}")
print("📦 Loading pre-installed CLIP model...")
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

# ─── INITIALIZE LEARNABLE CANVAS WITH BASE IMAGE ───
canvas_size = 448
BASE_IMAGE_PATH = r"C:\Users\adams\Downloads\9282d86a-5060-4796-bbc2-854322ae252c.jpg"

if os.path.exists(BASE_IMAGE_PATH):
    print(f"🖼️ Loading base image for structure: {os.path.basename(BASE_IMAGE_PATH)}")
    base_pil = Image.open(BASE_IMAGE_PATH).convert("RGB").resize((canvas_size, canvas_size), Image.Resampling.BILINEAR)
    base_tensor = torch.from_numpy(np.array(base_pil)).permute(2, 0, 1).float() / 255.0
    base_tensor = base_tensor.unsqueeze(0).to(device)
    
    # We parameterize the canvas as logits (inverse sigmoid) of the base image
    # so we start exactly with the base image structure
    eps = 1e-6
    raw_canvas = torch.log(base_tensor.clamp(eps, 1.0 - eps) / (1.0 - base_tensor.clamp(eps, 1.0 - eps)))
    raw_canvas.requires_grad = True
else:
    print("⚠️ Base image not found! Falling back to neutral grey start.")
    raw_canvas = torch.zeros(1, 3, canvas_size, canvas_size, device=device)
    raw_canvas.requires_grad = True

# Conservative LR: prevents gradient explosion that causes high-freq noise
optimizer = torch.optim.Adam([raw_canvas], lr=LEARNING_RATE)

# CLIP normalization constants
CLIP_MEAN = torch.tensor([0.48145466, 0.4578275, 0.40821073], device=device).view(1, 3, 1, 1)
CLIP_STD = torch.tensor([0.26862954, 0.26130258, 0.27577711], device=device).view(1, 3, 1, 1)

print("\n🎨 Commencing CLIP backpropagation loop...")
t0 = time.perf_counter()

# Multi-crop augmentation sizes: forces CLIP to see coherent structure at
# multiple scales simultaneously, preventing adversarial single-view noise.
CROP_SIZES = [224, 192, 160]

for step in range(1, STEPS + 1):
    optimizer.zero_grad()
    
    # 1. Map raw canvas values to [0, 1] range using sigmoid
    img_tensor = torch.sigmoid(raw_canvas)

    # 2. Multi-crop augmentation: average CLIP loss across random crops
    #    This is the PRIMARY noise fix — a single 224px view allows the optimizer
    #    to hide high-frequency noise that CLIP can't detect at one scale.
    clip_losses = []
    for crop_size in CROP_SIZES:
        # Random crop offset
        max_offset = canvas_size - crop_size
        oy = torch.randint(0, max(1, max_offset), (1,)).item()
        ox = torch.randint(0, max(1, max_offset), (1,)).item()
        crop = img_tensor[:, :, oy:oy+crop_size, ox:ox+crop_size]
        
        # Resize crop to 224x224 for CLIP
        clip_input = F.interpolate(crop, size=(224, 224), mode='bilinear', align_corners=False)
        
        # Normalize with CLIP constants
        clip_input_normalized = (clip_input - CLIP_MEAN) / CLIP_STD
        
        # Get CLIP image embedding
        vision_outputs = model.vision_model(pixel_values=clip_input_normalized)
        image_features = model.visual_projection(vision_outputs[1])  # pooler_output
        image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
        
        sim = torch.cosine_similarity(text_features, image_features)
        clip_losses.append(1.0 - sim.mean())
    
    clip_loss = torch.stack(clip_losses).mean()
    similarity = 1.0 - clip_loss  # for logging

    # 3. Total Variation loss — weight increased 10x to aggressively suppress noise.
    #    TV / pixels normalizes by canvas area so it scales correctly.
    tv_loss = torch.sum(torch.abs(img_tensor[:, :, :, :-1] - img_tensor[:, :, :, 1:])) + \
              torch.sum(torch.abs(img_tensor[:, :, :-1, :] - img_tensor[:, :, 1:, :]))
    tv_normalized = tv_loss / (canvas_size * canvas_size)

    # 4. Anchor loss: if base image exists, penalize straying too far from it.
    #    This preserves original structure and prevents full dissolution into noise.
    if os.path.exists(BASE_IMAGE_PATH):
        anchor_loss = F.mse_loss(img_tensor, base_tensor.detach())
    else:
        anchor_loss = torch.tensor(0.0, device=device)

    total_loss = clip_loss + 0.03 * tv_normalized + 0.05 * anchor_loss
    
    total_loss.backward()
    optimizer.step()
    
    # Dynamic prints
    if step % 40 == 0 or step == 1:
        print(f"   Step {step:03d}/{STEPS} | Cosine Sim: {similarity.item():.4f} | TV: {tv_normalized.item():.4f} | Total Loss: {total_loss.item():.4f}")

t_opt = time.perf_counter() - t0
print(f"✅ Optimization complete in {t_opt:.2f} seconds.")

# ─── EXPORT RESULT ───
with torch.no_grad():
    final_img = torch.sigmoid(raw_canvas).squeeze(0).permute(1, 2, 0).cpu().numpy()
    final_img = (final_img * 255.0).astype(np.uint8)
    
    pil_img = Image.fromarray(final_img)
    pil_img.save(OUTPUT_PATH)
    print(f"\n📁 Generative Artwork saved to: {os.path.abspath(OUTPUT_PATH)}")
