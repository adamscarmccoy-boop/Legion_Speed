import pandas as pd
import numpy as np
import torch
import pyaudio as pa
import pyarrow as pas
import polars as pls
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

# Load Clean Enriched Samples
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
