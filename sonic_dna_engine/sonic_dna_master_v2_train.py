"""
sonic_dna_master_v2_train.py
============================
Pulls 5,908 segments from omni_semantic_baselines LanceDB.
Derives mastering params via build_section_board logic.
Trains student model: DSP features -> [gain_db, ratio, threshold_db].
Exports sonic_dna_master_v2.pt + .onnx
"""
import sys, os, warnings
warnings.filterwarnings("ignore")
try: sys.stdout.reconfigure(encoding="utf-8")
except: pass

import numpy as np
import pandas as pd

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

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import lancedb
import ray

print("=" * 65)
print("  SONIC DNA MASTER v2 -- Label Extract + Train")
print("=" * 65)

LANCEDB_PATH = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
TABLE_NAME   = "omni_semantic_baselines"
OUTPUT_DIR   = r"C:\WEB CASE STUDY\sonic_dna_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

LIMITER_CEILING_DB = -0.3
DSP_COLS = ["rms_db","crest_factor","sub_bass_energy","bass_energy",
            "mid_energy","high_energy","spectral_centroid",
            "spectral_bandwidth","spectral_rolloff","spectral_contrast",
            "zero_crossing_rate"]

# ── PHASE 1: Load LanceDB ───────────────────────────────────────────────────
print("\n[PHASE 1] Loading omni_semantic_baselines...")
db = lancedb.connect(LANCEDB_PATH)
t  = db.open_table(TABLE_NAME)
df = t.to_pandas()
print(f"  Loaded {len(df)} segments from {df['track_name'].nunique()} tracks")

# Convert rms -> rms_db
df["rms_db"] = df["rms"].apply(lambda v: float(20 * np.log10(max(v, 1e-9))) if pd.notna(v) else -60.0)
df = df.dropna(subset=DSP_COLS).reset_index(drop=True)
print(f"  Clean segments: {len(df)}")

# ── PHASE 2: Identify Chris Lake reference segments ─────────────────────────
print("\n[PHASE 2] Building Chris Lake reference space...")
cl_mask = df["track_name"].str.contains("chris lake|somebody|Somebody", case=False, na=False)
df_cl   = df[cl_mask].reset_index(drop=True)
df_other = df[~cl_mask].reset_index(drop=True)

if len(df_cl) == 0:
    # Fall back to Sam Shure or any single artist as reference
    all_tracks = df["track_name"].unique()
    ref_track = all_tracks[0]
    print(f"  No Chris Lake found. Using fallback reference: {ref_track[:60]}")
    df_cl = df[df["track_name"] == ref_track].reset_index(drop=True)
    df_other = df[df["track_name"] != ref_track].reset_index(drop=True)
else:
    print(f"  Chris Lake segments: {len(df_cl)} from {df_cl['track_name'].nunique()} tracks")
    print(f"  Other segments: {len(df_other)}")

X_cl = df_cl[DSP_COLS].values.astype(np.float32)

# ── PHASE 3: Derive mastering labels ────────────────────────────────────────
print("\n[PHASE 3] Deriving mastering params (build_section_board logic)...")

def build_section_board_params(current_rms, current_crest, target_rms, target_crest):
    """Mirrors build_section_board() from upgraded_dynamic_batch_master_v2.py"""
    if current_crest > target_crest * 1.05:
        ratio = float(np.clip(2.0 + (current_crest - target_crest) * 0.75, 1.8, 4.5))
        threshold_db = current_rms - 3.0
    else:
        ratio = 1.0
        threshold_db = 0.0
    gain_db = float(np.clip(target_rms - current_rms, -12.0, 12.0))
    return gain_db, ratio, threshold_db

from scipy.spatial.distance import cdist

X_other = df_other[DSP_COLS].values.astype(np.float32)

# Normalize for distance matching (just RMS+crest for matching, same as mastering script)
MATCH_COLS = ["rms_db","crest_factor","sub_bass_energy","bass_energy","mid_energy","high_energy"]
from sklearn.preprocessing import StandardScaler
scaler_match = StandardScaler()
X_cl_match    = scaler_match.fit_transform(df_cl[MATCH_COLS].values.astype(np.float32))
X_other_match = scaler_match.transform(df_other[MATCH_COLS].values.astype(np.float32))

