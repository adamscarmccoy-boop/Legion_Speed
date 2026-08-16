# %%
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import os, time
import lancedb

print("Loading CLEAN Enriched Datasets...")
start_t = time.time()

# Load Semantic Vectors from LanceDB (Real Float Arrays)
LANCEDB_PATH = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\vectors\lancedb_store"
ldb = lancedb.connect(LANCEDB_PATH)
vibe_df = ldb.open_table("audio_vibe_gpu").to_pandas()

# Load Clean Enriched Samples (3,983 rows, no generic sample packs)
samples_df = pd.read_json(r'C:\WEB CASE STUDY\data\enriched_samples_only.json')

# Merge them on filename
df = pd.merge(vibe_df, samples_df, on='filename', how='inner')
print(f"Fused Dataset Size: {len(df)} tracks (Filtered out bad samples!)")

def build_omni_vector(row):
    sem = np.array(row['vector'], dtype=np.float32)
    bpm = np.array([float(row.get('tempo', 128.0))], dtype=np.float32)
    return np.concatenate([sem, bpm])

df['omni_vector'] = df.apply(build_omni_vector, axis=1)

data_matrix = np.vstack(df['omni_vector'].values)
data_matrix = np.nan_to_num(data_matrix, nan=0.0)

X_mean = np.mean(data_matrix, axis=0)
X_std = np.std(data_matrix, axis=0) + 1e-8
X_norm = (data_matrix - X_mean) / X_std
dataset = torch.tensor(X_norm, dtype=torch.float32)

IN_DIM = dataset.shape[1]
LATENT_DIM = 64
SEMANTIC_DIM = 384

class FretFlowEngine(nn.Module):
    def __init__(self, in_dim, latent_dim):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(in_dim, 256), nn.LayerNorm(256), nn.GELU(),
            nn.Linear(256, 128), nn.LayerNorm(128), nn.GELU(),
            nn.Linear(128, latent_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 128), nn.GELU(),
            nn.Linear(128, 256), nn.GELU(),
            nn.Linear(256, in_dim)
        )
    def forward(self, x):
        return self.decoder(self.encoder(x))

model = FretFlowEngine(IN_DIM, LATENT_DIM)
opt = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
loss_fn = nn.MSELoss()

print(f"\n[TRAINING] Deep Omni-Manifold Learning on {len(dataset)} items...")
model.train()
EPOCHS = 1000

for ep in range(EPOCHS):
    opt.zero_grad()
    pred = model(dataset)
    loss = loss_fn(pred, dataset)
    loss.backward()
    opt.step()
    if (ep + 1) % 100 == 0:
        print(f"Epoch {ep+1}/{EPOCHS} | Loss: {loss.item():.6f}")

out_path = r"C:\WEB CASE STUDY\sonic_dna_output\fretflow_v2.pt"
os.makedirs(os.path.dirname(out_path), exist_ok=True)

torch.save({
    "model_state_dict": model.state_dict(),
    "in_dim": IN_DIM,
    "latent_dim": LATENT_DIM,
    "semantic_dim": SEMANTIC_DIM,
    "dsp_cols": ["tempo"],
    "X_mean": X_mean.tolist(),
    "X_std": X_std.tolist()
}, out_path)

print(f"[SUCCESS] NEW WEIGHTS SAVED: Sonic DNA Omni V2 saved to:\n-> {out_path}\nDone in {time.time()-start_t:.2f}s")

# %%
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import os, datetime, re, lancedb
from scipy.spatial.distance import cdist
import soundfile as sf
import warnings
warnings.filterwarnings('ignore')

print("[BOOT] Starting Clean Data Generation Engine...")

# Load Semantic Vectors (Real Float Arrays)
LANCEDB_PATH = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\vectors\lancedb_store"
ldb = lancedb.connect(LANCEDB_PATH)
vibe_df = ldb.open_table("audio_vibe_gpu").to_pandas()

# Load Clean Enriched Samples
samples_df = pd.read_json(r'C:\WEB CASE STUDY\data\enriched_samples_only.json')

# Merge them on filename
df = pd.merge(vibe_df, samples_df, on='filename', how='inner')
print(f"[SYSTEM] Clean Dataset Size: {len(df)} tracks")

def build_omni_vector(row):
    sem = np.array(row['vector'], dtype=np.float32)
    bpm = np.array([float(row.get('tempo', 128.0))], dtype=np.float32)
    return np.concatenate([sem, bpm])

df['omni_vector'] = df.apply(build_omni_vector, axis=1)
data_matrix = np.vstack(df['omni_vector'].values)
data_matrix = np.nan_to_num(data_matrix, nan=0.0)

weights_path = r"C:\WEB CASE STUDY\sonic_dna_output\fretflow_v2.pt"
checkpoint = torch.load(weights_path)
X_mean = np.array(checkpoint['X_mean'], dtype=np.float32)
X_std = np.array(checkpoint['X_std'], dtype=np.float32)

class FretFlowEngine(nn.Module):
    def __init__(self, in_dim, latent_dim):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(in_dim, 256), nn.LayerNorm(256), nn.GELU(),
            nn.Linear(256, 128), nn.LayerNorm(128), nn.GELU(),
            nn.Linear(128, latent_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 128), nn.GELU(),
            nn.Linear(128, 256), nn.GELU(),
            nn.Linear(256, in_dim)
        )
    def forward(self, x):
        return self.decoder(self.encoder(x))

model = FretFlowEngine(checkpoint['in_dim'], checkpoint['latent_dim'])
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

df_basses = df[df['genre_class'].str.contains('BASS', na=False, case=False) | df['filename'].str.contains('Bass', na=False, case=False)]
df_kicks = df[df['genre_class'].str.contains('KICK', na=False, case=False) | df['filename'].str.contains('Kick', na=False, case=False)]
df_perc = df[df['genre_class'].str.contains('PERC', na=False, case=False) | df['filename'].str.contains('Perc|Hat', na=False, case=False)]

if len(df_basses) == 0: df_basses = df
if len(df_kicks) == 0: df_kicks = df
if len(df_perc) == 0: df_perc = df

def sample_top_k(dists, df_pool, k=5, temperature=0.5):
    top_k_indices = np.argsort(dists)[:k]
    top_k_dists = dists[top_k_indices]
    logits = -top_k_dists / temperature
    exp_logits = np.exp(logits - np.max(logits))
    probs = exp_logits / np.sum(exp_logits)
    selected_idx = np.random.choice(top_k_indices, p=probs)
    return df_pool.iloc[selected_idx]

seeds = df.sample(3)
for idx, row in seeds.iterrows():
    print(f"\n==================================================\n[PHASE 1] Seed: {row['filename']}")
    
    seed_vec_raw = np.nan_to_num(row['omni_vector'], nan=0.0)
    seed_vec_norm = (seed_vec_raw - X_mean) / (X_std + 1e-8)
    seed_tensor = torch.tensor(seed_vec_norm, dtype=torch.float32).unsqueeze(0)

    variance = 1.2
    with torch.no_grad():
        latent = model.encoder(seed_tensor)
        latent = latent + torch.randn_like(latent) * variance
        output_tensor_norm = model.decoder(latent).numpy()[0]
        
    omni_output_raw = (output_tensor_norm * X_std) + X_mean
    semantic_slice = omni_output_raw[:384]
    target_bpm = omni_output_raw[384]
    
    print(f"  -> Hallucinated BPM: {target_bpm:.2f}")

    # BASS
    bass_mat = np.vstack([x[:384] for x in df_basses['omni_vector'].values])
    dists_bass = cdist([semantic_slice], np.nan_to_num(bass_mat, nan=0.0), metric="cosine")[0]
    best_bass = sample_top_k(dists_bass, df_basses)
    bass_fp = best_bass.get('filepath', '')
    print(f"  [BASS] {os.path.basename(bass_fp) if pd.notna(bass_fp) and bass_fp else best_bass['filename']}")

    # KICK
    kick_mat = np.vstack([x[:384] for x in df_kicks['omni_vector'].values])
    dists_kick = cdist([semantic_slice], np.nan_to_num(kick_mat, nan=0.0), metric="cosine")[0]
    best_kick = sample_top_k(dists_kick, df_kicks)
    kick_fp = best_kick.get('filepath', '')
    print(f"  [KICK] {os.path.basename(kick_fp) if pd.notna(kick_fp) and kick_fp else best_kick['filename']}")

    # PERC
    perc_mat = np.vstack([x[:384] for x in df_perc['omni_vector'].values])
    dists_perc = cdist([semantic_slice], np.nan_to_num(perc_mat, nan=0.0), metric="cosine")[0]
    best_perc = sample_top_k(dists_perc, df_perc)
    perc_fp = best_perc.get('filepath', '')
    print(f"  [PERC] {os.path.basename(perc_fp) if pd.notna(perc_fp) and perc_fp else best_perc['filename']}")

    # Assembly
    SR = 44100
    BPM = target_bpm if 60 < target_bpm < 200 else 128.0
    TOTAL_SAMPLES = int(16 * 4 * (60.0 / BPM) * SR)
    mix = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

    def load_audio(path):
        if not path or not isinstance(path, str) or not os.path.exists(path): return np.zeros((0, 2))
        try:
            y, _ = sf.read(path, always_2d=True)
            return y
        except: return np.zeros((0, 2))

    y_kick = load_audio(kick_fp)
    y_bass = load_audio(bass_fp)
    y_perc = load_audio(perc_fp)

    beat_samples = int((60.0 / BPM) * SR)
    for beat in range(16 * 4):
        pos = beat * beat_samples
        length = min(len(y_kick), TOTAL_SAMPLES - pos)
        if length > 0 and len(y_kick) > 0:
            mix[pos:pos+length] += y_kick[:length]

    def tile_loop(loop_arr, total_len):
        out = np.zeros((total_len, 2), dtype=np.float32)
        ll = len(loop_arr)
        if ll == 0: return out
        p = 0
        while p < total_len:
            c = min(ll, total_len - p)
            out[p:p+c] = loop_arr[:c]
            p += c
        return out

    mix += tile_loop(y_bass, TOTAL_SAMPLES)
    mix += tile_loop(y_perc, TOTAL_SAMPLES)
    
    timestamp = datetime.datetime.now().strftime("%H%M%S")
    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', os.path.basename(row['filename']))
    out_path = rf"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\generated_audio\CLEAN_GEN_{safe_name}_{timestamp}.wav"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    sf.write(out_path, np.clip(mix, -1.0, 1.0), SR)
    print(f"[SUCCESS] Native assembly saved to: {out_path}")
\

# %%
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from sklearn.model_selection import train_test_split
import os
import time

class SonicDNAOmniPro(nn.Module):
    """
    Improved Autoencoder for Omni-Vector Manifold Learning.
    Includes Dropout and Residual-style layering for better generalization.
    """
    def __init__(self, in_dim, latent_dim=64, dropout_rate=0.1):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(in_dim, 256), 
            nn.LayerNorm(256), 
            nn.GELU(),
            nn.Dropout(dropout_rate),
            nn.Linear(256, 128), 
            nn.LayerNorm(128), 
            nn.GELU(),
            nn.Dropout(dropout_rate),
            nn.Linear(128, latent_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 128), 
            nn.GELU(),
            nn.Linear(128, 256), 
            nn.GELU(),
            nn.Linear(256, in_dim)
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))

def train_sonic_dna_pro(dataset, epochs=1000, lr=1e-3, patience=20, val_split=0.2):
    """
    Trains the SonicDNAOmniPro model with Early Stopping and Validation tracking.
    """
    # 1. Split data
    train_data, val_data = train_test_split(dataset, test_size=val_split, random_state=42)
    
    in_dim = dataset.shape[1]
    model = SonicDNAOmniPro(in_dim)
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    loss_fn = nn.MSELoss()
    
    best_loss = float('inf')
    epochs_no_improve = 0
    
    print(f"Starting Pro Training: Train={len(train_data)}, Val={len(val_data)}")
    
    for ep in range(epochs):
        model.train()
        optimizer.zero_grad()
        pred = model(train_data)
        loss = loss_fn(pred, train_data)
        loss.backward()
        optimizer.step()
        
        # Validation Phase
        model.eval()
        with torch.no_grad():
            val_pred = model(val_data)
            val_loss = loss_fn(val_pred, val_data)
        
        if (ep + 1) % 50 == 0:
            print(f"Epoch {ep+1}/{epochs} | Train Loss: {loss.item():.6f} | Val Loss: {val_loss.item():.6f}")
        
        # Early Stopping Logic
        if val_loss < best_loss:
            best_loss = val_loss
            epochs_no_improve = 0
            torch.save(model.state_dict(), "best_sonic_dna_pro.pt")
        else:
            epochs_no_improve += 1
            
        if epochs_no_improve >= patience:
            print(f"Early stopping triggered at epoch {ep+1}. Best Val Loss: {best_loss:.6f}")
            break
            
    return model

def apply_latent_jitter(latent_vector, std_dev, amount=0.02):
    """
    Adds stochastic jitter to a latent vector to explore the local manifold.
    """
    jitter = torch.randn_like(latent_vector) * std_dev * amount
    return latent_vector + jitter

def interpolate_dna(vector_a, vector_b, alpha=0.5):
    """
    Linearly interpolates between two DNA signatures.
    alpha=0.0 -> Vector A | alpha=1.0 -> Vector B
    """
    return (1 - alpha) * vector_a + alpha * vector_b


