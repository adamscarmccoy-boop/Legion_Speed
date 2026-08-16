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
INPUT_FILE = r"E:\music\iMAC Different3pianooo3.wav"
OUTPUT_DIR = Path(r"C:\WEB CASE STUDY\style_comparison")
LANCEDB_PATH = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
PARQUET_DIR = Path(r"C:\STUDIES_BACKUP\data\metadata\parquet_exports")

os.makedirs(OUTPUT_DIR, exist_ok=True)

FEATURE_COLS = ["rms", "crest_factor", "spectral_centroid"]
TARGET_COLS = ["gain", "ratio", "threshold"]

# ==============================================================================
# SOVEREIGN STYLE ENGINE
# ==============================================================================
class SovereignStyleEngine:
    def __init__(self, training_data):
        self.data = training_data
        self.scaler_x = StandardScaler()
        self.scaler_y = StandardScaler()
        self.forest = None
        self._train_forest()

    def _train_forest(self):
        X = self.data[FEATURE_COLS].fillna(0).values.astype(np.float32)
        Y = self.data[TARGET_COLS].fillna(0).values.astype(np.float32)
        X_scaled = self.scaler_x.fit_transform(X)
        Y_scaled = self.scaler_y.fit_transform(Y)
        self.forest = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42)
        self.forest.fit(X_scaled, Y_scaled)

    def render_with_style(self, input_path, target_vector, style_name):
        print(f"  [+] Sculpting Style: {style_name}...")
        y, sr = librosa.load(input_path, sr=None, mono=False)
        if y.ndim == 1: y = y[np.newaxis, :]
        
        hop_length = 512
        win_length = 2048
        rms = librosa.feature.rms(y=y[0], frame_length=win_length, hop_length=hop_length)[0]
        crest = np.ones_like(rms) * 3.0 
        centroid = librosa.feature.spectral_centroid(y=y[0], sr=sr, n_fft=win_length, hop_length=hop_length)[0]
        
        X_points = np.stack([rms, crest, centroid], axis=1)
        X_scaled = self.scaler_x.transform(X_points)
        
        # The "Sovereign Shift": We offset the predictions by the lapped Target Vector
        predictions_scaled = self.forest.predict(X_scaled)
        # We shift the scaled predictions toward the target lapped DNA
        predictions_scaled = (predictions_scaled * 0.5) + (target_vector * 0.5)
        
        predictions = self.scaler_y.inverse_transform(predictions_scaled)
        
        time_axis = np.arange(len(predictions))
        curves = {}
        for i, col in enumerate(TARGET_COLS):
            f = interp1d(time_axis, predictions[:, i], kind='cubic', fill_value="extrapolate")
            curves[col] = f(time_axis)
            
        gain_node = Gain(gain_db=0.0)
        comp_node = Compressor(threshold_db=-20.0, ratio=3.0)
        board = Pedalboard([gain_node, comp_node, Limiter(threshold_db=-0.3)])
        
        mastered = np.zeros_like(y)
        block_size = hop_length
        for start_samp in range(0, y.shape[1] - block_size, block_size):
            end_samp = start_samp + block_size
            idx = start_samp // hop_length
            if idx >= len(predictions): break
            gain_node.gain_db = float(curves['gain'][idx])
            comp_node.ratio = max(1.0, float(curves['ratio'][idx]))
            comp_node.threshold_db = float(curves['threshold'][idx])
            chunk = y[:, start_samp:end_samp]
            mastered[:, start_samp:end_samp] = board(chunk, sample_rate=sr)
            
        output_path = OUTPUT_DIR / f"STYLE_{style_name}_{os.path.basename(input_path)}"
        sf.write(output_path, mastered.T, sr)
        print(f"  ✅ Saved: {output_path}")

# ==============================================================================
# DATA HARVESTER
# ==============================================================================
def harvest_universal_data():
    all_frames = []
    for pf in PARQUET_DIR.glob("*.parquet"):
        try:
            df = pd.read_parquet(pf)
            if all(col in df.columns for col in FEATURE_COLS):
                if not all(col in df.columns for col in TARGET_COLS):
                    df['gain'] = df['rms'] * -1.0
                    df['ratio'] = df['crest_factor'] * 0.5
                    df['threshold'] = -20.0
                all_frames.append(df[FEATURE_COLS + TARGET_COLS])
        except Exception: continue
    return pd.concat(all_frames, ignore_index=True) if all_frames else None

if __name__ == "__main__":
    print("Initializing Sovereign Style-Transfer Pipeline...")
    data = harvest_universal_data()
    if data is None:
        print("FATAL: No data found."); sys.exit(1)
        
    engine = SovereignStyleEngine(data)
    
    # 1. Get Artist DNA (Lancedb)
    try:
        db = lancedb.connect(LANCEDB_PATH)
        table = db.open_table("omni_semantic_baselines")
        
        # Artist Vector (Mean of Chris Lake)
        cl_df = table.search([]).where("track_name LIKE '%Chris Lake%'").to_pandas()
        artist_vec = np.mean(np.stack(cl_df["vector"].tolist()), axis=0).astype(np.float32)
        artist_vec = artist_vec[:12] if artist_vec.shape[0] > 12 else np.pad(artist_vec, (0, 12 - artist_vec.shape[0]))
        
        # Universal Vector (Mean of all laptoptop lapped lapped lapped lapped data)
        uni_df = table.to_pandas()
        uni_vec = np.mean(np.stack(uni_df["vector"].tolist()), axis=0).astype(np.float32)
        uni_vec = uni_vec[:12] if uni_vec.shape[0] > 12 else np.pad(uni_vec, (0, 12 - uni_vec.shape[0]))
        
        # 2. THE DOUBLE RENDER
        engine.render_with_style(INPUT_FILE, artist_vec, "ChrisLake")
        engine.render_with_style(INPUT_FILE, uni_vec, "Universal")
        
    except Exception as e:
        print(f"FATAL: Lancedb error: {e}")
        
    print("\n" + "=" * 40)
    print("STYLE COMPARISON COMPLETE")
    print("=" * 40)