print(f"  Computing nearest Chris Lake match for {len(df_other)} segments...")
# Batch to avoid OOM on large matrix
BATCH = 500
labels = []
for i in range(0, len(X_other_match), BATCH):
    batch = X_other_match[i:i+BATCH]
    dists = cdist(batch, X_cl_match, metric="euclidean")
    best_idxs = np.argmin(dists, axis=1)
    for j, bidx in enumerate(best_idxs):
        seg_idx = i + j
        current_rms   = float(df_other["rms_db"].iloc[seg_idx])
        current_crest = float(df_other["crest_factor"].iloc[seg_idx])
        target_rms    = float(df_cl["rms_db"].iloc[bidx])
        target_crest  = float(df_cl["crest_factor"].iloc[bidx])
        gain_db, ratio, threshold_db = build_section_board_params(
            current_rms, current_crest, target_rms, target_crest)
        labels.append([gain_db, ratio, threshold_db])
    if (i // BATCH) % 5 == 0:
        print(f"  ... {min(i+BATCH, len(X_other_match))}/{len(X_other_match)}")

labels = np.array(labels, dtype=np.float32)
print(f"  Labels shape: {labels.shape}")
print(f"  gain_db  : min={labels[:,0].min():.2f}  max={labels[:,0].max():.2f}  mean={labels[:,0].mean():.2f}")
print(f"  ratio    : min={labels[:,1].min():.2f}  max={labels[:,1].max():.2f}  mean={labels[:,1].mean():.2f}")
print(f"  threshold: min={labels[:,2].min():.2f}  max={labels[:,2].max():.2f}  mean={labels[:,2].mean():.2f}")

# ── PHASE 4: Train with Ray ──────────────────────────────────────────────────
print("\n[PHASE 4] Training mastering student model via Ray...")

try:
    ray.init(ignore_reinit_error=True, num_cpus=4,
             logging_level="error", log_to_driver=False)
    print("  Ray initialized")
except Exception as e:
    print(f"  Ray: {e}")

@ray.remote
class MasteringTrainer:
    def train(self, X_data, Y_data, epochs=150, lr=1e-3):
        import torch, torch.nn as nn, torch.optim as optim
        import numpy as np
        from torch.utils.data import DataLoader, TensorDataset

        X = torch.tensor(X_data, dtype=torch.float32)
        Y = torch.tensor(Y_data, dtype=torch.float32)

        Xm = X.mean(0); Xs = X.std(0) + 1e-8
        Xn = (X - Xm) / Xs
        Ym = Y.mean(0); Ys = Y.std(0) + 1e-8
        Yn = (Y - Ym) / Ys   # normalize targets too

        in_dim  = Xn.shape[1]
        out_dim = Yn.shape[1]

        class MasteringNet(nn.Module):
            def __init__(self):
                super().__init__()
                self.encoder = nn.Sequential(
                    nn.Linear(in_dim, 128), nn.LayerNorm(128), nn.GELU(),
                    nn.Linear(128, 64),    nn.LayerNorm(64),  nn.GELU(),
                )
                self.sonic_dna = nn.Linear(64, 64)      # Sonic DNA embedding
                self.master_head = nn.Sequential(         # Mastering params
                    nn.Linear(64, 32), nn.GELU(),
                    nn.Linear(32, out_dim)
                )
            def forward(self, x):
                h = self.encoder(x)
                z = self.sonic_dna(h)
                z = z / (z.norm(dim=-1, keepdim=True) + 1e-8)
                params = self.master_head(h)
                return z, params

        model = MasteringNet()
        opt   = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
        sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
        loader = DataLoader(TensorDataset(Xn, Yn), batch_size=64, shuffle=True)

        losses = []
        for ep in range(epochs):
            model.train()
            ep_loss = 0
            for xb, yb in loader:
                opt.zero_grad()
                z, params = model(xb)
                loss = nn.functional.mse_loss(params, yb)
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step()
                ep_loss += loss.item()
            sched.step()
            losses.append(ep_loss / len(loader))

        return {
            "state_dict": {k: v.numpy().tolist() for k, v in model.state_dict().items()},
            "X_mean": Xm.numpy().tolist(), "X_std": Xs.numpy().tolist(),
            "Y_mean": Ym.numpy().tolist(), "Y_std": Ys.numpy().tolist(),
            "in_dim": in_dim, "out_dim": out_dim,
            "losses": losses,
        }

trainer = MasteringTrainer.remote()
import time; t0 = time.time()
result_ref = trainer.train.remote(X_other.tolist(), labels.tolist())
result = ray.get(result_ref)
print(f"  Done in {time.time()-t0:.1f}s  |  Final loss: {result['losses'][-1]:.5f}")

# ── PHASE 5: Rebuild + Export ────────────────────────────────────────────────
print("\n[PHASE 5] Exporting model...")

IN_DIM  = result["in_dim"]
OUT_DIM = result["out_dim"]

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
        return self.master_head(h)   # inference: return mastering params only

model = MasteringNet(IN_DIM, OUT_DIM)
state = {k: torch.tensor(np.array(v)) for k, v in result["state_dict"].items()}
model.load_state_dict(state)
model.eval()

X_mean = torch.tensor(result["X_mean"])
X_std  = torch.tensor(result["X_std"])
Y_mean = torch.tensor(result["Y_mean"])
Y_std  = torch.tensor(result["Y_std"])

pt_path = os.path.join(OUTPUT_DIR, "sonic_dna_master_v2.pt")
torch.save({
    "model_state_dict": model.state_dict(),
    "dsp_cols": DSP_COLS, "in_dim": IN_DIM, "out_dim": OUT_DIM,
    "X_mean": result["X_mean"], "X_std": result["X_std"],
    "Y_mean": result["Y_mean"], "Y_std": result["Y_std"],
    "label_cols": ["gain_db","comp_ratio","threshold_db"],
    "final_loss": result["losses"][-1],
    "n_segments": len(df_other),
}, pt_path)
print(f"  .pt  -> {pt_path}")

try:
    dummy = torch.randn(1, IN_DIM)
    onnx_path = os.path.join(OUTPUT_DIR, "sonic_dna_master_v2.onnx")
    torch.onnx.export(model, dummy, onnx_path,
        input_names=["dsp_features"], output_names=["mastering_params"],
        dynamic_axes={"dsp_features": {0:"batch"}, "mastering_params": {0:"batch"}},
        opset_version=18)
    print(f"  .onnx-> {onnx_path}")
except Exception as e:
    print(f"  ONNX: {e}")

# ── PHASE 6: Quick inference demo ────────────────────────────────────────────
print("\n[PHASE 6] Inference demo on 3 segments...")
model.eval()
sample = torch.tensor(X_other[:3], dtype=torch.float32)
sample_norm = (sample - X_mean) / X_std
with torch.no_grad():
    raw_out = model(sample_norm)
    # Denormalize
    params_out = raw_out * Y_std + Y_mean

for i in range(3):
    name = df_other["track_name"].iloc[i][:45]
    seg  = df_other["segment_name"].iloc[i]
    g, r, th = params_out[i].tolist()
    print(f"  [{i+1}] {name} | {seg}")
    print(f"       gain={g:.2f}dB  ratio={r:.2f}:1  threshold={th:.2f}dB")

print("\n" + "=" * 65)
print("  SONIC DNA MASTER v2 -- COMPLETE")
print("=" * 65)
print(f"  Training segments:  {len(df_other)}")
print(f"  DSP features:       {IN_DIM}")
print(f"  Outputs:            gain_db, comp_ratio, threshold_db")
print(f"  Model params:       {sum(p.numel() for p in model.parameters()):,}")
print(f"  Final loss:         {result['losses'][-1]:.5f}")
print(f"  Weights:            sonic_dna_master_v2.pt")
print(f"  ONNX:               sonic_dna_master_v2.onnx")
print()
print("  INTEGRATION: Replace build_section_board LanceDB lookup in")
print("  upgraded_dynamic_batch_master_v2.py with model forward pass")
print("=" * 65)
ray.shutdown()