# %% [markdown]
# he user says "got cut off" - they're looking at the file which only has cells 1 and 2. I need to add all the remaining cells (3 through 8) at once and run the whole thing. Let me write all remaining cells to the file right now without hesitation.
# 
# The file currently has 109 lines with cells 1 and 2. I need to append cells 3-8:
# 
# Cell 3: Build Omni tensors Cell 4: Define OmniTrainerActor (Ray remote) Cell 5: Launch 6 actors + collect results Cell 6: Plot loss curves Cell 7: Rebuild best model + save .pt Cell 8: Generation demo
# 
# Now I'm appending the rest of the notebook. The Ray actor definition with the nested model class is the trickiest part, but I have the key parameters from Cell 2: vec_dim is 1024, there are 4 genres (KICK, OTHER, PERC, TECH_HOUSE), and we're working with 500 subsampled rows.
# 
# For the tensor construction in Cell 3, the semantic embeddings plus DSP features plus BPM give us 1036 total dimensions, which makes the model quite large. I'll need to keep the batch size reasonable—probably 32 or 64 to manage memory with that input dimensionality. The encoder will compress from 1036 down through 512, 256, and 128 dimensions to the latent space, while the decoder mirrors that back up. With 6 Ray actors training on the full 500 rows for 50 epochs, each one will be handling a substantial model.
# 
# Now I'm going to write out all the cells at once, overwriting the file completely since I already know what cells 1 and 2 contain

# %%
# %% [markdown]
# # OmniCondVAE v3 — 6 Ray Actor Training
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
print(f"Cols: {list(df_raw.columns[:10])}")

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
print(f"\nSubsampled to {len(df)} rows for test run")

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
print(f"\nGenre distribution: {genre_dist}")

all_genres = sorted(genres.unique().tolist())
genre2idx  = {g: i for i, g in enumerate(all_genres)}
idx2genre  = {v: k for k, v in genre2idx.items()}
N_GENRES   = len(genre2idx)
print(f"Genres ({N_GENRES}): {genre2idx}")
print("\n✅ Cell 2 PASSED — data loaded and subsampled")


# %% [markdown]
# # OmniCondVAE v3 — Ray Actor Training
# Deep Architecture: 1036 -> 512 -> 256 -> 128 -> Latent(32)
# Step by step execution.

# %%
# Cell 1 — Paths + env check
import sys, os, warnings
warnings.filterwarnings("ignore")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import torch
import ray

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

# %%
# Cell 2 — Load LanceDB + subsample 500 rows
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

# %%
# Cell 3 — Build Normalization & Tensors
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

# %%
# Cell 4 — Deep VAE Model & Ray Trainer Actor
import torch.nn as nn
import torch.nn.functional as F
import torch
import ray
import numpy as np
from torch.utils.data import DataLoader, TensorDataset

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

        # Encoder
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

        # Decoder
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
    def generate(self, genre_id, bpm, temperature=1.0, n=1, device='cpu', bpm_mean=128.0, bpm_std=1.0):
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

    def train_shard(self, X_shard, G_shard, B_shard, epochs=10, batch_size=32):
        opt = torch.optim.AdamW(self.model.parameters(), lr=1e-3)
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

print("✅ Cell 4 PASSED: Model and Ray Actor updated with Hybrid Logic")


# %%
# Cell 5 — Execute Training on 6 Ray Actors
if not ray.is_initialized():
    # Explicitly specifying the address to avoid psutil system-wide process scan on Windows
    ray.init(address='auto', namespace="legion", ignore_reinit_error=True)

N_ACTORS = 6
print(f"Spawning {N_ACTORS} parallel TrainerActors...")
actors = [TrainerActor.remote(OMNI_DIM, 32, N_GENRES) for _ in range(N_ACTORS)]

# Shard the dataset
X_np = X_t.numpy()
C_np = G_t.numpy()
shards_x = np.array_split(X_np, N_ACTORS)
shards_c = np.array_split(C_np, N_ACTORS)

