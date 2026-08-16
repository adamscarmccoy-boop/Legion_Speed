#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# =======================================================
# TRAINING: PURE 384-D NEURAL SPACE (audio_vibe_gpu.csv)
# =======================================================
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import re, os, time

print("Loading massive audio_vibe_gpu.csv dataset...")
start_t = time.time()
df = pd.read_csv(r'C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\data\audio_vibe_gpu.csv')

def parse_vector(s):
    s = str(s).strip('[]')
    s = re.sub(r'\s+', ' ', s).strip()
    return np.array([float(x) for x in s.split(' ')], dtype=np.float32)

print("Parsing 2,010 acoustic vectors into math tensors...")
parsed_vectors = df['vector'].apply(parse_vector).tolist()
data_matrix = np.vstack(parsed_vectors)
data_matrix = np.nan_to_num(data_matrix, nan=0.0)

X_mean = np.mean(data_matrix, axis=0)
X_std = np.std(data_matrix, axis=0) + 1e-8
X_norm = (data_matrix - X_mean) / X_std
dataset = torch.tensor(X_norm, dtype=torch.float32)

IN_DIM = dataset.shape[1]
LATENT_DIM = 64

class SonicDNAMini(nn.Module):
    def __init__(self, in_dim, latent_dim):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(in_dim, 128), nn.LayerNorm(128), nn.GELU(),
            nn.Linear(128, 64), nn.LayerNorm(64), nn.GELU(),
            nn.Linear(64, latent_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 64), nn.GELU(),
            nn.Linear(64, 128), nn.GELU(),
            nn.Linear(128, in_dim)
        )
    def forward(self, x):
        return self.decoder(self.encoder(x))

model = SonicDNAMini(IN_DIM, LATENT_DIM)
opt = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
loss_fn = nn.MSELoss()

print(f"\n[TRAINING] Deep Manifold Learning on {len(dataset)} items...")
model.train()
EPOCHS = 1000
for ep in range(EPOCHS):
    opt.zero_grad()
    pred = model(dataset)
    loss = loss_fn(pred, dataset)
    loss.backward()
    opt.step()

out_path = r"C:\WEB CASE STUDY\sonic_dna_output\sonic_dna_mini_v3.pt"
os.makedirs(os.path.dirname(out_path), exist_ok=True)

torch.save({
    "model_state_dict": model.state_dict(),
    "in_dim": IN_DIM,
    "latent_dim": LATENT_DIM,
    "X_mean": X_mean.tolist(),
    "X_std": X_std.tolist()
}, out_path)

print(f"[SUCCESS] Sonic DNA Mini V3 saved to: {out_path} in {time.time()-start_t:.2f}s")


# In[ ]:


# =======================================================
# PURE 384-D GENERATION & NEURAL DSP MASTERING
# =======================================================
import sys
import os

math_dir = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline"
master_dir = r"C:\WEB CASE STUDY\sonic_dna_engine"

if math_dir not in sys.path: sys.path.append(math_dir)
if master_dir not in sys.path: sys.path.append(master_dir)

from sovereign_math_inference import SovereignInferenceEngine
from sonic_dna_batch_master_v5_neural import SonicDNAMaster, process_track

# 1. Provide a keyword that exists in audio_vibe_gpu.csv
seed_audio_keyword = "chris lake"  
hallucination_variance = 0.0

generation_weights = r"C:\WEB CASE STUDY\sonic_dna_output\sonic_dna_mini_v3.pt"
mastering_weights = r"C:\WEB CASE STUDY\sonic_dna_engine\sonic_dna_master_v3.pt"

print(f"\n[BOOT] Using Semantic Seed: {seed_audio_keyword}")

# Initialize the Pure 384-D Engine
engine = SovereignInferenceEngine(model_path=generation_weights)
gen_result = engine.generate_from_kick(seed_audio_keyword, variance=hallucination_variance)
raw_output_path = gen_result["output_path"]

print(f"\n[CHECKPOINT] Raw Math Track generated at: {raw_output_path}")

# Apply Neural DSP Mastering
print(f"\n[BOOT] Applying Neural DSP Mastering to Generated Track...")
master_model = SonicDNAMaster(mastering_weights)
final_output_path = process_track(raw_output_path, master_model)

print(f"\n[SUCCESS] Final Mastered Track: {final_output_path}")

