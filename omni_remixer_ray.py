"""
=== SOVEREIGN OMNI-REMIXER & LAYERED VISUALIZER - RAY PARALLELIZED ===
Parallelizes frame rendering using Ray workers to fully saturate CPU cores.
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

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import ray

# ─── CONFIGURATION ───
REF_TRACK_PATH = r"E:\DJSUSAN\LEGION\what a waste-2 (Edit).wav"
TGT_TRACK_PATH = r"E:\DJSUSAN\LEGION\one two swing.mp3"
ARTWORK_PATH = r"E:\OTHER\SCAR BRANDING\IMG_1357-RSVP.jpeg"
OUTPUT_DIR = r"C:\WEB CASE STUDY\mastered_output\remix_test"
os.makedirs(OUTPUT_DIR, exist_ok=True)

VIDEO_W, VIDEO_H = 1080, 1920
VIDEO_FPS = 30
font_path = "C:/Windows/Fonts/arial.ttf"

# Initialize Ray (try connecting to active cluster first, fallback to local instance)
try:
    ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
    print("🚀 Connected to existing Ray cluster.")
except Exception:
    ray.init(ignore_reinit_error=True)
    print("🚀 Initialized new local Ray instance.")

# ─── RAY WORKER DEFINITION ───
@ray.remote
def render_frame_batch(
    batch_idx,
    frame_start,
    frame_end,
    bg_tensor_cpu,
    fg_tensor_cpu,
    mask_tensor_cpu,
    ref_rms_n_slice,
    ref_sub_n_slice,
    ref_mid_n_slice,
    ref_high_n_slice,
    ref_onset_n_slice,
    tgt_rms_n_slice,
    frame_rate,
    frames_to_map,
    ref_track_name,
    tgt_track_name
):
    # Set thread limit for PyTorch inside the worker to prevent thrashing
    torch.set_num_threads(1)
    
    # Check device (workers use CPU here unless CUDA is safe in multiprocessing)
    worker_device = torch.device("cpu")
    
    # Move tensors to worker device
    bg_tensor = bg_tensor_cpu.to(worker_device)
    fg_tensor = fg_tensor_cpu.to(worker_device)
    mask_tensor = mask_tensor_cpu.to(worker_device)

    # Fonts
    try:
        font_large = ImageFont.truetype(font_path, 48)
        font_small = ImageFont.truetype(font_path, 28)
        font_tiny = ImageFont.truetype(font_path, 20)
    except:
        font_large = ImageFont.load_default()
        font_small = font_large
        font_tiny = font_large

    hud_base = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    rendered_frames = []
    
    n_frames_to_render = frame_end - frame_start
    
    for local_idx in range(n_frames_to_render):
        frame_idx = frame_start + local_idx
        t = frame_idx / VIDEO_FPS
        
        # Extract slices indexes
        ref_energy = float(ref_rms_n_slice[local_idx])
        ref_sub_energy = float(ref_sub_n_slice[local_idx])
        ref_mid_energy = float(ref_mid_n_slice[local_idx])
        ref_high_energy = float(ref_high_n_slice[local_idx])
        ref_punch = float(ref_onset_n_slice[local_idx])
        tgt_energy = float(tgt_rms_n_slice[local_idx])

        # Base tensors
        bg = bg_tensor.clone()
        fg = fg_tensor.clone()

        # BG Zoom
        bg_zoom = 1.0 + ref_sub_energy * 0.20
        if bg_zoom > 1.01:
            ch = int(VIDEO_H / bg_zoom)
            cw = int(VIDEO_W / bg_zoom)
            ctop = (VIDEO_H - ch) // 2
            cleft = (VIDEO_W - cw) // 2
            bg = F.crop(bg, ctop, cleft, ch, cw)
            bg = torch.nn.functional.interpolate(
                bg.unsqueeze(0), size=(VIDEO_H, VIDEO_W), mode='bilinear', align_corners=False
            ).squeeze(0)

        # BG Adjustments
        bg = F.adjust_saturation(bg, 0.4 + ref_mid_energy * 1.5)
        bg = F.adjust_brightness(bg, 0.5 + ref_energy * 0.7)
        if ref_energy < 0.4:
            blur_rad = (0.4 - ref_energy) * 12.0
            k_size = int(blur_rad * 2) | 1
            if k_size > 1:
                bg = F.gaussian_blur(bg, [k_size, k_size], [blur_rad, blur_rad])

        # FG Zoom
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

        # Composite FG + BG
        blended = bg * (1.0 - mask_tensor) + fg * mask_tensor

        # Draw HUD
        hud = hud_base.copy()
        draw = ImageDraw.Draw(hud)

        # Vignette
        for gy in range(VIDEO_H - 400, VIDEO_H):
            alpha = int(220 * ((gy - (VIDEO_H - 400)) / 400))
            draw.rectangle([(0, gy), (VIDEO_W, gy + 1)], fill=(0, 0, 0, min(alpha, 220)))

        # Waveform Bars
        bar_y = VIDEO_H - 180
        bar_height = 80
        n_bars = 40
        for i in range(n_bars):
            # Left half is Ref, Right is Tgt
            if i < n_bars // 2:
                h_val = ref_rms_n_slice[local_idx]
                color = (int(100 + 155 * ref_high_energy), int(80 + 100 * ref_mid_energy), 255, 255)
            else:
                h_val = tgt_rms_n_slice[local_idx]
                color = (255, int(100 + 155 * ref_sub_energy), int(100 + 155 * ref_mid_energy), 255)

            bx = int(VIDEO_W * 0.1 + (VIDEO_W * 0.8) * i / n_bars)
            bw = max(4, int(VIDEO_W * 0.8 / n_bars) - 4)
            bh = int(bar_height * h_val)
            draw.rectangle([(bx, bar_y - bh), (bx + bw, bar_y)], fill=color)

        # Pulsing Ring
        ring_r = int(70 + ref_energy * 90)
        cx, cy = VIDEO_W // 2, VIDEO_H // 2
        ring_color = (int(200 + 55 * ref_punch), int(100 + 155 * ref_mid_energy), 255, 255)
        for ro in range(3):
            draw.ellipse([cx - ring_r - ro, cy - ring_r - ro, cx + ring_r + ro, cy + ring_r + ro], outline=ring_color, width=2)

        # Texts
        draw.text((VIDEO_W // 2, VIDEO_H - 130), "SOVEREIGN REMIX", fill=(255, 255, 255, 255), font=font_large, anchor="mm")
        draw.text((VIDEO_W // 2, VIDEO_H - 80), f"{tgt_track_name} x {ref_track_name}", fill=(200, 200, 200, 255), font=font_small, anchor="mm")
        draw.text((VIDEO_W // 2, VIDEO_H - 40), "▶ DUAL SIGNAL OMNI-REMIX (RAY)", fill=(180, 120, 255, 255), font=font_tiny, anchor="mm")

        draw.text((30, 30), f"{t:.1f}s", fill=(255, 255, 255, 180), font=font_small)
        draw.text((30, 65), f"REF RMS: {ref_energy:.2f} | TGT RMS: {tgt_energy:.2f}", fill=(180, 180, 180, 255), font=font_tiny)

        # Upload HUD & Blend
        hud_tensor = torch.from_numpy(np.array(hud)).permute(2, 0, 1).float() / 255.0
        hud_alpha = hud_tensor[3:4, :, :]
        hud_rgb = hud_tensor[0:3, :, :]
        
        final_tensor = blended * (1.0 - hud_alpha) + hud_rgb * hud_alpha
        frame_array = (final_tensor.permute(1, 2, 0).clamp(0.0, 1.0) * 255.0).byte().numpy()
        rendered_frames.append(frame_array)
        
    return batch_idx, rendered_frames

# ─── MAIN EXECUTION ───
if __name__ == "__main__":
    t0 = time.perf_counter()

    # Step 1: Audio load
    print("\n═══ STEP 1: Extracting reference envelopes & target content ═══")
    ref_y, ref_sr = librosa.load(REF_TRACK_PATH, sr=22050, mono=True)
    ref_duration = librosa.get_duration(y=ref_y, sr=ref_sr)
    tgt_y, tgt_sr = librosa.load(TGT_TRACK_PATH, sr=22050, mono=True)
    tgt_duration = librosa.get_duration(y=tgt_y, sr=tgt_sr)
    
    process_duration = min(ref_duration, tgt_duration, 30.0)
    ref_y = ref_y[:int(process_duration * ref_sr)]
    tgt_y = tgt_y[:int(process_duration * tgt_sr)]

    hop_length = 512
    frame_rate = ref_sr / hop_length
    ref_rms = librosa.feature.rms(y=ref_y, hop_length=hop_length)[0]
    ref_onset = librosa.onset.onset_strength(y=ref_y, sr=ref_sr, hop_length=hop_length)

    ref_S = np.abs(librosa.stft(ref_y, hop_length=hop_length))
    ref_freqs = librosa.fft_frequencies(sr=ref_sr)
    ref_sub = np.sum(ref_S[(ref_freqs >= 20) & (ref_freqs < 80), :], axis=0)
    ref_mid = np.sum(ref_S[(ref_freqs >= 250) & (ref_freqs < 2000), :], axis=0)
    ref_high = np.sum(ref_S[ref_freqs >= 2000, :], axis=0)

    def norm(x):
        mn, mx = x.min(), x.max()
        return (x - mn) / (mx - mn + 1e-9)

    ref_rms_n = norm(ref_rms)
    ref_onset_n = norm(ref_onset)
    ref_sub_n = norm(ref_sub)
    ref_mid_n = norm(ref_mid)
    ref_high_n = norm(ref_high)
    tgt_rms_n = norm(librosa.feature.rms(y=tgt_y, hop_length=hop_length)[0])

    # Step 2: Spectral Envelope Transfer
    print("\n═══ STEP 2: Performing Spectral Envelope Transfer (Remixing) ═══")
    tgt_stft = librosa.stft(tgt_y, hop_length=hop_length)
    tgt_mag = np.abs(tgt_stft)
    tgt_phase = np.angle(tgt_stft)

    n_envelope_frames = len(ref_rms_n)
    n_stft_cols = tgt_mag.shape[1]
    frames_to_map = min(n_envelope_frames, n_stft_cols)

    remixed_mag = tgt_mag.copy()
    for col in range(frames_to_map):
        remixed_mag[(ref_freqs >= 20) & (ref_freqs < 250), col] *= (0.2 + 1.2 * ref_sub_n[col])
        remixed_mag[(ref_freqs >= 250) & (ref_freqs < 2000), col] *= (0.3 + 1.0 * ref_mid_n[col])
        remixed_mag[ref_freqs >= 2000, col] *= (0.2 + 1.1 * ref_high_n[col])

    remixed_stft = remixed_mag * np.exp(1j * tgt_phase)
    remixed_y = librosa.istft(remixed_stft, hop_length=hop_length)
    remixed_audio_path = os.path.join(OUTPUT_DIR, "remixed_content.wav")
    sf.write(remixed_audio_path, remixed_y, ref_sr)

    # Step 3: Segment Subject
    print("\n═══ STEP 3: Isolating subject from artwork ═══")
    art_img = Image.open(ARTWORK_PATH).convert("RGB")
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

    use_fallback_mask = True
    fg_mask = None
    try:
        from torchvision.models.segmentation import deeplabv3_resnet50, DeepLabV3_ResNet50_Weights
        weights = DeepLabV3_ResNet50_Weights.DEFAULT
        model = deeplabv3_resnet50(weights=weights).eval()
        preprocess = weights.transforms()
        input_tensor = preprocess(cropped_art).unsqueeze(0)
        with torch.no_grad():
            output = model(input_tensor)['out'][0]
        output_predictions = output.argmax(0)
        person_mask = (output_predictions == 15).numpy().astype(np.uint8) * 255
        if person_mask.sum() > (person_mask.size * 0.02 * 255):
            fg_mask = Image.fromarray(person_mask).resize((VIDEO_W, VIDEO_H), Image.Resampling.BILINEAR)
            fg_mask = fg_mask.filter(ImageFilter.GaussianBlur(5))
            use_fallback_mask = False
            print("   ✅ Semantic subject isolated successfully.")
    except Exception as e:
        print(f"   ⚠️ Segmentation model bypassed/failed: {e}")

    if use_fallback_mask:
        mask_canvas = Image.new("L", (VIDEO_W, VIDEO_H), 0)
        draw_mask = ImageDraw.Draw(mask_canvas)
        cx, cy = VIDEO_W // 2, VIDEO_H // 2
        rx, ry = int(VIDEO_W * 0.35), int(VIDEO_H * 0.3)
        draw_mask.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
        fg_mask = mask_canvas.filter(ImageFilter.GaussianBlur(80))
        print("   ✅ Radial depth focal mask generated.")

    base_np = np.array(cropped_art)
    mask_np = np.array(fg_mask)[:, :, np.newaxis] / 255.0
    bg_np = (base_np * (1.0 - mask_np)).astype(np.uint8)
    fg_np = (base_np * mask_np).astype(np.uint8)

    bg_tensor_cpu = torch.from_numpy(bg_np).permute(2, 0, 1).float() / 255.0
    fg_tensor_cpu = torch.from_numpy(fg_np).permute(2, 0, 1).float() / 255.0
    mask_tensor_cpu = torch.from_numpy(mask_np).permute(2, 0, 1).float()

    # Step 4: Parallel Batch Allocation
    print("\n═══ STEP 4: Spawning Parallel Ray Workers ═══")
    total_video_frames = int(process_duration * VIDEO_FPS)
    
    # 4 CPU workers for local machine parallelization
    num_workers = 4
    batch_size = int(np.ceil(total_video_frames / num_workers))
    
    ref_track_name = os.path.basename(REF_TRACK_PATH)[:-4].upper()
    tgt_track_name = os.path.basename(TGT_TRACK_PATH)[:-4].upper()
    
    futures = []
    for b_idx in range(num_workers):
        f_start = b_idx * batch_size
        f_end = min(f_start + batch_size, total_video_frames)
        if f_start >= total_video_frames:
            break
            
        # Slice envelope arrays for the worker
        ref_rms_slice = ref_rms_n[f_start:f_end]
        ref_sub_slice = ref_sub_n[f_start:f_end]
        ref_mid_slice = ref_mid_n[f_start:f_end]
        ref_high_slice = ref_high_n[f_start:f_end]
        ref_onset_slice = ref_onset_n[f_start:f_end]
        tgt_rms_slice = tgt_rms_n[f_start:f_end]
        
        # Put large data objects in object store to optimize memory
        future = render_frame_batch.remote(
            b_idx,
            f_start,
            f_end,
            bg_tensor_cpu,
            fg_tensor_cpu,
            mask_tensor_cpu,
            ref_rms_slice,
            ref_sub_slice,
            ref_mid_slice,
            ref_high_slice,
            ref_onset_slice,
            tgt_rms_slice,
            frame_rate,
            frames_to_map,
            ref_track_name,
            tgt_track_name
        )
        futures.append(future)

    print(f"   Submitted {len(futures)} tasks to Ray.")
    
    # Resolve futures as they finish, and store in ordered dict
    results = {}
    remaining = list(futures)
    t_render_start = time.perf_counter()
    
    while remaining:
        ready, remaining = ray.wait(remaining, num_returns=1)
        for r in ready:
            b_idx, frames = ray.get(r)
            results[b_idx] = frames
            print(f"   ✅ Ray Worker {b_idx} finished.")

    t_render_total = time.perf_counter() - t_render_start
    print(f"   ⏱️ Ray parallel render completed in {t_render_total:.2f} sec.")

    # Muxing with PyAV
    print("\n═══ STEP 5: Muxing Audio and Video Stream ═══")
    output_video_path = os.path.join(OUTPUT_DIR, "sovereign_remix_reel.mp4")
    container = av.open(output_video_path, mode='w')
    stream = container.add_stream('libx264', rate=VIDEO_FPS)
    stream.width = VIDEO_W
    stream.height = VIDEO_H
    stream.pix_fmt = 'yuv420p'
    stream.options = {'crf': '18', 'preset': 'fast'}

    audio_stream = container.add_stream('aac', rate=ref_sr)
    audio_stream.layout = 'mono'

    # Write frames in order
    frame_pts = 0
    for b_idx in sorted(results.keys()):
        for frame_array in results[b_idx]:
            video_frame = av.VideoFrame.from_ndarray(frame_array, format='rgb24')
            video_frame.pts = frame_pts
            frame_pts += 1
            for packet in stream.encode(video_frame):
                container.mux(packet)

    for packet in stream.encode():
        container.mux(packet)

    # Write Audio
    print("   🔊 Muxing remixed audio track...")
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
    
    t_total = time.perf_counter() - t0
    file_size = os.path.getsize(output_video_path)
    
    print(f"\n═══ ✅ PARALLEL REMIX REEL COMPLETE ═══")
    print(f"   📁 Output: {output_video_path}")
    print(f"   ⏱️  Video render (Ray): {t_render_total:.2f} sec")
    print(f"   ⏱️  Total Pipeline Time: {t_total:.2f} sec")
    print(f"   💾 File size: {file_size / (1024*1024):.1f} MB")
    print(f"   🧠 Model/Fallback:      {'Semantic DeepLabV3' if not use_fallback_mask else 'Radial Vignette Depth'}")
    
    # Shutdown Ray
    ray.shutdown()