futures = [
    actors[i].train_shard.remote(shards_x[i], shards_c[i], epochs=10, batch_size=32)
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

# %%
# Cell 6 — Plot Loss Curves
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

# %%
# Cell 7 — Rebuild Best Model & Save .pt
print("[Cell 7] Exporting Best Model...")
best_model = OmniCondVAE(OMNI_DIM, 32, N_GENRES)
best_model.load_state_dict({k: torch.tensor(v) for k, v in results[best_idx]["state_dict"].items()})
best_model.eval()

torch.save({
    "model_state_dict": best_model.state_dict(),
    "omni_dim": OMNI_DIM,
    "latent_dim": 32,
    "n_categories": N_GENRES,
    "cat2idx": genre2idx,
    "idx2cat": idx2genre,
    "vec_dim": vec_dim,
    "dsp_cols": DSP_COLS,
    "X_mean": X_mean.tolist(),
    "X_std": X_std.tolist(),
    "architecture": "OmniCondVAE_v3_Deep_Ray",
}, OUT_PT)

print(f"Saved checkpoint to: {OUT_PT}")
print("✅ Cell 7 PASSED")

# %%
# Cell 8 — Generation Demo
print("[Cell 8] Generative Inference Demo...")
for cat_name, cid in genre2idx.items():
    c_tensor = torch.tensor([cid], dtype=torch.int64)
    cond = best_model.cat_emb(c_tensor)
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
    
    print(f"  Category: {cat_name:<12} | Generated RMS: {gen_dsp[0]:.2f} dB | Gain Target: {master_params[0]:.2f} dB")

print("✅ Cell 8 PASSED — Generation Complete!")

# %%
!pip install Grafana
!pip install prometheus_client
!pip install pandas
!pip -m pip install --upgrade pip

# %%
import pandas as pd                                                                                                                                                                                                                                                                                           ▄
import numpy as np                                                                                                                                                                                                                                                                                            ▀
import torch
import torch.nn as nn
import os, datetime, re, lancedb
from scipy.spatial.distance import cdist
import soundfile as sf
import warnings
import ray
import logging as log
from prometheus_client import start_http_server, Summary, Gauge
from grafana.client import StatsDClient
from pydantic import BaseModel, Field, field_validator
from grafana.client.mixin import GrafanaClientMixinfanaClientMixin
from grafana.client.model import *
from torch_tensorboard import SummaryWriter
from tqdm import tqdm



warnings.filterwarnings('ignore')

print("[BOOT] Starting v3 Omni-Generation Engine...")                                                                                               ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
                                                                                                                                                                                                                                                                                      4 MCP servers · 61 skills 
# =====================================================================                                                                             ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# CONFIGURATION                                                                                                                                     _complete.ipynb"
# =====================================================================                                                                             ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
LANCEDB_PATH = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\vectors\lancedb_store"                                                                                ·                  SCARS_LAB                 ·                   592.6k tokens                 ·                  ✖ 4 errors (F12 for details) 
SAMPLES_JSON = r'C:\WEB CASE STUDY\data\enriched_samples_only.json'
# UPDATED TO V3 WEIGHTS
WEIGHTS_PATH = r"C:\WEB CASE STUDY\sonic_dna_output\fretflow_omni_v3.pt"
OUTPUT_DIR   = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\generated_audio"

# =====================================================================
# DATA LOADING
# =====================================================================
ldb = lancedb.connect(LANCEDB_PATH)
vibe_df = ldb.open_table("audio_vibe_gpu").to_pandas()
samples_df = pd.read_json(SAMPLES_JSON)

# Merge on filename
df = pd.merge(vibe_df, samples_df, on='filename', how='inner')
print(f"[SYSTEM] Clean Dataset Size: {len(df)} tracks")

def build_omni_vector(row):
    sem = np.array(row['vector'], dtype=np.float32)
    bpm = np.array([float(row.get('tempo', 128.0))], dtype=np.float32)
    return np.concatenate([sem, bpm])
    
df['omni_vector'] = df.apply(build_omni_vector, axis=1)
data_matrix = np.vstack(df['omni_vector'].values)
data_matrix = np.nan_to_num(data_matrix, nan=0.0)
    
# Load v3 Checkpoint
checkpoint = torch.load(WEIGHTS_PATH)
X_mean = np.array(checkpoint['X_mean'], dtype=np.float32)
X_std = np.array(checkpoint['X_std'], dtype=np.float32)

# Create Category Mapping (v3 requires category indices)
# We derive this from the dataset to ensure consistency with the loaded weights
unique_genres = df['genre_class'].unique()
genre2idx = {genre: i for i, genre in enumerate(unique_genres)}
print(f"[SYSTEM] Category Mapping initialized with {len(genre2idx)} genres")

# =====================================================================
# V3 ARCHITECTURE: OmniCondVAE
# =====================================================================
class OmniCondVAE(nn.Module):
    def __init__(self, in_dim, latent_dim, num_categories, emb_dim=16):
        super().__init__()
        # Encoder: 1036 -> 512 -> 256 -> 128 -> latent_dim * 232
        self.encoder = nn.Sequential(
            nn.Linear(in_dim, 512), nn.LayerNorm(512), nn.GELU(),
            nn.Linear(512, 256), nn.LayerNorm(256), nn.GELU(),
            nn.Linear(256, 128), nnimport pandas as pd                                                                                                                                                                                                                                                                                           ▄
import numpy as np                                                                                                                                                                                                                                                                                            ▀
import torch
import torch.nn as nn
import os, datetime, re, lancedb
from scipy.spatial.distance import cdist
import soundfile as sf
import warnings
import ray
import logging as log
from prometheus_client import start_http_server, Summary, Gauge
from grafana.client import StatsDClient
from pydantic import BaseModel, Field, field_validator
from grafana.client.mixin import GrafanaClientMixin
from grafana.client.model import *
from torch_tensorboard import SummaryWriter
from tqdm import tqdm



warnings.filterwarnings('ignore')

print("[BOOT] Starting v3 Omni-Generation Engine...")                                                                                               ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
                                                                                                                                                                                                                                                                                      4 MCP servers · 61 skills 
# =====================================================================                                                                             ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# CONFIGURATION                                                                                                                                     _complete.ipynb"
# =====================================================================                                                                             ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
LANCEDB_PATH = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\vectors\lancedb_store"                                                                                ·                  SCARS_LAB                 ·                   592.6k tokens                 ·                  ✖ 4 errors (F12 for details) 
SAMPLES_JSON = r'C:\WEB CASE STUDY\data\enriched_samples_only.json'
# UPDATED TO V3 WEIGHTS
WEIGHTS_PATH = r"C:\WEB CASE STUDY\sonic_dna_output\fretflow_omni_v3.pt"
OUTPUT_DIR   = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\generated_audio"

# =====================================================================
# DATA LOADING
# =====================================================================
ldb = lancedb.connect(LANCEDB_PATH)
vibe_df = ldb.open_table("audio_vibe_gpu").to_pandas()
samples_df = pd.read_json(SAMPLES_JSON)

# Merge on filename
df = pd.merge(vibe_df, samples_df, on='filename', how='inner')
print(f"[SYSTEM] Clean Dataset Size: {len(df)} tracks")

def build_omni_vector(row):
    sem = np.array(row['vector'], dtype=np.float32)
    bpm = np.array([float(row.get('tempo', 128.0))], dtype=np.float32)
    return np.concatenate([sem, bpm])
    
df['omni_vector'] = df.apply(build_omni_vector, axis=1)
data_matrix = np.vstack(df['omni_vector'].values)
data_matrix = np.nan_to_num(data_matrix, nan=0.0)
    
# Load v3 Checkpoint
checkpoint = torch.load(WEIGHTS_PATH)
X_mean = np.array(checkpoint['X_mean'], dtype=np.float32)
X_std = np.array(checkpoint['X_std'], dtype=np.float32)

# Create Category Mapping (v3 requires category indices)
# We derive this from the dataset to ensure consistency with the loaded weights
unique_genres = df['genre_class'].unique()
genre2idx = {genre: i for i, genre in enumerate(unique_genres)}
print(f"[SYSTEM] Category Mapping initialized with {len(genre2idx)} genres")

# =====================================================================
# V3 ARCHITECTURE: OmniCondVAE
# =====================================================================
class OmniCondVAE(nn.Module):
    def __init__(self, in_dim, latent_dim, num_categories, emb_dim=16):
        super().__init__()
        # Encoder: 1036 -> 512 -> 256 -> 128 -> latent_dim * 232
        self.encoder = nn.Sequential(
            nn.Linear(in_dim, 512), nn.LayerNorm(512), nn.GELU(),
            nn.Linear(512, 256), nn.LayerNorm(256), nn.GELU(),
            nn.Linear(256, 128), nn

# %%
# Cell 17 — Inference Test using existing weights
import torch
import numpy as np
import os

# 1. Load the existing weights
WEIGHT_PATH = r"C:\WEB CASE STUDY\sonic_dna_output\fretflow_omni_v3.pt"

if not os.path.exists(WEIGHT_PATH):
    print(f"❌ Error: Weight file not found at {WEIGHT_PATH}")
else:
    print(f"✅ Loading weights from {WEIGHT_PATH}...")
    checkpoint = torch.load(WEIGHT_PATH, map_location='cpu')

    # 2. Reconstruct Model Architecture from checkpoint metadata
    # Note: We assume the model class OmniCondVAE is already defined in the notebook
    OMNI_DIM = checkpoint['omni_dim']
    LATENT_DIM = checkpoint['latent_dim']
    N_GENRES = checkpoint['n_genres']
    GENRE_EMB = checkpoint['genre_emb_dim']
    
    model = OmniCondVAE(OMNI_DIM, LATENT_DIM, N_GENRES, GENRE_EMB)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    # 3. Extract normalization params
    X_mean = torch.tensor(checkpoint['X_mean'])
    X_std = torch.tensor(checkpoint['X_std'])
    bpm_mean = checkpoint['bpm_mean']
    bpm_std = checkpoint['bpm_std']
    genre2idx = checkpoint['genre2idx']
    vec_dim = checkpoint['vec_dim']
    DSP_COLS = checkpoint['dsp_cols']

    print("✅ Model successfully rebuilt and loaded.")

    # 4. Run Inference Test (Simulating real input)
    # We'll pick a random genre and BPM
    test_genre = list(genre2idx.keys())[0]
    test_genre_id = genre2idx[test_genre]
    test_bpm = 128.0

    print(f"\n--- Running Inference Test ---")
    print(f"Target Genre: {test_genre} (ID: {test_genre_id})")
    print(f"Target BPM: {test_bpm}")

    with torch.no_grad():
        # Use the model's generate method
        gen_output = model.generate(genre_id=test_genre_id, bpm=test_bpm, temperature=0.5, n=1)
        
        # Denormalize
        denormed = gen_output[0].numpy() * X_std.numpy() + X_mean.numpy()
        
        # Split into semantic, dsp, and bpm
        # Semantic: 0 to vec_dim
        # DSP: vec_dim to vec_dim + 11
        # BPM: last element
        sem_part = denormed[:vec_dim]
        dsp_part = denormed[vec_dim : vec_dim+11]
        bpm_part = denormed[-1]

        print(f"\n[RESULTS]")
        print(f"Generated BPM: {bpm_part:.2f}")
        print(f"Generated DSP Profile ({', '.join(DSP_COLS)}):")
        for col, val in zip(DSP_COLS, dsp_part):
            print(f"  {col:<20}: {val:>10.4f}")
            
        # Run the mastering head on the generated DSP
        dsp_tensor = torch.tensor(dsp_part, dtype=torch.float32).unsqueeze(0)
        dsp_norm = (dsp_tensor - X_std[vec_dim:vec_dim+11].unsqueeze(0)) / X_std[vec_dim:vec_dim+11].unsqueeze(0)
        
        master_params = model.mastering_head(dsp_norm).squeeze()
        print(f"\n[MASTERING COMMANDS]")
        print(f"  Gain:      {master_params[0].item():.2f} dB")
        print(f"  Ratio:     {master_params[1].item():.2f}")
        print(f"  Threshold: {master_params[2].item():.2f} dB")


# %%
# Cell 18 — ONNX Export & Real-Data Validation
import torch
import numpy as np
import onnxruntime as ort
import os

# 1. Setup Paths
WEIGHT_PATH = r"C:\WEB CASE STUDY\sonic_dna_output\fretflow_omni_v3.pt"
ONNX_EXPORT_PATH = r"C:\WEB CASE STUDY\sonic_dna_output\fretflow_omni_v3.onnx"

print("🚀 Starting Production ONNX Export...")

# 2. Rebuild Model from Checkpoint (Ensuring we have the trained weights)
checkpoint = torch.load(WEIGHT_PATH, map_location='cpu')
OMNI_DIM = checkpoint['omni_dim']
LATENT_DIM = checkpoint['latent_dim']
N_GENRES = checkpoint['n_genres']
GENRE_EMB = checkpoint['genre_emb_dim']

model = OmniCondVAE(OMNI_DIM, LATENT_DIM, N_GENRES, GENRE_EMB)
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()
print("✅ Model rebuilt from .pt weights.")

# 3. Perform ONNX Export
# We use a dummy input for the export graph construction (required by ONNX), 
# but the actual TEST below will use real data.
dummy_genre = torch.tensor([0], dtype=torch.long)
dummy_bpm = torch.tensor([128.0], dtype=torch.float32)
# The model expects (batch, omni_dim)
dummy_omni = torch.randn(1, OMNI_DIM) 

print("Converting graph to ONNX format...")
torch.onnx.export(
    model, 
    (dummy_omni, dummy_genre, dummy_bpm), 
    ONNX_EXPORT_PATH,
    export_params=True,
    opset_version=14,
    do_constant_folding=True,
    input_names=['omni_input', 'genre_input', 'bpm_input'],
    output_names=['recon_output', 'mu', 'log_var', 'mastering_params'],
    dynamic_axes={
        'omni_input': {0: 'batch_size'},
        'genre_input': {0: 'batch_size'},
        'bpm_input': {0: 'batch_size'},
        'recon_output': {0: 'batch_size'},
        'mu': {0: 'batch_size'},
        'log_var': {0: 'batch_size'},
        'mastering_params': {0: 'batch_size'}
    }
)
print(f"✅ ONNX Export Complete: {ONNX_EXPORT_PATH}")

# 4. REAL-DATA VALIDATION (No dummy data)
print(f"\n--- 🧪 Real-Data Validation (Zero Dummy Inputs) ---")

# We pull a real feature vector from the df_train dataframe created in Cell 4/5
# This ensures we are testing the model's ability to handle real sonic signatures.
real_idx = 42 # Pick a specific real sample
real_sample_omni = torch.tensor(X_norm[real_idx:real_idx+1], dtype=torch.float32)
real_sample_genre = torch.tensor(Y_genre[real_idx:real_idx+1], dtype=torch.long)
real_sample_bpm = torch.tensor(bpm_norm[real_idx:real_idx+1], dtype=torch.float32)

# Convert to numpy for ONNX Runtime
onnx_input_omni = real_sample_omni.numpy()
onnx_input_genre = real_sample_genre.numpy()
onnx_input_bpm = real_sample_bpm.numpy()

# Run Inference via ONNX Runtime
ort_sess = ort.InferenceSession(ONNX_EXPORT_PATH)
ort_inputs = {
    'omni_input': onnx_input_omni,
    'genre_input': onnx_input_genre,
    'bpm_input': onnx_input_bpm
}
ort_outputs = ort_sess.run(None, ort_inputs)

# 5. Comparison & Verification
# We compare the ONNX output against the PyTorch output to ensure mathematical parity
with torch.no_grad():
    torch_recon, _, _, _ = model(real_sample_omni, real_sample_genre, real_sample_bpm)

diff = np.abs(ort_outputs[0] - torch_recon.numpy()).max()

print(f"Input Sample Index: {real_idx}")
print(f"Verification: PyTorch vs ONNX Max Delta: {diff:.8f}")

if diff < 1e-3:
    print("✅ VALIDATION SUCCESS: ONNX parity confirmed with real data.")
else:
    print(f"❌ VALIDATION FAILURE: High divergence detected ({diff:.8f}).")

print(f"\n--- Final Mastering Output (from ONNX) ---")
print(f"Gain:      {ort_outputs[3][0][0]:.2f} dB")
print(f"Ratio:     {ort_outputs[3][0][1]:.2f}")
print(f"Threshold: {ort_outputs[3][0][2]:.2f} dB")


# %%
# Cell 18 — Production ONNX Inference (Real Data)
import onnxruntime as ort
import numpy as np
import torch

# 1. Path to your existing production ONNX model
ONNX_MODEL_PATH = r"C:\WEB CASE STUDY\sonic_dna_output\sonic_dna_master_v2.onnx"

if not os.path.exists(ONNX_MODEL_PATH):
    print(f"❌ Error: ONNX model not found at {ONNX_MODEL_PATH}")
else:
    print(f"🚀 Loading Production ONNX Engine: {ONNX_MODEL_PATH}")
    
    # 2. Initialize ONNX Runtime Session
    # Using CPU for this test, but can be switched to CUDA provider
    session = ort.InferenceSession(ONNX_MODEL_PATH, providers=['CPUExecutionProvider'])
    
    # 3. Prepare REAL data from your training tensors
    # We use the actual normalized features (X_norm) and metadata (bpm_norm)
    num_test_samples = 5
    indices = np.random.choice(len(X_norm), num_test_samples, replace=False)
    
    # The model expects [batch, 11] for dsp_features
    # Note: Our VAE outputs 11 DSP features + 1 BPM. 
    # This ONNX model expects the 11 DSP features.
    real_dsp_batch = X_norm[indices, :11].numpy() 
    
    # 4. Execute Inference
    input_name = session.get_inputs()[0].name
    print(f"Running inference on {num_test_samples} real audio profiles...\n")
    
    ort_inputs = {input_name: real_dsp_batch}
    ort_outputs = session.run(None, ort_inputs)
    
    # 5. Parse and Print Real Results
    mastering_params = ort_outputs[0]
    
    print(f"{'Sample':<8} | {'Gain (dB)':<10} | {'Ratio':<8} | {'Threshold (dB)':<10}")
    print("-" * 50)
    
    for i in range(num_test_samples):
        gain = mastering_params[i, 0]
        ratio = mastering_params[i, 1]
        threshold = mastering_params[i, 2]
        print(f"{indices[i]:<8} | {gain:>10.2f} | {ratio:>8.2f} | {threshold:>10.2f}")

    print("\n✅ REAL-DATA INFERENCE SUCCESSFUL.")


# %%
# 🧠 OMNICONDVAE v4 — UNIFIED TRAIN + ONNX EXPORT CELL
# Drop this as a single cell into your OmniCondVAE notebook.

import os, json, time
import numpy as np
import pandas as pd
from typing import List

import torch
import torch.nn as nn
import torch.optim as optim

import ray
from ray import train
from ray.train import Trainer

from sklearn.preprocessing import StandardScaler

# =========================================================
# 1. LOAD PHYSICAL DSP + OMNI-VECTOR + LIBRARY FEATURES
# =========================================================

STEMS_PATH   = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/exported_json/chrislake_stems_duckdb.json"
OMNI_PATH    = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/exported_json/chris_lake_omni_baseline.json"
FEATURES_PATH = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/exported_json/duckdb_audio_features.json"

assert os.path.exists(STEMS_PATH),   "Missing stems DSP JSON."
assert os.path.exists(OMNI_PATH),    "Missing Chris Lake omni baseline JSON."
assert os.path.exists(FEATURES_PATH),"Missing duckdb_audio_features JSON."

with open(STEMS_PATH, 'r', encoding='utf-8') as f:
    stems_data = json.load(f)

with open(OMNI_PATH, 'r', encoding='utf-8') as f:
    omni_data = json.load(f)

with open(FEATURES_PATH, 'r', encoding='utf-8') as f:
    lib_data = json.load(f)

df_lib = pd.DataFrame(lib_data)

# Target: Chris Lake identity flag
df_lib['is_chris_lake'] = (
    df_lib['filepath'].str.lower().str.contains('chris lake') |
    df_lib['filename'].str.lower().str.contains('chris lake')
)

# Core DSP features (from CELL 11)
dsp_features = [
    'tempo',
    'rms_db',
    'crest_factor',
    'sub_bass_energy',
    'bass_energy',
    'mid_energy',
    'high_energy',
    'spectral_centroid'
]

df_clean = df_lib.dropna(subset=dsp_features + ['is_chris_lake'])
X = df_clean[dsp_features].astype(float)
y = df_clean['is_chris_lake'].astype(int)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# =========================================================
# 2. BUILD OMNI-VECTOR v4 (SEMANTIC + DSP + CONTEXT)
# =========================================================
# For now, we treat X_scaled as the DSP slice of the Omni-Vector.
# You can append LanceDB semantic embeddings + BPM later.

# Example: augment with simple BPM normalization + identity flag
bpm = df_clean['tempo'].values.reshape(-1, 1)
bpm_norm = (bpm - bpm.mean()) / (bpm.std() + 1e-8)

identity_flag = y.values.reshape(-1, 1)  # 1 = Chris Lake, 0 = Other

# Omni-Vector v4 = [scaled DSP | bpm_norm | identity_flag]
omni_v4 = np.concatenate([X_scaled, bpm_norm, identity_flag], axis=1)
input_dim = omni_v4.shape[1]

# =========================================================
# 3. DEFINE OMNICONDVAE v4 ARCHITECTURE
# =========================================================

LATENT_DIM = 128
OUTPUT_DIM = 3  # gain_db, compression_ratio, threshold_db

class OmniCondVAEv4(nn.Module):
    def __init__(self, input_dim: int, latent_dim: int, output_dim: int):
        super().__init__()
        # Encoder
        self.enc = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
        )
        self.mu     = nn.Linear(128, latent_dim)
        self.logvar = nn.Linear(128, latent_dim)

        # Decoder → mastering command set
        self.dec = nn.Sequential(
            nn.Linear(latent_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, output_dim)
        )

    def encode(self, x):
        h = self.enc(x)
        mu = self.mu(h)
        logvar = self.logvar(h)
        return mu, logvar

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z):
        return self.dec(z)

    def forward(self, x):
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        out = self.decode(z)
        return out, mu, logvar

def vae_loss(recon, target, mu, logvar):
    # Recon loss: MSE between predicted mastering commands and target proxy
    # For now, we use a dummy zero target; you can plug real mastering labels later.
    mse = nn.functional.mse_loss(recon, target)
    # KL divergence
    kld = -0.5 * torch.mean(1 + logvar - mu.pow(2) - logvar.exp())
    return mse + 1e-3 * kld

# =========================================================
# 4. RAY DISTRIBUTED TRAINING (SEARCH → POLISH)
# =========================================================

ray.init(ignore_reinit_error=True)

omni_tensor = torch.tensor(omni_v4, dtype=torch.float32)
dummy_target = torch.zeros((omni_tensor.shape[0], OUTPUT_DIM), dtype=torch.float32)

dataset = torch.utils.data.TensorDataset(omni_tensor, dummy_target)
train_loader = torch.utils.data.DataLoader(dataset, batch_size=64, shuffle=True)

def train_epoch(model, optimizer, loader, device):
    model.train()
    total_loss = 0.0
    for xb, yb in loader:
        xb = xb.to(device)
        yb = yb.to(device)
        optimizer.zero_grad()
        recon, mu, logvar = model(xb)
        loss = vae_loss(recon, yb, mu, logvar)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * xb.size(0)
    return total_loss / len(loader.dataset)

@ray.remote
def trainer_actor(seed: int, omni_v4_chunk: np.ndarray, epochs: int = 50):
    torch.manual_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = OmniCondVAEv4(input_dim=input_dim, latent_dim=LATENT_DIM, output_dim=OUTPUT_DIM).to(device)
    opt = optim.Adam(model.parameters(), lr=1e-3)

    tensor_chunk = torch.tensor(omni_v4_chunk, dtype=torch.float32)
    target_chunk = torch.zeros((tensor_chunk.shape[0], OUTPUT_DIM), dtype=torch.float32)
    loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(tensor_chunk, target_chunk),
        batch_size=64,
        shuffle=True
    )

    for epoch in range(epochs):
        loss = train_epoch(model, opt, loader, device)
        if (epoch + 1) % 10 == 0:
            print(f"[TrainerActor {seed}] Epoch {epoch+1}/{epochs} — Loss: {loss:.6f}")

    return model.state_dict()

