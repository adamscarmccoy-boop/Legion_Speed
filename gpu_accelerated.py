"""
=== SOVEREIGN MARKETING CREATOR - GPU ACCELERATED ===
Accelerates the rendering pipeline using PyTorch/torchvision GPU tensor operations.
Uses PIL on CPU only for drawing high-quality vector overlays (text, rings, bars),
then uploads them to the GPU for blending and sends them to PyAV/FFmpeg.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import os
import time
import json
import numpy as np
import soundfile as sf
import librosa
import av
import torch
import torchvision.transforms.functional as F
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# Set PyTorch device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🚀 Using PyTorch Device: {device}")

# ─── CONFIGURATION ───
TRACK_PATH = r"E:\DJSUSAN\LEGION\what a waste-2 (Edit).wav"
ARTWORK_FILES = [
    r"E:\OTHER\SCAR BRANDING\IMG_1357-RSVP.jpeg",
]
OUTPUT_DIR = r"C:\WEB CASE STUDY\mastered_output\marketing_test"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load artwork paths
artwork_files = [Path(f) for f in ARTWORK_FILES if os.path.exists(f)]

# Also try to grab more from SCAR BRANDING if available
scar_dir = Path(r"E:\OTHER\SCAR BRANDING")
if scar_dir.exists():
    for ext in ['*.jpeg', '*.jpg', '*.png']:
        for f in scar_dir.glob(ext):
            if f not in artwork_files and f.stat().st_size > 50000:
                artwork_files.append(f)
            if len(artwork_files) >= 6:
                break

print(f"🎵 Track: {os.path.basename(TRACK_PATH)}")
print(f"🎨 Artwork files: {len(artwork_files)}")
for f in artwork_files[:4]:
    print(f"   → {f.name}")

# ─── STEP 1: LOAD AUDIO & EXTRACT OMNI-VECTORS ───
print("\n═══ STEP 1: Loading audio & extracting Omni-Vectors ═══")
t0 = time.perf_counter()

y, sr = librosa.load(TRACK_PATH, sr=22050, mono=True)
duration = librosa.get_duration(y=y, sr=sr)
print(f"   Duration: {duration:.1f} sec, SR: {sr}")

# Frame-level Omni-Vectors (for driving visuals)
hop_length = 512
frame_rate = sr / hop_length  # ~43 fps

# Core Omni-Vector features (per-frame)
rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)[0]
spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr, hop_length=hop_length)[0]
spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=hop_length)[0]
zcr = librosa.feature.zero_crossing_rate(y=y, hop_length=hop_length)[0]
onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)

# Frequency band energies
S = np.abs(librosa.stft(y, hop_length=hop_length))
freqs = librosa.fft_frequencies(sr=sr)
sub_bass = np.sum(S[(freqs >= 20) & (freqs < 80), :], axis=0)
bass = np.sum(S[(freqs >= 80) & (freqs < 250), :], axis=0)
mids = np.sum(S[(freqs >= 250) & (freqs < 2000), :], axis=0)
highs = np.sum(S[freqs >= 2000, :], axis=0)

# Normalize all features to 0-1 range for visual mapping
def norm(x):
    mn, mx = x.min(), x.max()
    return (x - mn) / (mx - mn + 1e-9)

rms_n = norm(rms)
centroid_n = norm(spectral_centroid)
bandwidth_n = norm(spectral_bandwidth)
onset_n = norm(onset_env)
sub_bass_n = norm(sub_bass)
bass_n = norm(bass)
mids_n = norm(mids)
highs_n = norm(highs)

n_frames = min(len(rms_n), len(centroid_n), len(onset_n), len(sub_bass_n))
print(f"   Omni-Vector frames: {n_frames} ({n_frames/frame_rate:.1f} sec)")

t_analysis = time.perf_counter() - t0
print(f"   ⏱️ Analysis time: {t_analysis:.2f} sec")

# ─── STEP 2: LOAD & PREP ARTWORK AS PYTORCH TENSORS ───
print("\n═══ STEP 2: Loading artwork & converting to GPU Tensors ═══")
VIDEO_W, VIDEO_H = 1080, 1920  # 9:16 vertical
art_tensors = []

for art_path in artwork_files[:8]:
    try:
        # Load and convert image using PIL
        img = Image.open(art_path).convert("RGB")
        img_w, img_h = img.size
        
        # Calculate aspect ratio cover crop dimensions
        img_ratio = img_w / img_h
        vid_ratio = VIDEO_W / VIDEO_H
        if img_ratio > vid_ratio:
            new_h = VIDEO_H
            new_w = int(new_h * img_ratio)
        else:
            new_w = VIDEO_W
            new_h = int(new_w / img_ratio)
            
        resized = img.resize((new_w, new_h), Image.Resampling.BILINEAR)
        left = (new_w - VIDEO_W) // 2
        top = (new_h - VIDEO_H) // 2
        cropped = resized.crop((left, top, left + VIDEO_W, top + VIDEO_H))
        
        # Convert to float PyTorch tensor (C, H, W) scaled to [0, 1]
        tensor = torch.from_numpy(np.array(cropped)).permute(2, 0, 1).float() / 255.0
        art_tensors.append(tensor.to(device))
        print(f"   ✅ Loaded {art_path.name} to {device}")
    except Exception as e:
        print(f"   ❌ {art_path.name}: {e}")

if not art_tensors:
    print("No artwork loaded! Exiting.")
    sys.exit(1)

# ─── STEP 3: GENERATE AUDIO-REACTIVE VIDEO ───
print("\n═══ STEP 3: Generating GPU-accelerated marketing video ═══")
t_video = time.perf_counter()

VIDEO_FPS = 30
video_duration = min(duration, 30.0)  # Cap at 30 sec for social
total_video_frames = int(video_duration * VIDEO_FPS)

output_video_path = os.path.join(OUTPUT_DIR, "sovereign_marketing_reel.mp4")

# Open output container with PyAV
container = av.open(output_video_path, mode='w')
stream = container.add_stream('libx264', rate=VIDEO_FPS)
stream.width = VIDEO_W
stream.height = VIDEO_H
stream.pix_fmt = 'yuv420p'
stream.options = {'crf': '18', 'preset': 'fast'}

# Audio stream - write the original audio
audio_stream = container.add_stream('aac', rate=sr)
audio_stream.layout = 'mono'

# Brand text setup
try:
    font_large = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 48)
    font_small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 28)
    font_tiny = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 20)
except:
    font_large = ImageFont.load_default()
    font_small = font_large
    font_tiny = font_large

# Create solid base black overlay canvas with transparency for the HUD elements
hud_mask = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))

print(f"   Generating {total_video_frames} frames @ {VIDEO_FPS} fps ({video_duration:.1f} sec)...")

for frame_idx in range(total_video_frames):
    t = frame_idx / VIDEO_FPS
    audio_frame_idx = min(int(t * frame_rate), n_frames - 1)

    # Get current Omni-Vector values
    energy = float(rms_n[audio_frame_idx])
    brightness = float(centroid_n[audio_frame_idx])
    punch = float(onset_n[audio_frame_idx])
    low = float(sub_bass_n[audio_frame_idx])
    mid = float(mids_n[audio_frame_idx])
    high = float(highs_n[audio_frame_idx])

    # Select base artwork tensor
    cycle_period = max(1, total_video_frames // len(art_tensors))
    art_idx = (frame_idx // cycle_period) % len(art_tensors)
    bg_tensor = art_tensors[art_idx].clone()  # Shape: (3, 1920, 1080)

    # ─── GPU-REACTIVE TRANSFORMS ───

    # 1. Zoom pulse based on energy (RMS)
    zoom = 1.0 + energy * 0.15
    if zoom > 1.01:
        # Crop to zoom window center
        cropped_h = int(VIDEO_H / zoom)
        cropped_w = int(VIDEO_W / zoom)
        top = (VIDEO_H - cropped_h) // 2
        left = (VIDEO_W - cropped_w) // 2
        bg_tensor = F.crop(bg_tensor, top, left, cropped_h, cropped_w)
        # Interpolate back to original size
        bg_tensor = bg_tensor.unsqueeze(0)  # add batch dim
        bg_tensor = torch.nn.functional.interpolate(
            bg_tensor, size=(VIDEO_H, VIDEO_W), mode='bilinear', align_corners=False
        ).squeeze(0)

    # 2. Color adjustments (Saturation & Brightness)
    bg_tensor = F.adjust_saturation(bg_tensor, 0.6 + brightness * 1.2)
    bg_tensor = F.adjust_brightness(bg_tensor, 0.7 + energy * 0.6)

    # 3. Gaussian Blur on low energy
    if energy < 0.3:
        blur_radius = (0.3 - energy) * 6.0
        # Ensure kernel size is odd
        kernel_size = int(blur_radius * 2) | 1
        if kernel_size > 1:
            bg_tensor = F.gaussian_blur(bg_tensor, [kernel_size, kernel_size], [blur_radius, blur_radius])

    # ─── HUD OVERLAYS (PIL CPU -> GPU Composite) ───
    # We draw on a transparent canvas and upload/blend with the background tensor on GPU
    hud_img = hud_mask.copy()
    draw = ImageDraw.Draw(hud_img)

    # Bottom gradient overlay for readability
    for gy in range(VIDEO_H - 400, VIDEO_H):
        alpha = int(200 * ((gy - (VIDEO_H - 400)) / 400))
        draw.rectangle([(0, gy), (VIDEO_W, gy + 1)], fill=(0, 0, 0, min(alpha, 200)))

    # Waveform bar visualization at bottom
    bar_y = VIDEO_H - 180
    bar_height = 80
    n_bars = 40
    for i in range(n_bars):
        bar_audio_idx = min(int(audio_frame_idx + (i - n_bars // 2) * 0.5), n_frames - 1)
        bar_audio_idx = max(0, bar_audio_idx)
        bar_energy = float(rms_n[bar_audio_idx])

        bar_x = int(VIDEO_W * 0.1 + (VIDEO_W * 0.8) * i / n_bars)
        bar_w = max(4, int(VIDEO_W * 0.8 / n_bars) - 4)
        bh = int(bar_height * bar_energy)

        # Color based on frequency content
        r = int(180 + 75 * high)
        g = int(80 + 120 * mid)
        b = int(180 + 75 * low)
        r, g, b = min(r, 255), min(g, 255), min(b, 255)

        draw.rectangle(
            [(bar_x, bar_y - bh), (bar_x + bar_w, bar_y)],
            fill=(r, g, b, 255)
        )

    # Energy ring / pulse circle
    ring_radius = int(60 + energy * 100)
    ring_cx, ring_cy = VIDEO_W // 2, VIDEO_H // 3
    ring_color = (
        int(200 + 55 * punch),
        int(100 + 100 * brightness),
        int(200 + 55 * low),
        255
    )
    ring_color = tuple(min(255, c) for c in ring_color)
    for r_offset in range(3):
        draw.ellipse(
            [(ring_cx - ring_radius - r_offset, ring_cy - ring_radius - r_offset),
             (ring_cx + ring_radius + r_offset, ring_cy + ring_radius + r_offset)],
            outline=ring_color, width=2
        )

    # Track info text
    track_name = "WHAT A WASTE"
    subtitle = "SOVEREIGN LEGION"
    draw.text((VIDEO_W // 2, VIDEO_H - 120), track_name, fill=(255, 255, 255, 255), font=font_large, anchor="mm")
    draw.text((VIDEO_W // 2, VIDEO_H - 70), subtitle, fill=(200, 200, 200, 255), font=font_small, anchor="mm")
    draw.text((VIDEO_W // 2, VIDEO_H - 35), "▶ SCAER", fill=(180, 120, 255, 255), font=font_tiny, anchor="mm")

    # Timestamp / energy readout
    draw.text((30, 30), f"{t:.1f}s", fill=(255, 255, 255, 180), font=font_small)
    draw.text((30, 65), f"RMS: {energy:.2f} | PUNCH: {punch:.2f}", fill=(180, 180, 180, 255), font=font_tiny)

    # Convert HUD to tensor and upload to GPU
    hud_tensor = torch.from_numpy(np.array(hud_img)).permute(2, 0, 1).float() / 255.0
    hud_tensor = hud_tensor.to(device)

    # Blend HUD alpha channel with background
    alpha = hud_tensor[3:4, :, :]  # Shape (1, H, W)
    hud_rgb = hud_tensor[0:3, :, :]
    
    blended_tensor = bg_tensor * (1.0 - alpha) + hud_rgb * alpha
    
    # Scale back to uint8, bring back to CPU, and send to encoder
    out_frame_np = (blended_tensor.permute(1, 2, 0).clamp(0.0, 1.0) * 255.0).byte().cpu().numpy()

    # Convert to PyAV Frame
    video_frame = av.VideoFrame.from_ndarray(out_frame_np, format='rgb24')
    video_frame.pts = frame_idx
    for packet in stream.encode(video_frame):
        container.mux(packet)

    if frame_idx % (VIDEO_FPS * 5) == 0:
        print(f"   📹 Frame {frame_idx}/{total_video_frames} ({t:.1f}s)")

# Flush video
for packet in stream.encode():
    container.mux(packet)

# Write audio
print("   🔊 Writing audio track...")
y_full, sr_full = sf.read(TRACK_PATH, dtype='float32', always_2d=True)
samples_needed = int(video_duration * sr_full)
y_clip = y_full[:samples_needed]
if y_clip.ndim > 1:
    y_clip = y_clip[:, 0]  # mono

chunk_size = 1024
for i in range(0, len(y_clip), chunk_size):
    chunk = y_clip[i:i + chunk_size]
    if len(chunk) < chunk_size:
        chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
    audio_frame = av.AudioFrame.from_ndarray(
        chunk.reshape(1, -1).astype(np.float32), format='fltp', layout='mono'
    )
    audio_frame.sample_rate = sr_full
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
print(f"\n═══ ✅ MARKETING REEL COMPLETE ═══")
print(f"   📁 Output: {output_video_path}")
print(f"   📐 Format: {VIDEO_W}x{VIDEO_H} @ {VIDEO_FPS}fps (9:16 vertical)")
print(f"   ⏱️  Audio analysis: {t_analysis:.2f} sec")
print(f"   ⏱️  Video render:   {t_video_total:.2f} sec")
print(f"   ⏱️  Total:          {t_total:.2f} sec")
print(f"   💾 File size: {file_size / (1024*1024):.1f} MB")
print(f"   🎨 Artwork layers used: {len(art_tensors)}")
print(f"   🧬 Omni-Vector frames: {n_frames}")
print(f"\n   Ready for Instagram Reels / TikTok / YouTube Shorts 🚀")
