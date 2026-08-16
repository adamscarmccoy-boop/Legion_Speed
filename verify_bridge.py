import numpy as np
import pandas as pd
import lancedb
import onnxruntime as ort
import time
from sklearn.preprocessing import StandardScaler

# Paths
BASELINE_DB = r'C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag'
MODEL_PATH = r'C:\WEB CASE STUDY\sovereign_bridge_v1.onnx'

TARGET_COLS = [
    "rms", "crest_factor", "sub_bass_energy", "bass_energy", "mid_energy", 
    "high_energy", "spectral_centroid", "spectral_bandwidth", 
    "spectral_rolloff", "spectral_flatness", "spectral_contrast", "zero_crossing_rate"
]

def run_identity_test():
    print("=" * 70)
    print("  SOVEREIGN IDENTITY TEST: GOLD-TO-GOLD VERIFICATION")
    print("=" * 70)

    # 1. Load Model
    session = ort.InferenceSession(MODEL_PATH)
    input_name = session.get_inputs()[0].name
    
    # 2. Load Gold Baseline
    db = lancedb.connect(BASELINE_DB)
    df_gold = db.open_table("omni_semantic_baselines").to_pandas()
    mask = df_gold["track_name"].str.contains("chris lake|somebody", case=False, na=False)
    df_gold = df_gold[mask].reset_index(drop=True)
    
    # Fit the scaler on the gold targets
    scaler = StandardScaler()
    scaler.fit(df_gold[TARGET_COLS].fillna(0.0).values.astype(np.float32))
    
    # 3. Pick a Gold Sample
    sample_idx = 0
    gold_row = df_gold.iloc[sample_idx]
    actual_gold_values = gold_row[TARGET_COLS].values.astype(np.float32)
    
    # Use the actual semantic vector as the "DNA" input
    dna_vector = np.array(gold_row["vector"], dtype=np.float32).reshape(1, -1)
    if dna_vector.shape[1] != 64:
        if dna_vector.shape[1] > 64:
            dna_vector = dna_vector[:, :64]
        else:
            pad = np.zeros((1, 64 - dna_vector.shape[1]))
            dna_vector = np.concatenate([dna_vector, pad], axis=1)

    # 4. Inference
    t0 = time.perf_counter()
    norm_prediction = session.run(None, {input_name: dna_vector})[0][0]
    t1 = time.perf_counter()
    
    # 5. Inverse Scale to Real Units
    real_prediction = scaler.inverse_transform(norm_prediction.reshape(1, -1))[0]
    
    # 6. Calculate the "Identity Delta"
    print(f"\n  [+] Processing Gold Sample: {gold_row['track_name']}")
    print(f"  [+] Inference Speed: {(t1-t0)*1000:.4f} ms")
    
    print("\n  [!] Identity Delta (Gold vs Predicted):")
    print(f"  {'Variable':<20} | {'Actual Gold':<12} | {'Predicted':<12} | {'Delta':<10}")
    print("-" * 60)
    
    total_error = 0
    for i, col in enumerate(TARGET_COLS):
        actual = actual_gold_values[i]
        pred = real_prediction[i]
        delta = actual - pred # The Correction Vector
        total_error += abs(delta)
        print(f"{col:<20} | {actual:12.4f} | {pred:12.4f} | {delta:10.4f}")
    
    mae = total_error / len(TARGET_COLS)
    print("-" * 60)
    print(f"  IDENTITY MAE: {mae:.6f}")
    print("=" * 70)

if __name__ == "__main__":
    run_identity_test()
