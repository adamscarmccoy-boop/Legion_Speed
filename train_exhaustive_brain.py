import os
import sys
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import lancedb
import onnx
import onnxruntime as ort
from sklearn.preprocessing import StandardScaler
import ray
from pathlib import Path

# Force UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ==============================================================================
# CONFIGURATION
# ==============================================================================
SEARCH_PATHS = [
    Path(r"C:\WEB CASE STUDY\lancedb_data"),
    Path(r"C:\WEB CASE STUDY\lancedb_memory"),
    Path(r"C:\WEB CASE STUDY\lancedb_store"),
    Path(r"C:\WEB CASE STUDY\lancedb_web_intel_rag"),
    Path(r"C:\WEB CASE STUDY\data"),
    Path(r"C:\STUDIES_BACKUP\data\metadata\parquet_exports"),
]
LANCEDB_PATH = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
OUTPUT_MODEL = r"C:\WEB CASE STUDY\sovereign_big_brain_exhaustive.onnx"

TARGET_COLS = [
    "rms", "crest_factor", "sub_bass_energy", "bass_energy", "mid_energy", 
    "high_energy", "spectral_centroid", "spectral_bandwidth", 
    "spectral_rolloff", "spectral_flatness", "spectral_contrast", "zero_crossing_rate"
]

# ==============================================================================
# MODEL ARCHITECTURE
# ==============================================================================
class SovereignExhaustiveBrain(nn.Module):
    def __init__(self, in_dim=1024, out_dim=12):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 256), nn.LayerNorm(256), nn.GELU(),
            nn.Linear(256, 128), nn.LayerNorm(128), nn.GELU(),
            nn.Linear(128, 64), nn.LayerNorm(64), nn.GELU(),
            nn.Linear(64, out_dim)
        )

    def forward(self, x):
        return self.net(x)

def normalize_name(name):
    if not isinstance(name, str): return ""
    name = name.lower().strip()
    for ext in ['.wav', '.mp3', '.flac', '.aiff']:
        name = name.replace(ext, '')
    return name

def is_fuzzy_match(s1, s2, threshold=0.8):
    from difflib import SequenceMatcher
    return SequenceMatcher(None, s1, s2).ratio() > threshold

# ==============================================================================
# EXHAUSTIVE HARVESTER
# ==============================================================================
def run_exhaustive_harvest():
    print("=" * 80)
    print("  SOVEREIGN TOTAL HARVEST: FUZZY ALIGNMENT MODE")
    print("=" * 80)

    all_targets = []
    all_track_names = []
    
    for path in SEARCH_PATHS:
        if not path.exists(): continue
        print(f"Scanning: {path}...")
        for pf in path.rglob("*.parquet"):
            try:
                df = pd.read_parquet(pf)
                if all(col in df.columns for col in TARGET_COLS):
                    target_vals = df[TARGET_COLS].iloc[0].values.astype(np.float32)
                    all_targets.append(target_vals)
                    name = df["track_name"].iloc[0] if "track_name" in df.columns else pf.name
                    all_track_names.append(normalize_name(name))
            except Exception:
                continue

    if not all_targets:
        print("FATAL: No valid tuning data found.")
        return

    Y = np.array(all_targets)
    print(f"\n  [+] Harvested {len(Y)} target states.")

    print("Connecting to Lancedb for FUZZY alignment...")
    try:
        db = lancedb.connect(LANCEDB_PATH)
        table = db.open_table("omni_semantic_baselines")
        
        lancedb_df = table.to_pandas()
        lancedb_df['norm_name'] = lancedb_df['track_name'].apply(normalize_name)
        
        X_list = []
        final_Y = []
        
        for i, name in enumerate(all_track_names):
            try:
                match = lancedb_df[lancedb_df['norm_name'].str.contains(name, na=False, case=False) | 
                                   lancedb_df['norm_name'].apply(lambda x: is_fuzzy_match(name, x))]
                
                if not match.empty:
                    vec = np.array(match["vector"].iloc[0]).astype(np.float32)
                    if vec.shape[0] > 1024: vec = vec[:1024]
                    elif vec.shape[0] < 1024:
                        vec = np.pad(vec, (0, 1024 - vec.shape[0]))
                    
                    X_list.append(vec)
                    final_Y.append(Y[i])
            except Exception:
                continue
        
        X = np.array(X_list)
        Y = np.array(final_Y)
        print(f"  [+] Aligned {len(X)} samples using Fuzzy Match.")
    except Exception as e:
        print(f"FATAL: Alignment failed: {e}")
        return

    if len(X) == 0:
        print("FATAL: No overlapping DNA found even with fuzzy matching.")
        return

    scaler_x = StandardScaler()
    X_scaled = scaler_x.fit_transform(X)
    scaler_y = StandardScaler()
    Y_scaled = scaler_y.fit_transform(Y)
    
    X_tensor = torch.tensor(X_scaled)
    Y_tensor = torch.tensor(Y_scaled)
    
    dataset = TensorDataset(X_tensor, Y_tensor)
    loader = DataLoader(dataset, batch_size=16, shuffle=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = SovereignExhaustiveBrain().to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001)

    print(f"  [+] Training Exhaustive Brain on {device}...")
    model.train()
    for epoch in range(200):
        total_loss = 0
        for bx, by in loader:
            bx, by = bx.to(device), by.to(device)
            optimizer.zero_grad()
            out = model(bx)
            loss = criterion(out, by)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        if (epoch + 1) % 50 == 0:
            print(f"    Epoch {epoch+1}/200 | Loss: {total_loss/len(loader):.6f}")

    print(f"  [+] Exporting lapped lapped model: {OUTPUT_MODEL}...")
    model.eval()
    dummy_input = torch.randn(1, 1024).to(device)
    torch.onnx.export(
        model, 
        dummy_input, 
        OUTPUT_MODEL, 
        input_names=['dna_vector'], 
        output_names=['dsp_state'],
        dynamic_axes={'dna_vector': {0: 'batch_size'}, 'dsp_state': {0: 'batch_size'}}
    )
    
    print("=" * 80)
    print("  EXHAUSTIVE SOVEREIGN BRAIN COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    run_exhaustive_harvest()
