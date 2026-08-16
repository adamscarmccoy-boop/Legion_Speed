give it """
=== SOVEREIGN ARTWORK CREATOR ===
Procedurally generates a new, premium electronic music album cover (album art)
by isolating the subject from the original photo, creating a custom retro-tech
grid/gradient background, and overlaying modern streetwear typography.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import os
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path

# Setup device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ─── CONFIGURATION ───
ARTWORK_PATH = r"E:\OTHER\SCAR BRANDING\IMG_1357-RSVP.jpeg"
OUTPUT_DIR = r"C:\WEB CASE STUDY\mastered_output\artwork_creation"
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_SIZE = (1080, 1080) # Standard 1:1 Album Square Format

print("🎨 Initializing Sovereign Album Artwork Generator...")

# 1. Load and Crop Original Artwork to Square
try:
    src_img = Image.open(ARTWORK_PATH).convert("RGB")
    w, h = src_img.size
    min_dim = min(w, h)
    # Center crop to square
    left = (w - min_dim) // 2
    top = (h - min_dim) // 2
    src_square = src_img.crop((left, top, left + min_dim, top + min_dim)).resize(OUTPUT_SIZE, Image.Resampling.LANCZOS)
    print(f"   Loaded original image: {Path(ARTWORK_PATH).name}")
except Exception as e:
    print(f"   ❌ Error loading artwork: {e}. Creating placeholder base.")
    src_square = Image.new("RGB", OUTPUT_SIZE, (40, 20, 60))

# 2. Segment Subject (DeepLabV3)
use_fallback_mask = True
fg_mask = None

try:
    print("   Isolating subject using DeepLabV3...")
    from torchvision.models.segmentation import deeplabv3_resnet50, DeepLabV3_ResNet50_Weights
    
    weights = DeepLabV3_ResNet50_Weights.DEFAULT
    model = deeplabv3_resnet50(weights=weights).eval().to(device)
    
    preprocess = weights.transforms()
    input_tensor = preprocess(src_square).unsqueeze(0).to(device)
    
    with torch.no_grad():
        output = model(input_tensor)['out'][0]
        
    output_predictions = output.argmax(0)
    person_mask = (output_predictions == 15).cpu().numpy().astype(np.uint8) * 255
    
    if person_mask.sum() > (person_mask.size * 0.02 * 255):
        # Resize mask back to square dimensions
        fg_mask = Image.fromarray(person_mask).resize(OUTPUT_SIZE, Image.Resampling.BILINEAR)
        fg_mask = fg_mask.filter(ImageFilter.GaussianBlur(10)) # Smooth edges
        use_fallback_mask = False
        print("   ✅ Subject isolated.")
except Exception as e:
    print(f"   ⚠️ Model isolation bypassed: {e}")

if use_fallback_mask:
    # Fallback to high-quality center vignette
    mask_canvas = Image.new("L", OUTPUT_SIZE, 0)
    draw_mask = ImageDraw.Draw(mask_canvas)
    cx, cy = OUTPUT_SIZE[0] // 2, OUTPUT_SIZE[1] // 2
    rx, ry = int(OUTPUT_SIZE[0] * 0.38), int(OUTPUT_SIZE[1] * 0.38)
    draw_mask.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    fg_mask = mask_canvas.filter(ImageFilter.GaussianBlur(100))
    print("   ✅ Vignette focal mask generated.")

# 3. Create a Brand New Procedural Background
print("   Generating custom retro-tech background...")
cx, cy = OUTPUT_SIZE[0] // 2, OUTPUT_SIZE[1] // 2
bg = Image.new("RGB", OUTPUT_SIZE, (10, 8, 16)) # Deep space navy
draw_bg = ImageDraw.Draw(bg)

# Draw radial gradient center glow
glow = Image.new("L", OUTPUT_SIZE, 0)
draw_glow = ImageDraw.Draw(glow)
for r in range(OUTPUT_SIZE[0], 0, -8):
    alpha = int(140 * (1 - (r / OUTPUT_SIZE[0])**2))
    draw_glow.ellipse([cx - r//2, cy - r//2, cx + r//2, cy + r//2], fill=alpha)

glow_color = Image.new("RGB", OUTPUT_SIZE, (138, 43, 226)) # Purple Glow
bg = Image.composite(glow_color, bg, glow)

# Draw retro perspective grid lines
grid_draw = ImageDraw.Draw(bg)
grid_color = (40, 35, 70)
# Vertical perspective lines
for x in range(0, OUTPUT_SIZE[0] + 1, 60):
    grid_draw.line([(x, OUTPUT_SIZE[1]), (cx + (x - cx) * 0.2, OUTPUT_SIZE[1] - 400)], fill=grid_color, width=1)
# Horizontal lines
for y in range(OUTPUT_SIZE[1] - 400, OUTPUT_SIZE[1] + 1, 40):
    prog = (y - (OUTPUT_SIZE[1] - 400)) / 400.0
    grid_draw.line([(0, y), (OUTPUT_SIZE[0], y)], fill=grid_color, width=1)

# 4. Composite isolated subject with background
subject_only = Image.composite(src_square, Image.new("RGB", OUTPUT_SIZE, (0,0,0)), fg_mask)

# Add subtle drop shadow / outer glow to subject
shadow_mask = fg_mask.filter(ImageFilter.GaussianBlur(25))
shadow_color = Image.new("RGB", OUTPUT_SIZE, (255, 0, 128)) # Neon Pink Glow
bg = Image.composite(shadow_color, bg, shadow_mask)

# Blend subject onto background
final_art = Image.composite(src_square, bg, fg_mask)

# 5. Overlay Streetwear Graphic Design & Typography
print("   Overlaying streetwear graphic layout & typography...")
draw = ImageDraw.Draw(final_art)

# Font setup
try:
    font_large = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 64)
    font_medium = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 28)
    font_small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
    font_tiny = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 12)
except:
    font_large = ImageFont.load_default()
    font_medium = font_large
    font_small = font_large
    font_tiny = font_large

# Draw thin technical border frame
border_inset = 40
draw.rectangle(
    [border_inset, border_inset, OUTPUT_SIZE[0] - border_inset, OUTPUT_SIZE[1] - border_inset],
    outline=(100, 80, 150), width=1
)

# Text details
draw.text((border_inset + 20, border_inset + 20), "SOVEREIGN SYSTEM v0.2", fill=(180, 120, 255), font=font_small)
draw.text((OUTPUT_SIZE[0] - border_inset - 20, border_inset + 20), "CATALOG ID: SVG-002", fill=(180, 120, 255), font=font_small, anchor="ra")

# Bottom branding plate (dark transparent box)
plate_h = 160
draw.rectangle(
    [border_inset + 20, OUTPUT_SIZE[1] - border_inset - plate_h - 20, OUTPUT_SIZE[0] - border_inset - 20, OUTPUT_SIZE[1] - border_inset - 20],
    fill=(0, 0, 0, 180), outline=(138, 43, 226), width=1
)

# Typography on plate
draw.text((border_inset + 40, OUTPUT_SIZE[1] - border_inset - plate_h), "WHAT A WASTE", fill=(255, 255, 255), font=font_large)
draw.text((border_inset + 40, OUTPUT_SIZE[1] - border_inset - 55), "SOVEREIGN LEGION", fill=(180, 120, 255), font=font_medium)

# Tech specs on bottom right plate
draw.text((OUTPUT_SIZE[0] - border_inset - 40, OUTPUT_SIZE[1] - border_inset - plate_h + 10), "FORMAT: 48KHZ STEREO", fill=(150, 150, 180), font=font_tiny, anchor="ra")
draw.text((OUTPUT_SIZE[0] - border_inset - 40, OUTPUT_SIZE[1] - border_inset - plate_h + 30), "BPM: 128 | KEY: F# MIN", fill=(150, 150, 180), font=font_tiny, anchor="ra")
draw.text((OUTPUT_SIZE[0] - border_inset - 40, OUTPUT_SIZE[1] - border_inset - plate_h + 50), "OCTOBER 2026 RELEASE", fill=(150, 150, 180), font=font_tiny, anchor="ra")

# Draw a technical mock barcode in the corner
barcode_x = OUTPUT_SIZE[0] - border_inset - 140
barcode_y = OUTPUT_SIZE[1] - border_inset - 75
draw.rectangle([barcode_x, barcode_y, barcode_x + 100, barcode_y + 40], fill=(20, 15, 30))
bar_draw = ImageDraw.Draw(final_art)
np.random.seed(42)
curr_bx = barcode_x + 5
while curr_bx < barcode_x + 95:
    w_bar = np.random.choice([2, 4, 6])
    bar_draw.rectangle([curr_bx, barcode_y + 5, curr_bx + w_bar - 1, barcode_y + 35], fill=(255, 255, 255))
    curr_bx += w_bar + np.random.choice([2, 4])

output_art_path = os.path.join(OUTPUT_DIR, "new_album_art.png")
final_art.save(output_art_path)
print(f"\n✅ SUCCESS: New Album Cover generated at: {output_art_path}")