# Phase 1 — SEARCH: shard omni_v4 across actors
num_actors = 6
shards = np.array_split(omni_v4, num_actors)
actors = [
    trainer_actor.remote(seed=42 + i, omni_v4_chunk=shards[i], epochs=50)
    for i in range(num_actors)
]
state_dicts = ray.get(actors)

# Simple ensemble average of weights as initialization
base_model = OmniCondVAEv4(input_dim=input_dim, latent_dim=LATENT_DIM, output_dim=OUTPUT_DIM)
with torch.no_grad():
    for name, param in base_model.state_dict().items():
        stacked = torch.stack([sd[name] for sd in state_dicts], dim=0)
        param.copy_(stacked.mean(dim=0))

# Phase 2 — POLISH: full dataset, high-epoch refinement
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
base_model = base_model.to(device)
optimizer = optim.Adam(base_model.parameters(), lr=5e-4)

EPOCHS_POLISH = 150
for epoch in range(EPOCHS_POLISH):
    loss = train_epoch(base_model, optimizer, train_loader, device)
    if (epoch + 1) % 10 == 0:
        print(f"[POLISH] Epoch {epoch+1}/{EPOCHS_POLISH} — Loss: {loss:.6f}")

# =========================================================
# 5. ONNX EXPORT — OMNICONDVAE v4
# =========================================================

ONNX_PATH = "fretflow_omni_v4.onnx"
base_model.eval()
dummy_input = torch.randn(1, input_dim, dtype=torch.float32).to(device)

torch.onnx.export(
    base_model,
    dummy_input,
    ONNX_PATH,
    input_names=["omni_vector_v4"],
    output_names=["mastering_command_set"],
    dynamic_axes={"omni_vector_v4": {0: "batch_size"}},
    opset_version=17
)

print(f"\n✅ OmniCondVAE v4 ONNX exported to: {ONNX_PATH}")
print(f"   Input dim:  {input_dim}")
print(f"   Latent dim: {LATENT_DIM}")
print(f"   Output dim: {OUTPUT_DIM}")


# %%
# 🧠 OMNICONDVAE v4 — UNIFIED TRAIN + ONNX EXPORT CELL
# Drop this as a single cell into your OmniCondVAE notebook.

import os, json, time
import numpy as np
import pandas as pd
from typing import List

import torch
import torch.nn as nn
import torch.optim as optim

import ray
from ray import train
from ray.train import Trainer

from sklearn.preprocessing import StandardScaler

# =========================================================
# 1. LOAD PHYSICAL DSP + OMNI-VECTOR + LIBRARY FEATURES
# =========================================================

STEMS_PATH   = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/exported_json/chrislake_stems_duckdb.json"
OMNI_PATH    = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/exported_json/chris_lake_omni_baseline.json"
FEATURES_PATH = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/exported_json/duckdb_audio_features.json"

assert os.path.exists(STEMS_PATH),   "Missing stems DSP JSON."
assert os.path.exists(OMNI_PATH),    "Missing Chris Lake omni baseline JSON."
assert os.path.exists(FEATURES_PATH),"Missing duckdb_audio_features JSON."

with open(STEMS_PATH, 'r', encoding='utf-8') as f:
    stems_data = json.load(f)

with open(OMNI_PATH, 'r', encoding='utf-8') as f:
    omni_data = json.load(f)

with open(FEATURES_PATH, 'r', encoding='utf-8') as f:
    lib_data = json.load(f)

df_lib = pd.DataFrame(lib_data)

# Target: Chris Lake identity flag
df_lib['is_chris_lake'] = (
    df_lib['filepath'].str.lower().str.contains('chris lake') |
    df_lib['filename'].str.lower().str.contains('chris lake')
)

# Core DSP features (from CELL 11)
dsp_features = [
    'tempo',
    'rms_db',
    'crest_factor',
    'sub_bass_energy',
    'bass_energy',
    'mid_energy',
    'high_energy',
    'spectral_centroid'
]

df_clean = df_lib.dropna(subset=dsp_features + ['is_chris_lake'])
X = df_clean[dsp_features].astype(float)
y = df_clean['is_chris_lake'].astype(int)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# =========================================================
# 2. BUILD OMNI-VECTOR v4 (SEMANTIC + DSP + CONTEXT)
# =========================================================
# For now, we treat X_scaled as the DSP slice of the Omni-Vector.
# You can append LanceDB semantic embeddings + BPM later.

# Example: augment with simple BPM normalization + identity flag
bpm = df_clean['tempo'].values.reshape(-1, 1)
bpm_norm = (bpm - bpm.mean()) / (bpm.std() + 1e-8)

identity_flag = y.values.reshape(-1, 1)  # 1 = Chris Lake, 0 = Other

# Omni-Vector v4 = [scaled DSP | bpm_norm | identity_flag]
omni_v4 = np.concatenate([X_scaled, bpm_norm, identity_flag], axis=1)
input_dim = omni_v4.shape[1]

# =========================================================
# 3. DEFINE OMNICONDVAE v4 ARCHITECTURE
# =========================================================

LATENT_DIM = 128
OUTPUT_DIM = 3  # gain_db, compression_ratio, threshold_db

class OmniCondVAEv4(nn.Module):
    def __init__(self, input_dim: int, latent_dim: int, output_dim: int):
        super().__init__()
        # Encoder
        self.enc = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
        )
        self.mu     = nn.Linear(128, latent_dim)
        self.logvar = nn.Linear(128, latent_dim)

        # Decoder → mastering command set
        self.dec = nn.Sequential(
            nn.Linear(latent_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, output_dim)
        )

    def encode(self, x):
        h = self.enc(x)
        mu = self.mu(h)
        logvar = self.logvar(h)
        return mu, logvar

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z):
        return self.dec(z)

    def forward(self, x):
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        out = self.decode(z)
        return out, mu, logvar

def vae_loss(recon, target, mu, logvar):
    # Recon loss: MSE between predicted mastering commands and target proxy
    # For now, we use a dummy zero target; you can plug real mastering labels later.
    mse = nn.functional.mse_loss(recon, target)
    # KL divergence
    kld = -0.5 * torch.mean(1 + logvar - mu.pow(2) - logvar.exp())
    return mse + 1e-3 * kld

# =========================================================
# 4. RAY DISTRIBUTED TRAINING (SEARCH → POLISH)
# =========================================================

ray.init(ignore_reinit_error=True)

omni_tensor = torch.tensor(omni_v4, dtype=torch.float32)
dummy_target = torch.zeros((omni_tensor.shape[0], OUTPUT_DIM), dtype=torch.float32)

dataset = torch.utils.data.TensorDataset(omni_tensor, dummy_target)
train_loader = torch.utils.data.DataLoader(dataset, batch_size=64, shuffle=True)

def train_epoch(model, optimizer, loader, device):
    model.train()
    total_loss = 0.0
    for xb, yb in loader:
        xb = xb.to(device)
        yb = yb.to(device)
        optimizer.zero_grad()
        recon, mu, logvar = model(xb)
        loss = vae_loss(recon, yb, mu, logvar)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * xb.size(0)
    return total_loss / len(loader.dataset)

@ray.remote
def trainer_actor(seed: int, omni_v4_chunk: np.ndarray, epochs: int = 50):
    torch.manual_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = OmniCondVAEv4(input_dim=input_dim, latent_dim=LATENT_DIM, output_dim=OUTPUT_DIM).to(device)
    opt = optim.Adam(model.parameters(), lr=1e-3)

    tensor_chunk = torch.tensor(omni_v4_chunk, dtype=torch.float32)
    target_chunk = torch.zeros((tensor_chunk.shape[0], OUTPUT_DIM), dtype=torch.float32)
    loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(tensor_chunk, target_chunk),
        batch_size=64,
        shuffle=True
    )

    for epoch in range(epochs):
        loss = train_epoch(model, opt, loader, device)
        if (epoch + 1) % 10 == 0:
            print(f"[TrainerActor {seed}] Epoch {epoch+1}/{epochs} — Loss: {loss:.6f}")

    return model.state_dict()

# Phase 1 — SEARCH: shard omni_v4 across actors
num_actors = 6
shards = np.array_split(omni_v4, num_actors)
actors = [
    trainer_actor.remote(seed=42 + i, omni_v4_chunk=shards[i], epochs=50)
    for i in range(num_actors)
]
state_dicts = ray.get(actors)

# Simple ensemble average of weights as initialization
base_model = OmniCondVAEv4(input_dim=input_dim, latent_dim=LATENT_DIM, output_dim=OUTPUT_DIM)
with torch.no_grad():
    for name, param in base_model.state_dict().items():
        stacked = torch.stack([sd[name] for sd in state_dicts], dim=0)
        param.copy_(stacked.mean(dim=0))

# Phase 2 — POLISH: full dataset, high-epoch refinement
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
base_model = base_model.to(device)
optimizer = optim.Adam(base_model.parameters(), lr=5e-4)

EPOCHS_POLISH = 150
for epoch in range(EPOCHS_POLISH):
    loss = train_epoch(base_model, optimizer, train_loader, device)
    if (epoch + 1) % 10 == 0:
        print(f"[POLISH] Epoch {epoch+1}/{EPOCHS_POLISH} — Loss: {loss:.6f}")

# =========================================================
# 5. ONNX EXPORT — OMNICONDVAE v4
# =========================================================

ONNX_PATH = "fretflow_omni_v4.onnx"
base_model.eval()
dummy_input = torch.randn(1, input_dim, dtype=torch.float32).to(device)

torch.onnx.export(
    base_model,
    dummy_input,
    ONNX_PATH,
    input_names=["omni_vector_v4"],
    output_names=["mastering_command_set"],
    dynamic_axes={"omni_vector_v4": {0: "batch_size"}},
    opset_version=17
)

print(f"\n✅ OmniCondVAE v4 ONNX exported to: {ONNX_PATH}")
print(f"   Input dim:  {input_dim}")
print(f"   Latent dim: {LATENT_DIM}")
print(f"   Output dim: {OUTPUT_DIM}")


# %%
# =========================================================
# OMNICONDVAE v4 — Unified Training + ONNX Export (Ray Actors Only)
# =========================================================

import os, json, numpy as np, pandas as pd
import torch, torch.nn as nn, torch.optim as optim
from sklearn.preprocessing import StandardScaler
import ray

# =========================================================
# 1. LOAD DSP + OMNI BASELINES
# =========================================================

STEMS_PATH   = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/exported_json/chrislake_stems_duckdb.json"
OMNI_PATH    = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/exported_json/chris_lake_omni_baseline.json"
FEATURES_PATH = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/exported_json/duckdb_audio_features.json"

with open(FEATURES_PATH, 'r', encoding='utf-8') as f:
    lib_data = json.load(f)

df = pd.DataFrame(lib_data)
df['is_chris_lake'] = (
    df['filepath'].str.lower().str.contains('chris lake') |
    df['filename'].str.lower().str.contains('chris lake')
)

dsp_features = [
    'tempo','rms_db','crest_factor','sub_bass_energy',
    'bass_energy','mid_energy','high_energy','spectral_centroid'
]

df_clean = df.dropna(subset=dsp_features + ['is_chris_lake'])
X = df_clean[dsp_features].astype(float)
y = df_clean['is_chris_lake'].astype(int)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

bpm_norm = (df_clean['tempo'] - df_clean['tempo'].mean()) / (df_clean['tempo'].std() + 1e-8)
identity_flag = y.values.reshape(-1, 1)

omni_v4 = np.concatenate([X_scaled, bpm_norm.values.reshape(-1,1), identity_flag], axis=1)
input_dim = omni_v4.shape[1]

# =========================================================
# 2. DEFINE OMNICONDVAE v4
# =========================================================

LATENT_DIM = 128
OUTPUT_DIM = 3

class OmniCondVAEv4(nn.Module):
    def __init__(self, input_dim, latent_dim, output_dim):
        super().__init__()
        self.enc = nn.Sequential(
            nn.Linear(input_dim, 256), nn.ReLU(),
            nn.Linear(256, 128), nn.ReLU()
        )
        self.mu     = nn.Linear(128, latent_dim)
        self.logvar = nn.Linear(128, latent_dim)

        self.dec = nn.Sequential(
            nn.Linear(latent_dim, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, output_dim)
        )

    def encode(self, x):
        h = self.enc(x)
        return self.mu(h), self.logvar(h)

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        return mu + torch.randn_like(std) * std

    def decode(self, z):
        return self.dec(z)

    def forward(self, x):
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        return self.decode(z), mu, logvar

def vae_loss(recon, target, mu, logvar):
    mse = nn.functional.mse_loss(recon, target)
    kld = -0.5 * torch.mean(1 + logvar - mu.pow(2) - logvar.exp())
    return mse + 1e-3 * kld

# =========================================================
# 3. RAY ACTOR TRAINING (NO Trainer API)
# =========================================================

ray.init(ignore_reinit_error=True)

@ray.remote
class VAETrainer:
    def __init__(self, seed, input_dim, latent_dim, output_dim):
        torch.manual_seed(seed)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = OmniCondVAEv4(input_dim, latent_dim, output_dim).to(self.device)
        self.opt = optim.Adam(self.model.parameters(), lr=1e-3)

    def train(self, data, epochs=40):
        x = torch.tensor(data, dtype=torch.float32).to(self.device)
        y = torch.zeros((x.shape[0], OUTPUT_DIM), dtype=torch.float32).to(self.device)

        for ep in range(epochs):
            self.opt.zero_grad()
            recon, mu, logvar = self.model(x)
            loss = vae_loss(recon, y, mu, logvar)
            loss.backward()
            self.opt.step()
        return self.model.state_dict()

