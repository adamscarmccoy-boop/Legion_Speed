# RAG Export: sonic dna dsp cols transient density chroma semantic_dim latent_dim omni_vector_list

- Created: `2026-07-02T23:36:19`
- Selected DB path: `C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag`
- Embedding model: `snowflake-arctic-embed-l-v2.0-f16`
- Embedding status: `ok, dims=1024`
- Limit: `12`
- Snippet chars: `8000`

## Environment

- `lancedb`: ok
- `pandas`: ok
- `ray`: ok
- `pyarrow`: ok

## DB Path Probe

- `E:\WEB CASE STUDY\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag`
  - exists: `True`
  - score: `0`
  - tables: `NONE`
- `C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag`
  - exists: `True`
  - score: `2`
  - tables: `chris_lake_speed_test, chris_lake_web_intel, mined_code_vectors, mined_documentation_vectors`
- `C:\WEB CASE STUDY\lancedb_web_intel_rag`
  - exists: `True`
  - score: `0`
  - tables: `NONE`
- `C:\WEB CASE STUDY\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag`
  - exists: `False`
  - score: `0`
  - tables: `NONE`
- `E:\WEB CASE STUDY\lancedb_web_intel_rag`
  - exists: `False`
  - score: `0`
  - tables: `NONE`

## Selected LanceDB Tables

- `chris_lake_speed_test`
- `chris_lake_web_intel`
- `mined_code_vectors`
- `mined_documentation_vectors`

## Semantic Code Results

### Result 1: `C:/WEB CASE STUDY/upgraded_dynamic_batch_master_complete.py` | distance=0.9665

- Symbol: `SonicDNAMini`

```python
class SonicDNAMini(nn.Module):
    def __init__(self, in_dim, latent_dim):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(in_dim, 128), nn.LayerNorm(128), nn.GELU(),
            nn.Linear(128, 64), nn.LayerNorm(64), nn.GELU(),
            nn.Linear(64, latent_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 64), nn.GELU(),
            nn.Linear(64, 128), nn.GELU(),
            nn.Linear(128, in_dim)
        )
    def forward(self, x):
        return self.decoder(self.encoder(x))
```

### Result 2: `C:/WEB CASE STUDY/Acoustic-DNA-Audio-Engine/engine/analysis.py` | distance=1.0239

- Symbol: `process_buffer`

```python
def process_buffer(self, raw_buffer):
        """
        Applies DSP conditioning and extracts Chroma DNA.
        """
        if len(raw_buffer) != self.buffer_size:
            logger.warning(f"Buffer size mismatch! Expected {self.buffer_size}, got {len(raw_buffer)}")
        
        # 1. Condition
        conditioned = self.board(raw_buffer, sample_rate=self.sr)
        
        # 2. Extract Chroma (12-note energy vector)
        # Optimized hop_length for single-frame inference
        chroma = librosa.feature.chroma_stft(
            y=conditioned, 
            sr=self.sr, 
            n_fft=self.buffer_size, 
            hop_length=self.buffer_size + 1
        )
        
        dna_vector = np.mean(chroma, axis=1)
        
        # Log high-energy detections (simplified confidence)
        if np.max(dna_vector) > 0.8:
            logger.info(f"High-confidence note detected: NoteIndex={np.argmax(dna_vector)}")
            
        return dna_vector
```

### Result 3: `C:/WEB CASE STUDY/train_omni_v3_generation.py` | distance=1.0397

- Symbol: `module`

```python
"""
train_omni_v3_generation.py
===========================
Conditional VAE (OmniCondVAE v3) — full train + generate pipeline.

Data sources:
  - LanceDB omni_semantic_baselines  (5,908 rows: DSP + 384-dim semantic)
  - DuckDB  sonic_dna                (unmastered stems DSP)
  - JSON    enriched_samples_only    (3,983 rows: genre_class + BPM)

Output: sonic_dna_output/fretflow_omni_v3.pt
        sonic_dna_output/training_curve_omni_v3.png
"""
import sys, os, time, warnings
warnings.filterwarnings("ignore")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import ray

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────
LANCEDB_PATH      = r"C:\STUDIES_BACKUP\v
```

