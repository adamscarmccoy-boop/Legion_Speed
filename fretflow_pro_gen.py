import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import pandas as pd
import lancedb
import soundfile as sf
import os
import datetime
from scipy.spatial.distance import cdist
import warnings
from pydantic import BaseModel
from typing import List, Optional

warnings.filterwarnings('ignore')

# --- REAL-WORLD CONFIGURATION ---
WEIGHTS_PATH = r"C:\WEB CASE STUDY\sonic_dna_output\fretflow_omni_v3.pt"
SAMPLES_JSON = r"C:\WEB CASE STUDY\data\enriched_samples_only.json"
LANCEDB_PATH = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\vectors\lancedb_store"
TABLE_NAME = "audio_vibe_gpu"
OUTPUT_DIR = r"C:\WEB CASE STUDY\generated_audio_pro"
SR = 44100

# --- SCHEMAS ---
class AudioDNA(BaseModel):
    semantic_vec: List[float]
    target_bpm: float

class SampleMatch(BaseModel):
    filename: str
    filepath: str
    score: float

class GenerationRecipe(BaseModel):
    seed_filename: str
    target_bpm: float
    kick: SampleMatch
    bass: SampleMatch
    perc: SampleMatch

# ---------------------------------------------------------------------------
# 1. THE BRAIN: OmniCondVAE Architecture (Exact v3)
# ---------------------------------------------------------------------------
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
        self.omni_dim = omni_dim
        self.latent_dim = latent_dim
        self.cond_dim = genre_emb + 1

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
        self.fc_mu = nn.Linear(128, latent_dim)
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

    def decode(self, z, cond):
        return self.decoder(torch.cat([z, cond], dim=1))

