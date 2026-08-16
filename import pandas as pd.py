
from openai.types.audio import transcription_diarized_segment
from openai.types.audio import transcription_diarized_segment
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import os, datetime, re, lancedb
import soundfile as sf
import warnings
warnings.filterwarnings('ignore')

print("[BOOT] Starting v3 Data-Aware Generation Engine...")

# =====================================================================
# 1. CONFIGURATION & PATHS
# =====================================================================
LANCEDB_PATH = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\vectors\lancedb_store"
TRACKS_JSON  = r'C:\WEB CASE STUDY\data\enriched_tracks_only.json'
SAMPLES_JSON = r'C:\WEB CASE STUDY\data\enriched_samples_only.json'
WEIGHTS_PATH = r"C:\WEB CASE STUDY\sonic_dna_output\fretflow_omni_v3.pt"
OUTPUT_DIR   = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\generated_audio"

# =====================================================================
# 2. DATA LOADING (SPLIT TRACKS vs SAMPLES)
# =====================================================================
print("[1/6] Loading Vector Space & Data Split...")
ldb = lancedb.connect(LANCEDB_PATH)
vibe_df = ldb.open_table("audio_vibe_gpu").to_pandas()   
# A. Load Full Tracks (The Blueprints)
tracks_df = pd.read_json(TRACKS_JSON)
df_tracks = pd.merge(vibe_df, tracks_df, on='filename', how='inner')
# B. Load Samples (The Building Blocks)
samples_df = pd.read_json(SAMPLES_JSON)
df_samples = pd.merge(vibe_df, samples_df, on='filename', how='inner')
print(f"  -> Blueprint Pool (Tracks): {len(df_tracks)}")
print(f"  -> Assembly Pool (Samples): {len(df_samples)}")
def build_omni_vector(row):
    sem = np.array(row['vector'], dtype=np.float32)
    bpm = np.array([float(row.get('tempo', 128.0))], dtype=np.float32])
    return np.concatenate([sem, bpm])

# We only need Omni-Vectors for the tracks we seed from and samples we retrieve
df_tracks['omni_vector'] = df_tracks.apply(build_omni_vector, axis=1)
df_samples['omni_vector'] = df_samples.apply(build_omni_vector, axis=1)

# =====================================================================
# 3. V3 ARCHITECTURE: OmniCondVAE
# =====================================================================
print("[2/6] Initializing OmniCondVAE v3...")
checkpoint = torch.load(WEIGHTS_PATH)
X_mean = np.array(checkpoint['X_mean'], dtype=np.float32)
X_std = np.array(checkpoint['X_std'], dtype=np.float32)

# We derive categories from the TRACKS dataset (where the vibe intelligence lives)
unique_genres = df_tracks['genre_class'].dropna().unique()
genre2idx = {genre: i for i, genre in enumerate(unique_genres)}

class OmniCondVAE(nn.Module):
    def __init__(self, in_dim, latent_dim, num_categories, emb_dim=16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(in_dim, 512), nn.LayerNorm(512), nn.GELU(),
            nn.Linear(512, 256), nn.LayerNorm(256), nn.GELU(),
            nn.Linear(256, 128), nn.LayerNorm(128), nn.GELU(),
            nn.Linear(128, latent_dim)
        )
        self.cat_emb = nn.Embedding(num_categories, emb_dim)
        self.decoder_net = nn.Sequential(
            nn.Linear(latent_dim + emb_dim, 128), nn.GELU(),
            nn.Linear(128, 256), nn.GELU(),
            nn.Linear(256, 512), nn.GELU(),
            nn.Linear(512, in_dim)
        )
    def forward(self, x, cat_idx):
        z = self.encoder(x)
        cond = self.cat_emb(cat_idx)
        return self.decoder_net(torch.cat([z, cond], dim=1))
    
model = OmniCondVAE(
    in_dim=checkpoint['in_dim'],
    latent_dim=checkpoint['latent_dim'],
    num_categories=len(unique_genres))

model.load_state_dict(checkpoint['model_state_dict'])
model.eval()
print("  -> v3 Weights Loaded. Category Mapping Active.")

# =====================================================================
# 4. SAMPLE POOLS (Sourced from df_samples)
# =====================================================================
print("[3/6] Segmenting Sample Pools...")
df_basses = df_samples[df_samples['genre_class'].str.contains('BASS', na=False, case=False) | df_samples['filename'].str.contains('Bass', na=False,    
   case=False)]
df_kicks = df_samples[df_samples['genre_class'].str.contains('KICK', na=False, case=False) | df_samples['filename'].str.contains('Kick', na=False,     
   case=False)]
df_perc = df_samples[df_samples['genre_class'].str.contains('PERC', na=False, case=False) | df_samples['filename'].str.contains('Perc|Hat', na=False,  
   case=False)]
# Fallbacks to the full sample pool if specific categories are missing
if len(df_basses) == 0: df_basses = df_samples
if len(df_kicks) == 0: df_kicks = df_samples
if len(df_perc) == 0: df_perc = df_samples

