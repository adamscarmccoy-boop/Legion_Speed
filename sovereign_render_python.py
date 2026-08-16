import os
import sys
import numpy as np
import pandas as pd
import librosa
import soundfile as sf
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from scipy.interpolate import interp1d
from pathlib import Path
import lancedb
from pedalboard import Pedalboard, Compressor, HighpassFilter, Gain, Limiter

# Force UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ==============================================================================
# CONFIGURATION
# ==============================================================================
INPUT_DIR = Path(r"C:\Users\adams\Downloads")
OUTPUT_DIR = Path(r"C:\WEB CASE STUDY\python_masters")
CURVES_DIR = Path(r"C:\WEB CASE STUDY\curves")
LANCEDB_PATH = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
PARQUET_DIR = Path(r"C:\STUDIES_BACKUP\data\metadata\parquet_exports")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CURVES_DIR, exist_ok=True)

FEATURE_COLS = ["rms", "crest_factor", "spectral_centroid"]
TARGET_COLS = ["gain", "ratio", "threshold"]

# ==============================================================================
# SOVEREIGN ENGINE
# ==============================================================================
class SovereignRenderer:
    def __init__(self, training_data):
        self.data = training_data
        self.scaler_x = StandardScaler()
        self.scaler_y = StandardScaler()
        self.forest = None
        
        # Pre-train the Forest on the harvested data
        self._train_forest()

    def _train_forest(self):
        print("  [+] Training Sovereign Forest on Universal Data...")
        X = self.data[FEATURE_COLS].fillna(0).values.astype(np.float32)
        Y = self.data[TARGET_COLS].fillna(0).values.astype(np.float32)
        
        X_scaled = self.scaler_x.fit_transform(X)
        Y_scaled = self.scaler_y.fit_transform(Y)
        
        self.forest = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42)
        self.forest.fit(X_scaled, Y_scaled)
        self.scaler_y = self.scaler_y # store for inverse

    def process_file(self, input_path):
        file_name = input_path.name
        print(f"\n🚀 Processing: {file_name}")
        
        y, sr = librosa.load(input_path, sr=None, mono=False)
        if y.ndim == 1: y = y[np.newaxis, :]
        
        # 1. Extract "Points" (Sovereign Feature Extraction)
        # We use a sliding window to get the lapped features
        hop_length = 512
        win_length = 2048
        
        rms = librosa.feature.rms(y=y[0], frame_length=win_length, hop_length=hop_length)[0]
        # Simplified crest factor and centroid for the demo
        # In full mode, we'd use the exact lapped lancedb logic
        crest = np.ones_like(rms) * 3.0 
        centroid = librosa.feature.spectral_centroid(y=y[0], sr=sr, n_fft=win_length, hop_length=hop_length)[0]
        
        X_points = np.stack([rms, crest, centroid], axis=1)
        X_scaled = self.scaler_x.transform(X_points)
        
        # 2. Forest Prediction (Point -> Tuning)
        predictions_scaled = self.forest.predict(X_scaled)
        predictions = self.scaler_y.inverse_transform(predictions_scaled)
        
        # 3. Temporal Interpolation (Slew-Rate modulation)
        time_axis = np.arange(len(predictions))
        curves = {}
        for i, col in enumerate(TARGET_COLS):
            f = interp1d(time_axis, predictions[:, i], kind='cubic', fill_value="extrapolate")
            curves[col] = f(time_axis)
            
        # Save the curves for C++ verification
        curve_df = pd.DataFrame(curves)
        curve_df.to_csv(CURVES_DIR / f"{file_name}_curves.csv", index=False)
        
        # 4. Physical Rendering (Pedalboard)
        print("  [+] Applying Sovereign Flow...")
        gain_node = Gain(gain_db=0.0)
        comp_node = Compressor(threshold_db=-20.0, ratio=3.0)
        board = Pedalboard([gain_node, comp_node, Limiter(threshold_db=-0.3)])
        
        mastered = np.zeros_like(y)
        block_size = hop_length
        for start_samp in range(0, y.shape[1] - block_size, block_size):
            end_samp = start_samp + block_size
            idx = start_samp // hop_length
            if idx >= len(predictions): break
            
            # Update parameters in real-time
            gain_node.gain_db = float(curves['gain'][idx])
            comp_node.ratio = max(1.0, float(curves['ratio'][idx]))
            comp_node.threshold_db = float(curves['threshold'][idx])
            
            chunk = y[:, start_samp:end_samp]
            mastered[:, start_samp:end_samp] = board(chunk, sample_rate=sr)
            
        sf.write(OUTPUT_DIR / f"SOV_{file_name}", mastered.T, sr)
        print(f"  ✅ Saved: SOV_{file_name}")

# ==============================================================================
# HARVESTER
# ==============================================================================
def harvest_universal_data():
    all_frames = []
    # Scan Parquets
    for pf in PARQUET_DIR.glob("*.parquet"):
        try:
            df = pd.read_parquet(pf)
            if all(col in df.columns for col in FEATURE_COLS):
                if not all(col in df.columns for col in TARGET_COLS):
                    df['gain'] = df['rms'] * -1.0
                    df['ratio'] = df['crest_factor'] * 0.5
                    df['threshold'] = df_gold['rms'].mean() - 20.0 if 'df_gold' in locals() else -20.0
                all_frames.append(df[FEATURE_COLS + TARGET_COLS])
        except Exception: continue
    
    # Scan LanceDB
    try:
        db = lancedb.connect(LANCEDB_PATH)
        table = db.open_table("omni_semantic_baselines")
        df_lancedb = table.to_pandas()
        if all(col in df_lancedb.columns for col in FEATURE_COLS):
            if not all(col in df_lancedb.columns for col in TARGET_COLS):
                df_lancedb['gain'] = df_lancedb['rms'] * -1.0
                df_lancedb['ratio'] = df_lancedb['crest_factor'] * 0.5
                df_lancedb['threshold'] = -20.0
            all_frames.append(df_lancedb[FEATURE_COLS + TARGET_COLS])
    except Exception: pass
    
    return pd.concat(all_frames, ignore_index=True) if all_frames else None

if __name__ == "__main__":
    print("Initializing Sovereign Universal Renderer...")
    data = harvest_universal_data()
    if data is None:
        print("FATAL: No data found."); sys.exit(1)
        
    renderer = SovereignRenderer(data)
    
    wav_files = list(INPUT_DIR.glob("*.wav"))
    print(f"Found {len(wav_files)} files in Downloads.")
    
    for wf in wav_files:
        renderer.process_file(wf)
        
    print("\n" + "=" * 40)
    print("PYTHON RENDERING COMPLETE")
    print("Curves saved to: " + str(CURVES_DIR))
    print("=" * 40)
