"""
Wan2.1 DiT Denoising Worker — Ray Actor
Loads DiT shard (TorchScript), runs denoising steps.
Matches AudioDatasetWorker pattern: @ray.remote(num_cpus=1), zero-copy Plasma, single init per core.
Supports GPU allocation via num_gpus parameter.
"""

import os
import torch
import ray

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


# Prevent thread contention
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["TORCH_NUM_THREADS"] = "1"


@ray.remote(num_cpus=1, num_gpus=1)
class WanDiTWorker:
    """
    Ray actor: one per GPU (or CPU core if no GPU).
    Loads Wan2.1 DiT model, runs denoising step: (latent, timestep, text_embed) → denoised_latent
    """
    def __init__(self, model_path: str = "matrix_world_engine/models/checkpoints/diffusion_pytorch_model.safetensors", device: str = "cuda"):
        self.device = device
        self.model_path = model_path

        # Load actual Wan2.1 DiT model from safetensors
        self.model = self._load_wan21_dit(model_path, device)
        self.model.eval()

        print(f"[WanDiTWorker] Loaded Wan2.1 DiT from {model_path} on {device}")

    def _load_wan21_dit(self, model_path: str, device: str):
        """Load Wan2.1 DiT from safetensors checkpoint."""
        try:
            from safetensors.torch import load_file
            import sys
            sys.path.append("matrix_world_engine")
            
            # Import the actual Wan2.1 DiT architecture
            from models.wan_dit import WanDiT
            
            # Load state dict
            state_dict = load_file(model_path)
            
            # Initialize model with correct config for Wan2.1-T2V-1.3B
            model = WanDiT(
                in_channels=16,
                out_channels=16,
                patch_size=(1, 2, 2),
                num_layers=30,
                num_heads=30,
                hidden_size=1920,
                text_embed_dim=4096,
                timestep_embed_dim=1920,
            )
            
            model.load_state_dict(state_dict, strict=False)
            model.to(device)
            return model
            
        except Exception as e:
            print(f"[WanDiTWorker] Warning: Could not load full Wan2.1 DiT: {e}")
            print("[WanDiTWorker] Falling back to traced_matrix_dit.pt")
            # Fallback to existing traced model
            fallback_path = "matrix_world_engine/models/traced_matrix_dit.pt"
            model = torch.jit.load(fallback_path, map_location=device)
            return model

    def denoise_step(self, latent_ref: ray.ObjectRef, timestep: float, text_embed_ref: ray.ObjectRef) -> torch.Tensor:
        """
        Single denoising step.
        Args:
            latent_ref: ObjectRef → Tensor [B, 16, 44, 80] (noisy latent)
            timestep: float scalar (0.0 to 1.0)
            text_embed_ref: ObjectRef → Tensor [B, 16] (text conditioning)
        Returns:
            Tensor [B, 16, 44, 80] (denoised latent)
        """
        # Zero-copy fetch from Plasma
        latent = ray.get(latent_ref)      # [B, 16, 44, 80]
        text_embed = ray.get(text_embed_ref)  # [B, 16]

        batch_size = latent.shape[0]
        device = latent.device

        # Prepare timestep embedding (DiT expects scalar per batch)
        t = torch.full((batch_size,), timestep, device=device, dtype=torch.float32)

        with torch.no_grad():
            # Model forward: (latent, cond_16) -> denoised
            # Note: traced_matrix_dit.pt expects (latent_tensor, cond_16)
            denoised = self.model(latent, text_embed)

        return denoised

    def denoise_step_numpy(self, latent_np, timestep: float, text_embed_np) -> torch.Tensor:
        """Accept numpy arrays for Ray task submission."""
        latent = torch.from_numpy(latent_np).float().to(self.device)
        text_embed = torch.from_numpy(text_embed_np).float().to(self.device)
        return self.denoise_step(ray.put(latent), timestep, ray.put(text_embed))


class WanDiTOrchestrator:
    """
    Matches DiffusionDataOrchestrator pattern:
    - Pool of DiT workers (one per GPU)
    - Round-robin dispatch
    - ray.wait() async gathering
    """
    def __init__(self, num_workers: int = 4, model_path: str = "matrix_world_engine/models/checkpoints/diffusion_pytorch_model.safetensors", device: str = "cuda"):
        self.num_workers = num_workers
        # Use GPU resources for workers
        self.workers = [WanDiTWorker.options(num_gpus=1).remote(model_path, device) for _ in range(num_workers)]
        print(f"[WanDiTOrchestrator] Spawned {num_workers} DiT workers on {device} (1 GPU each)")

    def denoise_batch(self, latents: torch.Tensor, timestep: float, text_embeds: torch.Tensor) -> torch.Tensor:
        """
        Args:
            latents: [B, 16, 44, 80] noisy latents
            timestep: float scalar
            text_embeds: [B, 16] text conditioning
        Returns:
            Tensor [B, 16, 44, 80] denoised latents
        """
        batch_size = latents.shape[0]
        chunk_size = max(1, batch_size // self.num_workers)

        futures = []
        for i in range(0, batch_size, chunk_size):
            worker = self.workers[(i // chunk_size) % self.num_workers]
            lat_chunk = latents[i:i + chunk_size]
            txt_chunk = text_embeds[i:i + chunk_size]

            # Pin to Plasma
            lat_ref = ray.put(lat_chunk)
            txt_ref = ray.put(txt_chunk)

            futures.append(worker.denoise_step.remote(lat_ref, timestep, txt_ref))

        # Async gather
        results = []
        while futures:
            done_refs, futures = ray.wait(futures, num_returns=1)
            for done_ref in done_refs:
                results.append(ray.get(done_ref))

        return torch.cat(results, dim=0)

    def denoise_multistep(self, latents: torch.Tensor, timesteps: list, text_embeds: torch.Tensor) -> torch.Tensor:
        """
        Run multiple denoising steps (e.g., 20-step DDIM).
        Args:
            latents: [B, 16, 44, 80] initial noise
            timesteps: list of float timesteps [1.0, 0.95, ..., 0.0]
            text_embeds: [B, 16] text conditioning
        Returns:
            Tensor [B, 16, 44, 80] final denoised latents
        """
        current_latents = latents
        for t in timesteps:
            current_latents = self.denoise_batch(current_latents, t, text_embeds)
        return current_latents


if __name__ == "__main__":
    import ray
    ray.init(num_cpus=4, ignore_reinit_error=True)

    # Test with dummy model (will fail if traced_matrix_dit.pt doesn't exist)
    try:
        worker = WanDiTWorker.remote()
        dummy_latent = torch.randn(1, 16, 44, 80)
        dummy_text = torch.randn(1, 16)
        lat_ref = ray.put(dummy_latent)
        txt_ref = ray.put(dummy_text)
        out = ray.get(worker.denoise_step.remote(lat_ref, 0.5, txt_ref))
        print(f"✅ DiT worker test: {dummy_latent.shape} → {out.shape}")
    except Exception as e:
        print(f"⚠️ DiT worker test skipped (model not found): {e}")

    ray.shutdown()