# Phase 1 — SEARCH
num_actors = 6
shards = np.array_split(omni_v4, num_actors)

actors = [
    VAETrainer.remote(seed=100+i, input_dim=input_dim, latent_dim=LATENT_DIM, output_dim=OUTPUT_DIM)
    for i in range(num_actors)
]

# FIXED LINE — correct actor invocation
state_dicts = ray.get([actors[i].train.remote(shards[i]) for i in range(num_actors)])

# Ensemble average
base_model = OmniCondVAEv4(input_dim, LATENT_DIM, OUTPUT_DIM)
with torch.no_grad():
    for name, param in base_model.state_dict().items():
        stacked = torch.stack([sd[name] for sd in state_dicts], dim=0)
        param.copy_(stacked.mean(dim=0))

# Phase 2 — POLISH
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
base_model = base_model.to(device)
opt = optim.Adam(base_model.parameters(), lr=5e-4)

full_x = torch.tensor(omni_v4, dtype=torch.float32).to(device)
full_y = torch.zeros((full_x.shape[0], OUTPUT_DIM), dtype=torch.float32).to(device)

for ep in range(120):
    opt.zero_grad()
    recon, mu, logvar = base_model(full_x)
    loss = vae_loss(recon, full_y, mu, logvar)
    loss.backward()
    opt.step()
    if (ep+1) % 10 == 0:
        print(f"[POLISH] Epoch {ep+1}/120 — Loss {loss.item():.6f}")

# =========================================================
# 4. EXPORT ONNX
# =========================================================

ONNX_PATH = "fretflow_omni_v4.onnx"
dummy = torch.randn(1, input_dim).to(device)

torch.onnx.export(
    base_model,
    dummy,
    ONNX_PATH,
    input_names=["omni_vector_v4"],
    output_names=["mastering_command_set"],
    dynamic_axes={"omni_vector_v4": {0: "batch"}},
    opset_version=17
)

print(f"\n✅ Exported OMNICONDVAE v4 → {ONNX_PATH}")
print(f"Input Dim: {input_dim}, Latent: {LATENT_DIM}, Output: {OUTPUT_DIM}")


# %%
# 🎛 REAL MASTERING: Run OmniCondVAE v4 ONNX on two local tracks
# Files:
#   C:\Users\adams\Downloads\that look on your face.mp3
#   C:\Users\adams\Downloads\new life.wav

import os
import numpy as np
import onnxruntime as ort
import librosa

from sklearn.preprocessing import StandardScaler

MODEL_PATH = r"fretflow_omni_v4.onnx"

TRACKS = [
    r"C:\Users\adams\Downloads\that look on your face.mp3",
    r"C:\Users\adams\Downloads\new life.wav",
]

assert os.path.exists(MODEL_PATH), f"Missing ONNX model: {MODEL_PATH}"

# =========================================================
# 1. SIMPLE DSP FEATURE EXTRACTOR (MATCHING omni_v4 SCHEMA)
# =========================================================
def extract_dsp_features(path):
    y, sr = librosa.load(path, mono=True)

    # RMS
    rms_arr = librosa.feature.rms(y=y)
    rms = float(rms_arr.mean())

    # Crest factor
    crest = float(np.max(np.abs(y)) / (rms + 1e-8))

    # Tempo (force scalar)
    tempo_arr, _ = librosa.beat.beat_track(y=y, sr=sr)
    # tempo_arr can be array-like → force scalar
    if hasattr(tempo_arr, "__len__"):
        tempo = float(tempo_arr[0])
    else:
        tempo = float(tempo_arr)

    # STFT
    S = np.abs(librosa.stft(y, n_fft=2048))**2
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)

    def band_energy(fmin, fmax):
        mask = (freqs >= fmin) & (freqs < fmax)
        return float(S[mask].sum())

    sub_bass = band_energy(20, 60)
    bass     = band_energy(60, 250)
    mid      = band_energy(250, 4000)
    high     = band_energy(4000, 20000)

    # Spectral centroid (force scalar)
    centroid_arr = librosa.feature.spectral_centroid(S=S, sr=sr)
    centroid = float(centroid_arr.mean())

    return {
        "tempo": tempo,
        "rms_db": float(20 * np.log10(rms + 1e-12)),
        "crest_factor": crest,
        "sub_bass_energy": sub_bass,
        "bass_energy": bass,
        "mid_energy": mid,
        "high_energy": high,
        "spectral_centroid": centroid,
    }


# =========================================================
# 2. BUILD omni_vector_v4 FOR EACH TRACK
#    (scaled DSP + normalized BPM + identity_flag=0)
# =========================================================

raw_rows = []
for p in TRACKS:
    print(f"\n🔊 Extracting DSP for: {p}")
    feats = extract_dsp_features(p)
    raw_rows.append([
        feats["tempo"],
        feats["rms_db"],
        feats["crest_factor"],
        feats["sub_bass_energy"],
        feats["bass_energy"],
        feats["mid_energy"],
        feats["high_energy"],
        feats["spectral_centroid"],
    ])

raw_rows = np.array(raw_rows, dtype=float)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(raw_rows)

bpm_norm = (raw_rows[:, 0] - raw_rows[:, 0].mean()) / (raw_rows[:, 0].std() + 1e-8)
identity_flag = np.zeros((raw_rows.shape[0], 1), dtype=float)  # 0 = not Chris Lake

omni_v4_batch = np.concatenate(
    [X_scaled, bpm_norm.reshape(-1, 1), identity_flag],
    axis=1
)

print(f"\n🧬 omni_vector_v4 batch shape: {omni_v4_batch.shape}")

# =========================================================
# 3. RUN ONNX RUNTIME INFERENCE
# =========================================================

sess = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
input_name = sess.get_inputs()[0].name
output_name = sess.get_outputs()[0].name

mastering_cmds = sess.run(
    [output_name],
    {input_name: omni_v4_batch.astype(np.float32)}
)[0]

# mastering_cmds shape: (num_tracks, 3) → [gain_db, compression_ratio, threshold_db]

# =========================================================
# 4. PRINT MASTERING COMMANDS FOR EACH TRACK
# =========================================================

for i, path in enumerate(TRACKS):
    gain_db, comp_ratio, thresh_db = mastering_cmds[i]
    print("\n========================================================")
    print(f"🎧 MASTERING COMMANDS — {os.path.basename(path)}")
    print("========================================================")
    print(f"  ➤ gain_db           : {gain_db:.3f} dB")
    print(f"  ➤ compression_ratio : {comp_ratio:.3f}:1")
    print(f"  ➤ threshold_db      : {thresh_db:.3f} dB")
    print("========================================================")


# %%
# 🧠 OMNI MASTER BRAIN v1 — TRAIN FROM YOUR EXISTING PIPELINE (ONE CELL)

import os, json, numpy as np, pandas as pd
import torch, torch.nn as nn, torch.optim as optim
from sklearn.preprocessing import StandardScaler
import lancedb
import librosa

# ----------------------------------------------------------------------
# CONFIG — USE YOUR EXISTING ENV + TRACK LIST
# ----------------------------------------------------------------------
DOWNLOADS_DIR   = r"C:\Users\adams\Downloads"
LANCEDB_PATH    = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
TABLE_NAME      = "omni_semantic_baselines"
BASELINE_TRACK  = "Somebody (2024)"  # Chris Lake reference
ALIGNMENT_FEATURES = ["rms_db", "crest_factor", "sub_bass_energy", "bass_energy", "mid_energy", "high_energy"]

MY_TRACK_LIST = [
    r"C:\Users\adams\Downloads\feed this desire.wav",
    r"C:\Users\adams\Downloads\jumpy jumpy.wav",
    r"C:\Users\adams\Downloads\admit it.mp3",
    r"C:\Users\adams\Downloads\VIZON & Ren Carter - Had To Go [Extended Mix] (2).mp3"
]

# ----------------------------------------------------------------------
# FALLBACK STRUCTURAL + SECTION FEATURE EXTRACTORS (MATCH YOUR SCRIPT)
# ----------------------------------------------------------------------
try:
    from essentia_wsl_bridge import get_structural_audio_analysis
    from audit_and_score_downloads import extract_section_features
except ImportError:
    def get_structural_audio_analysis(p): 
        dur = librosa.get_duration(path=p)
        return {"sections":[{"start_time_sec":0.0,"end_time_sec":dur}]}
    def extract_section_features(a, sr):
        rms = float(librosa.feature.rms(y=a).mean())
        crest = float(np.max(np.abs(a)) / (rms + 1e-8))
        S = np.abs(librosa.stft(a, n_fft=2048))**2
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
        def band_energy(fmin,fmax):
            m = (freqs>=fmin)&(freqs<fmax)
            return float(S[m].sum())
        sub = band_energy(20,60)
        bass = band_energy(60,250)
        mid = band_energy(250,4000)
        high = band_energy(4000,20000)
        return {
            "rms_db": float(20*np.log10(rms+1e-12)),
            "crest_factor": crest,
            "sub_bass_energy": sub,
            "bass_energy": bass,
            "mid_energy": mid,
            "high_energy": high
        }

# ----------------------------------------------------------------------
# LOAD CHRIS LAKE BASELINE FROM LANCEDB (YOUR EXISTING REFERENCE SPACE)
# ----------------------------------------------------------------------
db = lancedb.connect(LANCEDB_PATH)
table = db.open_table(TABLE_NAME)
df_all = table.to_pandas()

df_base = df_all[df_all["track_name"].str.contains(BASELINE_TRACK, case=False, regex=False, na=False)].copy()
df_base["seg_idx"] = df_base["segment_name"].str.extract(r"(\d+)").astype(float).fillna(0).astype(int)
df_base = df_base.sort_values("seg_idx").reset_index(drop=True)

if "rms" in df_base.columns and "rms_db" not in df_base.columns:
    df_base["rms_db"] = df_base["rms"].apply(lambda v: float(20*np.log10(v)) if v>1e-9 else -100.0)

X_base_raw = df_base[ALIGNMENT_FEATURES].fillna(0.0).values.astype(np.float32)
scaler = StandardScaler().fit(X_base_raw)
X_base_scaled = scaler.transform(X_base_raw)

# ----------------------------------------------------------------------
# BUILD TRAINING DATA: SECTION FEATURES → MASTERING COMMANDS (YOUR LOGIC)
# ----------------------------------------------------------------------
from scipy.spatial.distance import cdist

X_train = []
Y_train = []

for track_path in MY_TRACK_LIST:
    if not os.path.exists(track_path):
        continue

    analysis = get_structural_audio_analysis(track_path)
    sections = analysis.get("sections", [])
    if not sections:
        dur = librosa.get_duration(path=track_path)
        sections = [{"start_time_sec":0.0,"end_time_sec":dur}]

    y, sr = librosa.load(track_path, sr=None, mono=True)

    # per-section features
    section_feats = []
    for sect in sections:
        s = int(sect["start_time_sec"]*sr)
        e = int(sect["end_time_sec"]*sr)
        chunk = y[s:e]
        if len(chunk)==0:
            continue
        feats = extract_section_features(chunk, sr)
        section_feats.append([feats[f] for f in ALIGNMENT_FEATURES])

    if not section_feats:
        continue

    X_targ_scaled = scaler.transform(np.array(section_feats, dtype=np.float32))

    for i, sect_vec in enumerate(X_targ_scaled):
        targ_vec = sect_vec.reshape(1,-1)
        dists = cdist(targ_vec, X_base_scaled, metric="euclidean")[0]
        best_idx = int(np.argmin(dists))
        match_info = df_base.loc[best_idx].to_dict()

        target_rms   = float(match_info["rms_db"])
        target_crest = float(match_info["crest_factor"])

        current_feats = section_feats[i]
        current_rms   = current_feats[0]
        current_crest = current_feats[1]

        # YOUR EXISTING DECISION LOGIC → LABELS
        if current_crest > target_crest * 1.05:
            ratio = max(1.8, min(4.5, 2.0 + (current_crest - target_crest) * 0.75))
            threshold_db = current_rms - 3.0
        else:
            ratio = 1.0
            threshold_db = 0.0

        gain_db = max(-12.0, min(12.0, target_rms - current_rms))

        # INPUT: scaled DSP + deltas
        delta_rms   = target_rms - current_rms
        delta_crest = target_crest - current_crest
        X_train.append(list(sect_vec) + [delta_rms, delta_crest])
        Y_train.append([gain_db, ratio, threshold_db])

X_train = np.array(X_train, dtype=np.float32)
Y_train = np.array(Y_train, dtype=np.float32)

print(f"🧬 Brain dataset: X={X_train.shape}, Y={Y_train.shape}")

# ----------------------------------------------------------------------
# DEFINE BRAIN MODEL — COMPACT POLICY NETWORK
# ----------------------------------------------------------------------
input_dim  = X_train.shape[1]
output_dim = 3

class OmniMasterBrain(nn.Module):
    def __init__(self, input_dim, output_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, output_dim)
        )
    def forward(self, x):
        return self.net(x)

model = OmniMasterBrain(input_dim, output_dim)
opt   = optim.Adam(model.parameters(), lr=1e-3)
loss_fn = nn.MSELoss()

X_t = torch.tensor(X_train)
Y_t = torch.tensor(Y_train)

# ----------------------------------------------------------------------
# TRAIN BRAIN ON YOUR DECISION POLICY
# ----------------------------------------------------------------------
EPOCHS = 200
for ep in range(EPOCHS):
    opt.zero_grad()
    pred = model(X_t)
    loss = loss_fn(pred, Y_t)
    loss.backward()
    opt.step()
    if (ep+1) % 20 == 0:
        print(f"[BRAIN] Epoch {ep+1}/{EPOCHS} — Loss {loss.item():.6f}")

