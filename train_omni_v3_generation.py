"""
train_omni_v3_generation.py
===========================
Conditional VAE (OmniCondVAE v3) — full train + generate pipeline.

Data sources:
  - LanceDB omni_semantic_baselines  (5,908 rows: DSP + 384-dim semantic)
  - DuckDB  sonic_dna                (unmastered stems DSP)
  - JSON    enriched_samples_only    (3,983 rows: genre_class + BPM)

Output: sonic_dna_output/fretflow_omni_v3.pt
        sonic_dna_output/training_curve_omni_v3.png
"""
import sys, os, time, warnings

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

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import ray

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CONFIG & CONSTANTS (Safe for Import)
# ─────────────────────────────────────────────────────────────────────────────
LANCEDB_PATH      = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
DUCKDB_PATH       = r"C:\WEB CASE STUDY\web_intel_sonicdb.duckdb"
ENRICHED_JSON     = r"C:\WEB CASE STUDY\data\enriched_samples_only.json"
OUTPUT_DIR        = r"C:\WEB CASE STUDY\sonic_dna_output"
OUT_PT            = os.path.join(OUTPUT_DIR, "fretflow_omni_v3.pt")
OUT_CURVE         = os.path.join(OUTPUT_DIR, "training_curve_omni_v3.png")

DSP_COLS = [
    "rms_db", "crest_factor", "sub_bass_energy", "bass_energy",
    "mid_energy", "high_energy", "spectral_centroid",
    "spectral_bandwidth", "spectral_rolloff", "spectral_contrast",
    "zero_crossing_rate",
]

# Set device and seed globally so imports work
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.manual_seed(42)
np.random.seed(42)

# ─────────────────────────────────────────────────────────────────────────────
# MODEL ARCHITECTURE (Safe for Import)
# ─────────────────────────────────────────────────────────────────────────────
class ResBlock(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim, dim), nn.LayerNorm(dim), nn.GELU(),
            nn.Linear(dim, dim), nn.LayerNorm(dim),
        )
    def forward(self, x):
        return F.gelu(x + self.net(x))


class OmniCondVAE(nn.Module):
    def __init__(self, omni_dim, latent_dim, n_genres, genre_emb=32):
        super().__init__()
        self.omni_dim   = omni_dim
        self.latent_dim = latent_dim
        self.cond_dim   = genre_emb + 1

        self.genre_emb = nn.Embedding(n_genres, genre_emb)

        enc_in = omni_dim + self.cond_dim
        self.encoder = nn.Sequential(
            nn.Linear(enc_in, 512), nn.LayerNorm(512), nn.GELU(),
            ResBlock(512),
            nn.Linear(512, 256), nn.LayerNorm(256), nn.GELU(),
            ResBlock(256),
            nn.Linear(256, 128), nn.LayerNorm(128), nn.GELU(),
        )
        self.fc_mu  = nn.Linear(128, latent_dim)
        self.fc_var = nn.Linear(128, latent_dim)

        dec_in = latent_dim + self.cond_dim
        self.decoder = nn.Sequential(
            nn.Linear(dec_in, 128), nn.LayerNorm(128), nn.GELU(),
            ResBlock(128),
            nn.Linear(128, 256), nn.LayerNorm(256), nn.GELU(),
            ResBlock(256),
            nn.Linear(256, 512), nn.LayerNorm(512), nn.GELU(),
            nn.Linear(512, omni_dim),
        )

        self.mastering_head = nn.Sequential(
            nn.Linear(11, 64), nn.GELU(),
            nn.Linear(64, 32), nn.GELU(),
            nn.Linear(32, 3),
        )

    def _cond(self, genre_ids, bpm_n):
        return torch.cat([self.genre_emb(genre_ids), bpm_n.unsqueeze(1)], dim=1)

    def encode(self, x, cond):
        h = self.encoder(torch.cat([x, cond], dim=1))
        return self.fc_mu(h), self.fc_var(h)

    def reparameterize(self, mu, log_var):
        return mu + torch.exp(0.5 * log_var) * torch.randn_like(mu)

    def decode(self, z, cond):
        return self.decoder(torch.cat([z, cond], dim=1))

    def forward(self, x, genre_ids, bpm_n):
        cond = self._cond(genre_ids, bpm_n)
        mu, log_var = self.encode(x, cond)
        z = self.reparameterize(mu, log_var)
        recon = self.decode(z, cond)
        dsp_slice = recon[:, -12:-1]
        master_params = self.mastering_head(dsp_slice)
        return recon, mu, log_var, master_params

    @torch.no_grad()
    def generate(self, genre_id, bpm, temperature=1.0, n=1, bpm_mean=0.0, bpm_std=1.0):
        self.eval()
        g = torch.tensor([genre_id] * n, device=device)
        b = torch.tensor([(bpm - bpm_mean) / bpm_std] * n, dtype=torch.float32, device=device)
        cond = self._cond(g, b)
        z = torch.randn(n, self.latent_dim, device=device) * temperature
        return self.decode(z, cond)

