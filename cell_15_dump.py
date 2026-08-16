import pandas as pd                                                                                                                                                                                                                                                                                           ▄
import numpy as np                                                                                                                                                                                                                                                                                            ▀
import torch
import torch.nn as nn
import os, datetime, re, lancedb
from scipy.spatial.distance import cdist
import soundfile as sf
import warnings
import ray
import logging as log
from prometheus_client import start_http_server, Summary, Gauge
from grafana.client import StatsDClient
from pydantic import BaseModel, Field, field_validator
from grafana.client.mixin import GrafanaClientMixinfanaClientMixin
from grafana.client.model import *
from torch_tensorboard import SummaryWriter
from tqdm import tqdm



warnings.filterwarnings('ignore')

print("[BOOT] Starting v3 Omni-Generation Engine...")                                                                                               ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
                                                                                                                                                                                                                                                                                      4 MCP servers · 61 skills 
# =====================================================================                                                                             ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# CONFIGURATION                                                                                                                                     _complete.ipynb"
# =====================================================================                                                                             ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
LANCEDB_PATH = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\vectors\lancedb_store"                                                                                ·                  SCARS_LAB                 ·                   592.6k tokens                 ·                  ✖ 4 errors (F12 for details) 
SAMPLES_JSON = r'C:\WEB CASE STUDY\data\enriched_samples_only.json'
# UPDATED TO V3 WEIGHTS
WEIGHTS_PATH = r"C:\WEB CASE STUDY\sonic_dna_output\fretflow_omni_v3.pt"
OUTPUT_DIR   = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\generated_audio"

# =====================================================================
# DATA LOADING
# =====================================================================
ldb = lancedb.connect(LANCEDB_PATH)
vibe_df = ldb.open_table("audio_vibe_gpu").to_pandas()
samples_df = pd.read_json(SAMPLES_JSON)

# Merge on filename
df = pd.merge(vibe_df, samples_df, on='filename', how='inner')
print(f"[SYSTEM] Clean Dataset Size: {len(df)} tracks")

def build_omni_vector(row):
    sem = np.array(row['vector'], dtype=np.float32)
    bpm = np.array([float(row.get('tempo', 128.0))], dtype=np.float32)
    return np.concatenate([sem, bpm])
    
df['omni_vector'] = df.apply(build_omni_vector, axis=1)
data_matrix = np.vstack(df['omni_vector'].values)
data_matrix = np.nan_to_num(data_matrix, nan=0.0)
    
# Load v3 Checkpoint
checkpoint = torch.load(WEIGHTS_PATH)
X_mean = np.array(checkpoint['X_mean'], dtype=np.float32)
X_std = np.array(checkpoint['X_std'], dtype=np.float32)

# Create Category Mapping (v3 requires category indices)
# We derive this from the dataset to ensure consistency with the loaded weights
unique_genres = df['genre_class'].unique()
genre2idx = {genre: i for i, genre in enumerate(unique_genres)}
print(f"[SYSTEM] Category Mapping initialized with {len(genre2idx)} genres")

# =====================================================================
# V3 ARCHITECTURE: OmniCondVAE
# =====================================================================
class OmniCondVAE(nn.Module):
    def __init__(self, in_dim, latent_dim, num_categories, emb_dim=16):
        super().__init__()
        # Encoder: 1036 -> 512 -> 256 -> 128 -> latent_dim * 232
        self.encoder = nn.Sequential(
            nn.Linear(in_dim, 512), nn.LayerNorm(512), nn.GELU(),
            nn.Linear(512, 256), nn.LayerNorm(256), nn.GELU(),
            nn.Linear(256, 128), nnimport pandas as pd                                                                                                                                                                                                                                                                                           ▄
import numpy as np                                                                                                                                                                                                                                                                                            ▀
import torch
import torch.nn as nn
import os, datetime, re, lancedb
from scipy.spatial.distance import cdist
import soundfile as sf
import warnings
import ray
import logging as log
from prometheus_client import start_http_server, Summary, Gauge
from grafana.client import StatsDClient
from pydantic import BaseModel, Field, field_validator
from grafana.client.mixin import GrafanaClientMixin
from grafana.client.model import *
from torch_tensorboard import SummaryWriter
from tqdm import tqdm



warnings.filterwarnings('ignore')

print("[BOOT] Starting v3 Omni-Generation Engine...")                                                                                               ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
                                                                                                                                                                                                                                                                                      4 MCP servers · 61 skills 
# =====================================================================                                                                             ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# CONFIGURATION                                                                                                                                     _complete.ipynb"
# =====================================================================                                                                             ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
LANCEDB_PATH = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\vectors\lancedb_store"                                                                                ·                  SCARS_LAB                 ·                   592.6k tokens                 ·                  ✖ 4 errors (F12 for details) 
SAMPLES_JSON = r'C:\WEB CASE STUDY\data\enriched_samples_only.json'
# UPDATED TO V3 WEIGHTS
WEIGHTS_PATH = r"C:\WEB CASE STUDY\sonic_dna_output\fretflow_omni_v3.pt"
OUTPUT_DIR   = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\generated_audio"

# =====================================================================
# DATA LOADING
# =====================================================================
ldb = lancedb.connect(LANCEDB_PATH)
vibe_df = ldb.open_table("audio_vibe_gpu").to_pandas()
samples_df = pd.read_json(SAMPLES_JSON)

# Merge on filename
df = pd.merge(vibe_df, samples_df, on='filename', how='inner')
print(f"[SYSTEM] Clean Dataset Size: {len(df)} tracks")

def build_omni_vector(row):
    sem = np.array(row['vector'], dtype=np.float32)
    bpm = np.array([float(row.get('tempo', 128.0))], dtype=np.float32)
    return np.concatenate([sem, bpm])
    
df['omni_vector'] = df.apply(build_omni_vector, axis=1)
data_matrix = np.vstack(df['omni_vector'].values)
data_matrix = np.nan_to_num(data_matrix, nan=0.0)
    
# Load v3 Checkpoint
checkpoint = torch.load(WEIGHTS_PATH)
X_mean = np.array(checkpoint['X_mean'], dtype=np.float32)
X_std = np.array(checkpoint['X_std'], dtype=np.float32)

# Create Category Mapping (v3 requires category indices)
# We derive this from the dataset to ensure consistency with the loaded weights
unique_genres = df['genre_class'].unique()
genre2idx = {genre: i for i, genre in enumerate(unique_genres)}
print(f"[SYSTEM] Category Mapping initialized with {len(genre2idx)} genres")

# =====================================================================
# V3 ARCHITECTURE: OmniCondVAE
# =====================================================================
class OmniCondVAE(nn.Module):
    def __init__(self, in_dim, latent_dim, num_categories, emb_dim=16):
        super().__init__()
        # Encoder: 1036 -> 512 -> 256 -> 128 -> latent_dim * 232
        self.encoder = nn.Sequential(
            nn.Linear(in_dim, 512), nn.LayerNorm(512), nn.GELU(),
            nn.Linear(512, 256), nn.LayerNorm(256), nn.GELU(),
            nn.Linear(256, 128), nn