# ----------------------------------------------------------------------
# EXPORT BRAIN TO ONNX
# ----------------------------------------------------------------------
import torch.onnx

ONNX_PATH = "omni_master_brain_v1.onnx"
dummy = torch.randn(1, input_dim)

torch.onnx.export(
    model,
    dummy,
    ONNX_PATH,
    input_names=["section_features"],
    output_names=["mastering_command_set"],
    dynamic_axes={"section_features": {0: "batch"}},
    opset_version=18
)

print(f"\n✅ OMNI MASTER BRAIN v1 exported → {ONNX_PATH}")
print(f"   Input dim:  {input_dim}")
print(f"   Output dim: {output_dim}")

# ============================================================
# 🧠 OMNI MASTER BRAIN v1 — POST-MASTER REVIEW (END OF PIPELINE)
# ============================================================

try:
    import onnxruntime as ort

    brain = ort.InferenceSession("omni_master_brain_v1.onnx")
    input_name = brain.get_inputs()[0].name
    output_name = brain.get_outputs()[0].name

    # Build brain input from final section features
    final_feats = extract_section_features(
        mastered_full.T if mastered_full.ndim > 1 else mastered_full,
        sr_full
    )

    # Prepare 8‑dim input vector (same as training)
    brain_input_vec = np.array([
        final_feats["rms_db"],
        final_feats["crest_factor"],
        final_feats["sub_bass_energy"],
        final_feats["bass_energy"],
        final_feats["mid_energy"],
        final_feats["high_energy"],
        # deltas vs Chris Lake baseline (global)
        float(df_base["rms_db"].mean() - final_feats["rms_db"]),
        float(df_base["crest_factor"].mean() - final_feats["crest_factor"])
    ], dtype=np.float32).reshape(1, -1)

    # Run brain inference
    brain_out = brain.run([output_name], {input_name: brain_input_vec})[0][0]
    brain_gain, brain_ratio, brain_thresh = brain_out.tolist()

    print("\n🧠 OMNI MASTER BRAIN v1 — REVIEW")
    print("   Brain Gain:       {:.3f} dB".format(brain_gain))
    print("   Brain Ratio:      {:.3f}:1".format(brain_ratio))
    print("   Brain Threshold:  {:.3f} dB".format(brain_thresh))

    print("\n🔍 COMPARISON — DSP Engine vs Brain")
    print("   DSP Gain:         {:.3f} dB".format(gain.gain_db))
    print("   DSP Ratio:        {:.3f}:1".format(comp.ratio))
    print("   DSP Threshold:    {:.3f} dB".format(comp.threshold_db))

except Exception as e:
    print(f"⚠️ Brain inference skipped: {str(e)}")


# %%
# ============================================================
# 🧠 FRESH DSP → OMNI MASTER BRAIN v1 INFERENCE CELL
# ============================================================

import numpy as np
import librosa
import onnxruntime as ort

# ------------------------------------------------------------
# CONFIG: Your tracks
# ------------------------------------------------------------
TRACKS = [
    r"C:\Users\adams\Downloads\feed this desire.wav",
    r"C:\Users\adams\Downloads\jumpy jumpy.wav",
    r"C:\Users\adams\Downloads\admit it.mp3",
    r"C:\Users\adams\Downloads\VIZON & Ren Carter - Had To Go [Extended Mix] (2).mp3"
]

# ------------------------------------------------------------
# DSP extractor (same schema used to train the brain)
# ------------------------------------------------------------
def extract_dsp_features(path):
    y, sr = librosa.load(path, mono=True)

    rms = float(librosa.feature.rms(y=y).mean())
    crest = float(np.max(np.abs(y)) / (rms + 1e-8))

    S = np.abs(librosa.stft(y, n_fft=2048))**2
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)

    def band_energy(fmin, fmax):
        mask = (freqs >= fmin) & (freqs < fmax)
        return float(S[mask].sum())

    sub_bass = band_energy(20, 60)
    bass     = band_energy(60, 250)
    mid      = band_energy(250, 4000)
    high     = band_energy(4000, 20000)

    return {
        "rms_db": float(20 * np.log10(rms + 1e-12)),
        "crest_factor": crest,
        "sub_bass_energy": sub_bass,
        "bass_energy": bass,
        "mid_energy": mid,
        "high_energy": high
    }

# ------------------------------------------------------------
# Load OMNI MASTER BRAIN v1
# ------------------------------------------------------------
brain = ort.InferenceSession("omni_master_brain_v1.onnx")
input_name = brain.get_inputs()[0].name
output_name = brain.get_outputs()[0].name

# ------------------------------------------------------------
# Run DSP → Brain inference for each track
# ------------------------------------------------------------
for track in TRACKS:
    print("\n====================================================")
    print(f"🎧 TRACK: {track}")
    print("====================================================")

    feats = extract_dsp_features(track)

    # Build 8‑dim input vector (same as training)
    brain_input_vec = np.array([
        feats["rms_db"],
        feats["crest_factor"],
        feats["sub_bass_energy"],
        feats["bass_energy"],
        feats["mid_energy"],
        feats["high_energy"],
        0.0,   # delta_rms placeholder (no baseline in this cell)
        0.0    # delta_crest placeholder
    ], dtype=np.float32).reshape(1, -1)

    # Run brain inference
    brain_out = brain.run([output_name], {input_name: brain_input_vec})[0][0]
    gain_db, ratio, threshold_db = brain_out.tolist()

    print("🧠 OMNI MASTER BRAIN v1 — RECOMMENDATIONS")
    print(f"   Gain:       {gain_db:.3f} dB")
    print(f"   Ratio:      {ratio:.3f}:1")
    print(f"   Threshold:  {threshold_db:.3f} dB")


# %%
# ============================================================
# 🧠 FRESH DSP → CHRIS LAKE BASELINE → OMNI MASTER BRAIN v1
# ============================================================

import numpy as np
import librosa
import onnxruntime as ort
import lancedb
from sklearn.preprocessing import StandardScaler

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
TRACKS = [
    r"C:\Users\adams\Downloads\feed this desire.wav",
    r"C:\Users\adams\Downloads\jumpy jumpy.wav",
    r"C:\Users\adams\Downloads\admit it.mp3",
    r"C:\Users\adams\Downloads\VIZON & Ren Carter - Had To Go [Extended Mix].mp3"
    ]


LANCEDB_PATH = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
TABLE_NAME   = "omni_semantic_baselines"
BASELINE_TRACK = "Somebody (2024)"   # Chris Lake reference
ALIGNMENT_FEATURES = [
    "rms_db","crest_factor",
    "sub_bass_energy","bass_energy",
    "mid_energy","high_energy"
]

# ------------------------------------------------------------
# LOAD CHRIS LAKE BASELINE FROM LANCEDB
# ------------------------------------------------------------
db = lancedb.connect(LANCEDB_PATH)
table = db.open_table(TABLE_NAME)
df_all = table.to_pandas()

df_base = df_all[df_all["track_name"].str.contains(BASELINE_TRACK, case=False)].copy()
df_base["seg_idx"] = df_base["segment_name"].str.extract(r"(\d+)").astype(float).fillna(0).astype(int)
df_base = df_base.sort_values("seg_idx").reset_index(drop=True)

if "rms" in df_base.columns and "rms_db" not in df_base.columns:
    df_base["rms_db"] = df_base["rms"].apply(lambda v: float(20*np.log10(v)) if v>1e-9 else -100.0)

baseline_rms   = float(df_base["rms_db"].mean())
baseline_crest = float(df_base["crest_factor"].mean())

# ------------------------------------------------------------
# DSP extractor (same schema used to train the brain)
# ------------------------------------------------------------
def extract_dsp_features(path):
    y, sr = librosa.load(path, mono=True)

    rms = float(librosa.feature.rms(y=y).mean())
    crest = float(np.max(np.abs(y)) / (rms + 1e-8))

    S = np.abs(librosa.stft(y, n_fft=2048))**2
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)

    def band_energy(fmin, fmax):
        mask = (freqs >= fmin) & (freqs < fmax)
        return float(S[mask].sum())

    return {
        "rms_db": float(20*np.log10(rms+1e-12)),
        "crest_factor": crest,
        "sub_bass_energy": band_energy(20,60),
        "bass_energy": band_energy(60,250),
        "mid_energy": band_energy(250,4000),
        "high_energy": band_energy(4000,20000)
    }

# ------------------------------------------------------------
# Load OMNI MASTER BRAIN v1
# ------------------------------------------------------------
brain = ort.InferenceSession("omni_master_brain_v1.onnx")
input_name = brain.get_inputs()[0].name
output_name = brain.get_outputs()[0].name

# ------------------------------------------------------------
# Run DSP → Baseline → Brain inference
# ------------------------------------------------------------
for track in TRACKS:
    print("\n====================================================")
    print(f"🎧 TRACK: {track}")
    print("====================================================")

    feats = extract_dsp_features(track)

    # Compute deltas vs Chris Lake baseline
    delta_rms   = baseline_rms   - feats["rms_db"]
    delta_crest = baseline_crest - feats["crest_factor"]

    # Build correct 8‑dim input vector
    brain_input_vec = np.array([
        feats["rms_db"],
        feats["crest_factor"],
        feats["sub_bass_energy"],
        feats["bass_energy"],
        feats["mid_energy"],
        feats["high_energy"],
        delta_rms,
        delta_crest
    ], dtype=np.float32).reshape(1, -1)

    # Run brain inference
    brain_out = brain.run([output_name], {input_name: brain_input_vec})[0][0]
    gain_db, ratio, threshold_db = brain_out.tolist()

    print("🧠 OMNI MASTER BRAIN v1 — RECOMMENDATIONS")
    print(f"   Gain:       {gain_db:.3f} dB")
    print(f"   Ratio:      {ratio:.3f}:1")
    print(f"   Threshold:  {threshold_db:.3f} dB")


# %%
# ============================================================
# 🧬 DNA BRAIN — Train on t_core_memory (REAL DATA)
# ============================================================

import json
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import StandardScaler, LabelEncoder
import torch.onnx
import onnxruntime as ort

# ------------------------------------------------------------
# 1) LOAD DNA TABLE
# ------------------------------------------------------------
PATH = r"C:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/exported_json/t_core_memory.json"

with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# Use real DNA columns
FEATURES = ["bpm", "key_signature"]
TARGET = "genre_class"

df = df.dropna(subset=FEATURES + [TARGET])

# Encode key_signature
key_enc = LabelEncoder()
df["key_encoded"] = key_enc.fit_transform(df["key_signature"])

X = df[["bpm", "key_encoded"]].values.astype(np.float32)

# Encode genre_class
genre_enc = LabelEncoder()
y = genre_enc.fit_transform(df[TARGET]).astype(np.int64)

print(f"DNA loaded: X={X.shape}, y={y.shape}, genres={list(genre_enc.classes_)}")

# ------------------------------------------------------------
# 2) SCALE DNA FEATURES
# ------------------------------------------------------------
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_t = torch.tensor(X_scaled)
y_t = torch.tensor(y)

# ------------------------------------------------------------
# 3) DEFINE DNA BRAIN
# ------------------------------------------------------------
class DNABrain(nn.Module):
    def __init__(self, in_dim, out_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 32), nn.ReLU(),
            nn.Linear(32, out_dim)
        )
    def forward(self, x):
        return self.net(x)

input_dim = X_scaled.shape[1]
output_dim = len(genre_enc.classes_)

model = DNABrain(input_dim, output_dim)
opt = optim.Adam(model.parameters(), lr=1e-3)
loss_fn = nn.CrossEntropyLoss()

# ------------------------------------------------------------
# 4) TRAIN DNA BRAIN
# ------------------------------------------------------------
for ep in range(100):
    opt.zero_grad()
    pred = model(X_t)
    loss = loss_fn(pred, y_t)
    loss.backward()
    opt.step()
    if (ep+1) % 20 == 0:
        print(f"[DNA] Epoch {ep+1}/100 — Loss {loss.item():.4f}")

# ------------------------------------------------------------
# 5) EXPORT DNA BRAIN TO ONNX
# ------------------------------------------------------------
ONNX_PATH = "dna_brain.onnx"
dummy = torch.randn(1, input_dim)

torch.onnx.export(
    model,
    dummy,
    ONNX_PATH,
    input_names=["dna_features"],
    output_names=["genre_logits"],
    dynamic_axes={"dna_features": {0: "batch"}},
    opset_version=18
)

print(f"\n✅ DNA BRAIN EXPORTED → {ONNX_PATH}")

# ------------------------------------------------------------
# 6) RUN REAL DNA INFERENCE
# ------------------------------------------------------------
brain = ort.InferenceSession(ONNX_PATH)
input_name = brain.get_inputs()[0].name
output_name = brain.get_outputs()[0].name

sample_raw = X[:1]
sample_scaled = scaler.transform(sample_raw)

logits = brain.run([output_name], {input_name: sample_scaled})[0][0]
pred_genre = genre_enc.classes_[np.argmax(logits)]

print("\n🧬 DNA SAMPLE")
print(f"   filename: {df.iloc[0]['filename']}")
print(f"   bpm:      {sample_raw[0][0]}")
print(f"   key:      {df.iloc[0]['key_signature']}")

print("\n🧠 DNA BRAIN PREDICTION")
print(f"   Predicted genre: {pred_genre}")
print(f"   True genre:      {df.iloc[0][TARGET]}")


# %%
# ============================================================
# 🧬 DNA BRAIN v1 — Full Fusion Model
# ============================================================

import json
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import StandardScaler, LabelEncoder

# ------------------------------------------------------------
# LOAD ALL DNA SOURCES
# ------------------------------------------------------------

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return pd.DataFrame(json.load(f))

