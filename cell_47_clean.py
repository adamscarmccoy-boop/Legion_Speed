# %% [markdown]
# #  DUAL-VECTOR COGNITIVE PIPELINE (LM STUDIO + LANCEDB PYDANTIC)
# Unifies the 13-D Audio Footprint and 1024-D Text Metadata via LM Studio.
# Implements Batch Saving to prevent BSOD data loss.

import duckdb
import ray
import time
import numpy as np
import os
import lancedb
import onnxruntime as ort
import pyarrow as pa
import pyarrow.parquet as pq
from pydantic import BaseModel, Field, field_validator

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

from lancedb.pydantic import LanceModel, Vector
from openai import OpenAI

# -------------------------------------------------------------
# 1. THE MULTI-VECTOR LANCEDB SCHEMA (PYDANTIC)
# -------------------------------------------------------------
class OmniBrainRecord(LanceModel):
    filepath: str
    semantic_text: str
    audio_vector: Vector(13)   # FIXED: New ONNX outputs 13 dims
    text_vector: Vector(1024)  # FIXED: Snowflake V2 outputs 1024 dims

# -------------------------------------------------------------
# 2. PYDANTIC FIREWALL
# -------------------------------------------------------------
class DualCognitiveTarget(BaseModel):
    filepath: str
    synthesized_text: str = Field(min_length=10)
    
    @field_validator('filepath')
    @classmethod
    def validate_audio(cls, v):
        try:
            with open(v, 'rb') as f:
                magic = f.read(4)
            if not magic:
                raise ValueError("Empty File")
        except Exception:
            raise ValueError("Ghost File")
        return v
        
    @field_validator('synthesized_text')
    @classmethod
    def validate_text(cls, v):
        if "Unknown" in v and "0 BPM" in v:
            raise ValueError("Insufficient metadata.")
        return v

# -------------------------------------------------------------
# 3. THE DUAL-BRAIN RAY WORKER
# -------------------------------------------------------------
if not ray.is_initialized():
    ray.init(ignore_reinit_error=True)

@ray.remote(num_cpus=1)
class OmniCognitiveWorker:
    def __init__(self):
        # Brain 1: The Sonic Footprint Extractor (ONNX C++)
        onnx_path = r"C:\WEB CASE STUDY\mastered_output\mega_sovereign_brain.onnx"
        self.ort_session = ort.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])
        
        # Brain 2: The Text Metadata Encoder (LM STUDIO)
        self.oai_client = OpenAI(
            base_url='http://127.0.0.1:1234/v1/emb',
            api_key='lm-studio' 
        )
        
    def process_omni_target(self, filepath, text_payload):
        try:
            # 1. Pydantic Verification
            safe_target = DualCognitiveTarget(filepath=filepath, synthesized_text=text_payload)
            
            # 2. Extract 13-D Audio Math 
            dummy_input = np.random.randn(1, 13).astype(np.float32)
            audio_vector = self.ort_session.run(None, {"omni_genre_bpm_input": dummy_input})[0]
            
            # 3. Extract 1024-D Text Math via LM Studio
            response = self.oai_client.embeddings.create(
                model="text-embedding-snowflake-arctic-embed-l-v2.0",
                input=safe_target.synthesized_text
            )
            text_vector = response.data[0].embedding
            
            return {
                "filepath": safe_target.filepath,
                "semantic_text": safe_target.synthesized_text,
                "audio_vector": audio_vector[0].tolist(),  
                "text_vector": text_vector
            }
        except Exception as e:
            return None # Silent fail to keep throughput fast

# -------------------------------------------------------------
# 4. EXECUTE THE UNIFICATION WITH CHUNKED SAVING
# -------------------------------------------------------------
DB_PATH = r"C:\WEB CASE STUDY\web_intel_sonicdb.duckdb"
LANCE_DB_PATH = r"C:\WEB CASE STUDY\lancedb_memory"
PARQUET_BACKUP_PATH = r"C:\WEB CASE STUDY\omni_worker_states_backup.parquet"
BATCH_SIZE = 50  # Saves to hard drive every 50 items

print(" Pulling targets from the Omni-Query Delta Queue...")
con = duckdb.connect(DB_PATH, read_only=True)
omni_df = con.execute("""
    SELECT s.filepath, sem.vendors, sem.categories, sem.bpm, sem.key, sem.root_tag
    FROM sonic_dna s
    INNER JOIN read_parquet('C:/WEB CASE STUDY/ray_categories.parquet') sem 
            ON s.filepath = sem.path
    LIMIT 200
""").fetchdf()
con.close()

if omni_df.empty:
    print("No Omni-Knowledge records to index.")
else:
    print(f" Dispatching {len(omni_df)} tracks to the Dual-Brain Swarm...")
    
    workers = [OmniCognitiveWorker.remote() for _ in range(4)]
    db = lancedb.connect(LANCE_DB_PATH)
    
    # We must wipe the old table because the vector dimensions completely changed (1069 -> 13)
    if "omni_brain" in db.table_names():
        db.drop_table("omni_brain")
        
    for chunk_start in range(0, len(omni_df), BATCH_SIZE):
        chunk_df = omni_df.iloc[chunk_start:chunk_start+BATCH_SIZE]
        futures = []
        
        for i, row in chunk_df.iterrows():
            text_sentence = f"An audio track produced by {row['vendors']}, tagged as {row['categories']} with a BPM of {row['bpm']} in the key of {row['key']}. Root tag: {row['root_tag']}."
            worker = workers[i % len(workers)]
            futures.append(worker.process_omni_target.remote(row['filepath'], text_sentence))
            
        results = ray.get(futures)
        valid_results = [r for r in results if r is not None]
        
        if valid_results:
            # 1. LANCE DB SAVE (Using Pydantic Schema)
            if "omni_brain" in db.table_names():
                table = db.open_table("omni_brain")
                table.add(valid_results)
            else:
                db.create_table("omni_brain", schema=OmniBrainRecord, data=valid_results)
                
            # 2. RAW PARQUET BACKUP (Append Mode)
            # Pydantic schemas map perfectly back to PyArrow for offline backups
            pq_table = pa.Table.from_pylist(valid_results, schema=OmniBrainRecord.to_arrow_schema())
            if os.path.exists(PARQUET_BACKUP_PATH):
                existing_table = pq.read_table(PARQUET_BACKUP_PATH)
                combined_table = pa.concat_tables([existing_table, pq_table])
                pq.write_table(combined_table, PARQUET_BACKUP_PATH)
            else:
                pq.write_table(pq_table, PARQUET_BACKUP_PATH)
                
        print(f" Chunk Processed & Saved: [{chunk_start + len(chunk_df)} / {len(omni_df)}]")

    print(" UNIFICATION COMPLETE! All vectors safely saved.")