### Result 4: `C:/WEB CASE STUDY/Acoustic-DNA-Audio-Engine/engine/analysis.py` | distance=1.0443

- Symbol: `AcousticDNAEngine`

```python
class AcousticDNAEngine:
    """
    Production-ready feature extraction core.
    Designed for zero-copy buffer handoffs with integrated H.O.R.N. logging.
    """
    def __init__(self, sample_rate=44100, buffer_size=1024):
        self.sr = sample_rate
        self.buffer_size = buffer_size
        self.board = Pedalboard([Gain(gain_db=6.0)])
        logger.info(f"Acoustic DNA Engine Initialized: SR={self.sr}, Buffer={self.buffer_size}")

    def process_buffer(self, raw_buffer):
        """
        Applies DSP conditioning and extracts Chroma DNA.
        """
        if len(raw_buffer) != self.buffer_size:
            logger.warning(f"Buffer size mismatch! Expected {self.buffer_size}, got {len(raw_buffer)}")
        
        # 1. Condition
        conditioned = self.board(raw_buffer, sample_rate=self.sr)
        
        # 2. Extract Chroma (12-note energy vector)
        # Optimized hop_length for single-frame inference
        chroma = librosa.feature.chroma_stft(
            y=conditioned, 
            sr=self.sr, 
            n_fft=self.buffer_size, 
            hop_length=self.buffer_size + 1
        )
        
        dna_vector = np.mean(chroma, axis=1)
        
        # Log high-energy detections (simplified confidence)
        if np.max(dna_vector) > 0.8:
            logger.info(f"High-confidence note detected: NoteIndex={np.argmax(dna_vector)}")
            
        return dna_vector

    def get_latency_optimized_window(self):
        """Returns the recommended
```

### Result 5: `C:/WEB CASE STUDY/execute_clean_generation.py` | distance=1.0483

- Symbol: `module`

```python
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import os
import datetime
import re
import lancedb
from scipy.spatial.distance import cdist
import soundfile as sf
import warnings
warnings.filterwarnings('ignore')

print("[BOOT] Starting Clean Data Generation Engine...")

# Load Semantic Vectors (Real Float Arrays)
LANCEDB_PATH = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\vectors\lancedb_store"
ldb = lancedb.connect(LANCEDB_PATH)
vibe_df = ldb.open_table("audio_vibe_gpu").to_pandas()

# Load Clean Enriched Samples
samples_df = pd.read_json(r'C:\WEB CASE STUDY\data\enriched_samples_only.json')

# Merge them on filename
df = pd.merge(vibe_df, samples_df, on='filename', how='inner')
print(f"[SYSTEM] Clean Dataset Size: {len(df)} tracks")

def build_omni_vector(row):
    sem = np.array(row['vector'], dtype=np.float32)
    bpm = np.array([float(row.get('tempo', 128.0))], dtype=np.float32)
    return np.concatenate([sem, bpm])

df['omni_vector'] = df.apply(build_omni
```

### Result 6: `C:/WEB CASE STUDY/Acoustic-DNA-Audio-Engine/tests/test_engine.py` | distance=1.0536

- Symbol: `test_feature_extraction_shape`

```python
def test_feature_extraction_shape(engine):
    """Ensure the Acoustic DNA vector is exactly 12 dimensions (C through B)."""
    dummy_buffer = np.random.uniform(-0.1, 0.1, 1024).astype(np.float32)
    dna = engine.process_buffer(dummy_buffer)
    assert dna.shape == (12,)
    assert np.all(dna >= 0)
```

### Result 7: `C:/WEB CASE STUDY/omni_v3_train.py` | distance=1.0563

- Symbol: `__init__`

