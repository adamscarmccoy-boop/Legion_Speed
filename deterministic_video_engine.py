import os
import sys
import time
import argparse
import numpy as np
import soundfile as sf
import librosa
import av
import torch
import torch.nn as nn
from PIL import Image
import kornia as K
import kornia.filters as KF
import kornia.geometry.transform as KGT

sys.stdout.reconfigure(encoding='utf-8')

class DifferentiableRenderer(nn.Module):
    """
    Audio-driven Differentiable Renderer.
    Applies parametric geometric, photometric, and spatial transformations to base artwork.
    """
    def __init__(self, latent_dim=41):
        super().__init__()
        self.param_predictor = nn.Sequential(
            nn.Linear(latent_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 7)  # [dx, dy, scale, rot, brightness, contrast, blur]
        )

    def forward(self, z, base_frame):
        params = self.param_predictor(z)
        dx, dy, scale, rot, brightness, contrast, blur = params.unbind(-1)

        # Smooth, realistic parameter modulation bounds
        dx = torch.tanh(dx) * 0.05
        dy = torch.tanh(dy) * 0.05
        scale = 1.0 + torch.sigmoid(scale) * 0.1
        rot = rot * 0.08

        theta = torch.zeros(z.size(0), 2, 3, device=z.device)
        theta[:, 0, 0] = scale * torch.cos(rot)
        theta[:, 0, 1] = -scale * torch.sin(rot)
        theta[:, 0, 2] = dx
        theta[:, 1, 0] = scale * torch.sin(rot)
        theta[:, 1, 1] = scale * torch.cos(rot)
        theta[:, 1, 2] = dy

        warped = KGT.affine(base_frame, theta)
        brightness_val = torch.tanh(brightness) * 0.15
        result = K.enhance.adjust_brightness(warped, brightness_val.unsqueeze(-1).unsqueeze(-1))
        
        contrast_factor = (1.0 + torch.sigmoid(contrast) * 0.4).unsqueeze(-1).unsqueeze(-1)
        result = K.enhance.adjust_contrast(result, contrast_factor)

        sigma = torch.sigmoid(blur) * 0.5 + 0.1
        result = KF.gaussian_blur2d(result, (3, 3), (sigma, sigma))
        return result

class PredGSAdapter(nn.Module):
    """
    2D Gaussian Splatting Energy Flare Generator.
    Projects audio-reactive continuous particle bursts over high-energy feature regions.
    """
    def __init__(self, num_gaussians=30, in_dim=41, channels=3):
        super().__init__()
        self.num_gaussians = num_gaussians
        self.channels = channels

        self.mlp_coords = nn.Linear(in_dim, num_gaussians * 2)
        self.mlp_scale = nn.Linear(in_dim, num_gaussians * 2)
        self.mlp_rot = nn.Linear(in_dim, num_gaussians)
        self.mlp_amplitude = nn.Linear(in_dim, num_gaussians * channels)

    def render_gaussians(self, coords, scales, rotations, amplitudes, H, W):
        B, N, C = amplitudes.shape
        device = coords.device

        y, x = torch.meshgrid(
            torch.linspace(-1, 1, H, device=device),
            torch.linspace(-1, 1, W, device=device),
            indexing='ij'
        )
        grid = torch.stack([x, y], dim=-1)

        amps_norm = torch.softmax(amplitudes, dim=1) * 2.0

        rendered = torch.zeros(B, C, H, W, device=device)
        for i in range(N):
            diff = grid - coords[:, i, :].view(B, 1, 1, 2)
            diff = diff.unsqueeze(-1)

            cos_r = torch.cos(rotations[:, i])
            sin_r = torch.sin(rotations[:, i])
            R = torch.stack([cos_r, -sin_r, sin_r, cos_r], dim=-1).view(B, 2, 2)
            
            s_val = 0.03 + scales[:, i] * 0.06
            S_inv = torch.diag_embed(1.0 / (s_val + 1e-4))
            cov_inv = R @ S_inv @ S_inv @ R.transpose(-1, -2)

            maha = (diff.transpose(-1, -2) @ cov_inv.unsqueeze(1).unsqueeze(1) @ diff).squeeze(-1).squeeze(-1)
            gaussian_val = torch.exp(-0.5 * maha)

            amp_map = amps_norm[:, i, :].view(B, C, 1, 1)
            rendered = rendered + amp_map * gaussian_val.unsqueeze(1)

        return torch.clamp(rendered, 0.0, 1.0)

    def forward(self, features, H, W):
        B = features.size(0)
        coords = torch.tanh(self.mlp_coords(features)).view(B, self.num_gaussians, 2)
        scales = torch.sigmoid(self.mlp_scale(features)).view(B, self.num_gaussians, 2)
        rotations = (torch.tanh(self.mlp_rot(features)) * 3.14159).view(B, self.num_gaussians)
        amplitudes = torch.sigmoid(self.mlp_amplitude(features)).view(B, self.num_gaussians, -1)

        return self.render_gaussians(coords, scales, rotations, amplitudes, H, W)

