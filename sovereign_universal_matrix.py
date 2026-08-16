import os
import sys
import numpy as np
import pandas as pd
import torch
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from scipy.interpolate import interp1d
from pathlib import Path
import lancedb

# Force UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ==============================================================================
# CONFIGURATION
# ==============================================================================
PARQUET_DIR = Path(r"C:\STUDIES_BACKUP\data\metadata\parquet_exports")
LANCEDB_PATH = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"

# The "Tuning Trinity"
FEATURE_COLS = ["rms", "crest_factor", "spectral_centroid"]
TARGET_COLS = ["gain", "ratio", "threshold"] # We will map to these if available, else use proxy targets

# ==============================================================================
# THE SOVEREIGN ENGINE
# ==============================================================================
class SovereignMatrixEngine:
    def __init__(self, data):
        self.data = data
        self.scaler_x = StandardScaler()
        self.scaler_y = StandardScaler()
        
    def run_pipeline(self, window_size=2048, forest_depth=10):
        print(f"\n  [!] Running Option: Window={window_size}, Depth={forest_depth}")
        
        # 1. Feature Extraction (Point Readings)
        # In this lapped version, we use the existing PyArrow features as 'points'
        X = self.data[FEATURE_COLS].fillna(0).values.astype(np.float32)
        Y = self.data[TARGET_COLS].fillna(0).values.astype(np.float32)
        
        if len(X) < 10:
            return "Insufficient Data"

        # 2. The Forest Mapping
        X_scaled = self.scaler_x.fit_transform(X)
        Y_scaled = self.scaler_y.fit_transform(Y)
        
        forest = RandomForestRegressor(n_estimators=100, max_depth=forest_depth, random_state=42)
        forest.fit(X_scaled, Y_scaled)
        
        # 3. Temporal Interpolation (The "Flow")
        # We simulate a track's timeline to create the curve
        time_axis = np.linspace(0, 1, 100)
        # Predict targets for this timeline (simulated as a walk through the data)
        points_to_predict = X_scaled[np.random.choice(len(X_scaled), 100)]
        predictions_scaled = forest.predict(points_to_predict)
        predictions = self.scaler_y.inverse_transform(predictions_scaled)
        
        # Interpolate each parameter (Gain, Ratio, Threshold)
        curves = {}
        for i, col in enumerate(TARGET_COLS):
            f = interp1d(np.linspace(0, 1, 100), predictions[:, i], kind='cubic')
            curves[col] = f(np.linspace(0, 1, 100))
            
        return curves

# ==============================================================================
# DATA HARVESTER
# ==============================================================================
def harvest_all_pyarrow():
    print("=" * 80)
    print("  Sovereign Universal Harvester: SCANNING ALL PYARROW TABLES")
    print("=" * 80)
    
    all_frames = []
    
    # 1. Scan Parquet Directory
    print(f"Scanning {PARQUET_DIR}...")
    for pf in PARQUET_DIR.glob("*.parquet"):
        try:
            df = pd.read_parquet(pf)
            # We check if it has the required features
            if all(col in df.columns for col in FEATURE_COLS):
                # If it doesn't have targets, we create 'Sovereign Proxy' targets 
                # based on the features (this is how we handle tables without tuning)
                if not all(col in df.columns for col in TARGET_COLS):
                    df['gain'] = df['rms'] * -1.0 # Simple proxy
                    df['ratio'] = df['crest_factor'] * 0.5
                    df['threshold'] = df['rms'] - 20.0
                
                all_frames.append(df[FEATURE_COLS + TARGET_COLS])
        except Exception:
            continue

    # 2. Scan LanceDB
    try:
        db = lancedb.connect(LANCEDB_PATH)
        table = db.open_table("omni_semantic_baselines")
        df_lancedb = table.to_pandas()
        if all(col in df_lancedb.columns for col in FEATURE_COLS):
            if not all(col in df_lancedb.columns for col in TARGET_COLS):
                df_lancedb['gain'] = df_lancedb['rms'] * -1.0
                df_lancedb['ratio'] = df_lancedb['crest_factor'] * 0.5
                df_lancedb['threshold'] = df_lancedb['rms'] - 20.0
            all_frames.append(df_lancedb[FEATURE_COLS + TARGET_COLS])
    except Exception as e:
        print(f"LanceDB skip: {e}")

    if not all_frames:
        return None
        
    return pd.concat(all_frames, ignore_index=True)

# ==============================================================================
# EXECUTION MATRIX
# ==============================================================================
if __name__ == "__main__":
    full_data = harvest_all_pyarrow()
    
    if full_data is None:
        print("FATAL: No usable data found across all PyArrow tables.")
        sys.exit(1)
        
    print(f"\n[+] Total Harvested Points: {len(full_data)}")
    
    # Split into 3 Datasets
    datasets = {
        "Profile A (High Energy)": full_data[full_data['rms'] > full_data['rms'].median()],
        "Profile B (Dynamic)": full_data[full_data['crest_factor'] > full_data['crest_factor'].median()],
        "Profile C (Universal)": full_data
    }
    
    # Define Variable Options (Window, Depth)
    options = [
        {"window": 1024, "depth": 5},  # Option 1: Tight/Shallow
        {"window": 4096, "depth": 15}, # Option 2: Smooth/Deep
        {"window": 8192, "depth": 30}, # Option 3: Aggressive/Complex
    ]
    
    for ds_name, ds_df in datasets.items():
        print(f"\n\n{'#'*40}\n {ds_name}\n{'#'*40}")
        engine = SovereignMatrixEngine(ds_df)
        
        for i, opt in enumerate(options):
            result = engine.run_pipeline(window_size=opt["window"], forest_depth=opt["depth"])
            if isinstance(result, str):
                print(f"Option {i+1}: {result}")
            else:
                # Print the average Gain for this option to show the difference
                print(f"Option {i+1} [W:{opt['window']} D:{opt['depth']}] -> Avg Gain: {np.mean(result['gain']):.4f}")

    print("\n" + "=" * 80)
    print("  SOVEREIGN MATRIX EXECUTION COMPLETE")
    print("=" * 80)