```python
def __init__(self, omni_dim, latent_dim, n_genres):
        super().__init__()
        self.omni_dim = omni_dim
        self.latent_dim = latent_dim
        self.genre_emb = nn.Embedding(n_genres, 16)
        
        # Encoder: 1036+16 -> 512 -> 256 -> 128 -> (mu, var)
        self.encoder_net = nn.Sequential(
            nn.Linear(omni_dim + 16, 512), nn.LayerNorm(512), nn.GELU(),
            nn.Linear(512, 256), nn.LayerNorm(256), nn.GELU(),
            nn.Linear(256, 128), nn.LayerNorm(128), nn.GELU(),
        )
        self.fc_mu = nn.Linear(128, latent_dim)
        self.fc_var = nn.Linear(128, latent_dim)
        
        # Decoder: latent+16 -> 128 -> 256 -> 512 -> 1036
        self.decoder_net = nn.Sequential(
            nn.Linear(latent_dim + 16, 128), nn.LayerNorm(128), nn.GELU(),
            nn.Linear(128, 256), nn.LayerNorm(256), nn.GELU(),
            nn.Linear(256, 512), nn.LayerNorm(512), nn.GELU(),
            nn.Linear(512, omni_dim)
        )
        
        # Mastering Head: 11 DSP -> 3 Params
        self.mastering_head = nn.Sequential(
            nn.Linear(11, 32), nn.GELU(), nn.Linear(32, 3)
        )
```

### Result 8: `C:/WEB CASE STUDY/bulk_generator_clean.py` | distance=1.0619

- Symbol: `module`

```python
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import os
import datetime
from scipy.spatial.distance import cdist
import lancedb
import warnings
warnings.filterwarnings('ignore')

print("[BOOT] Running CLEAN BULK Generation Trace (100 Tracks)...")

# Load Semantic Vectors
LANCEDB_PATH = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\vectors\lancedb_store"
ldb = lancedb.connect(LANCEDB_PATH)
vibe_df = ldb.open_table("audio_vibe_gpu").to_pandas()

# Load Clean Enriched Samples
samples_df = pd.read_json(r'C:\WEB CASE STUDY\data\enriched_samples_only.json')

# Merge them on filename
df = pd.merge(vibe_df, samples_df, on='filename', how='inner')

def build_omni_vector(row):
    sem = np.array(row['vector'], dtype=np.float32)
    bpm = np.array([float(row.get('tempo', 128.0))], dtype=np.float32)
    return np.concatenate([sem, bpm])

df['omni_vector'] = df.apply(build_omni_vector, axis=1)

weights_path = r"C:\WEB CASE STUDY\sonic_dna_output\fretflow_v2.pt"
checkpoint =
```

### Result 9: `C:/WEB CASE STUDY/train_omni_v3_generation.py` | distance=1.0743

- Symbol: `__init__`

```python
def __init__(self, omni_dim, latent_dim, n_genres, genre_emb=32):
        super().__init__()
        self.omni_dim   = omni_dim
        self.latent_dim = latent_dim
        self.cond_dim   = genre_emb + 1

        self.genre_emb = nn.Embedding(n_genres, genre_emb)

        # ── Encoder ──────────────────────────────────────────────────────────
        enc_in = omni_dim + self.cond_dim
        self.encoder = nn.Sequential(
            nn.Linear(enc_in, 512), nn.LayerNorm(512), nn.GELU(),
            ResBlock(512),
            nn.Linear(512, 256), nn.LayerNorm(256), nn.GELU(),
            ResBlock(256),
            nn.Linear(256, 128), nn.LayerNorm(128), nn.GELU(),
        )
        self.fc_mu  = nn.Linear(128, latent_dim)
        self.fc_var = nn.Linear(128, latent_dim)

        # ── Decoder ──────────────────────────────────────────────────────────
        dec_in = latent_dim + self.cond_dim
        self.decoder = nn.Sequential(
            nn.Linear(dec_in, 128), nn.LayerNorm(128), nn.GELU(),
            ResBlock(128),
            nn.Linear(128, 256), nn.LayerNorm(256), nn.GELU(),
            ResBlock(256),
            nn.Linear(256, 512), nn.LayerNorm(512), nn.GELU(),
            nn.Linear(512, omni_dim),
        )

        # ── Mastering head (DSP -> compression params) ────────────────────────
        self.mastering_head = nn.Sequential(
            nn.Linear(11, 64), nn.GELU(),
            nn.Linear(64, 32), nn.GELU(),
            nn.Linear(32, 3),   # gain_db, comp_rati
```

