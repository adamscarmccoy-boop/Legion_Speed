"""
sonic_dna_master_v3_train.py
============================
Trains the Mastering Neural Network properly.
Instead of using mastered commercial tracks for input (which confused the model),
we pull UNMASTERED stems/loops from web_intel_sonicdb.duckdb (sonic_dna table)
and map them against MASTERED Chris Lake baselines (omni_semantic_baselines)
to derive the (Gain, Ratio, Threshold) training labels.
"""
import sys, os, warnings
warnings.filterwarnings("ignore")
try: sys.stdout.reconfigure(encoding="utf-8")
except: pass

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import lancedb
import duckdb
from scipy.spatial.distance import cdist
from sklearn.preprocessing import StandardScaler

print("=" * 70)
print("  SONIC DNA MASTER v3 -- UNMASTERED -> MASTERED TRAINING")
print("=" * 70)

OUTPUT_DIR = r"C:\WEB CASE STUDY\sonic_dna_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DSP_COLS = ["rms_db","crest_factor","sub_bass_energy","bass_energy",
            "mid_energy","high_energy","spectral_centroid",
            "spectral_bandwidth","spectral_rolloff","spectral_contrast",
            "zero_crossing_rate"]

# ── 1. Load MASTERED Chris Lake references ───────────────────────────────────
print("\n[PHASE 1] Loading MASTERED baselines from LanceDB...")
db_lance = lancedb.connect(r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag")
df_lance = db_lance.open_table("omni_semantic_baselines").to_pandas()
df_lance["rms_db"] = df_lance["rms"].apply(lambda v: float(20 * np.log10(max(v, 1e-9))) if pd.notna(v) else -60.0)
df_lance = df_lance.dropna(subset=DSP_COLS).reset_index(drop=True)

cl_mask = df_lance["track_name"].str.contains("chris lake|somebody|Somebody", case=False, na=False)
df_cl = df_lance[cl_mask].reset_index(drop=True)
if len(df_cl) == 0:
    print("Warning: No Chris Lake found, using all LanceDB rows.")
    df_cl = df_lance

print(f"  Chris Lake Mastered segments: {len(df_cl)}")

# ── 2. Load UNMASTERED Splice loops ──────────────────────────────────────────
print("\n[PHASE 2] Loading UNMASTERED stems from DuckDB...")
conn = duckdb.connect(r"C:\WEB CASE STUDY\web_intel_sonicdb.duckdb", read_only=True)
df_unm = conn.execute("SELECT * FROM sonic_dna").fetchdf()
conn.close()

# Rename zcr to zero_crossing_rate to match DSP_COLS
if "zcr" in df_unm.columns and "zero_crossing_rate" not in df_unm.columns:
    df_unm = df_unm.rename(columns={"zcr": "zero_crossing_rate"})

df_unm = df_unm.dropna(subset=DSP_COLS).reset_index(drop=True)
print(f"  Unmastered stems/loops: {len(df_unm)}")

# ── 3. Map Unmastered to Mastered (Generate Labels) ──────────────────────────
print("\n[PHASE 3] Generating training labels via DSP distance...")

def build_section_board_params(current_rms, current_crest, target_rms, target_crest):
    if current_crest > target_crest * 1.05:
        ratio = float(np.clip(2.0 + (current_crest - target_crest) * 0.75, 1.8, 4.5))
        threshold_db = current_rms - 3.0
    else:
        ratio = 1.0
        threshold_db = 0.0
    gain_db = float(np.clip(target_rms - current_rms, -12.0, 12.0))
    return gain_db, ratio, threshold_db

MATCH_COLS = ["rms_db","crest_factor","sub_bass_energy","bass_energy","mid_energy","high_energy"]

scaler_match = StandardScaler()
X_cl_match  = scaler_match.fit_transform(df_cl[MATCH_COLS].values.astype(np.float32))
X_unm_match = scaler_match.transform(df_unm[MATCH_COLS].values.astype(np.float32))

labels = []
dists = cdist(X_unm_match, X_cl_match, metric="euclidean")
best_idxs = np.argmin(dists, axis=1)

for i, bidx in enumerate(best_idxs):
    current_rms   = float(df_unm["rms_db"].iloc[i])
    current_crest = float(df_unm["crest_factor"].iloc[i])
    target_rms    = float(df_cl["rms_db"].iloc[bidx])
    target_crest  = float(df_cl["crest_factor"].iloc[bidx])
    
    gain_db, ratio, threshold_db = build_section_board_params(
        current_rms, current_crest, target_rms, target_crest)
    labels.append([gain_db, ratio, threshold_db])

labels = np.array(labels, dtype=np.float32)
X_unm_full = df_unm[DSP_COLS].values.astype(np.float32)

print(f"  gain_db  : min={labels[:,0].min():.2f}  max={labels[:,0].max():.2f}  mean={labels[:,0].mean():.2f}")
print(f"  ratio    : min={labels[:,1].min():.2f}  max={labels[:,1].max():.2f}  mean={labels[:,1].mean():.2f}")
print(f"  threshold: min={labels[:,2].min():.2f}  max={labels[:,2].max():.2f}  mean={labels[:,2].mean():.2f}")

# ── 4. Train Neural Network ──────────────────────────────────────────────────
print("\n[PHASE 4] Training Student Network (No Ray, pure PyTorch)...")

X = torch.tensor(X_unm_full, dtype=torch.float32)
Y = torch.tensor(labels, dtype=torch.float32)

X_mean = X.mean(0); X_std = X.std(0) + 1e-8
Y_mean = Y.mean(0); Y_std = Y.std(0) + 1e-8
Xn = (X - X_mean) / X_std
Yn = (Y - Y_mean) / Y_std

in_dim  = X.shape[1]
out_dim = Y.shape[1]

class MasteringNet(nn.Module):
    def __init__(self, in_dim, out_dim):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(in_dim, 128), nn.LayerNorm(128), nn.GELU(),
            nn.Linear(128, 64),    nn.LayerNorm(64),  nn.GELU(),
        )
        self.sonic_dna   = nn.Linear(64, 64)
        self.master_head = nn.Sequential(nn.Linear(64, 32), nn.GELU(), nn.Linear(32, out_dim))
    def forward(self, x):
        h = self.encoder(x)
        z = self.sonic_dna(h)
        z = z / (z.norm(dim=-1, keepdim=True) + 1e-8)
        return self.master_head(h)

model = MasteringNet(in_dim, out_dim)
opt   = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=200)
loader = DataLoader(TensorDataset(Xn, Yn), batch_size=32, shuffle=True)

model.train()
for ep in range(200):
    ep_loss = 0
    for xb, yb in loader:
        opt.zero_grad()
        params = model(xb)
        loss = nn.functional.mse_loss(params, yb)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        ep_loss += loss.item()
    sched.step()
    if (ep+1) % 50 == 0:
        print(f"  Epoch {ep+1}/200  Loss: {ep_loss/len(loader):.5f}")

# ── 5. Export ────────────────────────────────────────────────────────────────
pt_path = os.path.join(OUTPUT_DIR, "sonic_dna_master_v3.pt")
torch.save({
    "model_state_dict": model.state_dict(),
    "dsp_cols": DSP_COLS, "in_dim": in_dim, "out_dim": out_dim,
    "X_mean": X_mean.numpy().tolist(), "X_std": X_std.numpy().tolist(),
    "Y_mean": Y_mean.numpy().tolist(), "Y_std": Y_std.numpy().tolist(),
    "label_cols": ["gain_db","comp_ratio","threshold_db"],
}, pt_path)
print(f"\n[OK] Model exported to {pt_path}")
