"""
sonic_dna_query.py
==================
Test the trained Sonic DNA model.
Give it any track filepath -> get its Sonic DNA embedding + nearest neighbors.

Usage:
  python sonic_dna_query.py
  python sonic_dna_query.py "E:\\music\\HOUSE\\some_track.mp3"
"""

import sys, os, warnings
warnings.filterwarnings("ignore")

import torch
import torch.nn as nn
import numpy as np
import requests

# ── Load model weights ───────────────────────────────────────────────────────
PT_PATH  = r"C:\WEB CASE STUDY\sonic_dna_output\sonic_dna_mini_v1.pt"
ONYX_API = "http://localhost:8002/query/duckdb"

checkpoint = torch.load(PT_PATH, weights_only=False)
IN_DIM    = checkpoint["in_dim"]
LAT_DIM   = checkpoint["latent_dim"]
DSP_COLS  = checkpoint["dsp_cols"]
X_MEAN    = torch.tensor(checkpoint["X_mean"])
X_STD     = torch.tensor(checkpoint["X_std"])

# ── Rebuild encoder (no decoder needed at inference) ─────────────────────────
class SonicDNA(nn.Module):
    def __init__(self, in_dim, latent_dim):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(in_dim, 128), nn.LayerNorm(128), nn.GELU(),
            nn.Linear(128, 64),    nn.LayerNorm(64),  nn.GELU(),
            nn.Linear(64, latent_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 64), nn.GELU(),
            nn.Linear(64, 128),         nn.GELU(),
            nn.Linear(128, in_dim)
        )
    def forward(self, x):
        z = self.encoder(x)
        return z / (z.norm(dim=-1, keepdim=True) + 1e-8)

model = SonicDNA(IN_DIM, LAT_DIM)
model.load_state_dict(checkpoint["model_state_dict"], strict=False)
model.eval()
print(f"[OK] Model loaded: {IN_DIM}D DSP -> {LAT_DIM}D Sonic DNA  ({sum(p.numel() for p in model.parameters()):,} params)")

# ── Pull the 20-track reference catalog from DB ───────────────────────────────
print("[OK] Fetching reference catalog from DuckDB...")
resp = requests.post(ONYX_API, json={"sql_query": "SELECT * FROM audio_features LIMIT 20;"}, timeout=10)
df   = __import__("pandas").DataFrame(resp.json()["results"])
df   = df[[c for c in DSP_COLS if c in df.columns] + ["filepath","filename"]].dropna()

X_ref = torch.tensor(df[DSP_COLS].values.astype("float32"))
X_ref_norm = (X_ref - X_MEAN) / X_STD

with torch.no_grad():
    ref_embeddings = model(X_ref_norm).numpy()  # (N, 64)

print(f"[OK] {len(df)} reference tracks embedded\n")

# ── Query function ────────────────────────────────────────────────────────────
def embed_from_row(row_dict):
    """Turn a dict of DSP features into a 64-dim Sonic DNA vector."""
    vec = torch.tensor([row_dict.get(c, 0.0) for c in DSP_COLS], dtype=torch.float32)
    vec_norm = (vec - X_MEAN) / X_STD
    with torch.no_grad():
        return model(vec_norm.unsqueeze(0)).squeeze().numpy()

def find_nearest(query_embedding, top_k=5):
    """Cosine similarity search against reference catalog."""
    sims = ref_embeddings @ query_embedding / (
        np.linalg.norm(ref_embeddings, axis=1) * np.linalg.norm(query_embedding) + 1e-8
    )
    top_idx = np.argsort(sims)[::-1][:top_k]
    return [(df["filename"].iloc[i], float(sims[i])) for i in top_idx]

# ── DEMO: query a track by filepath ──────────────────────────────────────────
query_path = sys.argv[1] if len(sys.argv) > 1 else None

if query_path:
    # Look it up in the DB
    safe = query_path.replace("'","''")
    r2 = requests.post(ONYX_API, json={
        "sql_query": f"SELECT * FROM audio_features WHERE filepath LIKE '%{os.path.basename(safe)}%' LIMIT 1;"
    }, timeout=10)
    rows = r2.json().get("results", [])
    if not rows:
        print(f"Track not found in DB: {query_path}")
        sys.exit(1)
    query_row = rows[0]
    label = os.path.basename(query_path)
else:
    # Default: use the first track in reference catalog as query
    query_row = df[DSP_COLS].iloc[0].to_dict()
    label = df["filename"].iloc[0]

print("=" * 60)
print(f"QUERY TRACK")
print(f"  {label[:55]}")
print("=" * 60)

sonic_dna_vec = embed_from_row(query_row)
print(f"Sonic DNA vector (first 8 dims): {np.round(sonic_dna_vec[:8], 4)}")
print(f"Vector norm: {np.linalg.norm(sonic_dna_vec):.4f}  (should be ~1.0)")

print("\nTop-5 Nearest Neighbors:")
print("-" * 60)
neighbors = find_nearest(sonic_dna_vec, top_k=5)
for rank, (name, score) in enumerate(neighbors):
    bar = "#" * int(score * 20)
    print(f"  {rank+1}. [{score:.4f}] {bar}")
    print(f"       {name[:55]}")

print("\n[SONIC DNA MODEL IS WORKING]")
print(f"Weights: {PT_PATH}")