### Result 10: `C:/WEB CASE STUDY/omni_v3_train.py` | distance=1.0803

- Symbol: `OmniCondVAE`

```python
class OmniCondVAE(nn.Module):
    def __init__(self, omni_dim, latent_dim, n_genres):
        super().__init__()
        self.omni_dim = omni_dim
        self.latent_dim = latent_dim
        self.genre_emb = nn.Embedding(n_genres, 16)
        
        # Encoder: 1036+16 -> 512 -> 256 -> 128 -> (mu, var)
        self.encoder_net = nn.Sequential(
            nn.Linear(omni_dim + 16, 512), nn.LayerNorm(512), nn.GELU(),
            nn.Linear(512, 256), nn.LayerNorm(256), nn.GELU(),
            nn.Linear(256, 128), nn.LayerNorm(128), nn.GELU(),
        )
        self.fc_mu = nn.Linear(128, latent_dim)
        self.fc_var = nn.Linear(128, latent_dim)
        
        # Decoder: latent+16 -> 128 -> 256 -> 512 -> 1036
        self.decoder_net = nn.Sequential(
            nn.Linear(latent_dim + 16, 128), nn.LayerNorm(128), nn.GELU(),
            nn.Linear(128, 256), nn.LayerNorm(256), nn.GELU(),
            nn.Linear(256, 512), nn.LayerNorm(512), nn.GELU(),
            nn.Linear(512, omni_dim)
        )
        
        # Mastering Head: 11 DSP -> 3 Params
        self.mastering_head = nn.Sequential(
            nn.Linear(11, 32), nn.GELU(), nn.Linear(32, 3)
        )

    def forward(self, x, genre_ids):
        cond = self.genre_emb(genre_ids)
        h = self.encoder_net(torch.cat([x, cond], dim=1))
        mu = self.fc_mu(h)
        log_var = self.fc_var(h)
        
        # Reparameterization
        std = torch.exp(0.5 * log_var)
        eps = torch.randn_like(std)
        z = 
```

### Result 11: `C:/WEB CASE STUDY/train_omni_v3_generation.py` | distance=1.0828

- Symbol: `OmniCondVAE`

```python
class OmniCondVAE(nn.Module):
    """
    Conditional VAE:
      encode(x, cond) -> mu, log_var
      decode(z, cond) -> x_recon
      mastering_head(dsp_slice) -> (gain_db, comp_ratio, threshold_db)
    Generation:
      sample z ~ N(0,I), decode with desired genre+BPM condition
    """
    def __init__(self, omni_dim, latent_dim, n_genres, genre_emb=32):
        super().__init__()
        self.omni_dim   = omni_dim
        self.latent_dim = latent_dim
        self.cond_dim   = genre_emb + 1

        self.genre_emb = nn.Embedding(n_genres, genre_emb)

        # ── Encoder ──────────────────────────────────────────────────────────
        enc_in = omni_dim + self.cond_dim
        self.encoder = nn.Sequential(
            nn.Linear(enc_in, 512), nn.LayerNorm(512), nn.GELU(),
            ResBlock(512),
            nn.Linear(512, 256), nn.LayerNorm(256), nn.GELU(),
            ResBlock(256),
            nn.Linear(256, 128), nn.LayerNorm(128), nn.GELU(),
        )
        self.fc_mu  = nn.Linear(128, latent_dim)
        self.fc_var = nn.Linear(128, latent_dim)

        # ── Decoder ──────────────────────────────────────────────────────────
        dec_in = latent_dim + self.cond_dim
        self.decoder = nn.Sequential(
            nn.Linear(dec_in, 128), nn.LayerNorm(128), nn.GELU(),
            ResBlock(128),
            nn.Linear(128, 256), nn.LayerNorm(256), nn.GELU(),
            ResBlock(256),
            nn.Linear(256, 512), nn.LayerNorm(512), nn.GELU(),
            nn.Lin
```