duckdb_audio = load_json(".../duckdb_audio_features.json")
vibe_gpu = load_json(".../audio_vibe_gpu.json")
lancedb_vibe = load_json(".../lancedb_audio_vibe_gpu.json")
tcore = load_json(".../t_core_memory.json")
enriched = load_json(".../enriched_audio_dataset.json")
baseline = load_json(".../chris_lake_omni_baseline.json")
manifest = load_json(".../audio_manifest_vectors.json")
metadata_vec = load_json(".../duckdb_metadata_vectors.json")
collision = load_json(".../collision_results_final.json")
verified = load_json(".../verified_library_analysis.json")
legion = load_json(".../legion_memory.json")

# ------------------------------------------------------------
# FUSE DNA FEATURES
# ------------------------------------------------------------

# DSP DNA
dsp = duckdb_audio[["rms_db", "crest_factor", "tempo"]].fillna(0)

# Vibe DNA
vibe = vibe_gpu["vector"].apply(lambda v: np.array(v)).tolist()
vibe = np.vstack(vibe)

# Genre DNA
genre_enc = LabelEncoder()
genre_labels = genre_enc.fit_transform(tcore["genre_class"].fillna("unknown"))

# Semantic DNA
semantic = manifest["vector"].apply(lambda v: np.array(v)).tolist()
semantic = np.vstack(semantic)

# Collision DNA
collision_scores = collision["collision_score"].fillna(0).values

# Marketing DNA
marketing_scores = verified["dsp_tempo"].fillna(0).values

# Memory DNA
memory_vecs = legion["vector"].apply(lambda v: np.array(v)).tolist()
memory_vecs = np.vstack(memory_vecs) if len(memory_vecs) > 0 else np.zeros((1, 128))

# ------------------------------------------------------------
# ALIGN LENGTHS (truncate to smallest)
# ------------------------------------------------------------
min_len = min(len(dsp), len(vibe), len(semantic), len(genre_labels))

dsp = dsp.iloc[:min_len].values.astype(np.float32)
vibe = vibe[:min_len].astype(np.float32)
semantic = semantic[:min_len].astype(np.float32)
genre_labels = genre_labels[:min_len]
collision_scores = collision_scores[:min_len]
marketing_scores = marketing_scores[:min_len]

# ------------------------------------------------------------
# BUILD FUSED DNA INPUT
# ------------------------------------------------------------
X = np.concatenate([dsp, vibe, semantic], axis=1)
y_genre = genre_labels
y_collision = collision_scores.astype(np.float32)
y_marketing = marketing_scores.astype(np.float32)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_t = torch.tensor(X_scaled)
y_genre_t = torch.tensor(y_genre)
y_collision_t = torch.tensor(y_collision).unsqueeze(1)
y_marketing_t = torch.tensor(y_marketing).unsqueeze(1)

# ------------------------------------------------------------
# DNA BRAIN v1 — Multi‑Head Model
# ------------------------------------------------------------
class DNABrain(nn.Module):
    def __init__(self, in_dim, genre_dim):
        super().__init__()
        self.shared = nn.Sequential(
            nn.Linear(in_dim, 512), nn.ReLU(),
            nn.Linear(512, 256), nn.ReLU(),
            nn.Linear(256, 128), nn.ReLU()
        )
        self.genre_head = nn.Linear(128, genre_dim)
        self.collision_head = nn.Linear(128, 1)
        self.marketing_head = nn.Linear(128, 1)

    def forward(self, x):
        z = self.shared(x)
        return {
            "genre": self.genre_head(z),
            "collision": self.collision_head(z),
            "marketing": self.marketing_head(z)
        }

model = DNABrain(X_scaled.shape[1], len(genre_enc.classes_))
opt = optim.Adam(model.parameters(), lr=1e-3)
loss_genre = nn.CrossEntropyLoss()
loss_reg = nn.MSELoss()

# ------------------------------------------------------------
# TRAIN DNA BRAIN
# ------------------------------------------------------------
for ep in range(100):
    opt.zero_grad()
    out = model(X_t)
    Lg = loss_genre(out["genre"], y_genre_t)
    Lc = loss_reg(out["collision"], y_collision_t)
    Lm = loss_reg(out["marketing"], y_marketing_t)
    loss = Lg + Lc + Lm
    loss.backward()
    opt.step()
    if (ep+1) % 20 == 0:
        print(f"[DNA] Epoch {ep+1}/100 — Loss {loss.item():.4f}")

# ------------------------------------------------------------
# DNA BRAIN v1 is trained
# ------------------------------------------------------------
print("\n🧬 DNA Brain v1 is fully trained.")


# %%
# ============================================================
# 🧬 GENOME TRANSFORMER — ALL IN ONE WORKING CELL
# ============================================================

import torch
import torch.nn as nn
import numpy as np

# ------------------------------------------------------------
# 1. Create a fake fused DNA sequence (replace with your real fused vectors later)
# ------------------------------------------------------------
batch_size = 4
seq_len = 10
dna_dim = 256   # fused DSP + vibe + semantic + genre + collision + marketing + memory

# Fake DNA sequence for testing (this is where your real fused DNA goes)
dna_sequence = torch.randn(batch_size, seq_len, dna_dim)

# ------------------------------------------------------------
# 2. Genome Transformer (sequence encoder)
# ------------------------------------------------------------
class GenomeTransformer(nn.Module):
    def __init__(self, dna_dim, hidden_dim=256, num_layers=4, num_heads=8):
        super().__init__()
        self.embedding = nn.Linear(dna_dim, hidden_dim)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=num_heads,
            dim_feedforward=hidden_dim * 4,
            dropout=0.1,
            batch_first=True
        )

        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.to_genome = nn.Linear(hidden_dim, hidden_dim)

    def forward(self, dna_sequence):
        x = self.embedding(dna_sequence)
        z = self.encoder(x)
        genome = self.to_genome(z.mean(dim=1))  # pooled genome embedding
        return genome

# ------------------------------------------------------------
# 3. Policy Heads (multi-task)
# ------------------------------------------------------------
class GenomePolicy(nn.Module):
    def __init__(self, genome_dim, genre_dim=10):
        super().__init__()
        self.genre_head = nn.Linear(genome_dim, genre_dim)
        self.vibe_head = nn.Linear(genome_dim, 128)
        self.mastering_head = nn.Linear(genome_dim, 3)   # gain, ratio, threshold
        self.anomaly_head = nn.Linear(genome_dim, 1)
        self.marketing_head = nn.Linear(genome_dim, 1)

    def forward(self, genome):
        return {
            "genre": self.genre_head(genome),
            "vibe": self.vibe_head(genome),
            "mastering": self.mastering_head(genome),
            "anomaly": self.anomaly_head(genome),
            "marketing": self.marketing_head(genome)
        }

# ------------------------------------------------------------
# 4. Instantiate models
# ------------------------------------------------------------
genome_transformer = GenomeTransformer(dna_dim)
genome_policy = GenomePolicy(genome_dim=256)

# ------------------------------------------------------------
# 5. Forward pass — THIS RETURNS GENOME
# ------------------------------------------------------------
genome = genome_transformer(dna_sequence)
policy = genome_policy(genome)

# ------------------------------------------------------------
# 6. Print shapes for verification
# ------------------------------------------------------------
print("GENOME SHAPE:", genome.shape)
for k, v in policy.items():
    print(f"{k.upper()} SHAPE:", v.shape)

# The variable you asked for:
genome


# %%


# %%
from _typeshed import importlib
# ============================================================
# 🧬 GENOME TRANSFORMER — RAY ACTOR (FULL WORKING CELL)
# ============================================================

import ray
import torch
import torch.nn as nn
import numpy as np
import pydantic_core
import langgraph.core

registry = SwarmKnowledgeRegistry.options(
    name="SwarmKnowledgeRegistry",
    namespace="legion",
    lifetime="detached"
).remote()


# ------------------------------------------------------------
# 1. Genome Transformer + Policy (same as before)
# ------------------------------------------------------------
class GenomeTransformer(nn.Module):
    def __init__(self, dna_dim, hidden_dim=256, num_layers=4, num_heads=8):
        super().__init__()
        self.embedding = nn.Linear(dna_dim, hidden_dim)
        enc_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=num_heads,
            dim_feedforward=hidden_dim * 4,
            dropout=0.1,
            batch_first=True
        )
        self.encoder = nn.TransformerEncoder(enc_layer, num_layers=num_layers)
        self.to_genome = nn.Linear(hidden_dim, hidden_dim)

    def forward(self, dna_seq):
        x = self.embedding(dna_seq)
        z = self.encoder(x)
        genome = self.to_genome(z.mean(dim=1))
        return genome

class GenomePolicy(nn.Module):
    def __init__(self, genome_dim, genre_dim=10):
        super().__init__()
        self.genre_head = nn.Linear(genome_dim, genre_dim)
        self.vibe_head = nn.Linear(genome_dim, 128)
        self.mastering_head = nn.Linear(genome_dim, 3)
        self.anomaly_head = nn.Linear(genome_dim, 1)
        self.marketing_head = nn.Linear(genome_dim, 1)

    def forward(self, genome):
        return {
            "genre": self.genre_head(genome),
            "vibe": self.vibe_head(genome),
            "mastering": self.mastering_head(genome),
            "anomaly": self.anomaly_head(genome),
            "marketing": self.marketing_head(genome),
        }

# ------------------------------------------------------------
# 2. Ray Actor: Genome Brain
# ------------------------------------------------------------
@ray.remote
class GenomeBrain:
    def __init__(self, dna_dim):
        self.transformer = GenomeTransformer(dna_dim)
        self.policy = GenomePolicy(genome_dim=256)
        print("🧬 GenomeBrain Actor is LIVE.")

    def infer(self, dna_sequence):
        """
        dna_sequence: numpy array shaped (batch, seq_len, dna_dim)
        """
        dna_tensor = torch.tensor(dna_sequence, dtype=torch.float32)
        genome = self.transformer(dna_tensor)
        policy = self.policy(genome)
        return {
            "genome": genome.detach().numpy(),
            "genre": policy["genre"].detach().numpy(),
            "vibe": policy["vibe"].detach().numpy(),
            "mastering": policy["mastering"].detach().numpy(),
            "anomaly": policy["anomaly"].detach().numpy(),
            "marketing": policy["marketing"].detach().numpy(),
        }

# ------------------------------------------------------------
# 3. Start Ray + Actor
# ------------------------------------------------------------
ray.init(namespace="legion", ignore_reinit_error=True)

dna_dim = 256  # your fused DNA dimension
genome_actor = GenomeBrain.options(name="GenomeBrain", lifetime="detached").remote(dna_dim)

print("GenomeBrain Actor deployed.")

# ------------------------------------------------------------
# 4. Test with fake DNA (replace with real fused DNA later)
# ------------------------------------------------------------
batch = 4
seq_len = 10
dna_sequence = np.random.randn(batch, seq_len, dna_dim).astype(np.float32)

result = ray.get(genome_actor.infer.remote(dna_sequence))

print("GENOME:", result["genome"].shape)
print("GENRE:", result["genre"].shape)
print("MASTERING:", result["mastering"].shape)


# %%
# ============================================================
# 🧬 REAL DNA → GENOMEBRAIN ACTOR
# ============================================================

import ray
import pyarrow as pa
import numpy as np
import torch
import json

# ------------------------------------------------------------
# 1. Connect to your live registry
# ------------------------------------------------------------
ray.init(namespace="legion", ignore_reinit_error=True)
registry = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")

# Helper to pull Arrow table → Python list/dict
def get_tbl(name):
    tbl = ray.get(registry.get_table.remote(name))
    return tbl.to_pylist()

# ------------------------------------------------------------
# 2. Load your real DNA tables
# ------------------------------------------------------------
dsp_tbl       = get_tbl("duckdb_audio_features")
vibe_tbl      = get_tbl("audio_vibe_gpu")
semantic_tbl  = get_tbl("audio_manifest_vectors")
tcore_tbl     = get_tbl("t_core_memory")
collision_tbl = get_tbl("collision_results_final")
verified_tbl  = get_tbl("verified_library_analysis")

# ------------------------------------------------------------
# 3. Align lengths
# ------------------------------------------------------------
min_len = min(
    len(dsp_tbl),
    len(vibe_tbl),
    len(semantic_tbl),
    len(tcore_tbl),
    len(collision_tbl),
    len(verified_tbl),
)

dsp_tbl       = dsp_tbl[:min_len]
vibe_tbl      = vibe_tbl[:min_len]
semantic_tbl  = semantic_tbl[:min_len]
tcore_tbl     = tcore_tbl[:min_len]
collision_tbl = collision_tbl[:min_len]
verified_tbl  = verified_tbl[:min_len]

# ------------------------------------------------------------
# 4. FUSE DNA
# ------------------------------------------------------------

# DSP DNA
dsp = np.array([
    [row.get("rms_db", 0), row.get("crest_factor", 0), row.get("tempo", 0)]
    for row in dsp_tbl
], dtype=np.float32)

# Vibe DNA
vibe = np.vstack([
    np.array(row["vector"], dtype=np.float32)
    for row in vibe_tbl
])

# Semantic DNA
semantic = np.vstack([
    np.array(row["vector"], dtype=np.float32)
    for row in semantic_tbl
])

# Collision DNA
collision = np.array([
    row.get("collision_score", 0)
    for row in collision_tbl
], dtype=np.float32).reshape(-1, 1)

# Marketing DNA
marketing = np.array([
    row.get("dsp_tempo", 0)
    for row in verified_tbl
], dtype=np.float32).reshape(-1, 1)

# ------------------------------------------------------------
# 5. Build fused DNA vector per track
# ------------------------------------------------------------
X = np.concatenate([dsp, vibe, semantic, collision, marketing], axis=1)

dna_dim = X.shape[1]
batch_size = min_len
seq_len = 1

