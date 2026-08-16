"""
Wan2.1 DiT Latent Vectorizer — Ray Actor
Projects 128-dim fused latent (from antigravity_hypothesis_run.py) → [B, 16, 44, 80] for DiT input.
Matches AudioDatasetWorker pattern: @ray.remote(num_cpus=1), zero-copy Plasma, single init per core.
Respects existing Ray cluster resources (12 CPUs, GPU if available).
"""

import os
import torch
import torch.nn as nn
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


# Prevent thread contention — CRITICAL for your 12-core pool
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["TORCH_NUM_THREADS"] = "1"


@ray.remote(num_cpus=1, max_restarts=3, max_task_retries=2)
class WanLatentVectorizer:
    """
    Ray actor: one per physical CPU core.
    Projects fused 128-dim latent → Wan2.1 DiT input shape [B, 16, 44, 80].
    """
    def __init__(self, latent_dim: int = 128, dit_channels: int = 16, dit_height: int = 44, dit_width: int = 80):
        self.latent_dim = latent_dim
        self.dit_channels = dit_channels
        self.dit_height = dit_height
        self.dit_width = dit_width
        self.output_dim = dit_channels * dit_height * dit_width  # 16 * 44 * 80 = 56,320

        # Projection head: 128 → 56,320
        self.proj = nn.Linear(latent_dim, self.output_dim)
        self.proj.eval()  # inference only

        # Optional: load pretrained projection weights if you have them
        # self.load_projection_weights(path)

        print(f"[WanLatentVectorizer] Initialized: {latent_dim} → {self.output_dim} ({dit_channels}×{dit_height}×{dit_width})")

    def vectorize(self, fused_128: torch.Tensor) -> torch.Tensor:
        """
        Args:
            fused_128: [B, 128] fused latent from antigravity_hypothesis_run.py fusion_node
        Returns:
            Tensor [B, 16, 44, 80] ready for DiT forward pass
        """
        with torch.no_grad():
            # Project: [B, 128] → [B, 56320]
            projected = self.proj(fused_128)
            # Reshape: [B, 56320] → [B, 16, 44, 80]
            dit_input = projected.view(-1, self.dit_channels, self.dit_height, self.dit_width)
        return dit_input

    def vectorize_numpy(self, fused_128_np) -> torch.Tensor:
        """Accept numpy array, return torch tensor (for Ray ObjectRef passing)."""
        fused_128 = torch.from_numpy(fused_128_np).float()
        return self.vectorize(fused_128)

    def load_projection_weights(self, path: str):
        """Load pretrained projection head weights."""
        state = torch.load(path, map_location="cpu")
        self.proj.load_state_dict(state)
        print(f"[WanLatentVectorizer] Loaded projection weights from {path}")


class WanVectorizerOrchestrator:
    """
    Matches DiffusionDataOrchestrator pattern:
    - Creates pool of vectorizer actors (one per CPU core)
    - Distributes work round-robin
    - Uses ray.wait() for async gathering
    - Respects existing Ray cluster resources
    """
    def __init__(self, num_workers: int = None):
        # Auto-detect available CPUs from Ray cluster
        if num_workers is None:
            resources = ray.cluster_resources()
            num_workers = int(resources.get("CPU", 12))
            # Cap at 12 to match your existing pool
            num_workers = min(num_workers, 12)
        
        self.num_workers = num_workers
        self.workers = [WanLatentVectorizer.remote() for _ in range(num_workers)]
        print(f"[WanVectorizerOrchestrator] Spawned {num_workers} vectorizer actors (Ray CPUs: {ray.cluster_resources().get('CPU', 'unknown')})")

    def vectorize_batch(self, fused_latents: torch.Tensor) -> torch.Tensor:
        """
        Args:
            fused_latents: [B, 128] batch of fused latents
        Returns:
            Tensor [B, 16, 44, 80] concatenated results
        """
        batch_size = fused_latents.shape[0]
        # Split batch across workers
        chunk_size = max(1, batch_size // self.num_workers)
        chunks = [fused_latents[i:i + chunk_size] for i in range(0, batch_size, chunk_size)]

        futures = []
        for i, chunk in enumerate(chunks):
            worker = self.workers[i % self.num_workers]
            # Pin chunk to Plasma (zero-copy)
            chunk_ref = ray.put(chunk)
            futures.append(worker.vectorize.remote(chunk_ref))

        # Async gather with ray.wait (matches your pattern)
        results = []
        while futures:
            done_refs, futures = ray.wait(futures, num_returns=1)
            for done_ref in done_refs:
                results.append(ray.get(done_ref))

        # Concatenate along batch dimension
        return torch.cat(results, dim=0)


if __name__ == "__main__":
    # Quick local test — connects to existing Ray cluster if running, otherwise starts one
    import ray
    
    # Try to connect to existing cluster first (your 12-CPU pool)
    try:
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        print(f"[Test] Connected to existing Ray cluster: {ray.cluster_resources()}")
    except Exception:
        ray.init(num_cpus=4, namespace="legion", ignore_reinit_error=True)
        print("[Test] Started local Ray cluster")

    vectorizer = WanLatentVectorizer.remote()
    dummy_fused = torch.randn(2, 128)
    ref = ray.put(dummy_fused)
    out = ray.get(vectorizer.vectorize.remote(ref))
    print(f"Input: {dummy_fused.shape} → Output: {out.shape}")
    assert out.shape == (2, 16, 44, 80)
    print("✅ WanLatentVectorizer test passed")
    ray.shutdown()