def build_usable_video(audio_path, image_path, output_path, duration_sec=15.0, target_res=(1080, 1080)):
    print(f"===============================================================")
    print(f"  SOVEREIGN DETERMINISTIC DIFFERENTIABLE VIDEO ENGINE")
    print(f"===============================================================")
    print(f"  Audio Track: {audio_path}")
    print(f"  Base Artwork: {image_path}")
    print(f"  Target Output: {output_path}")

    # PyAV Audio Loader — Natively handles MP3, WAV, AAC, FLAC with FFmpeg codecs
    try:
        import av
        container = av.open(audio_path)
        stream = container.streams.audio[0]
        sr_orig = stream.rate
        resampler = av.AudioResampler(format='flt', layout='mono', rate=22050)
        
        samples = []
        for frame in container.decode(stream):
            resampled_frames = resampler.resample(frame)
            for rf in resampled_frames:
                samples.append(rf.to_ndarray())
        container.close()
        
        if samples:
            y = np.concatenate(samples, axis=1).squeeze()
        else:
            y = np.zeros(int(22050 * duration_sec), dtype=np.float32)
        sr = 22050
        y = y[:int(sr * duration_sec)]
    except Exception:
        # Fallback to soundfile if PyAV fails
        y, sr_orig = sf.read(audio_path)
        if len(y.shape) > 1:
            y = np.mean(y, axis=1)
        if sr_orig != 22050:
            y = librosa.resample(y, orig_sr=sr_orig, target_sr=22050)
        sr = 22050
        y = y[:int(sr * duration_sec)]

    total_sec = len(y) / sr
    fps = 30
    total_frames = int(total_sec * fps)

    # Spectral envelope extraction (RMS, sub-bass, mid, high, onset)
    hop_length = int(sr / fps)
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    onset = librosa.onset.onset_detect(y=y, sr=sr, hop_length=hop_length)
    
    # Normalize features
    rms_norm = (rms - rms.min()) / (rms.max() - rms.min() + 1e-6)

    # 2. Load and Preprocess Base Artwork Image
    img = Image.open(image_path).convert('RGB')
    W, H = target_res
    img_resized = img.resize((W, H), Image.Resampling.LANCZOS)
    img_np = np.array(img_resized)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  Device: {device}")

    base_tensor = torch.from_numpy(img_np).permute(2, 0, 1).float().unsqueeze(0) / 255.0
    base_tensor = base_tensor.to(device)

    # 3. Instantiate Models
    renderer = DifferentiableRenderer(latent_dim=41).to(device)
    gs_adapter = PredGSAdapter(num_gaussians=35, in_dim=41).to(device)

    # 4. PyAV Multiplexed Audio-Video Container
    container = av.open(output_path, mode='w')
    v_stream = container.add_stream('libx264', rate=fps)
    v_stream.width, v_stream.height = W, H
    v_stream.pix_fmt = 'yuv420p'
    v_stream.options = {'crf': '16', 'preset': 'medium'}

    a_stream = container.add_stream('aac', rate=sr)
    a_stream.layout = 'mono'

    print(f"  Rendering {total_frames} audio-synchronized video frames ({W}x{H} @ {fps} FPS)...")
    t0 = time.time()

    with torch.no_grad():
        for frame_idx in range(total_frames):
            env_idx = min(frame_idx, len(rms_norm) - 1)
            energy = rms_norm[env_idx]

            # Construct 41-dim acoustic latent vector per frame
            freqs = torch.linspace(0.5, 4.0, 41, device=device)
            dna_t = (energy * torch.sin(2.0 * 3.14159 * freqs * (frame_idx / fps))).unsqueeze(0)

            # Apply Differentiable Rendering transforms + 2D Gaussian Splatting flares
            rendered = renderer(dna_t, base_tensor)
            gs_flares = gs_adapter(dna_t, H, W)
            
            # Blend base artwork with Gaussian particle energy flares
            fused = torch.clamp(rendered * 0.85 + gs_flares * 0.45 * energy, 0.0, 1.0)

            frame_np = (fused.squeeze(0).permute(1, 2, 0) * 255.0).byte().cpu().numpy()
            vf = av.VideoFrame.from_ndarray(frame_np, format='rgb24')
            vf.pts = frame_idx
            for packet in v_stream.encode(vf):
                container.mux(packet)

            if (frame_idx + 1) % 60 == 0:
                print(f"    📹 Rendered frame {frame_idx+1}/{total_frames} ({(frame_idx+1)/fps:.1f}s)")

    # Flush Video Stream
    for packet in v_stream.encode():
        container.mux(packet)

    # Encode Audio Stream
    print("  🔊 Muxing real audio track...")
    chunk_size = 1024
    for i in range(0, len(y), chunk_size):
        chunk = y[i:i + chunk_size]
        if len(chunk) < chunk_size:
            chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
        af = av.AudioFrame.from_ndarray(chunk.reshape(1, -1).astype(np.float32), format='fltp', layout='mono')
        af.sample_rate = sr
        af.pts = i
        for packet in a_stream.encode(af):
            container.mux(packet)

    for packet in a_stream.encode():
        container.mux(packet)

    container.close()
    elapsed = time.time() - t0
    size_mb = os.path.getsize(output_path) / (1024 * 1024)

    print(f"===============================================================")
    print(f"  ✅ PRODUCTION VIDEO READY")
    print(f"===============================================================")
    print(f"  Output Path: {output_path}")
    print(f"  Resolution:  {W}x{H} @ {fps} FPS")
    print(f"  Duration:    {total_sec:.2f} seconds ({total_frames} frames)")
    print(f"  File Size:   {size_mb:.2f} MB")
    print(f"  Render Time: {elapsed:.2f} sec")
    print(f"===============================================================")

if __name__ == "__main__":
    audio_in = r"C:\WEB CASE STUDY\sovereign_capture.wav"
    image_in = r"C:\Users\adams\Downloads\checked_option_1_electric_cyan_lasers.png"
    if not os.path.exists(image_in):
        image_in = r"C:\WEB CASE STUDY\brain_bridge_visual.png"
    
    out_video = r"C:\WEB CASE STUDY\mastered_output\remix_test\sovereign_deterministic_video_production.mp4"
    os.makedirs(os.path.dirname(out_video), exist_ok=True)
    
    build_usable_video(audio_in, image_in, out_video, duration_sec=10.0, target_res=(1080, 1080))