### Result 12: `C:/WEB CASE STUDY/test_weights_on_mastered.py` | distance=1.0941

- Symbol: `SonicDNAMaster`

```python
class SonicDNAMaster:
    def __init__(self, model_path):
        ckpt = torch.load(model_path, weights_only=False)
        self.in_dim  = ckpt["in_dim"]
        self.out_dim = ckpt["out_dim"]
        self.dsp_cols = ckpt["dsp_cols"]
        self.X_mean  = torch.tensor(ckpt["X_mean"])
        self.X_std   = torch.tensor(ckpt["X_std"])
        self.Y_mean  = torch.tensor(ckpt["Y_mean"])
        self.Y_std   = torch.tensor(ckpt["Y_std"])
        self.model   = _MasteringNet(self.in_dim, self.out_dim)
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.model.eval()

    def predict(self, feat_dict: dict):
        vec = torch.tensor([float(feat_dict.get(c, 0.0)) for c in self.dsp_cols], dtype=torch.float32)
        vec_norm = (vec - self.X_mean) / self.X_std
        with torch.no_grad():
            raw = self.model(vec_norm.unsqueeze(0)).squeeze()
        out = raw * self.Y_std + self.Y_mean
        gain_db      = float(np.clip(out[0].item(), -12.0, 12.0))
        comp_ratio   = float(np.clip(out[1].item(), 1.0, 4.5))
        threshold_db = float(np.clip(out[2].item(), -80.0, 0.0))
        return gain_db, comp_ratio, threshold_db
```

## Semantic Documentation Results

### Match 1 | distance=1.2198

