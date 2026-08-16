import os, sys
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler
import torch
import torch.nn as nn

# Force UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

print("Loading unified Notebook LM + Code Swarm data...")
df_code = pd.read_parquet(r"C:\WEB CASE STUDY\code_knowledge_audit.parquet")
df_nb = pd.read_parquet(r"C:\WEB CASE STUDY\notebook_knowledge_audit.parquet")
shard_dir = Path(r"C:\WEB CASE STUDY\ray_cat_shards")
shard_dfs = []
for f in shard_dir.glob("*.jsonl"):
    try:
        shard_dfs.append(pd.read_json(f, lines=True))
    except Exception:
        pass
df_shards = pd.concat(shard_dfs, ignore_index=True)
df_shards['size_kb'] = df_shards.get('size_bytes', 0) / 1024.0
df_shards['rows'] = 0

cols_to_keep = ['filename', 'size_kb', 'rows']
df = pd.concat([
    df_code[[c for c in cols_to_keep if c in df_code.columns]],
    df_nb[[c for c in cols_to_keep if c in df_nb.columns]],
    df_shards[[c for c in cols_to_keep if c in df_shards.columns]]
], ignore_index=True)

df['ext'] = df['filename'].apply(lambda x: os.path.splitext(x)[1].lower() if isinstance(x, str) else '.unknown')
valid_classes = df['ext'].value_counts()[df['ext'].value_counts() >= 2].index
df_clean = df[df['ext'].isin(valid_classes)].copy().reset_index(drop=True)

features = ['size_kb', 'rows']
X = df_clean[features].fillna(0)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print(f"Data scaled perfectly. Initiating PyTorch Generative Autoencoder...")

class CodeGenomeAutoencoder(nn.Module):
    def __init__(self, in_dim, latent_dim=16, dropout_rate=0.1):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(in_dim, 64), nn.LayerNorm(64), nn.GELU(), nn.Dropout(dropout_rate), nn.Linear(64, latent_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 64), nn.LayerNorm(64), nn.GELU(), nn.Linear(64, in_dim)
        )
    def forward(self, x):
        return self.decoder(self.encoder(x))
    def generate_synthetic_footprint(self, x, jitter_amount=0.5):
        self.eval()
        with torch.no_grad():
            latent_dna = self.encoder(x)
            jitter = torch.randn_like(latent_dna) * jitter_amount
            mutated_dna = latent_dna + jitter
            synthetic_footprint = self.decoder(mutated_dna)
        return synthetic_footprint

in_dim = X_scaled.shape[1]
generative_model = CodeGenomeAutoencoder(in_dim=in_dim)

print("\n--- GRABBING A RANDOM NOTEBOOK LM FILE AS SEED ---")
# Find a json or ipynb file from the real dataset to use as the base DNA
seed_idx = df_clean[df_clean['filename'].str.contains('.json|.ipynb', na=False, case=False, regex=True)].index[0]
seed_name = df_clean.loc[seed_idx, 'filename']
seed_raw = X.loc[seed_idx].values
seed_scaled = X_scaled[seed_idx:seed_idx+1]

print(f"Seed Source DNA: {seed_name}")
print(f"Raw Seed: Size = {seed_raw[0]:.2f} KB | Rows = {seed_raw[1]:.0f}")

sample_tensor = torch.tensor(seed_scaled, dtype=torch.float32)
synthetic_tensor = generative_model.generate_synthetic_footprint(sample_tensor, jitter_amount=1.2)

print(f"\n🧬 GENOMIC INFERENCE TEST (Jitter Applied = 1.2)")
print(f"Scaled Mutated Tensor: {synthetic_tensor.numpy()[0]}")

synthetic_raw = scaler.inverse_transform(synthetic_tensor.numpy())
print(f"\n🔮 The PyTorch Autoencoder just mathematically hallucinated a synthetic Notebook LM footprint:")
print(f"   Generated Size: {synthetic_raw[0][0]:.2f} KB")
print(f"   Generated Rows: {int(abs(synthetic_raw[0][1]))}")
