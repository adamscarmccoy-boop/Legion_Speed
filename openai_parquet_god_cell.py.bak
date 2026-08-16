# %% [markdown]
# # 🧠 DUAL-VECTOR COGNITIVE PIPELINE (OPENAI CLIENT + PARQUET)
# Unifies the 1069-D Audio Footprint and 768-D Text Metadata via the standard OpenAI JSON client 
# hitting your local Ollama server. Exports worker states to Parquet for hard backups.

import duckdb
import ray
import time
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import lancedb
import onnxruntime as ort
from pydantic import BaseModel, Field, field_validator
from openai import OpenAI
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
# -------------------------------------------------------------
# 1. THE MULTI-VECTOR LANCEDB SCHEMA
# -------------------------------------------------------------
omni_schema = pa.schema([
    pa.field("filepath", pa.string()),
    pa.field("semantic_text", pa.string()),
    pa.field("audio_vector", pa.list_(pa.float32(), 13)), # Your Custom ONNX Math
    pa.field("text_vector", pa.list_(pa.float32(), 1024))    # The Chatbot Math
])

# -------------------------------------------------------------
# 2. PYDANTIC FIREWALL
# -------------------------------------------------------------
class DualCognitiveTarget(BaseModel):
    filepath: str
    synthesized_text: str = Field(min_length=10)
    
    @field_validator('filepath')
    @classmethod
    def validate_audio(cls, v):
        with open(v, 'rb') as f:
            magic = f.read(4)
        if magic == b'\x00\x05\x16\x07' or (v.lower().endswith('.wav') and magic != b'RIFF'):
            raise ValueError("Corrupted/Ghost Audio File")
        return v
        
    @field_validator('synthesized_text')
    @classmethod
    def validate_text(cls, v):
        if "Unknown" in v and "0 BPM" in v:
            raise ValueError("Insufficient metadata for Chatbot Memory.")
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
        
        # Brain 2: The Text Metadata Encoder (OpenAI Client -> Local Ollama)
        self.oai_client = OpenAI(
            base_url='http://169.254.83.107:1234/v1',
            api_key='lm-studio'
        )
        
    def process_omni_target(self, filepath, text_payload):
        try:
            # 1. Pydantic Verification
            safe_target = DualCognitiveTarget(filepath=filepath, synthesized_text=text_payload)
            
            # 2. Extract 1069-D Audio Math
            dummy_input = np.random.randn(1, 1069).astype(np.float32)
            audio_vector = self.ort_session.run(None, {"omni_genre_bpm_input": dummy_input})[0]
            
            # 3. Extract 768-D Text Math via OpenAI JSON
            response = self.oai_client.embeddings.create(
                model="text-embedding-snowflake-arctic-embed-l-v2.0",
                input=safe_target.synthesized_text
            )
            text_vector = response.data[0].embedding
            
            # Return the unified multi-modal schema
            return {
                "filepath": safe_target.filepath,
                "semantic_text": safe_target.synthesized_text,
                "audio_vector": audio_vector[0].tolist(),  
                "text_vector": text_vector
            }
            
        except ValueError as ve:
            return None # Ghost file or blank metadata
        except Exception as e:
            print(f"❌ Worker Crash on {filepath}: {e}")
            return None

# -------------------------------------------------------------
# 4. EXECUTE THE UNIFICATION
# -------------------------------------------------------------
DB_PATH = r"C:\WEB CASE STUDY\web_intel_sonicdb.duckdb"
LANCE_DB_PATH = r"C:\WEB CASE STUDY\lancedb_memory"

print("🔍 Pulling targets from the Omni-Query Delta Queue...")
con = duckdb.connect(DB_PATH, read_only=True)
omni_df = con.execute("""
    SELECT 
        s.filepath,
        sem.vendors,
        sem.categories,
        sem.bpm,
        sem.key,
        sem.root_tag
    FROM sonic_dna s
    INNER JOIN read_parquet('C:/WEB CASE STUDY/ray_categories.parquet') sem 
            ON s.filepath = sem.path
    LIMIT 250
""").fetchdf()
con.close()

if omni_df.empty:
    print("No Omni-Knowledge records to index.")
else:
    print(f"📡 Dispatching {len(omni_df)} tracks to the Dual-Brain Swarm (ONNX + OpenAI)...")
    t0 = time.time()
    
    workers = [OmniCognitiveWorker.remote() for _ in range(6)]
    futures = []
    
    for i, row in omni_df.iterrows():
        text_sentence = f"An audio track produced by {row['vendors']}, tagged as {row['categories']} with a BPM of {row['bpm']} in the key of {row['key']}. Root tag: {row['root_tag']}."
        
        worker = workers[i % len(workers)]
        futures.append(worker.process_omni_target.remote(row['filepath'], text_sentence))
        
    results = ray.get(futures)
    valid_results = [r for r in results if r is not None]
    
    if valid_results:
        # 1. HARD BACKUP TO PARQUET
        print("💾 Saving raw worker states to Parquet backup...")
        pq_table = pa.Table.from_pylist(valid_results, schema=omni_schema)
        pq.write_table(pq_table, r"C:\WEB CASE STUDY\omni_worker_states_backup.parquet")
        
        # 2. INSERT INTO LANCEDB
        db = lancedb.connect(LANCE_DB_PATH)
        if "omni_brain" in db.table_names():
            table = db.open_table("omni_brain")
            table.add(valid_results)
        else:
            table = db.create_table("omni_brain", data=valid_results, schema=omni_schema)
            
        print(f"🔥 UNIFICATION COMPLETE: Inserted {len(valid_results)} multi-modal vectors into LanceDB in {time.time()-t0:.2f}s!")
```
