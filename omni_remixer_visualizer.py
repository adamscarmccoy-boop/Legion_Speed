"""
=== SOVEREIGN OMNI-REMIXER & SUBJECT-ISOLATED VISUALIZER ===
Implements Option 2 (Subject-Isolated Visualizer) and Option 3 (Envelope/Spectral Transfer).
Takes a Reference track (dynamics) + Target track (audio content) + Artwork → Remixed Audio + Layered Video.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import os
import time
import numpy as np
import soundfile as sf
import librosa
import av
import torch
import torchvision.transforms.functional as F
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path

# Setup device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🚀 Using Device: {device}")

# ─── CONFIGURATION ───
REF_TRACK_PATH = r"C:\WEB CASE STUDY\sovereign_onnx_masters\ONNX_SCAR-red strobe.mp3"
TGT_TRACK_PATH = r"C:\WEB CASE STUDY\sovereign_onnx_masters\ONNX_SCAR-red strobe.mp3"
ARTWORK_PATH = r"C:\Users\adams\Downloads\9282d86a-5060-4796-bbc2-854322ae252c.jpg"
OUTPUT_DIR = r"C:\WEB CASE STUDY\mastered_output\remix_test"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── STEP 1: LOAD AUDIO & EXTRACT ENVELOPES ───
print("\n═══ STEP 1: Extracting reference envelopes & target content ═══")
t0 = time.perf_counter()

# Load Reference
ref_y, ref_sr = librosa.load(REF_TRACK_PATH, sr=22050, mono=True)
ref_duration = librosa.get_duration(y=ref_y, sr=ref_sr)

# Load Target
tgt_y, tgt_sr = librosa.load(TGT_TRACK_PATH, sr=22050, mono=True)
tgt_duration = librosa.get_duration(y=tgt_y, sr=tgt_sr)

process_duration = min(ref_duration, tgt_duration, 30.0) # limit to 30s
print(f"   Reference Track: {os.path.basename(REF_TRACK_PATH)} ({ref_duration:.1f}s)")
print(f"   Target Track:    {os.path.basename(TGT_TRACK_PATH)} ({tgt_duration:.1f}s)")
print(f"   Processing Duration: {process_duration:.1f}s")

# Cut both to processing duration
ref_y = ref_y[:int(process_duration * ref_sr)]
tgt_y = tgt_y[:int(process_duration * tgt_sr)]

# Extract Reference Envelopes (Omni-Vectors)
hop_length = 512
frame_rate = ref_sr / hop_length
ref_rms = librosa.feature.rms(y=ref_y, hop_length=hop_length)[0]
ref_onset = librosa.onset.onset_strength(y=ref_y, sr=ref_sr, hop_length=hop_length)

# Reference Frequency Band Envelopes
ref_S = np.abs(librosa.stft(ref_y, hop_length=hop_length))
ref_freqs = librosa.fft_frequencies(sr=ref_sr)
ref_sub = np.sum(ref_S[(ref_freqs >= 20) & (ref_freqs < 80), :], axis=0)
ref_mid = np.sum(ref_S[(ref_freqs >= 250) & (ref_freqs < 2000), :], axis=0)
ref_high = np.sum(ref_S[ref_freqs >= 2000, :], axis=0)

# Normalize Envelopes
def norm(x):
    mn, mx = x.min(), x.max()
    return (x - mn) / (mx - mn + 1e-9)

ref_rms_n = norm(ref_rms)
ref_onset_n = norm(ref_onset)
ref_sub_n = norm(ref_sub)
ref_mid_n = norm(ref_mid)
ref_high_n = norm(ref_high)

# Extract Target Envelopes (for visual sync of foreground)
tgt_rms = librosa.feature.rms(y=tgt_y, hop_length=hop_length)[0]
tgt_rms_n = norm(tgt_rms)

t_analysis = time.perf_counter() - t0

# ─── STEP 2: SPECTRAL ENVELOPE TRANSFER (OPTION 3) ───
print("\n═══ STEP 2: Performing Spectral Envelope Transfer (Remixing) ═══")
# Compute STFT of Target
tgt_stft = librosa.stft(tgt_y, hop_length=hop_length)
tgt_mag = np.abs(tgt_stft)
tgt_phase = np.angle(tgt_stft)

# Map target frames to match reference envelope length
n_envelope_frames = len(ref_rms_n)
n_stft_cols = tgt_mag.shape[1]
frames_to_map = min(n_envelope_frames, n_stft_cols)

# Apply reference envelopes to target magnitude bands
remixed_mag = tgt_mag.copy()
for col in range(frames_to_map):
    # Retrieve reference multipliers (scale target bands dynamically)
    low_mult = ref_sub_n[col]
    mid_mult = ref_mid_n[col]
    high_mult = ref_high_n[col]
    
    # Apply gains to target bins (smooth gating/remixing)
    remixed_mag[(ref_freqs >= 20) & (ref_freqs < 250), col] *= (0.2 + 1.2 * low_mult)
    remixed_mag[(ref_freqs >= 250) & (ref_freqs < 2000), col] *= (0.3 + 1.0 * mid_mult)
    remixed_mag[ref_freqs >= 2000, col] *= (0.2 + 1.1 * high_mult)

# Reconstruct Audio using Inverse STFT (ISTFT)
remixed_stft = remixed_mag * np.exp(1j * tgt_phase)
remixed_y = librosa.istft(remixed_stft, hop_length=hop_length)

remixed_audio_path = os.path.join(OUTPUT_DIR, "remixed_content.wav")
sf.write(remixed_audio_path, remixed_y, ref_sr)
print(f"   ✅ Remixed audio written to: {remixed_audio_path}")

# ─── STEP 3: SUBJECT ISOLATION (OPTION 2) ───
print("\n═══ STEP 3: Isolating subject from artwork ═══")
VIDEO_W, VIDEO_H = 1080, 1920

# Load Artwork
try:
    art_img = Image.open(ARTWORK_PATH).convert("RGB")
    # Resize and Crop to 1080x1920
    img_ratio = art_img.width / art_img.height
    vid_ratio = VIDEO_W / VIDEO_H
    if img_ratio > vid_ratio:
        new_h = VIDEO_H
        new_w = int(new_h * img_ratio)
    else:
        new_w = VIDEO_W
        new_h = int(new_w / img_ratio)
    resized_art = art_img.resize((new_w, new_h), Image.Resampling.BILINEAR)
    left = (new_w - VIDEO_W) // 2
    top = (new_h - VIDEO_H) // 2
    cropped_art = resized_art.crop((left, top, left + VIDEO_W, top + VIDEO_H))
except Exception as e:
    print(f"   ❌ Error loading artwork: {e}. Generating blank artwork.")
    cropped_art = Image.new("RGB", (VIDEO_W, VIDEO_H), (30, 15, 45))

# Attempt Semantic Segmentation using DeepLabV3
use_fallback_mask = True
fg_mask = None

try:
    print("   Attempting to load DeepLabV3 segmentation model...")
    from torchvision.models.segmentation import deeplabv3_resnet50, DeepLabV3_ResNet50_Weights
    
    # Load model with weights from local hub or download
    weights = DeepLabV3_ResNet50_Weights.DEFAULT
    model = deeplabv3_resnet50(weights=weights).eval().to(device)
    
    # Transform image for model input
    preprocess = weights.transforms()
    input_tensor = preprocess(cropped_art).unsqueeze(0).to(device)
    
    with torch.no_grad():
        output = model(input_tensor)['out'][0]
    
    # Generate binary mask of all detected objects/persons (classes > 0)
    output_predictions = output.argmax(0)
    # Class 15 is person in COCO dataset
    person_mask = (output_predictions == 15).cpu().numpy().astype(np.uint8) * 255
    
    # If a person/subject is detected, use it
    if person_mask.sum() > (person_mask.size * 0.02 * 255):
        # Resize mask back to original video dimensions
        fg_mask = Image.fromarray(person_mask).resize((VIDEO_W, VIDEO_H), Image.Resampling.BILINEAR)
        fg_mask = fg_mask.filter(ImageFilter.GaussianBlur(5)) # Soften edges
        use_fallback_mask = False
        print("   ✅ Semantic subject isolated successfully.")
except Exception as e:
    print(f"   ⚠️ Segmentation model failed or not found: {e}. Using intelligent fallback mask.")

if use_fallback_mask:
    # Build a high-quality radial/vignette center mask (common visual composition focal point)
    mask_canvas = Image.new("L", (VIDEO_W, VIDEO_H), 0)
    draw_mask = ImageDraw.Draw(mask_canvas)
    # Draw soft ellipse in the center 60%
    cx, cy = VIDEO_W // 2, VIDEO_H // 2
    rx, ry = int(VIDEO_W * 0.35), int(VIDEO_H * 0.3)
    draw_mask.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    fg_mask = mask_canvas.filter(ImageFilter.GaussianBlur(80))
    print("   ✅ Radial depth focal mask generated.")

# Separate into Foreground (Subject) and Background Tensors
base_np = np.array(cropped_art)
mask_np = np.array(fg_mask)[:, :, np.newaxis] / 255.0

bg_np = (base_np * (1.0 - mask_np)).astype(np.uint8)
fg_np = (base_np * mask_np).astype(np.uint8)

# Upload both layers to GPU/Device
bg_tensor = torch.from_numpy(bg_np).permute(2, 0, 1).float() / 255.0
bg_tensor = bg_tensor.to(device)

fg_tensor = torch.from_numpy(fg_np).permute(2, 0, 1).float() / 255.0
fg_tensor = fg_tensor.to(device)

# Alpha transparency tensor
mask_tensor = torch.from_numpy(mask_np).permute(2, 0, 1).float()
mask_tensor = mask_tensor.to(device)

# ─── STEP 4: LAYERED RENDER LOOP ───
print("\n═══ STEP 4: Rendering Layered Audio-Reactive Video ═══")
t_video = time.perf_counter()

VIDEO_FPS = 30
total_video_frames = int(process_duration * VIDEO_FPS)
output_video_path = os.path.join(OUTPUT_DIR, "sovereign_remix_reel.mp4")

# PyAV setup
container = av.open(output_video_path, mode='w')
stream = container.add_stream('libx264', rate=VIDEO_FPS)
stream.width = VIDEO_W
stream.height = VIDEO_H
stream.pix_fmt = 'yuv420p'
stream.options = {'crf': '18', 'preset': 'fast'}

# Audio output stream
audio_stream = container.add_stream('aac', rate=ref_sr)
audio_stream.layout = 'mono'

# Font setup
try:
    font_large = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 48)
    font_small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 28)
    font_tiny = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 20)
except:
    font_large = ImageFont.load_default()
    font_small = font_large
    font_tiny = font_large

hud_base = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))

print(f"   Rendering {total_video_frames} frames...")
for frame_idx in range(total_video_frames):
    t = frame_idx / VIDEO_FPS
    env_idx = min(int(t * frame_rate), frames_to_map - 1)
    
    # Retrieve envelopes
    ref_energy = float(ref_rms_n[env_idx])
    ref_sub_energy = float(ref_sub_n[env_idx])
    ref_mid_energy = float(ref_mid_n[env_idx])
    ref_high_energy = float(ref_high_n[env_idx])
    ref_punch = float(ref_onset_n[env_idx])
    
    tgt_energy = float(tgt_rms_n[env_idx])

    # Clone base layer tensors
    bg = bg_tensor.clone()
    fg = fg_tensor.clone()

    # --- BG EFFECTS (Reacts to Reference Sub-Bass / overall energy) ---
    # Zoom background (Scaled Down)
    bg_zoom = 1.0 + ref_sub_energy * 0.05
    if bg_zoom > 1.01:
        ch = int(VIDEO_H / bg_zoom)
        cw = int(VIDEO_W / bg_zoom)
        ctop = (VIDEO_H - ch) // 2
        cleft = (VIDEO_W - cw) // 2
        bg = F.crop(bg, ctop, cleft, ch, cw)
        bg = torch.nn.functional.interpolate(
            bg.unsqueeze(0), size=(VIDEO_H, VIDEO_W), mode='bilinear', align_corners=False
        ).squeeze(0)
        
    # Effect 1: Dynamic Hue Shifting (Scaled Down)
    hue_val = float(ref_mid_energy * 0.15 - 0.075) 
    bg = F.adjust_hue(bg, hue_val)
    
    # Effect 2: High Frequency Rotation Warp (Scaled Down)
    rotation_angle = float(ref_high_energy * 8.0) 
    bg = F.rotate(bg, rotation_angle)
    
    # Effect 3: The Flashbang Invert (Extremely high threshold so it rarely triggers)
    if ref_punch > 0.95:
        bg = F.invert(bg)
        
    bg = F.adjust_saturation(bg, 0.4 + ref_mid_energy * 1.5)
    bg = F.adjust_brightness(bg, 0.5 + ref_energy * 0.7)

    # --- FG EFFECTS (Reacts to Target track dynamics to keep original presence) ---
    # Foreground slight pulse
    fg_zoom = 1.0 + tgt_energy * 0.08
    if fg_zoom > 1.01:
        ch = int(VIDEO_H / fg_zoom)
        cw = int(VIDEO_W / fg_zoom)
        ctop = (VIDEO_H - ch) // 2
        cleft = (VIDEO_W - cw) // 2
        fg = F.crop(fg, ctop, cleft, ch, cw)
        fg = torch.nn.functional.interpolate(
            fg.unsqueeze(0), size=(VIDEO_H, VIDEO_W), mode='bilinear', align_corners=False
        ).squeeze(0)
        
    fg = F.adjust_saturation(fg, 0.9 + tgt_energy * 0.5)

    # --- COMPOSE FOREGROUND + BACKGROUND ---
    # Blend bg and fg using mask
    final_tensor = bg * (1.0 - mask_tensor) + fg * mask_tensor
    
    # Download and encode
    frame_array = (final_tensor.permute(1, 2, 0).clamp(0.0, 1.0) * 255.0).byte().cpu().numpy()
    video_frame = av.VideoFrame.from_ndarray(frame_array, format='rgb24')
    video_frame.pts = frame_idx
    for packet in stream.encode(video_frame):
        container.mux(packet)

    if frame_idx % (VIDEO_FPS * 5) == 0:
        print(f"   📹 Rendered frame {frame_idx}/{total_video_frames} ({t:.1f}s)")

# Flush video
for packet in stream.encode():
    container.mux(packet)

# Write remixed audio track
print("   🔊 Writing remixed audio track...")
chunk_size = 1024
for i in range(0, len(remixed_y), chunk_size):
    chunk = remixed_y[i:i + chunk_size]
    if len(chunk) < chunk_size:
        chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
    audio_frame = av.AudioFrame.from_ndarray(
        chunk.reshape(1, -1).astype(np.float32), format='fltp', layout='mono'
    )
    audio_frame.sample_rate = ref_sr
    audio_frame.pts = i
    for packet in audio_stream.encode(audio_frame):
        container.mux(packet)

for packet in audio_stream.encode():
    container.mux(packet)

container.close()

t_video_total = time.perf_counter() - t_video
t_total = time.perf_counter() - t0

# ─── RESULTS ───
file_size = os.path.getsize(output_video_path)
print(f"\n═══ ✅ REMIX REEL COMPLETE ═══")
print(f"   📁 Output: {output_video_path}")
print(f"   📐 Format: {VIDEO_W}x{VIDEO_H} @ {VIDEO_FPS}fps (9:16 vertical)")
print(f"   ⏱️  Audio processing: {t_analysis:.2f} sec")
print(f"   ⏱️  Video render:     {t_video_total:.2f} sec")
print(f"   ⏱️  Total:            {t_total:.2f} sec")
print(f"   💾 File size: {file_size / (1024*1024):.1f} MB")
print(f"   🧠 Model/Fallback:   {'Semantic DeepLabV3' if not use_fallback_mask else 'Radial Vignette Depth'}")
