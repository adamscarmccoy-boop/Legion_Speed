## Next Steps: Building Deterministic Differentiable Video in PyTorch

Here's a concrete implementation roadmap, moving from basic to advanced.

---

### Step 1: Install the Core Libraries

```bash
# Differentiable computer vision (the DDSP analog for images/video)
pip install kornia

# Differentiable 3D rendering
pip install pytorch3d

# For the PDR approach (2D Gaussian splatting for video)
# Clone and install from: https://github.com/... (paper pending release)
```

---

### Step 2: Build a Deterministic Differentiable Video Processing Block

The audio analogy was: encoder → DSP program → audio out. For video, it's: encoder → **differentiable vision program** → video out.

Here's a minimal **Kornia-based differentiable video filter pipeline**:

```python
import torch
import kornia as K
import kornia.filters as KF
import kornia.geometry.transform as KGT

class DeterministicVideoProcessor(torch.nn.Module):
    """
    A differentiable, deterministic video processing block.
    No generative components — pure signal flow.
    """
    def __init__(self):
        super().__init__()
        # These parameters are *learnable* via gradient descent,
        # but the operation itself is deterministic
        self.blur_sigma = torch.nn.Parameter(torch.tensor(1.0))
        self.brightness = torch.nn.Parameter(torch.tensor(0.0))
        self.rotation = torch.nn.Parameter(torch.tensor(0.0))

    def forward(self, video):
        # video shape: (B, T, C, H, W)
        B, T, C, H, W = video.shape
        frames = video.view(B * T, C, H, W)

        # Apply differentiable Gaussian blur (deterministic)
        blurred = KF.gaussian_blur2d(frames, (5, 5),
                                     (self.blur_sigma, self.blur_sigma))

        # Adjust brightness (deterministic)
        adjusted = K.enhance.adjust_brightness(blurred, self.brightness)

        # Rotate frames (differentiable affine transform)
        rotated = KGT.rotate(adjusted, self.rotation)

        return rotated.view(B, T, C, H, W)

# Usage: gradient flows through the entire deterministic pipeline
video = torch.randn(2, 10, 3, 64, 64, requires_grad=True)
processor = DeterministicVideoProcessor()
output = processor(video)
loss = output.mean()
loss.backward()  # works!
```

---

### Step 3: The DDSP-Style Autoencoder for Video

