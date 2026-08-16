import sys
sys.stdout.reconfigure(encoding="utf-8")

import json
import numpy as pnp
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import StandardScaler

# ─── CONFIG ───
DATA_PATH       = r"E:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/exported_json/duckdb_audio_features.json"
MODEL_SAVE_PATH = r"E:/WEB CASE STUDY/sovereign_vision_brain.onnx"

# The 12 Semantic Anchors from sonic_to_visual_bridge.py
SEMANTIC_ANCHORS = [
    "Cybernetic", "Organic", "Brutalist", "Ethereal", "Glitch",
    "High-Energy", "Dark", "Retro-Futurism", "Luxury", "Chaos",
    "Minimal", "Surreal"
]

# Ground truth: artist -> target 12-dim vibe vector
ARTIST_VIBE_MAP = {
    "Chris Lake":           [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],  # Cybernetic + High Energy
    "Fisher":               [1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0],  # Cybernetic + Glitch + Energy
    "Charlotte de Witte":   [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0],  # Brutalist + Dark
    "Sam Shure":            [0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],  # Organic + Ethereal + Surreal
    "Eli Brown":            [1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0],  # Cybernetic + Brutalist + Glitch + Dark
}

# ─── MODEL ───
class VisionBrainMLP(nn.Module):
    def __init__(self, input_dim: int, output_dim: int = 12):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, output_dim),
            nn.Softmax(dim=1)
        )

    def forward(self, x):
        return self.net(x)

# ─── TRAINING ───
def train():
    sys.stdout.write("Loading audio feature lake...\n")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    skip_cols = {"artist", "filepath", "timestamp"}
    feature_cols = [c for c in df.columns if c not in skip_cols and df[c].dtype in [float, int, "float64", "int64"]]
    df_clean = df.dropna(subset=feature_cols)

    X = df_clean[feature_cols].values
    y_names = df_clean["artist"].values if "artist" in df_clean.columns else ["Other"] * len(df_clean)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Map artist labels to 12-dim semantic targets
    sys.stdout.write("Mapping artists to semantic dimensions...\n")
    Y = np.zeros((len(y_names), 12), dtype=np.float32)
    for i, name in enumerate(y_names):
        name_lower = str(name).lower()
        for artist_key, vibe_vector in ARTIST_VIBE_MAP.items():
            if artist_key.lower() in name_lower:
                Y[i] = vibe_vector
                break

    input_dim = X_scaled.shape[1]
    model = VisionBrainMLP(input_dim)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    X_tensor = torch.FloatTensor(X_scaled)
    Y_tensor = torch.FloatTensor(Y)

    sys.stdout.write(f"Training Vision Brain (Input: {input_dim}D -> Output: 12D)...\n")
    model.train()
    for epoch in range(100):
        optimizer.zero_grad()
        outputs = model(X_tensor)
        loss = criterion(outputs, Y_tensor)
        loss.backward()
        optimizer.step()
        if epoch % 10 == 0:
            sys.stdout.write(f"  Epoch {epoch:3d} | Loss: {loss.item():.6f}\n")
    # ─── STAGE 1: SECURE THE WEIGHTS ───
    WEIGHTS_PATH = r"E:/WEB CASE STUDY/sovereign_vision_brain.pth"
    sys.stdout.write(f"Securing Brain weights to: {WEIGHTS_PATH}\n")
    torch.save(model.state_dict(), WEIGHTS_PATH)
    sys.stdout.write("Weights secured. Logic is safe.\n")

if __name__ == "__main__":
    train()
