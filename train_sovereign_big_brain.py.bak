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

# ==============================================================================
# SOVEREIGN LIFE-CYCLE STABILIZER (AUTO-INJECTED)
# Prevents dangling stdout/stdio pipes and GCS registry locks on Windows exit
# ==============================================================================
import atexit
import signal

def clean_exit_handler(*args, **kwargs):
    import sys
    sys.stderr.write("\n[LMS LIFECYCLE] Exit triggered. Flushing system streams...\n")
    sys.stderr.flush()
    try:
        import ray
        if ray.is_initialized():
            sys.stderr.write("[LMS LIFECYCLE] Active Ray session detected. Disconnecting...\n")
            ray.shutdown()
    except Exception:
        pass
    sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================


# Force UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ==============================================================================
# CONFIGURATION
# ==============================================================================
RAY_ADDRESS = "auto"
RAY_NAMESPACE = "legion"
REGISTRY_NAME = "SwarmKnowledgeRegistry"
OUTPUT_MODEL = r"C:\WEB CASE STUDY\sovereign_big_brain.onnx"

# The lapped 12-dim target variables
TARGET_COLS = [
    "rms", "crest_factor", "sub_bass_energy", "bass_energy", "mid_energy", 
    "high_energy", "spectral_centroid", "spectral_bandwidth", 
    "spectral_rolloff", "spectral_flatness", "spectral_contrast", "zero_crossing_rate"
]

# ==============================================================================
# MODEL ARCHITECTURE (The Big Brain)
# ==============================================================================
class SovereignBigBrain(nn.Module):
    def __init__(self, in_dim=64, out_dim=12):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 256), nn.LayerNorm(256), nn.GELU(),
            nn.Linear(256, 128), nn.LayerNorm(128), nn.GELU(),
            nn.Linear(128, 64), nn.LayerNorm(64), nn.GELU(),
            nn.Linear(64, out_dim)
        )

    def forward(self, x):
        return self.net(x)

# ==============================================================================
# TRAINING ENGINE (ZERO-COPY)
# ==============================================================================
def train_big_brain():
    print("=" * 70)
    print("  TRAINING SOVEREIGN BIG BRAIN: DNA -> 12-DIM DSP STATE")
    print("=" * 70)

    # 1. Connect to Ray and Registry
    ray.init(address=RAY_ADDRESS, namespace=RAY_NAMESPACE, ignore_reinit_error=True)
    try:
        registry = ray.get_actor(REGISTRY_NAME, namespace=RAY_NAMESPACE)
        print(f"  [+] Connected to {REGISTRY_NAME}")
    except Exception as e:
        print(f"FATAL: Registry not found: {e}")
        return

    # 2. Retrieve Real Data via Object Store (Zero-Copy)
    print("  [+] Pulling Gold Baseline lapped data...")
    try:
        df_gold = ray.get(registry.get_table.remote("chris_lake_omni_baseline"))
        if hasattr(df_gold, "to_pandas"):
            df_gold = df_gold.to_pandas()
        
        Y = df_gold[TARGET_COLS].fillna(0.0).values.astype(np.float32)
        
        # Using the semantic vectors as the DNA input (X)
        if "vector" in df_gold.columns:
            X = np.array([np.array(v) for v in df_gold["vector"]]).astype(np.float32)
            # Standardize to 64-dim
            if X.shape[1] > 64: X = X[:, :64]
            elif X.shape[1] < 64:
                pad = np.zeros((X.shape[0], 64 - X.shape[1]))
                X = np.concatenate([X, pad], axis=1)
        else:
            print("FATAL: No vector column found in Gold Baseline.")
            return
            
        print(f"  [+] Training set loaded: {len(df_gold)} samples. X: {X.shape}, Y: {Y.shape}")
    except Exception as e:
        print(f"FATAL: Data retrieval failed: {e}")
        return

    # 3. Normalize (Crucial for multi-variable stability)
    scaler_x = StandardScaler()
    X_scaled = scaler_x.fit_transform(X)
    scaler_y = StandardScaler()
    Y_scaled = scaler_y.fit_transform(Y)
    
    X_tensor = torch.tensor(X_scaled)
    Y_tensor = torch.tensor(Y_scaled)
    
    dataset = TensorDataset(X_tensor, Y_tensor)
    loader = DataLoader(dataset, batch_size=16, shuffle=True)

    # 4. Train
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = SovereignBigBrain().to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)

    print(f"  [+] Training on {device}...")
    model.train()
    for epoch in range(200): # Deeper training for the Big Brain
        total_loss = 0
        for bx, by in loader:
            bx, by = bx.to(device), by.to(device)
            optimizer.zero_grad()
            out = model(bx)
            loss = criterion(out, by)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        if (epoch + 1) % 20 == 0:
            print(f"    Epoch {epoch+1}/200 | Loss: {total_loss/len(loader):.6f}")

    # 5. Export to ONNX
    print(f"  [+] Exporting to ONNX: {OUTPUT_MODEL}...")
    model.eval()
    dummy_input = torch.randn(1, 64).to(device)
    torch.onnx.export(
        model, 
        dummy_input, 
        OUTPUT_MODEL, 
        input_names=['dna_vector'], 
        output_names=['dsp_state'],
        dynamic_axes={'dna_vector': {0: 'batch_size'}, 'dsp_state': {0: 'batch_size'}}
    )
    
    print("=" * 70)
    print("  SOVEREIGN BIG BRAIN TRAINING COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    train_big_brain()