"""
sonic_dna_mini_test.py
======================
Mini end-to-end pipeline test: DuckDB DSP features -> Student MLP Autoencoder -> .pt + .onnx
Uses existing 47-dim Sonic DNA DSP features as both input and reconstruction target.
MERT can replace the teacher target in the full run.

Phases:
  1. Fetch 20 tracks from DuckDB via Onyx API
  2. Train a student MLP autoencoder (47-dim -> 64-dim latent -> 47-dim) via Ray
  3. Export weights as .pt and .onnx
  4. Similarity search sanity check
"""

import os, sys, json, time, warnings

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

warnings.filterwarnings("ignore")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import requests
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import ray

print("=" * 65)
print("  SONIC DNA MINI TEST  --  Full Pipeline (20 tracks)")
print("=" * 65)

# CONFIG
ONYX_API   = "http://localhost:8002/query/duckdb"
MINI_N     = 20
LATENT_DIM = 64
EPOCHS     = 100
LR         = 1e-3
OUTPUT_DIR = r"C:\WEB CASE STUDY\sonic_dna_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DSP_COLS = [
    "tempo","rms_db","crest_factor","sub_bass_energy","bass_energy",
    "mid_energy","high_energy","spectral_centroid","spectral_rolloff",
    "spectral_bandwidth","spectral_contrast","zcr","onset_strength",
    "transient_density","harmonic_ratio","percussive_ratio",
    "mfcc_1","mfcc_2","mfcc_3","mfcc_4","mfcc_5","mfcc_6","mfcc_7",
    "mfcc_8","mfcc_9","mfcc_10","mfcc_11","mfcc_12","mfcc_13",
    "chroma_C","chroma_Cs","chroma_D","chroma_Ds","chroma_E","chroma_F",
    "chroma_Fs","chroma_G","chroma_Gs","chroma_A","chroma_As","chroma_B",
]

# ============================================================
# PHASE 1: Fetch from DuckDB
# ============================================================
print("\n[PHASE 1] Fetching tracks from Onyx API...")
t0 = time.time()
try:
    resp = requests.post(ONYX_API, json={
        "sql_query": f"SELECT * FROM audio_features LIMIT {MINI_N};"
    }, timeout=15)
    data = resp.json()
    assert data.get("status") == "success", f"API error: {data}"
    df = pd.DataFrame(data["results"])
    print(f"  OK  {len(df)} tracks in {time.time()-t0:.1f}s")
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

avail = [c for c in DSP_COLS if c in df.columns]
df_clean = df[avail + ["filepath","filename"]].dropna(subset=avail)
print(f"  DSP features: {len(avail)} cols | Clean rows: {len(df_clean)}")

# ============================================================
# PHASE 2: Ray actor trains the student autoencoder
# ============================================================
print("\n[PHASE 2] Launching Ray + training student autoencoder...")

try:
    ray.init(ignore_reinit_error=True, num_cpus=4,
             logging_level="error", log_to_driver=False)
    print("  Ray initialized")
except Exception as e:
    print(f"  Ray warning: {e}")

@ray.remote
class SonicDNATrainer:
    """
    Ray actor that owns training.
    Input/target: 47-dim DSP vector (autoencoder).
    Latent space: LATENT_DIM (64) -- this IS the Sonic DNA embedding.
    MERT embeddings can replace targets in the full run.
    """
    def train(self, X_data, latent_dim, epochs, lr):
        import torch, torch.nn as nn, torch.optim as optim
        import numpy as np
        from torch.utils.data import DataLoader, TensorDataset

        X = torch.tensor(X_data, dtype=torch.float32)
        mean_ = X.mean(0)
        std_  = X.std(0) + 1e-8
        Xn = (X - mean_) / std_

        in_dim = Xn.shape[1]

        class SonicDNA(nn.Module):
            def __init__(self):
                super().__init__()
                self.encoder = nn.Sequential(
                    nn.Linear(in_dim, 128), nn.LayerNorm(128), nn.GELU(),
                    nn.Linear(128, 64),    nn.LayerNorm(64),  nn.GELU(),
                    nn.Linear(64, latent_dim)
                )
                self.decoder = nn.Sequential(
                    nn.Linear(latent_dim, 64), nn.GELU(),
                    nn.Linear(64, 128),         nn.GELU(),
                    nn.Linear(128, in_dim)
                )
            def forward(self, x):
                z = self.encoder(x)
                z = z / (z.norm(dim=-1, keepdim=True) + 1e-8)
                return z, self.decoder(z)

        model = SonicDNA()
        opt = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
        sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
        loader = DataLoader(TensorDataset(Xn), batch_size=min(8, len(Xn)), shuffle=True)

        losses = []
        for ep in range(epochs):
            model.train()
            ep_loss = 0
            for (xb,) in loader:
                opt.zero_grad()
                z, recon = model(xb)
                loss = nn.functional.mse_loss(recon, xb)
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step()
                ep_loss += loss.item()
            sched.step()
            losses.append(ep_loss / len(loader))

        # Return state dict + scaler + losses
        return {
            "state_dict": {k: v.numpy().tolist() for k, v in model.state_dict().items()},
            "mean": mean_.numpy().tolist(),
            "std":  std_.numpy().tolist(),
            "in_dim": in_dim,
            "latent_dim": latent_dim,
            "losses": losses,
        }