@ray.remote
class TrainerActor:
    def __init__(self, omni_dim, latent_dim, n_genres, genre_emb=32):
        self.model = OmniCondVAE(omni_dim, latent_dim, n_genres, genre_emb)
        self.omni_dim = omni_dim

    def train_shard(self, X_shard, G_shard, B_shard, epochs=10, batch_size=32):
        opt = optim.AdamW(self.model.parameters(), lr=1e-3)
        X = torch.tensor(X_shard, dtype=torch.float32)
        G = torch.tensor(G_shard, dtype=torch.int64)
        B = torch.tensor(B_shard, dtype=torch.float32)
        dataset = TensorDataset(X, G, B)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        self.model.train()
        history = []
        for ep in range(epochs):
            ep_loss = 0
            for xb, gb, bb in loader:
                opt.zero_grad()
                recon, mu, log_var, _ = self.model(xb, gb, bb)
                recon_loss = F.mse_loss(recon, xb)
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

# ─────────────────────────────────────────────────────────────────────────────
# EXECUTION PIPELINE (Wrapped in main to prevent import side-effects)
# ─────────────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("=" * 70)
    print("  OMNI COND-VAE v3  —  FULL TRAIN + GENERATION")
    print("=" * 70)
    print(f"PyTorch  {torch.__version__}  |  device: {device}")

    # PHASE 1: Load LanceDB
    print("\n[PHASE 1] Loading LanceDB omni_semantic_baselines...")
    df_omni = pd.DataFrame()
    vec_dim = 0
    try:
        import lancedb
        db = lancedb.connect(LANCEDB_PATH)
        df_omni = db.open_table("omni_semantic_baselines").to_pandas()
        if "rms" in df_omni.columns and "rms_db" not in df_omni.columns:
            df_omni["rms_db"] = df_omni["rms"].apply(
                lambda v: float(20 * np.log10(max(float(v), 1e-9))) if pd.notna(v) else -60.0
            )
        missing_dsp = [c for c in DSP_COLS if c not in df_omni.columns]
        for c in missing_dsp: df_omni[c] = 0.0
        df_omni = df_omni.dropna(subset=DSP_COLS).reset_index(drop=True)
        if "vector" in df_omni.columns:
            sample_v = df_omni["vector"].iloc[0]
            if isinstance(sample_v, (list, np.ndarray)):
                vec_dim = len(sample_v)
    except Exception as e:
        print(f"  [WARN] LanceDB failed: {e}")

    # PHASE 2: Load DuckDB
    print("\n[PHASE 2] Loading DuckDB sonic_dna...")
    df_sonic = pd.DataFrame()
    try:
        import duckdb
        conn = duckdb.connect(DUCKDB_PATH, read_only=True)
        df_sonic = conn.execute("SELECT * FROM sonic_dna").fetchdf()
        conn.close()
        if "zcr" in df_sonic.columns and "zero_crossing_rate" not in df_sonic.columns:
            df_sonic = df_sonic.rename(columns={"zcr": "zero_crossing_rate"})
        df_sonic = df_sonic.dropna(subset=[c for c in DSP_COLS if c in df_sonic.columns])
        for c in DSP_COLS:
            if c not in df_sonic.columns: df_sonic[c] = 0.0
    except Exception as e:
        print(f"  [WARN] DuckDB failed: {e}")

    # PHASE 3: Load enriched samples
    print("\n[PHASE 3] Loading enriched_samples_only.json...")
    df_enr = pd.DataFrame()
    try:
        df_enr = pd.read_json(ENRICHED_JSON)
    except Exception as e:
        print(f"  [WARN] JSON failed: {e}")

    # PHASE 4: Build master training frame
    print("\n[PHASE 4] Building master training DataFrame...")
    frames = []
    if len(df_omni) > 0:
        f = df_omni[DSP_COLS].copy()
        f["source"] = "lancedb"
        bpm_col = next((c for c in ["tempo","bpm","audio_tempo"] if c in df_omni.columns), None)
        f["bpm"] = df_omni[bpm_col].fillna(128.0).values if bpm_col else 128.0
        if "track_name" in df_omni.columns:
            def derive_genre(name):
                n = str(name).lower()
                if "chris lake" in n or "somebody" in n: return "TECH_HOUSE"
                if "tech" in n or "house" in n: return "TECH_HOUSE"
                if "bass" in n or "sub" in n: return "BASS"
                if "kick" in n or "drum" in n: return "KICK"
                if "perc" in n or "hat" in n: return "PERC"
                return "OTHER"
            f["genre_class"] = df_omni["track_name"].apply(derive_genre)
        else: f["genre_class"] = "OTHER"
        if vec_dim > 0 and "vector" in df_omni.columns:
            vecs = np.array([np.array(v, dtype=np.float32) if isinstance(v, (list, np.ndarray)) else np.zeros(vec_dim, dtype=np.float32) for v in df_omni["vector"]])
            vecs = np.nan_to_num(vecs, nan=0.0)
            for i in range(vec_dim): f[f"sem_{i}"] = vecs[:, i]
        frames.append(f)

    if len(df_sonic) > 0:
        f2 = df_sonic[DSP_COLS].copy()
        f2["source"] = "duckdb"
        bpm_col2 = next((c for c in ["tempo","bpm"] if c in df_sonic.columns), None)
        f2["bpm"] = df_sonic[bpm_col2].fillna(128.0).values if bpm_col2 else 128.0
        gc_col = next((c for c in ["genre_class","genre","drum_type"] if c in df_sonic.columns), None)
        f2["genre_class"] = df_sonic[gc_col].fillna("OTHER").values if gc_col else "OTHER"
        if vec_dim > 0:
            for i in range(vec_dim): f2[f"sem_{i}"] = 0.0
        frames.append(f2)

    if len(df_enr) > 0:
        dsp_avail = [c for c in DSP_COLS if c in df_enr.columns]
        if len(dsp_avail) >= 4:
            f3 = pd.DataFrame()
            for c in DSP_COLS: f3[c] = df_enr[c].fillna(0.0) if c in df_enr.columns else 0.0
            f3["source"] = "enriched"
            bpm_col3 = next((c for c in ["tempo","bpm_enriched","bpm"] if c in df_enr.columns), None)
            f3["bpm"] = df_enr[bpm_col3].fillna(128.0).values if bpm_col3 else 128.0
            f3["genre_class"] = df_enr["genre_class"].fillna("OTHER").values if "genre_class" in df_enr.columns else "OTHER"
            if vec_dim > 0:
                for i in range(vec_dim): f3[f"sem_{i}"] = 0.0
            frames.append(f3)

    df_train = pd.concat(frames, ignore_index=True).fillna(0.0)
    
    # PHASE 5: Build tensors
    all_genres = sorted(df_train["genre_class"].unique().tolist())
    genre2idx = {g: i for i, g in enumerate(all_genres)}
    idx2genre = {v: k for k, v in genre2idx.items()}
    N_GENRES = len(genre2idx)

    X_dsp = df_train[DSP_COLS].values.astype(np.float32)
    X_dsp = np.nan_to_num(X_dsp, nan=0.0, posinf=0.0, neginf=0.0)
    X_bpm = df_train["bpm"].values.astype(np.float32).reshape(-1, 1)
    X_bpm = np.clip(X_bpm, 50.0, 250.0)
    if vec_dim > 0:
        sem_cols = [f"sem_{i}" for i in range(vec_dim)]
        X_sem = df_train[sem_cols].values.astype(np.float32)
        X_sem = np.nan_to_num(X_sem, nan=0.0)
        X_omni = np.concatenate([X_sem, X_dsp, X_bpm], axis=1)
    else:
        X_omni = np.concatenate([X_dsp, X_bpm], axis=1)

    OMNI_DIM = X_omni.shape[1]
    X_mean = X_omni.mean(0).astype(np.float32)
    X_std  = (X_omni.std(0) + 1e-8).astype(np.float32)
    X_norm = ((X_omni - X_mean) / X_std).astype(np.float32)
    bpm_raw = X_bpm.flatten()
    bpm_mean = float(bpm_raw.mean())
    bpm_std = float(bpm_raw.std() + 1e-8)
    bpm_norm = ((bpm_raw - bpm_mean) / bpm_std).astype(np.float32)
    Y_genre = np.array([genre2idx[g] for g in df_train["genre_class"]], dtype=np.int64)
    X_t, G_t, BPM_t = torch.tensor(X_norm).to(device), torch.tensor(Y_genre).to(device), torch.tensor(bpm_norm).to(device)

    # PHASE 6: Model
    LATENT_DIM, GENRE_EMB = 128, 32
    model = OmniCondVAE(OMNI_DIM, LATENT_DIM, N_GENRES, GENRE_EMB).to(device)

    # PHASE 7: Hybrid Train
    SEARCH_EPOCHS, POLISH_EPOCHS, LR, KL_WARMUP, KL_WEIGHT, BATCH_SIZE, N_ACTORS = 10, 1500, 3e-4, 400, 0.001, 128, 6
    if not ray.is_initialized():
        ray.init(address='auto', namespace="legion", ignore_reinit_error=True)
    
    actors = [TrainerActor.remote(OMNI_DIM, LATENT_DIM, N_GENRES, GENRE_EMB) for _ in range(N_ACTORS)]
    X_np, G_np, B_np = X_norm, Y_genre, bpm_norm
    shards_x, shards_g, shards_b = np.array_split(X_np, N_ACTORS), np.array_split(G_np, N_ACTORS), np.array_split(B_np, N_ACTORS)
    futures = [actors[i].train_shard.remote(shards_x[i], shards_g[i], shards_b[i], epochs=SEARCH_EPOCHS, batch_size=BATCH_SIZE) for i in range(N_ACTORS)]
    results = ray.get(futures)
    best_idx = np.argmin([r["final_loss"] for r in results])
    winner_state = results[best_idx]["state_dict"]
    model.load_state_dict({k: torch.tensor(v).to(device) for k, v in winner_state.items()})

    loader = DataLoader(TensorDataset(X_t, G_t, BPM_t), batch_size=BATCH_SIZE, shuffle=True)
    optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-5)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=POLISH_EPOCHS, eta_min=1e-5)
    history = {"recon": [], "kl": [], "total": []}
    model.train()
    t0 = time.time()
    for ep in range(1, POLISH_EPOCHS + 1):
        ep_recon = ep_kl = 0.0
        beta = min(1.0, ep / KL_WARMUP)
        for xb, gb, bb in loader:
            optimizer.zero_grad()
            recon, mu, log_var, _ = model(xb, gb, bb)
            recon_loss = F.mse_loss(recon, xb)
            kl_loss = -0.5 * torch.mean(1 + log_var - mu.pow(2) - log_var.exp())
            loss = recon_loss + beta * KL_WEIGHT * kl_loss
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            ep_recon += recon_loss.item()
            ep_kl += kl_loss.item()
        scheduler.step()
        history["recon"].append(ep_recon / len(loader))
        history["kl"].append(ep_kl / len(loader))
        if ep % 100 == 0: print(f"  ep {ep}/{POLISH_EPOCHS}  recon={history['recon'][-1]:.5f}")

    # PHASE 8 & 9: Save
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(14, 4))
        axes[0].plot(history["recon"]); axes[0].set_title("Recon Loss")
        axes[1].plot(history["kl"]); axes[1].set_title("KL Div")
        plt.savefig(OUT_CURVE); plt.close()
    except Exception: pass
    torch.save({"model_state_dict": model.state_dict(), "omni_dim": OMNI_DIM, "latent_dim": LATENT_DIM, "n_genres": N_GENRES, "genre_emb_dim": GENRE_EMB, "genre2idx": genre2idx, "idx2genre": idx2genre, "vec_dim": vec_dim, "dsp_cols": DSP_COLS, "X_mean": X_mean.tolist(), "X_std": X_std.tolist(), "bpm_mean": bpm_mean, "bpm_std": bpm_std}, OUT_PT)

    # PHASE 10: Demo
    def denorm(vec_norm): return vec_norm.numpy() * X_std + X_mean
    dsp_start = vec_dim
    for genre_name, gid in genre2idx.items():
        for target_bpm in [120.0, 128.0, 135.0]:
            gen = model.generate(genre_id=gid, bpm=target_bpm, bpm_mean=bpm_mean, bpm_std=bpm_std, n=1)
            gen_raw = denorm(gen[0])
            dsp = gen_raw[dsp_start : dsp_start + 11]
            dsp_t = torch.tensor(dsp[:11], dtype=torch.float32).unsqueeze(0).to(device)
            with torch.no_grad():
                dsp_norm = (dsp_t - torch.tensor(X_mean[dsp_start:dsp_start+11]).unsqueeze(0).to(device)) / \
                           torch.tensor(X_std[dsp_start:dsp_start+11]).unsqueeze(0).to(device)
                master_raw = model.mastering_head(dsp_norm).squeeze()
            print(f"Genre: {genre_name} | BPM: {target_bpm} | Gain: {master_raw[0].item():.2f}")

if __name__ == "__main__":
    main()