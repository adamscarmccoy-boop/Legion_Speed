# Single-cell pipeline: vector-first full rebuild
# Requirements: ray, requests, tqdm, pydantic, lancedb, duckdb, onnxruntime, pyarrow, pandas
# Assumptions: LM Studio running at http://127.0.0.1:1234, model names as used below,
#             Ray cluster available, LanceDB path and DuckDB path writable.

import os
import time
import json
import math
import ray
import requests
import duckdb
import lancedb
import numpy as np
import onnxruntime as ort

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

import pyarrow as pa
import pyarrow.parquet as pq
from tqdm import tqdm
from pydantic import BaseModel, ValidationError
from lancedb.pydantic import LanceModel, Vector

# ---------------------------
# CONFIG
# ---------------------------
LMSTUDIO_EMBED_URL = "http://127.0.0.1:1234/v1/embeddings"
LMSTUDIO_MODEL = "text-embedding-snowflake-arctic-embed-l-v2.0"  # 1024-D
ONNX_PATH = r"C:\WEB CASE STUDY\mastered_output\mega_sovereign_brain.onnx"
DUCKDB_PATH = r"C:\WEB CASE STUDY\web_intel_sonicdb.duckdb"
LANCE_DB_PATH = r"C:\WEB CASE STUDY\lancedb_memory"
PARQUET_BACKUP = r"C:\WEB CASE STUDY\omni_worker_states_backup.parquet"
BATCH_SIZE = 256                # embedding batch size
RAY_WORKERS = 6                 # parallel embedding workers
LANCE_TABLE_NAME = "omni_brain"  # final table name

# ---------------------------
# SCHEMAS
# ---------------------------
class RowModel(BaseModel):
    filepath: str
    vendors: str | None = None
    categories: str | None = None
    bpm: float | None = None
    key: str | None = None
    root_tag: str | None = None
    metadata: dict | None = {}

class OmniBrainRecord(LanceModel):
    filepath: str
    semantic_text: str
    audio_vector: Vector(13)
    text_vector: Vector(1024)

# ---------------------------
# HELPERS: LM Studio batch embed (HTTP)
# ---------------------------
def lmstudio_batch_embed(texts, model=LMSTUDIO_MODEL, url=LMSTUDIO_EMBED_URL, timeout=60):
    """
    Send a batch of texts to LM Studio embeddings endpoint.
    Returns list of embeddings (list of floats) in same order.
    """
    payload = {"input": texts, "model": model}
    r = requests.post(url, json=payload, timeout=timeout)
    r.raise_for_status()
    resp = r.json()
    # Expecting resp["data"] list with embeddings
    return [item["embedding"] for item in resp["data"]]

# ---------------------------
# RAY REMOTE WORKER: ONNX + LM Studio embed
# ---------------------------
if not ray.is_initialized():
    ray.init(ignore_reinit_error=True)

@ray.remote(num_cpus=1)
class EmbedWorker:
    def __init__(self, onnx_path=ONNX_PATH):
        # ONNX session for audio vector extraction (13-D)
        self.ort = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
        # LM Studio client will be called via HTTP in batches from driver to avoid many small HTTP calls

    def infer_audio(self, audio_dummy_seed=None):
        # Replace with real audio feature extraction if available.
        # Here we call ONNX with a deterministic dummy input for pipeline testing.
        inp = np.random.RandomState(audio_dummy_seed or int(time.time() * 1000) % 2**31).randn(1, 1069).astype(np.float32)
        out = self.ort.run(None, {"omni_genre_bpm_input": inp})[0]
        return out[0].tolist()

# ---------------------------
# DRIVER: load targets from DuckDB
# ---------------------------
    text_vectors.extend(emb_batch)

# Sanity check lengths
assert len(audio_vectors) == len(rows)
assert len(text_vectors) == len(rows)

# ---------------------------
# BUILD fused records and save to LanceDB + Parquet backup
# ---------------------------
records = []
for i, r in enumerate(rows):
    rec = {
        "filepath": r["filepath"],
        "semantic_text": r["semantic_text"],
        "audio_vector": audio_vectors[i],
        "text_vector": text_vectors[i]
    }
    records.append(rec)

# Save to LanceDB (create table)
print("Saving to LanceDB...")
db.create_table(LANCE_TABLE_NAME, schema=OmniBrainRecord, data=records)

# Save Parquet backup (append-safe)
print("Writing Parquet backup...")
pa_table = pa.Table.from_pylist(records, schema=OmniBrainRecord.to_arrow_schema())
if os.path.exists(PARQUET_BACKUP):
    existing = pq.read_table(PARQUET_BACKUP)
    combined = pa.concat_tables([existing, pa_table])
    pq.write_table(combined, PARQUET_BACKUP)
else:
    pq.write_table(pa_table, PARQUET_BACKUP)

# ---------------------------
# UPDATE DuckDB with new vector references (optional pointer columns)
# ---------------------------
con = duckdb.connect(DUCKDB_PATH)
# Create a small helper table with filepath -> text_vector (as JSON) for quick joins
tmp_parquet = r"C:\WEB CASE STUDY\temp_vectors_for_duckdb.parquet"
# Convert minimal mapping to parquet
map_rows = [{"filepath": r["filepath"], "text_vector": json.dumps(r["text_vector"])} for r in records]
pq.write_table(pa.Table.from_pylist(map_rows), tmp_parquet)
# Upsert into duckdb (create or replace a table)
con.execute(f"CREATE OR REPLACE TABLE omni_vectors AS SELECT * FROM read_parquet('{tmp_parquet}')")
con.close()
os.remove(tmp_parquet)

# ---------------------------
# TRIGGER: rebuild fused DNA index and (optionally) retrain GenomeBrain
# ---------------------------
# This is a placeholder for retraining orchestration. In production you would:
#  - export training dataset (fused DNA + labels) to training storage
#  - kick off a training job (Ray Train / PyTorch / HuggingFace)
# Here we write a small manifest for the training job to pick up.
manifest_path = r"C:\WEB CASE STUDY\genomebrain_retrain_manifest.json"
manifest = {
    "lance_table": LANCE_TABLE_NAME,
    "lance_path": LANCE_DB_PATH,
    "duckdb": DUCKDB_PATH,
    "parquet_backup": PARQUET_BACKUP,
    "num_records": len(records),
    "fused_dims": {"audio": 13, "text": 1024}
}
with open(manifest_path, "w", encoding="utf-8") as mf:
    json.dump(manifest, mf, indent=2)

# ---------------------------
# BENCHMARK SUMMARY
# ---------------------------
end_total = time.time()
print("\n================= FULL RUN SUMMARY =================")
print(f"Targets processed:        {len(rows)}")
print(f"Audio vectors (ONNX):     {len(audio_vectors)}")
print(f"Text vectors (GGUF):      {len(text_vectors)}")
print(f"LanceDB table created:    {LANCE_TABLE_NAME}")
print(f"Parquet backup path:      {PARQUET_BACKUP}")
print(f"GenomeBrain manifest:     {manifest_path}")
print(f"Total elapsed (s):        {(end_total - start_total):.2f}")
print("===================================================")

# ---------------------------
# CLEANUP Ray actors
# ---------------------------
for w in workers:
    try:
        ray.kill(w)
    except Exception:
        pass

# End of single-cell pipeline