X_data = df_clean[avail].values.astype(np.float32)
trainer = SonicDNATrainer.remote()
t1 = time.time()
result_ref = trainer.train.remote(X_data.tolist(), LATENT_DIM, EPOCHS, LR)
result = ray.get(result_ref)
print(f"  Training done in {time.time()-t1:.1f}s")
print(f"  Final loss: {result['losses'][-1]:.5f}")

# ============================================================
# PHASE 3: Reconstruct model + export
# ============================================================
print("\n[PHASE 3] Exporting model...")

in_dim = result["in_dim"]

class SonicDNA(nn.Module):
    def __init__(self, in_dim, latent_dim):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(in_dim, 128), nn.LayerNorm(128), nn.GELU(),
            nn.Linear(128, 64),    nn.LayerNorm(64),  nn.GELU(),
            nn.Linear(64, latent_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 64), nn.GELU(),
            nn.Linear(64, 128),         nn.GELU(),
            nn.Linear(128, in_dim)
        )
    def forward(self, x):
        z = self.encoder(x)
        return z / (z.norm(dim=-1, keepdim=True) + 1e-8)  # encoder-only for inference

model = SonicDNA(in_dim, LATENT_DIM)
state = {k: torch.tensor(np.array(v)) for k, v in result["state_dict"].items()}
model.load_state_dict(state, strict=False)  # ignore decoder keys
model.eval()

X_mean = torch.tensor(result["mean"])
X_std  = torch.tensor(result["std"])

pt_path = os.path.join(OUTPUT_DIR, "sonic_dna_mini_v1.pt")
torch.save({
    "model_state_dict": model.state_dict(),
    "in_dim":      in_dim,
    "latent_dim":  LATENT_DIM,
    "dsp_cols":    avail,
    "X_mean":      result["mean"],
    "X_std":       result["std"],
    "final_loss":  result["losses"][-1],
    "n_tracks":    len(df_clean),
}, pt_path)
print(f"  .pt saved  -> {pt_path}")

try:
    dummy = torch.randn(1, in_dim)
    onnx_path = os.path.join(OUTPUT_DIR, "sonic_dna_mini_v1.onnx")
    torch.onnx.export(
        model, dummy, onnx_path,
        input_names=["dsp_features"],
        output_names=["sonic_dna_embedding"],
        dynamic_axes={"dsp_features": {0: "batch"}, "sonic_dna_embedding": {0: "batch"}},
        opset_version=18
    )
    print(f"  .onnx saved -> {onnx_path}")
except Exception as e:
    print(f"  ONNX skipped: {e}")

# ============================================================
# PHASE 4: Similarity search sanity check
# ============================================================
print("\n[PHASE 4] Similarity search sanity check...")

X_tensor = torch.tensor(X_data)
X_norm   = (X_tensor - X_mean) / X_std
with torch.no_grad():
    all_embeddings = model(X_norm).numpy()

# Query = first track, find closest
query   = all_embeddings[0]
sims    = all_embeddings @ query / (
    np.linalg.norm(all_embeddings, axis=1) * np.linalg.norm(query) + 1e-8
)
top_idx = np.argsort(sims)[::-1][:4]  # top 4 (incl. self)

print(f"  Query: {df_clean['filename'].iloc[0][:55]}")
print(f"  Top matches:")
for rank, idx in enumerate(top_idx):
    name = df_clean['filename'].iloc[idx][:52]
    print(f"    {rank+1}. [{sims[idx]:.4f}] {name}")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 65)
print("  SONIC DNA MINI TEST -- COMPLETE")
print("=" * 65)
print(f"  Tracks:         {len(df_clean)}")
print(f"  DSP features:   {in_dim}")
print(f"  Latent dim:     {LATENT_DIM}")
print(f"  Params:         {sum(p.numel() for p in model.parameters()):,}")
print(f"  Final loss:     {result['losses'][-1]:.5f}")
print(f"  Output:         {OUTPUT_DIR}")
print()
print("  NEXT: Run full 1,085-track pipeline (sonic_dna_full_run.py)")
print("  UPGRADE: Replace autoencoder target with MERT embeddings")
print("=" * 65)
ray.shutdown()