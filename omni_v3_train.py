# %% [markdown]
# # OmniCondVAE v3 — 8 Cell Ray Actor Training
# Deep Architecture: 1036 -> 512 -> 256 -> 128 -> Latent(32)
# Step by step. Run each cell, confirm, then continue.

# %% Cell 1 — Paths + env check
import sys, os, warnings
warnings.filterwarnings("ignore")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

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


LANCEDB_PATH  = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
DUCKDB_PATH   = r"C:\WEB CASE STUDY\web_intel_sonicdb.duckdb"
ENRICHED_JSON = r"C:\WEB CASE STUDY\data\enriched_samples_only.json"
OUTPUT_DIR    = r"C:\WEB CASE STUDY\sonic_dna_output"
OUT_PT        = os.path.join(OUTPUT_DIR, "fretflow_omni_v3.pt")

os.makedirs(OUTPUT_DIR, exist_ok=True)

checks = {
    "LanceDB omni_baselines": LANCEDB_PATH,
    "DuckDB sonicdb":         DUCKDB_PATH,
    "Enriched samples JSON":  ENRICHED_JSON,
    "Output dir":             OUTPUT_DIR,
}

print(f"PyTorch : {torch.__version__}")
print(f"Ray     : {ray.__version__}")
print()
all_ok = True
for name, path in checks.items():
    ok = os.path.exists(path)
    print(f"  {'✅' if ok else '❌'} {name:<28} {path}")
    if not ok:
        all_ok = False

print()
print("✅ Cell 1 PASSED — all paths exist" if all_ok else "❌ Cell 1 FAILED — fix missing paths before continuing")

# %% Cell 2 — Load LanceDB + subsample 500 rows
import lancedb
import numpy as np
import pandas as pd

TEST_ROWS = 500

DSP_COLS = [
    "rms_db","crest_factor","sub_bass_energy","bass_energy",
    "mid_energy","high_energy","spectral_centroid",
    "spectral_bandwidth","spectral_rolloff","spectral_contrast",
    "zero_crossing_rate",
]

db      = lancedb.connect(LANCEDB_PATH)
df_raw  = db.open_table("omni_semantic_baselines").to_pandas()
print(f"LanceDB loaded: {len(df_raw)} rows | {df_raw.shape[1]} cols")

# rms -> rms_db
if "rms" in df_raw.columns and "rms_db" not in df_raw.columns:
    df_raw["rms_db"] = df_raw["rms"].apply(
        lambda v: float(20 * np.log10(max(float(v), 1e-9))) if pd.notna(v) else -60.0
    )

# Fill any missing DSP cols with 0
for c in DSP_COLS:
    if c not in df_raw.columns:
        df_raw[c] = 0.0

df_raw = df_raw.dropna(subset=DSP_COLS).reset_index(drop=True)
print(f"After DSP clean: {len(df_raw)} rows")

# Semantic vector dim
vec_dim = 0
if "vector" in df_raw.columns:
    s = df_raw["vector"].iloc[0]
    if isinstance(s, (list, np.ndarray)):
        vec_dim = len(s)
print(f"Semantic vector dim: {vec_dim}")

# Subsample for test
df = df_raw.sample(min(TEST_ROWS, len(df_raw)), random_state=42).reset_index(drop=True)
print(f"Subsampled to {len(df)} rows for test run")

# Genre labels from track_name
def derive_genre(name):
    n = str(name).lower()
    if "chris lake" in n or "somebody" in n: return "TECH_HOUSE"
    if "tech" in n or "house" in n:          return "TECH_HOUSE"
    if "bass" in n:                          return "BASS"
    if "kick" in n or "drum" in n:           return "KICK"
    if "perc" in n or "hat" in n:            return "PERC"
    return "OTHER"

genres     = df["track_name"].apply(derive_genre) if "track_name" in df.columns else pd.Series(["OTHER"]*len(df))
genre_dist = genres.value_counts().to_dict()
print(f"Genre distribution: {genre_dist}")

all_genres = sorted(genres.unique().tolist())
genre2idx  = {g: i for i, g in enumerate(all_genres)}
idx2genre  = {v: k for k, v in genre2idx.items()}
N_GENRES   = len(genre2idx)
print(f"Genres ({N_GENRES}): {genre2idx}")
print("✅ Cell 2 PASSED — data loaded and subsampled")

# %% Cell 3 — Build Normalization & Tensors
print("[Cell 3] Preparing Tensors...")
X_dsp = df[DSP_COLS].values.astype(np.float32)
X_dsp = np.nan_to_num(X_dsp, nan=0.0)

