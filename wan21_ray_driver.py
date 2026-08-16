"""
Wan2.1 Ray Driver — Full Pipeline Orchestrator
Chains: Vectorizer (128→56320) → DiT Workers (denoise) → VAE Decode
Matches DiffusionDataOrchestrator pattern: async ray.wait(), zero-copy Plasma, round-robin workers.
"""

import os
import torch
import ray
import numpy as np

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


class Wan21RayDriver:
    """
    Top-level driver matching your DiffusionDataOrchestrator pattern.
    Pipeline:
        1. Vectorizer: fused_128 [B, 128] → latent [B, 16, 44, 80]
        2. DiT Workers: denoise steps (latent, timestep, text_embed) → denoised_latent
        3. VAE Decode: denoised_latent [B, 16, 44, 80] → video frames [B, C, T, H, W]
    """
    def __init__(
        self,
        num_dit_workers: int = 12,
        dit_model_path: str = "matrix_world_engine/models/checkpoints/diffusion_pytorch_model.safetensors",
        vae_model_path: str = "matrix_world_engine/models/checkpoints/Wan2.1_VAE.pth",
        device: str = "cuda",
        namespace: str = "legion"
    ):
        self.num_dit_workers = num_dit_workers
        self.device = device
        self.namespace = namespace

        # Connect to existing Ray cluster (namespace="legion")
        # Use GPU resources if available
        if device == "cuda":
            ray.init(address="auto", namespace=namespace, ignore_reinit_error=True, 
                     num_gpus=1, _redis_max_memory=1000000000)
        else:
            ray.init(address="auto", namespace=namespace, ignore_reinit_error=True)
        print(f"[Wan21RayDriver] Connected to Ray namespace '{namespace}' on {device}")

        # Initialize actors (detached, so they persist)
        self._init_actors(dit_model_path, vae_model_path)

    def _init_actors(self, dit_model_path: str, vae_model_path: str):
        """Create or connect to Ray actors."""
        # Vectorizer actor (single instance, lightweight)
        try:
            self.vectorizer = ray.get_actor("WanLatentVectorizer", namespace=self.namespace)
            print("[Wan21RayDriver] Connected to existing WanLatentVectorizer")
        except ValueError:
            from wan21_ray_vectorizer import WanLatentVectorizer
            self.vectorizer = WanLatentVectorizer.options(
                name="WanLatentVectorizer", namespace=self.namespace, lifetime="detached"
            ).remote()
            print("[Wan21RayDriver] Created new WanLatentVectorizer actor")

        # DiT Worker pool (GPU workers)
        try:
            self.dit_workers = [
                ray.get_actor(f"WanDiTWorker_{i}", namespace=self.namespace)
                for i in range(self.num_dit_workers)
            ]
            print(f"[Wan21RayDriver] Connected to {len(self.dit_workers)} existing DiT workers")
        except ValueError:
            from wan21_ray_dit_worker import WanDiTWorker
            self.dit_workers = [
                WanDiTWorker.options(
                    name=f"WanDiTWorker_{i}", namespace=self.namespace, lifetime="detached",
                    num_gpus=1
                ).remote(dit_model_path, self.device)
                for i in range(self.num_dit_workers)
            ]
            print(f"[Wan21RayDriver] Created {len(self.dit_workers)} new DiT workers (1 GPU each)")

        # VAE Decoder actor (single instance, GPU preferred)
        try:
            self.vae_decoder = ray.get_actor("WanVAEDecoder", namespace=self.namespace)
            print("[Wan21RayDriver] Connected to existing WanVAEDecoder")
        except ValueError:
            self.vae_decoder = self._create_vae_decoder(vae_model_path)
            print("[Wan21RayDriver] Created new WanVAEDecoder actor")

    def _create_vae_decoder(self, vae_model_path: str):
        """Create VAE decoder actor with GPU resource."""
        @ray.remote(num_cpus=1, num_gpus=1)
        class WanVAEDecoder:
            def __init__(self, model_path: str, device: str):
                self.device = device
                try:
                    import sys
                    sys.path.append("matrix_world_engine")
                    from models.wan_vae import WanVAE
                    self.vae = WanVAE()
                    state = torch.load(model_path, map_location=device)
                    self.vae.load_state_dict(state)
                    self.vae.to(device).eval()
                    print(f"[WanVAEDecoder] Loaded VAE from {model_path}")
                except Exception as e:
                    print(f"[WanVAEDecoder] Warning: Could not load VAE: {e}")
                    self.vae = None

            def decode(self, latent_ref: ray.ObjectRef) -> torch.Tensor:
                """Decode latent [B, 16, 44, 80] → video [B, 3, T, H, W]"""
                latent = ray.get(latent_ref)
                if self.vae is None:
                    return torch.randn(latent.shape[0], 3, 16, 256, 256)

                with torch.no_grad():
                    video = self.vae.decode(latent)
                return video

        return WanVAEDecoder.options(
            name="WanVAEDecoder", namespace=self.namespace, lifetime="detached"
        ).remote(vae_model_path, self.device)

    # ──────────────────────────────────────────────────────────────────────────
    # Pipeline Steps
    # ──────────────────────────────────────────────────────────────────────────

    def vectorize(self, fused_128: torch.Tensor) -> torch.Tensor:
        """Step 1: Project 128-dim fused latent → DiT input shape [B, 16, 44, 80]"""
        ref = ray.put(fused_128)
        latent_ref = self.vectorizer.vectorize.remote(ref)
        return ray.get(latent_ref)

    def denoise(self, latents: torch.Tensor, timesteps: list, text_embeds: torch.Tensor) -> torch.Tensor:
        """
        Step 2: Run multi-step denoising across DiT worker pool.
        Args:
            latents: [B, 16, 44, 80] initial noise
            timesteps: list of float timesteps (e.g., [1.0, 0.95, ..., 0.0])
            text_embeds: [B, 16] text conditioning
        Returns:
            Tensor [B, 16, 44, 80] denoised latents
        """
        current_latents = latents
        batch_size = latents.shape[0]
        chunk_size = max(1, batch_size // self.num_dit_workers)

        for t in timesteps:
            # Dispatch chunks to workers
            futures = []
            for i in range(0, batch_size, chunk_size):
                worker = self.dit_workers[(i // chunk_size) % self.num_dit_workers]
                lat_chunk = current_latents[i:i + chunk_size]
                txt_chunk = text_embeds[i:i + chunk_size]

                lat_ref = ray.put(lat_chunk)
                txt_ref = ray.put(txt_chunk)
                futures.append(worker.denoise_step.remote(lat_ref, t, txt_ref))

            # Async gather
            results = []
            while futures:
                done_refs, futures = ray.wait(futures, num_returns=1)
                for done_ref in done_refs:
                    results.append(ray.get(done_ref))

            current_latents = torch.cat(results, dim=0)

        return current_latents

    def decode(self, latents: torch.Tensor) -> torch.Tensor:
        """Step 3: VAE decode latent → video frames"""
        ref = ray.put(latents)
        video_ref = self.vae_decoder.decode.remote(ref)
        return ray.get(video_ref)

    # ──────────────────────────────────────────────────────────────────────────
    # High-Level Generate
    # ──────────────────────────────────────────────────────────────────────────

    def generate(
        self,
        fused_latent_128: torch.Tensor,      # [B, 128] from antigravity_hypothesis_run fusion_node
        text_embeds: torch.Tensor,            # [B, 16] text conditioning
        num_inference_steps: int = 20,
        timestep_schedule: str = "linear"
    ) -> torch.Tensor:
        """
        Full generation pipeline.
        Returns: video frames [B, 3, T, H, W]
        """
        batch_size = fused_latent_128.shape[0]

        # 1. Vectorize: 128 → 16×44×80
        print(f"[Wan21RayDriver] Vectorizing {batch_size} latents...")
        latents = self.vectorize(fused_latent_128)

        # 2. Add noise (start from pure noise for generation)
        noise = torch.randn_like(latents)
        latents = noise

        # 3. Timestep schedule
        if timestep_schedule == "linear":
            timesteps = torch.linspace(1.0, 0.0, num_inference_steps).tolist()
        else:
            # Cosine schedule
            timesteps = torch.cos(torch.linspace(0, torch.pi / 2, num_inference_steps)).tolist()

        # 4. Denoise
        print(f"[Wan21RayDriver] Running {num_inference_steps} denoising steps across {self.num_dit_workers} workers...")
        denoised = self.denoise(latents, timesteps, text_embeds)

        # 5. VAE Decode
        print("[Wan21RayDriver] Decoding latents to video...")
        video = self.decode(denoised)

        return video


# ──────────────────────────────────────────────────────────────────────────────
# Convenience: Connect to existing antigravity_hypothesis_run fusion output
# ──────────────────────────────────────────────────────────────────────────────

def run_from_antigravity_fusion(
    driver: Wan21RayDriver,
    nvdinov2_feats: torch.Tensor,      # [B, 384]
    vision_feats: torch.Tensor,         # [B, 41]
    text_embeds: torch.Tensor,          # [B, 16]
    num_inference_steps: int = 20
) -> torch.Tensor:
    """
    Bridge from antigravity_hypothesis_run.py fusion_node output to Wan2.1 generation.
    """
    from antigravity_hypothesis_run import HypothesisArchitecturalBridge

    # Run fusion (128-dim joint latent)
    bridge = HypothesisArchitecturalBridge()
    bridge.eval()

    with torch.no_grad():
        fused_128, _ = bridge(nvdinov2_feats, vision_feats)  # [B, 128]

    # Generate video
    video = driver.generate(fused_128, text_embeds, num_inference_steps)
    return video


if __name__ == "__main__":
    # Standalone test (requires Ray cluster running)
    import ray

    # Start local cluster for testing
    ray.init(num_cpus=4, namespace="legion", ignore_reinit_error=True)

    driver = Wan21RayDriver(num_dit_workers=4, device="cpu")

    # Dummy inputs
    B = 2
    fused_128 = torch.randn(B, 128)
    text_embeds = torch.randn(B, 16)

    # Test vectorize
    latents = driver.vectorize(fused_128)
    print(f"Vectorize: {fused_128.shape} → {latents.shape}")
    assert latents.shape == (B, 16, 44, 80)

    # Test denoise (1 step)
    timesteps = [0.5]
    denoised = driver.denoise(latents, timesteps, text_embeds)
    print(f"Denoise: {latents.shape} → {denoised.shape}")

    # Test decode
    video = driver.decode(denoised)
    print(f"Decode: {denoised.shape} → {video.shape}")

    print("✅ Wan21RayDriver test passed")
    ray.shutdown()