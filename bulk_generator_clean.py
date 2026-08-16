import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import os
import datetime
from scipy.spatial.distance import cdist
import lancedb
import warnings
warnings.filterwarnings('ignore')

print("[BOOT] Running CLEAN BULK Generation Trace (100 Tracks)...")

# Load Semantic Vectors
LANCEDB_PATH = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\vectors\lancedb_store"
ldb = lancedb.connect(LANCEDB_PATH)
vibe_df = ldb.open_table("audio_vibe_gpu").to_pandas()

# Load Clean Enriched Samples
samples_df = pd.read_json(r'C:\WEB CASE STUDY\data\enriched_samples_only.json')

# Merge them on filename
df = pd.merge(vibe_df, samples_df, on='filename', how='inner')

def build_omni_vector(row):
    sem = np.array(row['vector'], dtype=np.float32)
    bpm = np.array([float(row.get('tempo', 128.0))], dtype=np.float32)
    return np.concatenate([sem, bpm])

df['omni_vector'] = df.apply(build_omni_vector, axis=1)

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

# Split into component pools
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

log_entries = []
seeds = df.sample(min(100, len(df)))

bass_mat = np.vstack([x[:384] for x in df_basses['omni_vector'].values])
kick_mat = np.vstack([x[:384] for x in df_kicks['omni_vector'].values])
perc_mat = np.vstack([x[:384] for x in df_perc['omni_vector'].values])

for idx, row in seeds.iterrows():
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

    dists_bass = cdist([semantic_slice], np.nan_to_num(bass_mat, nan=0.0), metric="cosine")[0]
    best_bass = sample_top_k(dists_bass, df_basses)
    bass_file = os.path.basename(best_bass.get('filepath', '')) if pd.notna(best_bass.get('filepath', '')) else best_bass['filename']

    dists_kick = cdist([semantic_slice], np.nan_to_num(kick_mat, nan=0.0), metric="cosine")[0]
    best_kick = sample_top_k(dists_kick, df_kicks)
    kick_file = os.path.basename(best_kick.get('filepath', '')) if pd.notna(best_kick.get('filepath', '')) else best_kick['filename']

    dists_perc = cdist([semantic_slice], np.nan_to_num(perc_mat, nan=0.0), metric="cosine")[0]
    best_perc = sample_top_k(dists_perc, df_perc)
    perc_file = os.path.basename(best_perc.get('filepath', '')) if pd.notna(best_perc.get('filepath', '')) else best_perc['filename']

    log_entries.append({
        "Seed": row['filename'],
        "Bass_File": bass_file,
        "Kick_File": kick_file,
        "Perc_File": perc_file
    })

log_df = pd.DataFrame(log_entries)
log_path = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\generated_audio\bulk_generation_clean_log.csv"
log_df.to_csv(log_path, index=False)

print(f"\n[SUCCESS] Bulk generations completed.")
print(f"Log saved to: {log_path}")
print("\n--- NEW CLEAN BASS DISTRIBUTION ---")
print(log_df["Bass_File"].value_counts().head(10))