# Build Omni: semantic (1024) + DSP (11) + BPM (1)
if vec_dim > 0 and "vector" in df.columns:
    X_sem = np.array([np.array(v, dtype=np.float32) for v in df["vector"]])
    X_sem = np.nan_to_num(X_sem, nan=0.0)
    X_bpm = np.ones((len(df), 1), dtype=np.float32) * 128.0
    X_omni = np.concatenate([X_sem, X_dsp, X_bpm], axis=1)
else:
    X_bpm = np.ones((len(df), 1), dtype=np.float32) * 128.0
    X_omni = np.concatenate([X_dsp, X_bpm], axis=1)

OMNI_DIM = X_omni.shape[1]
X_mean = X_omni.mean(0)
X_std = X_omni.std(0) + 1e-8
X_norm = (X_omni - X_mean) / X_std

Y_genre = np.array([genre2idx[g] for g in genres], dtype=np.int64)

X_t = torch.tensor(X_norm, dtype=torch.float32)
G_t = torch.tensor(Y_genre, dtype=torch.int64)

print(f"OMNI Tensor: {X_t.shape} | Genre Tensor: {G_t.shape}")
print(f"Input Dim: {OMNI_DIM}")
print("✅ Cell 3 PASSED")

# %% Cell 4 — Deep VAE Model & Ray Trainer Actor
import torch.nn as nn
import torch.nn.functional as F

class OmniCondVAE(nn.Module):
    def __init__(self, omni_dim, latent_dim, n_genres):
        super().__init__()
        self.omni_dim = omni_dim
        self.latent_dim = latent_dim
        self.genre_emb = nn.Embedding(n_genres, 16)
        
        # Encoder: 1036+16 -> 512 -> 256 -> 128 -> (mu, var)
        self.encoder_net = nn.Sequential(
            nn.Linear(omni_dim + 16, 512), nn.LayerNorm(512), nn.GELU(),
            nn.Linear(512, 256), nn.LayerNorm(256), nn.GELU(),
            nn.Linear(256, 128), nn.LayerNorm(128), nn.GELU(),
        )
        self.fc_mu = nn.Linear(128, latent_dim)
        self.fc_var = nn.Linear(128, latent_dim)
        
        # Decoder: latent+16 -> 128 -> 256 -> 512 -> 1036
        self.decoder_net = nn.Sequential(
            nn.Linear(latent_dim + 16, 128), nn.LayerNorm(128), nn.GELU(),
            nn.Linear(128, 256), nn.LayerNorm(256), nn.GELU(),
            nn.Linear(256, 512), nn.LayerNorm(512), nn.GELU(),
            nn.Linear(512, omni_dim)
        )
        
        # Mastering Head: 11 DSP -> 3 Params
        self.mastering_head = nn.Sequential(
            nn.Linear(11, 32), nn.GELU(), nn.Linear(32, 3)
        )

    def forward(self, x, genre_ids):
        cond = self.genre_emb(genre_ids)
        h = self.encoder_net(torch.cat([x, cond], dim=1))
        mu = self.fc_mu(h)
        log_var = self.fc_var(h)
        
        # Reparameterization
        std = torch.exp(0.5 * log_var)
        eps = torch.randn_like(std)
        z = mu + eps * std
        
        recon = self.decoder_net(torch.cat([z, cond], dim=1))
        
        # Mastering head maps DSP chunk of reconstruction (last 12 values minus BPM)
        dsp_slice = recon[:, -12:-1]
        master_params = self.mastering_head(dsp_slice)
        return recon, mu, log_var, master_params

@ray.remote
class TrainerActor:
    def __init__(self, omni_dim, latent_dim, n_genres):
        self.model = OmniCondVAE(omni_dim, latent_dim, n_genres)
        
    def train_shard(self, X_shard, G_shard, epochs=10, batch_size=32):
        opt = torch.optim.AdamW(self.model.parameters(), lr=1e-3)
        
        # Convert to tensors
        X = torch.tensor(X_shard, dtype=torch.float32)
        G = torch.tensor(G_shard, dtype=torch.int64)
        
        dataset = torch.utils.data.TensorDataset(X, G)
        loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        self.model.train()
        history = []
        
        for ep in range(epochs):
            ep_loss = 0
            for batch_x, batch_g in loader:
                opt.zero_grad()
                recon, mu, log_var, _ = self.model(batch_x, batch_g)
                
                recon_loss = F.mse_loss(recon, batch_x)
                kl_loss = -0.5 * torch.mean(1 + log_var - mu.pow(2) - log_var.exp())
                loss = recon_loss + 0.001 * kl_loss
                
                loss.backward()
                opt.step()
                ep_loss += loss.item()
            
            history.append(ep_loss / len(loader))
        
        return {
            "state_dict": {k: v.cpu().numpy() for k, v in self.model.state_dict().items()},
            "final_loss": history[-1],
            "history": history
        }

