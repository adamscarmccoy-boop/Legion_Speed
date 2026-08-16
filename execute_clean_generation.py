import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import os
import datetime
import re
import lancedb
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
    
    # Softmax with temperature
    logits = -top_k_dists / temperature
    exp_logits = np.exp(logits - np.max(logits))
    probs = exp_logits / np.sum(exp_logits)
    
    selected_idx = np.random.choice(top_k_indices, p=probs)
    return df_pool.iloc[selected_idx]

seeds = df.sample(3)
for idx, row in seeds.iterrows():
    print(f"\n{'='*50}\n[PHASE 1] Seed: {row['filename']}")
    
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