each series is a 1D list of floats/integers.
e.g., [[0.1, 0.2, ..., 0.N], [0.3, 0.4, ..., 0.M]]
Each series is a 1D list of floats/integers.
"""
# Convert list of 1D series to a 2D numpy array (batch_size, seq_len).
batch_x
=
np
.
array
(
batch_x
,
dtype
=
np
.
float32
)
batch_x
=
torch
.
from_numpy
(
batch_x
)
.
float
()
.
to
(
self
.
device
)
# Ensure batch_x is 3D: (batch_size, seq_len, num_features)
# For univariate 'S' models, num_features is 1.
if
batch_x
.
ndim
==
2
:
batch_x
=
batch_x
.
unsqueeze
(
-
1
)
with
torch
.
no_grad
():
outputs
=
self
.
model
(
batch_x
)
# Output shape: (batch_size, pred_len, features_out)
# Slice to get the prediction length part of the output.
# The [:, :, :] part takes all output features.
# For 'S' (single-feature) forecasting, DLinear typically outputs 1 feature.
# For 'M' (multi-feature) forecasting, DLinear typically outputs multiple features.
outputs
=
outputs
[:,
-
self
.
args
[
"pred_len"
]
:,
:]
# If 'S' (single feature forecasting) and the

### Match 2 | distance=1.2239

e text.
Generates embeddings.
Writes the results to Chroma DB.
# Constants for your data sources and vector store configuration
EMBEDDER_MODEL
=
"intfloat/multilingual-e5-large-instruct"
CHROMA_PATH
=
"/mnt/cluster_storage/vector_store"
CHROMA_COLLECTION_NAME
=
"anyscale_jobs_docs_embeddings"
# Build the processing pipeline using Ray Data API
processed_ds
=
(
ds
.
flat_map
(
Chunker
,
fn_constructor_kwargs
=
{
"method"
:
"recursive"
},
concurrency
=
5
,
num_cpus
=
1
)
.
map_batches
(
Embedder
,
fn_constructor_kwargs
=
{
"model_name"
:
EMBEDDER_MODEL
},
batch_size
=
800
,
concurrency
=
1
,
num_gpus
=
1
)
.
map_batches
(
ChromaWriter
,
batch_size
=
500
,
concurrency
=
1
,
num_cpus
=
1
,
fn_constructor_kwargs
=
{
"collection_name"
:
CHROMA_COLLECTION_NAME
,
"chroma_path"
:
CHROMA_PATH
}
)
)
Execute the Entire Text Processing Pipeline
#
Run the pipeline to process all documents:
# Execute pipeline
processed_ds
.
take_all
()
print
(
"Data ingestion completed successfully!"
)
Verifying and S

### Match 3 | distance=1.2393

parallel, so a simple
ds.map
distributes the work across the cluster’s CPU cores.
ds.map()
applies the transformation function to each record in parallel across the cluster. Whenever possible, Ray avoids transferring objects across network connections to take advantage of zero-copy reads, avoiding serialization and deserialization overhead.
As soon as blocks of data finish preprocessing, they can move to the next stage without waiting for the entire dataset.
def
resample
(
item
):
# Resample at 16kHz, which is what openai/whisper-large-v3-turbo was trained on.
audio_bytes
=
item
.
pop
(
"audio_bytes"
)
new_sampling_rate
=
16000
data
,
sampling_rate
=
sf
.
read
(
io
.
BytesIO
(
audio_bytes
),
dtype
=
"float32"
,
always_2d
=
True
)
waveform
=
torch
.
from_numpy
(
data
.
T
.
copy
())
waveform
=
T
.
Resample
(
sampling_rate
,
new_sampling_rate
)(
waveform
)
.
squeeze
()
item
[
"arr"
]
=
np
.
array
(
waveform
)
item
[
"sampling_rate"
]
=
new_sampling_rate
return
item
ds
=
raw_ds
.
map
(
re

### Match 4 | distance=1.2514

h metadata
import
uuid
all_chunks
=
[]
for
page
in
pages
:
chunks
=
chunker
.
chunk_document
(
page
[
"text"
])
for
chunk
in
chunks
:
all_chunks
.
append
({
"id"
:
str
(
uuid
.
uuid4
()),
# Generate a unique ID for each chunk
"text"
:
chunk
,
"metadata"
:
{
"source"
:
page
[
"source"
],
"doc_id"
:
page
[
"doc_id"
],
"file_name"
:
page
[
"file_name"
],
"file_type"
:
page
[
"file_type"
],
"page_number"
:
page
[
"page_number"
],
"chunk_method"
:
chunker
.
method
}
})
print
(
f
"Created
{
len
(
all_chunks
)
}
text chunks."
)
Generate Embeddings
#
Before setting up Chroma DB for vector storage, generate embeddings for your text chunks.
We are using
intfloat/multilingual-e5-large-instruct
model.
from
sentence_transformers
import
SentenceTransformer
# Initialize a SentenceTransformer model (choose one appropriate for your use case)
embed_model
=
SentenceTransformer
(
"intfloat/multilingual-e5-large-instruct"
)
# Gather all chunk texts for embedding generation
chunk_texts
=
[
chunk
[
"text"
]

### Match 5 | distance=1.2555

gle np.array for faster tensor creation.
spectograms
=
np
.
array
(
batch
[
"input_features"
])
spectograms
=
torch
.
tensor
(
spectograms
)
.
to
(
self
.
device
,
dtype
=
self
.
dtype
)
with
torch
.
no_grad
():
# Generate token IDs for the batched input features.
token_ids
=
self
.
model
.
generate
(
spectograms
)
return
{
"id"
:
batch
[
"id"
],
"token_ids"
:
token_ids
.
cpu
()
.
numpy
()}
# Transcribe audio to text tokens using Whisper.
# Use 2 workers using 1 GPU each.
ds
=
ds
.
map_batches
(
Transcriber
,
batch_size
=
2
,
batch_format
=
"numpy"
,
concurrency
=
2
,
num_gpus
=
1
)
Now decode the tokens into actual transcriptions. This step decouples from the previous step to prevent GPU blocks on CPU work and avoid idle time. This approach also allows independent scaling of the number of decoders from the number of Whisper replicas.
Separating the GPU work from CPU work eliminates GPU idle. The
concurrency=5
and
batch_size=32
parameters show how to use more CPU workers and bigger bat

### Match 6 | distance=1.2556

den_dim"
]
dropout_p
=
config
[
"dropout_p"
]
lr
=
config
[
"lr"
]
lr_factor
=
config
[
"lr_factor"
]
lr_patience
=
config
[
"lr_patience"
]
num_epochs
=
config
[
"num_epochs"
]
batch_size
=
config
[
"batch_size"
]
num_classes
=
config
[
"num_classes"
]
# Experiment tracking.
if
ray
.
train
.
get_context
()
.
get_world_rank
()
==
0
:
mlflow
.
set_tracking_uri
(
f
"file:
{
model_registry
}
"
)
mlflow
.
set_experiment
(
experiment_name
)
mlflow
.
start_run
()
mlflow
.
log_params
(
config
)
# Datasets.
train_ds
=
ray
.
train
.
get_dataset_shard
(
"train"
)
val_ds
=
ray
.
train
.
get_dataset_shard
(
"val"
)
# Model.
model
=
ClassificationModel
(
embedding_dim
=
embedding_dim
,
hidden_dim
=
hidden_dim
,
dropout_p
=
dropout_p
,
num_classes
=
num_classes
,
)
model
=
ray
.
train
.
torch
.
prepare_model
(
model
)
# Training components.
loss_fn
=
torch
.
nn
.
CrossEntropyLoss
()
optimizer
=
torch
.
optim
.
Adam
(
model
.
parameters
(),
lr
=
lr
)
scheduler
=
torch
.
optim
.
lr_scheduler
.
ReduceL

### Match 7 | distance=1.2597

peline
processed_ds
.
take_all
()
print
(
"Data ingestion completed successfully!"
)
Verifying and Searching the Data
#
Check Stored Embeddings
#
After processing, you can verify how many vectors have been stored in the Chroma DB:
import
chromadb
CHROMA_PATH
=
"/mnt/cluster_storage/vector_store"
CHROMA_COLLECTION_NAME
=
"anyscale_jobs_docs_embeddings"
# Initialize the Chroma client and retrieve (or create) your collection
chroma_client
=
chromadb
.
PersistentClient
(
path
=
CHROMA_PATH
)
collection
=
chroma_client
.
get_or_create_collection
(
name
=
CHROMA_COLLECTION_NAME
)
# Show how many vectors are stored in the collection.
vector_count
=
collection
.
count
()
print
(
"Total number of vectors in the collection:"
,
vector_count
)
You can also check the storage usage:
!
ls
-lh
/mnt/cluster_storage/vector_store
Performing a Vector Search
#
Now that the data is ingested, you can search for relevant document chunks. For example, to search for “how to submit anyscale jobs”:
from
pprint
im

### Match 8 | distance=1.2598

ation
for more information on using Ray Data with Anyscale and for more advanced use cases, see
Working with LLMs
.
On this page

### Match 9 | distance=1.2755

1
if
config
[
"features"
]
==
"MS"
else
0
# Slice for prediction length first.
outputs_pred_len
=
raw_pred
[:,
-
pred_len
:,
:]
batch_y_pred_len
=
batch_y
[:,
-
pred_len
:,
:]
# Then slice for features.
final_pred
=
outputs_pred_len
[:,
:,
f_dim_start_index
:]
final_target
=
batch_y_pred_len
[:,
:,
f_dim_start_index
:]
return
final_pred
,
final_target
# === Build Model ===
model
=
DLinear
(
config
)
.
float
()
# Convenience function to move the model to the correct device and set up
# parallel strategy.
model
=
train
.
torch
.
prepare_model
(
model
)
# === Get Data ===
train_ds
=
get_dataset_shard
(
"train"
)
# === Optimizer and Criterion ===
model_optim
=
optim
.
Adam
(
model
.
parameters
(),
lr
=
config
[
"learning_rate"
])
criterion
=
nn
.
MSELoss
()
# === AMP Scaler ===
scaler
=
None
if
config
[
"use_amp"
]:
scaler
=
torch
.
amp
.
GradScaler
(
"cuda"
)
# === Training Loop ===
for
epoch
in
range
(
config
[
"train_epochs"
]):
model
.
train
()
train_loss_epoch
=
[]
epoch_start_time
=

### Match 10 | distance=1.2783

- page_number
- source
- text (from documents)
- distance
- score
Parameters:
chroma_results (dict): The raw results from the Chroma DB query.
Returns:
list: A list of dictionaries with the desired keys.
"""
reformatted
=
[]
# Get the lists from the results. They are expected to be lists of lists.
metadatas
=
chroma_results
.
get
(
"metadatas"
,
[])
documents
=
chroma_results
.
get
(
"documents"
,
[])
distances
=
chroma_results
.
get
(
"distances"
,
[])
# Loop over each group (each inner list represents one set of matches)
chunk_index
=
1
for
meta_group
,
doc_group
,
distance_group
in
zip
(
metadatas
,
documents
,
distances
):
# Iterate over each item in the inner lists
for
meta
,
text
,
distance
in
zip
(
meta_group
,
doc_group
,
distance_group
):
item
=
{
"chunk_index"
:
chunk_index
,
"chunk_id"
:
meta
.
get
(
"chunk_id"
),
"doc_id"
:
meta
.
get
(
"doc_id"
),
"page_number"
:
meta
.
get
(
"page_number"
),
"source"
:
meta
.
get
(
"source"
),
"text"
:
text
,
"distance"
:
distance
,
"sco

### Match 11 | distance=1.2879

convert to pandas.
train_ds
=
train_ds
.
materialize
()
.
to_pandas
()
val_ds
=
val_ds
.
materialize
()
.
to_pandas
()
# Separate the labels from the features.
train_X
,
train_y
=
train_ds
.
drop
(
"target"
,
axis
=
1
),
train_ds
[
"target"
]
eval_X
,
eval_y
=
val_ds
.
drop
(
"target"
,
axis
=
1
),
val_ds
[
"target"
]
# Convert the data into DMatrix format for XGBoost.
dtrain
=
xgboost
.
DMatrix
(
train_X
,
label
=
train_y
)
deval
=
xgboost
.
DMatrix
(
eval_X
,
label
=
eval_y
)
# Do distributed data-parallel training.
# Ray Train sets up the necessary coordinator processes and
# environment variables for workers to communicate with each other.
_booster
=
xgboost
.
train
(
config
[
"xgboost_params"
],
dtrain
=
dtrain
,
evals
=
[(
dtrain
,
"train"
),
(
deval
,
"validation"
)],
num_boost_round
=
10
,
# Handles metric logging and checkpointing.
callbacks
=
[
RayTrainReportCallback
()],
)
# Parameters for the XGBoost model.
model_config
=
{
"xgboost_params"
:
{
"objective"
:
"binary:logist

### Match 12 | distance=1.2885

ct
:
"""
Process a batch of documents by adding them to the Chroma collection.
"""
# Prepare metadata for each entry in the batch
metadatas
=
[]
for
i
in
range
(
len
(
batch
[
"chunk_id"
])):
metadata
=
{
"source"
:
batch
[
"source"
][
i
],
"doc_id"
:
batch
[
"doc_id"
][
i
],
"page_number"
:
int
(
batch
[
"page_number"
][
i
]),
"chunk_id"
:
batch
[
"chunk_id"
][
i
]
}
metadatas
.
append
(
metadata
)
embeddings
=
batch
[
"embeddings"
]
.
tolist
()
documents
=
[
text
for
text
in
batch
[
"text"
]]
ids
=
[
id
for
id
in
batch
[
"chunk_id"
]]
# Add the embeddings, documents, ids, and metadata to the collection
self
.
collection
.
add
(
embeddings
=
embeddings
,
documents
=
documents
,
ids
=
ids
,
metadatas
=
metadatas
)
return
{}
Setting Up the Text Processing Pipeline
#
Finally, define constants for your data sources and vector store configuration. Then, build the Ray pipeline that:
Chunks the text.
Generates embeddings.
Writes the results to Chroma DB.
# Constants for your data sources and

## In-Memory Ray Registry Hits

Status: Connected. Searched 27 in-memory tables.

No Ray registry hits.