This is the direct video analog of the [DDSP autoencoder](https://www.alphaxiv.org/abs/2001.04643) — a **deterministic autoencoder** where the decoder is a differentiable rendering program rather than a neural network generating pixels.

```python
import torch
import torch.nn as nn
import kornia as K
import kornia.geometry.transform as KGT

class DifferentiableRenderer(nn.Module):
    """
    Deterministic rendering program: takes latent parameters
    and renders video frames via differentiable operations.
    """
    def __init__(self, latent_dim=64):
        super().__init__()
        # A light MLP that predicts *rendering parameters*,
        # not pixels
        self.param_predictor = nn.Sequential(
            nn.Linear(latent_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 7)  # [dx, dy, scale, rot, brightness, contrast, blur]
        )

    def forward(self, z, base_frame):
        """
        z: latent vector (B, latent_dim)
        base_frame: a canonical grid or base signal to transform (B, C, H, W)
        """
        params = self.param_predictor(z)
        dx, dy, scale, rot, brightness, contrast, blur = params.unbind(-1)

        # Build affine transform
        theta = torch.zeros(z.size(0), 2, 3, device=z.device)
        theta[:, 0, 0] = scale * torch.cos(rot)
        theta[:, 0, 1] = -scale * torch.sin(rot)
        theta[:, 0, 2] = dx
        theta[:, 1, 0] = scale * torch.sin(rot)
        theta[:, 1, 1] = scale * torch.cos(rot)
        theta[:, 1, 2] = dy

        # Apply differentiable geometric transform
        warped = KGT.affine(base_frame, theta)

        # Differentiable photometric adjustments
        result = K.enhance.adjust_brightness(warped, brightness.unsqueeze(-1).unsqueeze(-1))
        result = K.enhance.adjust_contrast(result, contrast.unsqueeze(-1).unsqueeze(-1))

        # Blur via differentiable convolution
        kernel_size = int(2 * round(blur.item()) + 1) if blur.item() > 0 else 3
        result = K.filters.gaussian_blur2d(result, (kernel_size, kernel_size),
                                           (blur.abs() + 0.5, blur.abs() + 0.5))
        return result
```

The key insight, exactly as in DDSP:

> *"DDSP components are able to dramatically improve autoencoder performance in the audio domain. Just as autoencoders utilizing convolutional layers outperform fully-connected autoencoders on images, we find DDSP components are able to dramatically improve autoencoder performance in the audio domain."*

The same logic applies to video: **replace pixel-generating decoders with differentiable rendering programs**.

---

### Step 4: Build the PDR-Style Video Prediction Pipeline

This implements the core idea from [Predictive Differentiable Rendering](https://www.alphaxiv.org/abs/2606.31050): bridge discrete pixel space and continuous **2D Gaussian** space.

```python
class PredGSAdapter(nn.Module):
    """
    Lightweight adapter that converts pixel-space features
    into 2D Gaussian parameters, then renders them back.
    """
    def __init__(self, num_gaussians=300, channels=3):
        super().__init__()
        self.num_gaussians = num_gaussians
        # Downsample features, then predict Gaussian params
        self.downsample = nn.AdaptiveAvgPool2d((8, 8))

        # One MLP per Gaussian parameter type
        in_dim = 64 * 8 * 8  # depends on your feature extractor
        self.mlp_coords = nn.Linear(in_dim, num_gaussians * 2)
        self.mlp_scale = nn.Linear(in_dim, num_gaussians * 2)
        self.mlp_rot = nn.Linear(in_dim, num_gaussians)
        self.mlp_amplitude = nn.Linear(in_dim, num_gaussians * channels)

    def render_gaussians(self, coords, scales, rotations, amplitudes, H, W):
        """
        Deterministic 2D Gaussian splatting renderer
        """
        B, N, C = amplitudes.shape
        device = coords.device

        # Build pixel grid
        y, x = torch.meshgrid(
            torch.linspace(-1, 1, H, device=device),
            torch.linspace(-1, 1, W, device=device),
            indexing='ij'
        )
        grid = torch.stack([x, y], dim=-1)  # (H, W, 2)

        # Compute each Gaussian's contribution
        rendered = torch.zeros(B, C, H, W, device=device)
        for i in range(N):
            # Gaussian formula: exp(-0.5 * (x-μ)ᵀ Σ⁻¹ (x-μ))
            diff = grid - coords[:, i, :].view(B, 1, 1, 2)
            diff = diff.unsqueeze(-1)  # (B, H, W, 2, 1)

            # Build covariance from scale + rotation
            cos_r = torch.cos(rotations[:, i])
            sin_r = torch.sin(rotations[:, i])
            R = torch.stack([cos_r, -sin_r, sin_r, cos_r], dim=-1).view(B, 2, 2)
            S_inv = torch.diag_embed(1.0 / (scales[:, i] + 1e-8))
            cov_inv = R @ S_inv @ S_inv @ R.transpose(-1, -2)

            # Mahalanobis distance squared
            maha = (diff.transpose(-1, -2) @ cov_inv.unsqueeze(1).unsqueeze(1) @ diff).squeeze(-1).squeeze(-1)
            gaussian_val = torch.exp(-0.5 * maha)

            # Weight by amplitude and accumulate
            amplitude_map = amplitudes[:, i, :].view(B, C, 1, 1)
            rendered += amplitude_map * gaussian_val.unsqueeze(1)

        return rendered

    def forward(self, features, H, W):
        """
        features: (B, C_feat, h, w) from a pixel-space predictor
        Returns: (B, C, H, W) rendered frame
        """
        B = features.size(0)
        flat = self.downsample(features).view(B, -1)

        # Predict Gaussian parameters (all deterministic)
        coords = torch.tanh(self.mlp_coords(flat)).view(B, self.num_gaussians, 2)
        scales = torch.sigmoid(self.mlp_scale(flat)).view(B, self.num_gaussians, 2)
        rotations = (torch.tanh(self.mlp_rot(flat)) * (3.14159 / 2)).view(B, self.num_gaussians)
        amplitudes = torch.sigmoid(self.mlp_amplitude(flat)).view(B, self.num_gaussians, -1)

        # Deterministic rendering
        return self.render_gaussians(coords, scales, rotations, amplitudes, H, W)
```

---

### Step 5: Combine Into a Full Deterministic Pipeline

```python
class DeterministicVideoPipeline(nn.Module):
    """
    End-to-end deterministic video processing.
    Combines pixel-space predictor + differentiable Gaussian rendering.
    No diffusion, no GAN, no autoregressive — pure signal flow.
    """
    def __init__(self, backbone='tau', num_gaussians=300):
        super().__init__()
        # Your pixel-space predictor (can be any architecture)
        # See TAU / SimVP / ConvLSTM as options
        from some_video_prediction_lib import TAU
        self.pixel_predictor = TAU(...)

        # PredGS adapter
        self.pred_gs = PredGSAdapter(num_gaussians=num_gaussians)

        # Fusion layer
        self.fusion = nn.Sequential(
            nn.Conv2d(6, 3, kernel_size=1),  # concat pixel + GS rendered
            nn.ReLU()
        )

    def forward(self, input_frames):
        """
        input_frames: (B, T_in, C, H, W)
        Returns: (B, T_out, C, H, W) predicted frames
        """
        # Coarse pixel-space prediction
        pixel_pred = self.pixel_predictor(input_frames)

        # Refine via continuous Gaussian rendering
        B, T, C, H, W = pixel_pred.shape
        refinements = []
        for t in range(T):
            features = pixel_pred[:, t]  # (B, C, H, W)
            rendered = self.pred_gs(features, H, W)
            fused = self.fusion(torch.cat([pixel_pred[:, t], rendered], dim=1))
            refinements.append(fused)

        return torch.stack(refinements, dim=1)
```

**Loss function** (critical — MSE alone destroys detail):

```python
def perceptual_video_loss(pred, target, lambda_l1=0.5, lambda_ssim=0.5):
    """Hybrid L1 + SSIM loss (as used in PDR)"""
    from kornia.losses import SSIMLoss
    ssim_loss = SSIMLoss(window_size=11)

    l1 = torch.nn.functional.l1_loss(pred, target)
    ssim = ssim_loss(pred, target)

    return lambda_l1 * l1 + lambda_ssim * ssim
```

---

### Implementation Roadmap

| Level | What to Build | Key References |
|---|---|---|
| **1. Basic** | Differentiable filter pipeline (blur → warp → color adjust) via Kornia | [Kornia paper](https://www.alphaxiv.org/abs/1910.02190) |
| **2. Intermediate** | DDSP-style autoencoder: encoder → differentiable renderer params → video out | [DDSP](https://www.alphaxiv.org/abs/2001.04643), but swap oscillators for Kornia transforms |
| **3. Advanced** | 2D Gaussian splatting renderer (write your own CUDA kernel for speed) | [PDR](https://www.alphaxiv.org/abs/2606.31050), [GaussianImage](https://arxiv.org/abs/2312.02120) |
| **4. Production** | Graph-based video processing pipeline (like GRAFX for video) | [GRAFX](https://www.alphaxiv.org/abs/2408.03204) — the node scheduling approach generalizes beyond audio |

The critical ***design principle*** to internalize (from the DDSP paper):

> *"We focus here on a **deterministic autoencoder** to investigate the strength of differentiable signal processing components independent of any particular approach to adversarial training, variational inference, or Jacobian design."*

Your neural network should predict **program parameters**, not pixels. The "program" — be it a filter chain, an affine warp, a 2D Gaussian renderer, or a full graphics pipeline — is deterministic and differentiable. That's the entire paradigm.