def sample_top_k(dists, df_pool, k=5, temperature=0.5):
    top_k_indices = np.argsort(dists)[:k]
    top_k_dists = dists[top_k_indices]
    logits = -top_k_dists / temperature
    exp_logits = np.exp(logits - np.max(logits))
    probs = exp_logits / np.sum(exp_logits)
    selected_idx = np.random.choice(top_k_indices, p=probs)
    return df_pool.iloc[selected_idx]

# =====================================================================
# 5. GENERATION LOOP
# =====================================================================
print("[4/6] Starting Generative Assembly...")

def load_audio(path):
    if not path or not isinstance(path, str) or not os.path.exists(path): return np.zeros((0, 2))
    try:
        y, _ = sf.read(path, always_2d=True)
        return y
    except: return np.zeros((0, 2))
    
# Seed from FULL TRACKS
seeds = df_tracks.sample(3)
for idx, row in seeds.iterrows():

# A. Normalize Seed
    seed_vec_raw = np.nan_to_num(row['omni_vector'], nan=0.0)
    seed_vec_norm = (seed_vec_raw - X_mean) / (X_std + 1e-8)
    seed_tensor = torch.tensor(seed_vec_norm, dtype=torch.float32).unsqueeze(0)

# B. Condition on Track Genre
    cat_name = row['genre_class'] if pd.notna(row['genre_class']) else unique_genres[0]
    cat_id = torch.tensor([genre2idx.get(cat_name, 0)], dtype=torch.int64)

# C. Hallucinate
    variance = 1.2
    with torch.no_grad():
        latent = model.encoder(seed_tensor)
        latent = latent + torch.randn_like(latent) * variance
        output_tensor_norm = model(seed_tensor, cat_id).numpy()[0]

    omni_output_raw = (output_tensor_norm * X_std) + X_mean
    semantic_slice = omni_output_raw[:384]
    target_bpm = omni_output_raw[384]

    print(f"  -> Hallucinated BPM: {target_bpm:.2f} | Genre: {cat_name}")

# D. Retrieval from SAMPLES
# BASS
    bass_mat = np.vstack([x[:384] for x in df_basses['omni_vector'].values])
    dists_bass = cdist([semantic_slice], np.nan_to_num(bass_mat, nan=0.0), metric="cosine")[0]
    best_bass = sample_top_k(dists_bass, df_basses)
    bass_fp = best_bass.get('filepath', '')

# KICK
    kick_mat = np.vstack([x[:384] for x in df_kicks['omni_vector'].values])
    dists_kick = cdist([semantic_slice], np.nan_to_num(kick_mat, nan=0.0), metric="cosine")[0]
    best_kick = sample_top_k(dists_kick, df_kicks)
    kick_fp = best_kick.get('filepath', '')

# PERC
    perc_mat = np.vstack([x[:384] for x in df_perc['omni_vector'].values])
    dists_perc = cdist([semantic_slice], np.nan_to_num(perc_mat, nan=0.0), metric="cosine")[0]
    best_perc = sample_top_k(dists_perc, df_perc)
    perc_fp = best_perc.get('filepath', '')

    print(f"  [BASS] {os.path.basename(bass_fp) if bass_fp else 'N/A'}")
    print(f"  [KICK] {os.path.basename(kick_fp) if kick_fp else 'N/A'}")
    print(f"  [PERC] {os.path.basename(perc_fp) if perc_fp else 'N/A'}")

# E. Assembly
    SR = 44100
   178     BPM = target_bpm if 60 < target_bpm < 200 else 128.0
   179     TOTAL_SAMPLES = int(16 * 4 * (60.0 / BPM) * SR)
   180     mix = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
   181
   182     y_kick = load_audio(kick_fp)
   183     y_bass = load_audio(bass_fp)
   184     y_perc = load_audio(perc_fp)
   185
   186     beat_samples = int((60.0 / BPM) * SR)
   187     for beat in range(16 * 4):
   188         pos = beat * beat_samples
   189         length = min(len(y_kick), TOTAL_SAMPLES - pos)
   190         if length > 0:
   191             mix[pos:pos+length] += y_kick[:length]
   192
   193     def tile_loop(loop_arr, total_len):
   194         out = np.zeros((total_len, 2), dtype=np.float32)
   195         ll = len(loop_arr)
   196         if ll == 0: return out
   197         p = 0
   198         while p < total_len:
   199             c = min(ll, total_len - p)
   200             out[p:p+c] = loop_arr[:c]
   201             p += c
   202         return out
   203
   204     mix += tile_loop(y_bass, TOTAL_SAMPLES)
   205     mix += tile_loop(y_perc, TOTAL_SAMPLES)
   206
   207     # F. Save
   208     timestamp = datetime.datetime.now().strftime("%H%M%S")
   209     safe_name = re.sub(r'[^a-zA-Z0-9]', '_', os.path.basename(row['filename']))
   210     out_path = os.path.join(OUTPUT_DIR, f"OMNI_V3_GEN_{safe_name}_{timestamp}.wav")
   211     os.makedirs(os.path.dirname(out_path), exist_ok=True)
   212     sf.write(out_path, np.clip(mix, -1.0, 1.0), SR)
   213     print(f"[SUCCESS] Assembly saved to: {out_path}")
   214
   215 print("\n[6/6] Process Complete.")