class FretFlowIntelligence:
    def __init__(self, weights_path, samples_json, ldb_path, table_name):
        # Load Weights
        self.checkpoint = torch.load(weights_path, map_location="cpu")
        self.X_mean = np.array(self.checkpoint['X_mean'], dtype=np.float32)
        self.X_std = np.array(self.checkpoint['X_std'], dtype=np.float32)
        
        print(f"  [AUDIT] X_mean shape: {self.X_mean.shape} | X_std shape: {self.X_std.shape}")
        
        in_dim = self.checkpoint.get('omni_dim', self.checkpoint.get('in_dim', 1036))
        latent_dim = self.checkpoint.get('latent_dim', 128)
        n_genres = self.checkpoint['n_genres']
        genre_emb = self.checkpoint['genre_emb_dim']
        
        self.genre2idx = self.checkpoint['genre2idx']
        self.bpm_mean = self.checkpoint['bpm_mean']
        self.bpm_std = self.checkpoint['bpm_std']

        self.model = OmniCondVAE(in_dim, latent_dim, n_genres, genre_emb)
        self.model.load_state_dict(self.checkpoint['model_state_dict'])
        self.model.eval()
        
        # Source of Truth: LanceDB
        ldb = lancedb.connect(ldb_path)
        table = ldb.open_table(table_name)
        self.df = table.to_pandas()
        
        # Merge Metadata (JSON)
        meta_df = pd.read_json(samples_json)
        self.df = pd.merge(self.df, meta_df[['filename', 'genre_class', 'tempo']], on='filename', how='left')
        self.df['genre_class'] = self.df['genre_class'].fillna('OTHER')
        self.df['tempo'] = self.df['tempo'].fillna(128.0)
        
        # Vectorize for fast search
        self.df['omni_vector'] = self.df.apply(self._build_omni_vector, axis=1)
        self.all_vecs = np.vstack(self.df['omni_vector'].values)
        self.all_vecs = np.nan_to_num(self.all_vecs, nan=0.0)

    def _build_omni_vector(self, row):
        sem = np.array(row['vector'], dtype=np.float32)
        bpm = np.array([float(row.get('tempo', 128.0))], dtype=np.float32)
        return np.concatenate([sem, bpm])

    def _derive_genre(self, filename):
        n = str(filename).lower()
        if "tech" in n or "house" in n: return "TECH_HOUSE"
        if "bass" in n or "sub" in n: return "BASS"
        if "kick" in n or "drum" in n: return "KICK"
        if "perc" in n or "hat" in n: return "PERC"
        return "OTHER"

    def hallucinate_dna(self, seed_row, variance=1.0) -> Optional[AudioDNA]:
        # 1. Look up vector in LanceDB source (self.df)
        filename = seed_row['filename']
        matches = self.df[self.df['filename'] == filename]
        if matches.empty:
            return None
            
        seed_row_full = matches.iloc[0]
        seed_vec = np.array(seed_row_full['vector'], dtype=np.float32)
        
        bpm = float(seed_row.get('tempo', 128.0))
        genre_name = self._derive_genre(filename)
        gid = self.genre2idx.get(genre_name, 0)
        
        # 2. Normalize (Symmetrically with training)
        seed_vec_norm = (seed_vec - self.X_mean[:len(seed_vec)]) / (self.X_std[:len(seed_vec)] + 1e-8)
        full_seed_norm = np.zeros(self.model.omni_dim, dtype=np.float32)
        full_seed_norm[:len(seed_vec_norm)] = seed_vec_norm
        
        seed_t = torch.tensor(full_seed_norm, dtype=torch.float32).unsqueeze(0)
        bpm_n = torch.tensor([(bpm - self.bpm_mean) / self.bpm_std], dtype=torch.float32)
        gid_t = torch.tensor([gid], dtype=torch.int64)
        
        # 3. VAE Cycle
        with torch.no_grad():
            cond = self.model._cond(gid_t, bpm_n)
            mu, log_var = self.model.encode(seed_t, cond)
            z = mu + torch.exp(0.5 * log_var) * torch.randn_like(mu) * variance
            recon = self.model.decode(z, cond).numpy()[0]
            
        # 4. Denormalize
        omni_output_raw = (recon * self.X_std) + self.X_mean
        
        # Extract semantic slice (First 384) and BPM (Last 1)
        sem_slice = omni_output_raw[:384]
        if np.isnan(sem_slice).any():
            sem_slice = seed_vec[:384]
            
        target_bpm = float(omni_output_raw[-1])
        if np.isnan(target_bpm):
            target_bpm = bpm

        return AudioDNA(
            semantic_vec=sem_slice.tolist(),
            target_bpm=target_bpm
        )

    def find_match(self, target_vec, pool_filter) -> SampleMatch:
        mask = (self.df['genre_class'].str.contains(pool_filter, na=False, case=False) | 
               self.df['filename'].str.contains(pool_filter, na=False, case=False))
        pool_df = self.df[mask] if not self.df[mask].empty else self.df
        pool_mat = np.vstack(pool_df['omni_vector'].values)
        pool_mat = np.nan_to_num(pool_mat, nan=0.0)
        
        # SLICE to match the 384-dim semantic target_vec
        pool_sem = pool_mat[:, :384]
        
        dists = cdist([target_vec], pool_sem, metric="cosine")[0]
        k = 5
        top_k = np.argsort(dists)[:k]
        logits = -dists[top_k] / 0.5
        probs = np.exp(logits - np.max(logits))
        probs /= np.sum(probs)
        
        idx = np.random.choice(top_k, p=probs)
        match = pool_df.iloc[idx]
        return SampleMatch(
            filename=match['filename'],
            filepath=match.get('filepath', ''),
            score=float(dists[idx])
        )