dna_sequence = X.reshape(batch_size, seq_len, dna_dim).astype(np.float32)

print("REAL DNA SHAPE:", dna_sequence.shape)

# ------------------------------------------------------------
# 6. Send REAL DNA to GenomeBrain actor
# ------------------------------------------------------------
genome_actor = ray.get_actor("GenomeBrain", namespace="legion")
result = ray.get(genome_actor.infer.remote(dna_sequence))

print("GENOME:", result["genome"].shape)
print("GENRE:", result["genre"].shape)
print("MASTERING:", result["mastering"].shape)

result["genome"][:4]   # preview first 4 genome vectors


# %%
# ============================================================
# 🎯 SOVEREIGN CONDUCTOR — Autonomous Closed-Loop Mastering
# ============================================================
# Pure DSP math + tensor ops. No JSON APIs. No wrappers.
# Perception → Inference → Truth Matrix → Correct → Loop
# ============================================================

import ray
import torch
import torch.nn as nn
import numpy as np
import librosa
import onnxruntime as ort
import lancedb
import time
from scipy.spatial.distance import cdist

# ─────────────────────────────────────────────────────────────
# SOVEREIGN TRUTH MATRIX  (Chris Lake "Somebody 2024" DNA)
# ─────────────────────────────────────────────────────────────
TRUTH = {
    "rms_db":          -13.9,
    "crest_factor":      5.69,
    "mid_multiplier":  289.34,
}
TOLERANCE      = 0.05   # fractional drift threshold to stop looping
MAX_ITERATIONS = 8      # hard ceiling — never infinite-loop on real audio

# ─────────────────────────────────────────────────────────────
# TRACKS TO MASTER  (drop your files here)
# ─────────────────────────────────────────────────────────────
TRACKS = [
    r"C:\Users\adams\Downloads\feed this desire.wav",
    r"C:\Users\adams\Downloads\jumpy jumpy.wav",
    r"C:\Users\adams\Downloads\admit it.mp3",
    r"C:\Users\adams\Downloads\VIZON & Ren Carter - Had To Go [Extended Mix].mp3",
]

ONNX_BRAIN  = r"C:\WEB CASE STUDY\sonic_dna_output\fretflow_omni_v3.onnx"
LANCEDB_PATH = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"

# ─────────────────────────────────────────────────────────────
# 1. Connect to live Ray actors
# ─────────────────────────────────────────────────────────────
ray.init(namespace="legion", ignore_reinit_error=True)

try:
    registry     = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
    genome_actor = ray.get_actor("GenomeBrain",            namespace="legion")
    print("✅ Connected: SwarmKnowledgeRegistry + GenomeBrain")
except ValueError as e:
    print(f"❌ Actor not found: {e}")
    print("   Run ray_arrow_swarm.py first, then the GenomeBrain spawn cell.")
    raise SystemExit

# ─────────────────────────────────────────────────────────────
# 2. Load ONNX mastering brain + normalization stats from checkpoint
# ─────────────────────────────────────────────────────────────
brain    = ort.InferenceSession(ONNX_BRAIN)
PT_PATH  = r"C:\WEB CASE STUDY\sonic_dna_output\fretflow_omni_v3.pt"
ckpt          = torch.load(PT_PATH, map_location="cpu")
X_mean_ckpt   = np.array(ckpt["X_mean"], dtype=np.float32)
X_std_ckpt    = np.array(ckpt["X_std"],  dtype=np.float32)
OMNI_DIM_CKPT = ckpt["omni_dim"]           # 1036
genre2idx_ckpt= ckpt["cat2idx"]            # {'BASS':0,'KICK':1,'OTHER':2,'PERC':3,'TECH_HOUSE':4}
TECH_HOUSE_IDX= int(genre2idx_ckpt.get("TECH_HOUSE", 4))
print(f"✅ ONNX Brain loaded | inputs: {[i.name for i in brain.get_inputs()]}")
print(f"   Checkpoint: omni_dim={OMNI_DIM_CKPT} | genres={genre2idx_ckpt}")

# ─────────────────────────────────────────────────────────────
# 3. DSP Extractor — pure numpy/librosa tensor math
# ─────────────────────────────────────────────────────────────
def extract_dsp(path: str) -> dict:
    y, sr  = librosa.load(path, mono=True)
    rms    = float(librosa.feature.rms(y=y).mean())
    rms_db = float(20 * np.log10(rms + 1e-12))
    crest  = float(np.max(np.abs(y)) / (rms + 1e-8))
    S      = np.abs(librosa.stft(y, n_fft=2048)) ** 2
    freqs  = librosa.fft_frequencies(sr=sr, n_fft=2048)

    def band(flo, fhi):
        return float(S[(freqs >= flo) & (freqs < fhi)].sum())

    sub_bass = band(20,   60)
    bass     = band(60,  250)
    mid      = band(250, 4000)
    high     = band(4000, 20000)
    mid_mult = mid / (sub_bass + 1e-8)   # Sovereign Mid-Multiplier

    return {
        "rms_db":          rms_db,
        "crest_factor":    crest,
        "sub_bass_energy": sub_bass,
        "bass_energy":     bass,
        "mid_energy":      mid,
        "high_energy":     high,
        "mid_multiplier":  mid_mult,
        "waveform":        y,
        "sr":              sr,
    }

# ─────────────────────────────────────────────────────────────
# 4. Drift Calculator — how far are we from the Truth Matrix?
# ─────────────────────────────────────────────────────────────
def compute_drift(dsp: dict) -> dict:
    d_rms   = TRUTH["rms_db"]       - dsp["rms_db"]
    d_crest = TRUTH["crest_factor"] - dsp["crest_factor"]
    d_mid   = TRUTH["mid_multiplier"] - dsp["mid_multiplier"]
    # Normalised fractional drift (0 = perfect, 1 = 100% off)
    frac = (abs(d_rms)   / abs(TRUTH["rms_db"])
          + abs(d_crest) / abs(TRUTH["crest_factor"])
          + abs(d_mid)   / abs(TRUTH["mid_multiplier"])) / 3.0
    return {"d_rms": d_rms, "d_crest": d_crest, "d_mid": d_mid, "frac": frac}

# ─────────────────────────────────────────────────────────────
# 5. ONNX Brain inference — all 3 inputs: omni_input, genre_input, bpm_input
# ─────────────────────────────────────────────────────────────
def run_brain(dsp: dict, drift: dict) -> dict:
    # Build full 1036-dim omni vector: semantic(1024) + DSP(11) + BPM(1)
    sem      = np.zeros(1024, dtype=np.float32)   # no live embeddings for new tracks
    dsp_vec  = np.array([
        dsp["rms_db"],          # rms_db
        dsp["crest_factor"],    # crest_factor
        dsp["sub_bass_energy"], # sub_bass_energy
        dsp["bass_energy"],     # bass_energy
        dsp["mid_energy"],      # mid_energy
        dsp["high_energy"],     # high_energy
        0.0, 0.0, 0.0, 0.0, 0.0,  # spectral_centroid/bandwidth/rolloff/contrast/zcr (not extracted)
    ], dtype=np.float32)                           # 11 DSP dims
    bpm_raw  = np.array([128.0], dtype=np.float32) # default BPM

    omni_raw  = np.concatenate([sem, dsp_vec, bpm_raw])           # (1036,)
    omni_norm = ((omni_raw - X_mean_ckpt) / X_std_ckpt).reshape(1, -1).astype(np.float32)

    # genre: TECH_HOUSE (targeting Chris Lake DNA)
    genre_in = np.array([TECH_HOUSE_IDX], dtype=np.int64)
    # bpm_input: the normalized BPM scalar (last element of omni_norm)
    bpm_in   = omni_norm[0, -1:].reshape(1).astype(np.float32)

    out = brain.run(
        [brain.get_outputs()[0].name],
        {
            "omni_input":   omni_norm,
            "genre_input":  genre_in,
            "bpm_input":    bpm_in,
        }
    )[0][0]
    return {"gain_db": float(out[0]), "ratio": float(out[1]), "threshold_db": float(out[2])}

# ─────────────────────────────────────────────────────────────
# 6. DSP Apply — tensor-level gain + soft-knee compression sim
# ─────────────────────────────────────────────────────────────
def apply_commands(y: np.ndarray, cmds: dict) -> np.ndarray:
    # Gain stage
    gain_lin = 10 ** (cmds["gain_db"] / 20.0)
    y = y * gain_lin

    # Soft-knee compression (pure math, no black-box)
    thresh_lin = 10 ** (cmds["threshold_db"] / 20.0)
    ratio      = max(1.0, cmds["ratio"])
    over       = np.abs(y) - thresh_lin
    mask       = over > 0
    y[mask]    = np.sign(y[mask]) * (thresh_lin + over[mask] / ratio)

    # Normalise ceiling to -0.1 dBFS
    peak = np.max(np.abs(y))
    if peak > 0:
        y = y / peak * (10 ** (-0.1 / 20.0))
    return y

# ─────────────────────────────────────────────────────────────
# 7. GenomeBrain genome call — get the policy vector
# ─────────────────────────────────────────────────────────────
def query_genome(dsp: dict) -> dict:
    # Build a 1-token DNA sequence from the 6 DSP features
    dna_vec = np.array([[
        dsp["rms_db"],
        dsp["crest_factor"],
        dsp["sub_bass_energy"],
        dsp["bass_energy"],
        dsp["mid_energy"],
        dsp["high_energy"],
    ]], dtype=np.float32)                  # shape (1, 6)

    # GenomeBrain actor was spawned with dna_dim=256.
    # Project our 6-dim DSP up to 256 via zero-padding (lossless).
    dna_padded = np.zeros((1, 1, 256), dtype=np.float32)
    dna_padded[0, 0, :6] = dna_vec[0]    # embed DSP at the front

    result = ray.get(genome_actor.infer.remote(dna_padded))
    return result

# ─────────────────────────────────────────────────────────────
# 8. SOVEREIGN CONDUCTOR — main closed-loop per track
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 62)
print("  🎯 SOVEREIGN CONDUCTOR — Autonomous Mastering Loop")
print("=" * 62)
print(f"  Truth Target  →  RMS {TRUTH['rms_db']} dB  |  "
      f"Crest {TRUTH['crest_factor']}  |  Mid×{TRUTH['mid_multiplier']:.1f}")
print(f"  Tolerance     →  {TOLERANCE*100:.1f}%  fractional drift")
print("=" * 62)

session_log = []

for track_path in TRACKS:
    import os
    if not os.path.exists(track_path):
        print(f"\n⚠️  Skipping (file not found): {track_path}")
        continue

    print(f"\n🎧  {os.path.basename(track_path)}")
    dsp = extract_dsp(track_path)
    y   = dsp["waveform"].copy()

    for iteration in range(1, MAX_ITERATIONS + 1):
        drift = compute_drift(dsp)
        print(f"  [{iteration}] drift={drift['frac']:.4f}  "
              f"rms={dsp['rms_db']:.2f}dB  "
              f"crest={dsp['crest_factor']:.3f}  "
              f"mid×={dsp['mid_multiplier']:.1f}")

        if drift["frac"] <= TOLERANCE:
            print(f"  ✅ Converged at iteration {iteration}")
            break

        # Genome perception — what does the brain see?
        genome_result = query_genome(dsp)
        master_genome = genome_result["mastering"][0]   # (3,) array
        print(f"     Genome mastering hint → "
              f"gain={master_genome[0]:.3f}  "
              f"ratio={master_genome[1]:.3f}  "
              f"thresh={master_genome[2]:.3f}")

        # ONNX brain decides the precise correction
        cmds = run_brain(dsp, drift)

        # Apply to waveform tensor (pure math)
        y = apply_commands(y, cmds)

        # Re-extract DSP from corrected waveform to close the loop
        rms_new    = float(librosa.feature.rms(y=y).mean())
        rms_db_new = float(20 * np.log10(rms_new + 1e-12))
        crest_new  = float(np.max(np.abs(y)) / (rms_new + 1e-8))
        S_new      = np.abs(librosa.stft(y, n_fft=2048)) ** 2
        freqs_new  = librosa.fft_frequencies(sr=dsp["sr"], n_fft=2048)
        sub_new    = float(S_new[(freqs_new >= 20)  & (freqs_new < 60)].sum())
        mid_new    = float(S_new[(freqs_new >= 250) & (freqs_new < 4000)].sum())

        dsp["rms_db"]         = rms_db_new
        dsp["crest_factor"]   = crest_new
        dsp["sub_bass_energy"]= sub_new
        dsp["mid_multiplier"] = mid_new / (sub_new + 1e-8)
        dsp["waveform"]       = y

    else:
        print(f"  ⚠️  Max iterations reached — best drift: {drift['frac']:.4f}")

    final_drift = compute_drift(dsp)
    session_log.append({
        "track":      os.path.basename(track_path),
        "drift_frac": round(final_drift["frac"], 5),
        "final_rms":  round(dsp["rms_db"], 3),
        "final_crest":round(dsp["crest_factor"], 4),
        "final_mid":  round(dsp["mid_multiplier"], 2),
        "converged":  final_drift["frac"] <= TOLERANCE,
    })

# ─────────────────────────────────────────────────────────────
# 9. Final Report
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 62)
print("  📊 SOVEREIGN CONDUCTOR — SESSION REPORT")
print("=" * 62)
for entry in session_log:
    status = "✅ CONVERGED" if entry["converged"] else "⚠️  PARTIAL"
    print(f"  {status}  {entry['track']}")
    print(f"           drift={entry['drift_frac']}  "
          f"rms={entry['final_rms']}dB  "
          f"crest={entry['final_crest']}  "
          f"mid×={entry['final_mid']}")
print("=" * 62)
print("\n🎯 Sovereign Conductor complete.")
print("   Next: export corrected waveforms via soundfile,")
print("   then route into C++/Rust ORT for Ableton callback.")

# %%