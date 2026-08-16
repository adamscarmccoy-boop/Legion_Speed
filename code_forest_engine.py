import os
import sys
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

# Force UTF-8 to prevent Windows terminal crashes
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

print("🌲 CODE FOREST ENGINE - Test Run 🌲")

# 1. Load All Datasets (Code Mined, Notebooks, and Full Folder Shards)
from pathlib import Path

# A. Code Mined
df_code = pd.read_parquet(r"C:\WEB CASE STUDY\code_knowledge_audit.parquet")
df_code['source'] = 'code'

# B. Notebook Data
df_nb = pd.read_parquet(r"C:\WEB CASE STUDY\notebook_knowledge_audit.parquet")
df_nb['source'] = 'notebook'

# C. Full Folder (ray_cat_shards)
print("Loading Ray Cat Shards (Full Folder)...")
shard_dir = Path(r"C:\WEB CASE STUDY\ray_cat_shards")
shard_dfs = []
for f in shard_dir.glob("*.jsonl"):
    try:
        sdf = pd.read_json(f, lines=True)
        shard_dfs.append(sdf)
    except Exception as e:
        print(f"Skipping {f.name}: {e}")
df_shards = pd.concat(shard_dfs, ignore_index=True)
df_shards['size_kb'] = df_shards.get('size_bytes', 0) / 1024.0
df_shards['rows'] = 0 # Audio files have 0 code rows
df_shards['source'] = 'audio_shard'

# Unify them!
cols_to_keep = ['filename', 'size_kb', 'rows', 'source']
df = pd.concat([
    df_code[[c for c in cols_to_keep if c in df_code.columns]],
    df_nb[[c for c in cols_to_keep if c in df_nb.columns]],
    df_shards[[c for c in cols_to_keep if c in df_shards.columns]]
], ignore_index=True)

print(f"Loaded Unified Dataset: {len(df_code)} Code | {len(df_nb)} Notebooks | {len(df_shards)} Audio Shards")
print(f"Total Unified Records: {len(df)}")


# 2. Feature Engineering
# Extract extension from filename to use as our target prediction classes
df['ext'] = df['filename'].apply(lambda x: os.path.splitext(x)[1].lower() if isinstance(x, str) else '.unknown')

# Keep only classes with at least 2 samples for the test run
valid_classes = df['ext'].value_counts()[df['ext'].value_counts() >= 2].index
df_clean = df[df['ext'].isin(valid_classes)].copy()

features = ['size_kb', 'rows']
X = df_clean[features].fillna(0)

# Scale the features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Encode Labels (Predicting the file extension based on its size and row count footprint)
le = LabelEncoder()
y = le.fit_transform(df_clean['ext'])

print(f"Extracted Features: {features}")
print(f"Predicting across {len(le.classes_)} Code Categories: {list(le.classes_)}")

# 3. Isolation Forest (Anomaly Detection)
iso = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
df_clean['anomaly'] = iso.fit_predict(X_scaled)
anomalies = df_clean[df_clean['anomaly'] == -1]
print(f"\n🚨 Isolation Forest flagged {len(anomalies)} files as structural anomalies (extreme size/rows).")
if len(anomalies) > 0:
    print(f"   -> Example Anomaly: {anomalies.iloc[0]['filename']} ({anomalies.iloc[0]['size_kb']} KB)")

# 4. Random Forest Classifier
rf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
rf.fit(X_scaled, y)
score = rf.score(X_scaled, y)
print(f"\n✅ Random Forest Training Complete. Accuracy on Swarm Data: {score*100:.2f}%")

# 5. Export to ONNX Code Genome
onnx_path = r"C:\WEB CASE STUDY\mastered_output\code_genome_brain.onnx"
os.makedirs(os.path.dirname(onnx_path), exist_ok=True)

# Define the ONNX input footprint (matching the number of features)
initial_type = [('code_footprint_input', FloatTensorType([None, X_scaled.shape[1]]))]
onnx_model = convert_sklearn(rf, initial_types=initial_type)

with open(onnx_path, "wb") as f:
    f.write(onnx_model.SerializeToString())

print(f"\n🧬 Code Genome ONNX Model Successfully Exported to: {onnx_path}")
print("   -> Ready for inference!")
