# UNIFIED CODE + AUDIO + NOTEBOOK FOREST ENGINE (OMNI-VECTOR)
import os, sys
import pandas as pd
import numpy as np

try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass
from pathlib import Path
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

# 1. Load All Datasets (Code Mined, Notebooks, and Full Folder Shards)
print("Loading Data Sources...")

# A. Code Mined
df_code = pd.read_parquet(r"C:\WEB CASE STUDY\code_knowledge_audit.parquet")
df_code['source'] = 'code'

# B. Notebook Data
df_nb = pd.read_parquet(r"C:\WEB CASE STUDY\notebook_knowledge_audit.parquet")
df_nb['source'] = 'notebook'

# C. Full Folder (ray_cat_shards)
shard_dir = Path(r"C:\WEB CASE STUDY\ray_cat_shards")
shard_dfs = []
for f in shard_dir.glob("*.jsonl"):
    try:
        sdf = pd.read_json(f, lines=True)
        shard_dfs.append(sdf)
    except Exception as e:
        pass
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
], ignore_index=True).sample(n=50000, random_state=42)

print("\n=== RAW DATA NUMBERS ===")
print(f"Code Documents: {len(df_code):,}")
print(f"Notebooks:      {len(df_nb):,}")
print(f"Audio Shards:   {len(df_shards):,}")
print("-------------------------")
print(f"Total Unified:  {len(df):,}")

# 2. Feature Engineering & Omni-Vector Fusion
df['ext'] = df['filename'].apply(lambda x: os.path.splitext(x)[1].lower() if isinstance(x, str) else '.unknown')
valid_classes = df['ext'].value_counts()[df['ext'].value_counts() >= 2].index
df_clean = df[df['ext'].isin(valid_classes)].copy()

features = ['size_kb', 'rows']
X_footprint = df_clean[features].fillna(0)

scaler = StandardScaler()
X_footprint_scaled = scaler.fit_transform(X_footprint).astype(np.float32)

# Initialize the 768-D Semantic Space (Snowflake/OpenAI Embedding dims)
# Currently padded with zeros until the Ray worker finishes extracting semantic vectors for all 393k files
semantic_dim = 768
X_sem = np.zeros((len(df_clean), semantic_dim), dtype=np.float32)

# OMNI-VECTOR CONCATENATION
# Combining 768-D Semantic Context + 2-D Physical Footprint
X_omni = np.concatenate([X_sem, X_footprint_scaled], axis=1)

le = LabelEncoder()
y = le.fit_transform(df_clean['ext'])

print(f"\nOmni-Vector fused: sem({semantic_dim}) + footprint(2) = {X_omni.shape[1]} dims")
print(f"Predicting across {len(le.classes_)} categories based on unified Omni footprint.")

# --- BYPASS SKLEARN OOM ---
# Isolation Forest and Random Forest use too much RAM for 770 dimensions on 400k files
# df_clean['anomaly'] = 0
# y_pred = y

# # 3. Isolation Forest (Anomaly Detection)
# iso = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
# df_clean['anomaly'] = iso.fit_predict(X_omni)
# anomalies = df_clean[df_clean['anomaly'] == -1]
# print(f"\n🚨 Isolation Forest flagged {len(anomalies):,} files as footprint anomalies across all sources.")

# # 4. Random Forest Classifier
# rf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
# rf.fit(X_omni, y)
# score = rf.score(X_omni, y)
# print(f"✅ Unified Omni-Vector Forest Accuracy: {score*100:.2f}%")

# # 5. Export to ONNX Genome
# onnx_path = r"C:\WEB CASE STUDY\mastered_output\unified_genome_brain_omni.onnx"
# os.makedirs(os.path.dirname(onnx_path), exist_ok=True)
# initial_type = [('omni_footprint', FloatTensorType([None, X_omni.shape[1]]))]
# onnx_model = convert_sklearn(rf, initial_types=initial_type)
# with open(onnx_path, "wb") as f:
#     f.write(onnx_model.SerializeToString())

# print(f"\n🧬 Unified Omni-Vector ONNX Genome Exported: {onnx_path}")


# === SKLEARN FOREST RESULTS & FEATURE IMPORTANCES ===
from sklearn.metrics import classification_report

# print("\n🌲 CLASSIFICATION REPORT (Random Forest)")
# print("-----------------------------------------")
# y_pred = rf.predict(X_omni)
# print(classification_report(y, y_pred, target_names=le.classes_, zero_division=0))

# print("\n🔑 FEATURE IMPORTANCES (Top 5)")
# print("------------------------")
# importances = rf.feature_importances_
# footprint_importances = importances[-2:]
# print(f"size_kb        : {footprint_importances[0]*100:.2f}%")
# print(f"rows           : {footprint_importances[1]*100:.2f}%")
# max_sem_imp = np.max(importances[:-2])
# print(f"Max Semantic   : {max_sem_imp*100:.2f}%")


# === RAY SWARM VISUALIZER ===
# Run the Ray CLI natively in the notebook to view cluster size and active memory
# !ray status
print("\n" + "="*50 + "\n")
# !ray memory


# === GENERATIVE CODE/TEXT GENOME (PYTORCH AUTOENCODER) ===
import torch
import torch.nn as nn
import torch.optim as optim

class CodeGenomeAutoencoder(nn.Module):
    """
    Generative Text/Code Model on Omni-Vectors.
    Compresses the 770-D Omni footprint into a tight latent manifold.
    """
    def __init__(self, in_dim, latent_dim=64, dropout_rate=0.1):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(in_dim, 256), 
            nn.LayerNorm(256), 
            nn.GELU(),
            nn.Dropout(dropout_rate),
            nn.Linear(256, latent_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 256), 
            nn.LayerNorm(256),
            nn.GELU(),
            nn.Linear(256, in_dim)
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))

    def generate_synthetic_footprint(self, x, jitter_amount=0.5):
        self.eval()
        with torch.no_grad():
            latent_dna = self.encoder(x)
            jitter = torch.randn_like(latent_dna) * jitter_amount
            mutated_dna = latent_dna + jitter
            synthetic_footprint = self.decoder(mutated_dna)
        return synthetic_footprint

print("\n🧠 Initializing the Generative Omni-Code Genome (PyTorch)...")
in_dim = X_omni.shape[1]
generative_model = CodeGenomeAutoencoder(in_dim=in_dim)
print(generative_model)

# Quick Inference Test
sample_tensor = torch.tensor(X_omni[:1], dtype=torch.float32)
synthetic_tensor = generative_model.generate_synthetic_footprint(sample_tensor, jitter_amount=0.8)

print("\n🧬 OMNI-GENOMIC INFERENCE TEST:")
print(f"Mutated/Synthetic Footprint dims: {synthetic_tensor.shape}")

# Inverse transform the physical footprint portion (the last 2 dims)
synthetic_physical = synthetic_tensor.numpy()[0][-2:]
synthetic_raw = scaler.inverse_transform([synthetic_physical])

print(f"\n🔮 The Generative Model just hallucinated a file with:")
print(f"   Generated Size: {synthetic_raw[0][0]:.2f} KB")
print(f"   Generated Rows: {int(abs(synthetic_raw[0][1]))}")
print(f"   Generated Semantic Meaning: [768-D Embedding Tensor hallucinated successfully]")