# ---------------------------------------------------------------------------
# 2. THE MUSCLE: Local Professional Renderer
# ---------------------------------------------------------------------------
class FretFlowRenderer:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _load_and_stretch(self, path, target_len=None):
        if not path or not os.path.exists(path):
            return np.zeros((0, 2), dtype=np.float32)
        try:
            y, sr = sf.read(path, always_2d=True)
            if target_len and len(y) != target_len:
                idx = np.linspace(0, len(y)-1, target_len)
                y = np.stack([np.interp(idx, np.arange(len(y)), y[i]) for i in range(2)], axis=1)
            return y.astype(np.float32)
        except Exception as e:
            print(f"  [ERROR] Loading {path}: {e}")
            return np.zeros((0, 2), dtype=np.float32)

    def render(self, recipe: GenerationRecipe):
        BPM = recipe.target_bpm if 60 < recipe.target_bpm < 200 else 128.0
        TOTAL_SAMPLES = int(16 * 4 * (60.0 / BPM) * SR)
        mix = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

        four_bar_len = int(4 * 4 * (60.0 / BPM) * SR)
        y_kick = self._load_and_stretch(recipe.kick.filepath)
        y_bass = self._load_and_stretch(recipe.bass.filepath, target_len=four_bar_len)
        y_perc = self._load_and_stretch(recipe.perc.filepath, target_len=four_bar_len)

        beat_samples = int((60.0 / BPM) * SR)
        G_KICK, G_BASS, G_PERC = 1.0, 0.6, 0.4

        for beat in range(16 * 4):
            pos = beat * beat_samples
            length = min(len(y_kick), TOTAL_SAMPLES - pos)
            if length > 0:
                mix[pos:pos+length] += y_kick[:length] * G_KICK

        bass_layer = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
        p = 0
        while p < TOTAL_SAMPLES:
            c = min(len(y_bass), TOTAL_SAMPLES - p)
            bass_layer[p:p+c] = y_bass[:c]
            p += len(y_bass)
        bass_layer *= G_BASS

        for beat in range(16 * 4):
            pos = beat * beat_samples
            duck_len = int(0.1 * SR)
            end = min(pos + duck_len, TOTAL_SAMPLES)
            ramp = np.linspace(0.2, 1.0, end - pos)
            bass_layer[pos:end, 0] *= ramp
            bass_layer[pos:end, 1] *= ramp

        mix += bass_layer
        
        perc_layer = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
        p = 0
        while p < TOTAL_SAMPLES:
            c = min(len(y_perc), TOTAL_SAMPLES - p)
            perc_layer[p:p+c] = y_perc[:c]
            p += len(y_perc)
        mix += perc_layer * G_PERC

        out_name = f"PRO_GEN_{recipe.seed_filename}_{datetime.datetime.now().strftime('%H%M%S')}.wav"
        out_path = os.path.join(self.output_dir, out_name)
        sf.write(out_path, np.clip(mix, -1.0, 1.0), SR)
        return out_path

# ---------------------------------------------------------------------------
# 3. Orchestrator
# ---------------------------------------------------------------------------
def main():
    print("[BOOT] Starting Professional FretFlow Generation Pipeline (Local Mode)...")
    
    # Initialize Intelligence
    intel = FretFlowIntelligence(WEIGHTS_PATH, SAMPLES_JSON, LANCEDB_PATH, TABLE_NAME)
    
    # Initialize Local Renderer
    renderer = FretFlowRenderer(OUTPUT_DIR)
    
    # Load real seeds from the vector store (source of truth)
    seeds = intel.df.sample(3)
    
    for _, row in seeds.iterrows():
        print(f"\n[GEN] Seed: {row['filename']}")
        
        # A. Intelligence Phase
        dna = intel.hallucinate_dna(row)
        if dna is None:
            print("  [SKIP] Seed error.")
            continue
            
        print(f"  -> DNA Hallucinated: BPM {dna.target_bpm:.2f}")
        
        kick = intel.find_match(np.array(dna.semantic_vec), "KICK")
        bass = intel.find_match(np.array(dna.semantic_vec), "BASS")
        perc = intel.find_match(np.array(dna.semantic_vec), "PERC")
        
        print(f"  [MATCH] K: {os.path.basename(kick.filepath)} | B: {os.path.basename(bass.filepath)} | P: {os.path.basename(perc.filepath)}")
        
        # B. The Recipe
        recipe = GenerationRecipe(
            seed_filename=row['filename'],
            target_bpm=dna.target_bpm,
            kick=kick,
            bass=bass,
            perc=perc
        )
        
        # C. Local Rendering Phase
        out_file = renderer.render(recipe)
        print(f"  [SUCCESS] Pro Render: {out_file}")

if __name__ == "__main__":
    main()