print("✅ Cell 4 PASSED")

# %% Cell 5 — Execute Training on 6 Ray Actors
if not ray.is_initialized():
    ray.init(namespace="legion", ignore_reinit_error=True)

N_ACTORS = 6
print(f"Spawning {N_ACTORS} parallel TrainerActors...")
actors = [TrainerActor.remote(OMNI_DIM, 32, N_GENRES) for _ in range(N_ACTORS)]

# Shard the dataset
X_np = X_t.numpy()
G_np = G_t.numpy()
shards_x = np.array_split(X_np, N_ACTORS)
shards_g = np.array_split(G_np, N_ACTORS)

futures = [
    actors[i].train_shard.remote(shards_x[i], shards_g[i], epochs=50, batch_size=32)
    for i in range(N_ACTORS)
]
results = ray.get(futures)

print("Ray Actors Training Results:")
best_idx = 0
best_loss = float('inf')
for idx, res in enumerate(results):
    loss = res["final_loss"]
    print(f"  Actor {idx} Final Loss: {loss:.5f}")
    if loss < best_loss:
        best_loss = loss
        best_idx = idx

print(f"Winner: Actor {best_idx} (Loss: {best_loss:.5f})")
print("✅ Cell 5 PASSED")

# %% Cell 6 — Plot Loss Curves
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
for idx, res in enumerate(results):
    plt.plot(res["history"], label=f"Actor {idx}")

plt.title("OmniCondVAE v3 Training Convergence (Ray Ensemble)")
plt.xlabel("Epoch")
plt.ylabel("Combined Loss (MSE + KL)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig(os.path.join(OUTPUT_DIR, "training_loss.png"))
plt.show()
print(f"Loss plot saved to {OUTPUT_DIR}/training_loss.png")
print("✅ Cell 6 PASSED")

# %% Cell 7 — Rebuild Best Model & Save .pt
print("[Cell 7] Exporting Best Model...")
best_model = OmniCondVAE(OMNI_DIM, 32, N_GENRES)
best_model.load_state_dict({k: torch.tensor(v) for k, v in results[best_idx]["state_dict"].items()})
best_model.eval()

torch.save({
    "model_state_dict": best_model.state_dict(),
    "omni_dim": OMNI_DIM,
    "latent_dim": 32,
    "n_genres": N_GENRES,
    "genre2idx": genre2idx,
    "idx2genre": idx2genre,
    "vec_dim": vec_dim,
    "dsp_cols": DSP_COLS,
    "X_mean": X_mean.tolist(),
    "X_std": X_std.tolist(),
    "architecture": "OmniCondVAE_v3_Deep_Ray",
}, OUT_PT)

print(f"Saved checkpoint to: {OUT_PT}")
print("✅ Cell 7 PASSED")

# %% Cell 8 — Generation Demo
print("[Cell 8] Generative Inference Demo...")
for g_name, gid in genre2idx.items():
    g_tensor = torch.tensor([gid], dtype=torch.int64)
    cond = best_model.genre_emb(g_tensor)
    z = torch.randn(1, 32)
    
    with torch.no_grad():
        # Generate Omni Vector
        gen_norm = best_model.decoder_net(torch.cat([z, cond], dim=1)).squeeze(0)
    
    # Denormalize to real values
    gen_raw = gen_norm.numpy() * X_std + X_mean
    gen_dsp = gen_raw[-12:-1] # Extract DSP part
    
    # Calculate mastering parameters using the Mastering Head
    # We normalize the generated DSP slice using the saved mean/std
    dsp_slice_norm = (torch.tensor(gen_dsp, dtype=torch.float32).unsqueeze(0) - torch.tensor(X_mean[-12:-1])) / torch.tensor(X_std[-12:-1])
    
    with torch.no_grad():
        master_params = best_model.mastering_head(dsp_slice_norm).squeeze(0).numpy()
    
    print(f"  Genre: {g_name:<12} | Generated RMS: {gen_dsp[0]:.2f} dB | Gain Target: {master_params[0]:.2f} dB")

print("✅ Cell 8 PASSED — Generation Complete!")