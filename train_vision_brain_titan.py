import sys
import os
sys.stdout.reconfigure(encoding="utf-8")

# Force E: drive libraries
VENV_PATH = r"C:\WEB CASE STUDY\.venv\Lib\site-packages"
if VENV_PATH not in sys.path:
    sys.path.insert(0, VENV_PATH)

import json
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# --- CONFIG ---
DATA_PATH = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/exported_json/duckdb_audio_features.json"
WEIGHTS_PATH = r"C:\WEB CASE STUDY\sovereign_vision_brain.pth"

class VisionBrainMLP(nn.Module):
    def __init__(self, input_dim: int, output_dim: int = 12):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, output_dim),
            nn.Softmax(dim=1)
        )
    def forward(self, x): return self.net(x)

def train():
    print("🧬 Loading Feature Lake...")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    skip = {"artist", "filepath", "timestamp"}
    feats = [c for c in df.columns if c not in skip and df[c].dtype in [float, int, "float64", "int64"]]
    df = df.dropna(subset=feats)

    X_scaled = StandardScaler().fit_transform(df[feats].values)
    input_dim = X_scaled.shape[1]
    
    # ─── FIX: Derive real labels from audio features via k-means clustering ───
    # Previously Y was all-zeros, which trained the brain to output uniform
    # Softmax noise (0.083 per class). Now each track gets a dominant cluster
    # label that maps to one of the 12 aesthetic classes.
    N_CLASSES = 12
    print(f"   K-Means clustering {len(df)} tracks into {N_CLASSES} aesthetic classes...")
    kmeans = KMeans(n_clusters=N_CLASSES, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)  # shape: (N,)
    
    # Convert to one-hot targets so the MLP learns a clear dominant aesthetic
    Y = np.zeros((len(df), N_CLASSES), dtype=np.float32)
    for i, lbl in enumerate(cluster_labels):
        Y[i, lbl] = 1.0
    print(f"   ✅ Labels derived. Cluster distribution: {np.bincount(cluster_labels)}")
    model = VisionBrainMLP(input_dim)
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    X_t, Y_t = torch.FloatTensor(X_scaled), torch.FloatTensor(Y)

    print(f"🔥 Training Brain ({input_dim}D)...")
    for epoch in range(101):
        optimizer.zero_grad()
        loss = torch.nn.MSELoss()(model(X_t), Y_t)
        loss.backward(); optimizer.step()
        if epoch % 50 == 0: print(f"   | Epoch {epoch} | Loss: {loss.item():.6f}")

    print(f"💾 SECURING WEIGHTS TO: {WEIGHTS_PATH}")
    torch.save(model.state_dict(), WEIGHTS_PATH)
    print("✅ SUCCESS. Brain logic is now persistent.")

if __name__ == "__main__":
    train()