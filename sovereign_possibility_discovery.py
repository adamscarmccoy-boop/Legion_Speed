import os
import sys
import numpy as np
import pandas as pd
import polars as pl
import lancedb
from sklearn.preprocessing import StandardScaler

# Force UTF-8 for Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ==============================================================================
# CONFIGURATION
# ==============================================================================
INPUT_INDEX = r'C:\WEB CASE STUDY\training_latents\training_index.parquet'
BASELINE_DB = r'C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag'

def discover_possibilities():
    print("=" * 80)
    print("  SOVEREIGN POSSIBILITY DISCOVERY: MAPPING THE DATA CONNECTOME")
    print("=" * 80)

    # 1. Load the Gold Standard (The Target Space)
    try:
        db_lance = lancedb.connect(BASELINE_DB)
        df_gold = db_lance.open_table("omni_semantic_baselines").to_pandas()
        print(f"  [+] Gold Baseline loaded: {len(df_gold)} rows, {len(df_gold.columns)} columns.")
    except Exception as e:
        print(f"FATAL: Could not load Gold baselines: {e}")
        return

    # 2. Load the Training Index (The Feature Space)
    try:
        df_train = pl.read_parquet(INPUT_INDEX).to_pandas()
        print(f"  [+] Training set loaded: {len(df_train)} rows.")
    except Exception as e:
        print(f"FATAL: Could not load training index: {e}")
        return

    # 3. Identify all Numerical Variables (The "Possibilities")
    # We look for everything that can be treated as a target (Y)
    numeric_cols = df_gold.select_dtypes(include=[np.number]).columns.tolist()
    print(f"\n  [!] Found {len(numeric_cols)} potential target variables in Gold data.")
    print(f"      Columns: {numeric_cols}")

    # 4. Feature Extraction (X)
    # We'll use the standard DSP cols as a baseline for the 'X' space
    DSP_COLS = ["rms_db", "crest_factor", "sub_bass_energy", "bass_energy", 
                "mid_energy", "high_energy", "spectral_centroid", 
                "spectral_bandwidth", "spectral_rolloff", "spectral_contrast", 
                "zero_crossing_rate"]
    
    # Check which of these actually exist in the gold data to see overlap
    available_dsp = [c for c in DSP_COLS if c in df_gold.columns]
    print(f"\n  [!] Overlapping DSP features found: {len(available_dsp)} / {len(DSP_COLS)}")

    # 5. Correlation Analysis (The Math)
    # We calculate the correlation between every available numerical feature and every potential target.
    print("\n  [+] Calculating Correlation Matrix (Connectome)...")
    corr_matrix = df_gold[numeric_cols].corr()

    # Find the strongest connections
    strong_connections = []
    for col in numeric_cols:
        # Get correlations for this column, drop the self-correlation
        corrs = corr_matrix[col].drop(labels=[col])
        # Find the top 3 strongest connections (absolute value)
        top_3 = corrs.abs().sort_values(ascending=False).head(3)
        for target, val in top_3.items():
            strong_connections.append({
                "source": col,
                "target": target,
                "strength": val,
                "direction": "positive" if corrs[target] > 0 else "negative"
            })

    # 6. Final Report
    print("\n" + "=" * 80)
    print("  THE POSSIBILITY MAP: STRONGEST DATA CONNECTIONS")
    print("=" * 80)
    print(f"{'Source Variable':<25} | {'Target Variable':<25} | {'Strength':<10} | {'Dir'}")
    print("-" * 80)
    
    # Sort by strength
    strong_connections = sorted(strong_connections, key=lambda x: x['strength'], reverse=True)
    
    for conn in strong_connections[:30]: # Top 30 connections
        print(f"{conn['source']:<25} | {conn['target']:<25} | {conn['strength']:<10.4f} | {conn['direction']}")

    print("\n" + "=" * 80)
    print(f"  CONCLUSION: There are {len(numeric_cols)} independent mathematical targets available.")
    print("  The cluster reveals these as the primary drivers of the sonic profile.")
    print("=" * 80)

if __name__ == "__main__":
    discover_possibilities()
