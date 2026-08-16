# %% [markdown]
# # 🧠 CHATBOT MEMORY INDEXER (RAY + OLLAMA + PYDANTIC)
# Synthesizes DuckDB data into natural language sentences, validates them via Pydantic,
# and hits your local Ollama models across the Ray Swarm to generate LanceDB Text Embeddings.

import duckdb
import ray
import time
import requests
import pyarrow as pa
import lancedb
from pydantic import BaseModel, Field, field_validator

# -------------------------------------------------------------
# 1. PYDANTIC FIREWALL (SEMANTIC VALIDATION)
# -------------------------------------------------------------
class SemanticSentence(BaseModel):
    filepath: str
    synthesized_text: str = Field(min_length=10)
    
    @field_validator('synthesized_text')
    @classmethod
    def prevent_garbage_text(cls, v):
        if v.strip() == "":
            raise ValueError("Empty semantic string generated.")
        if "Unknown" in v and "0 BPM" in v:
            # We don't want the chatbot learning totally blank metadata
            raise ValueError("Too much missing metadata to be useful for Chat.")
        return v

# -------------------------------------------------------------
# 2. RAY WORKER FOR LOCAL OLLAMA EMBEDDINGS
# -------------------------------------------------------------

@ray.remote(num_cpus=1)
class OllamaEmbeddingWorker:
    def __init__(self, ollama_url="http://localhost:11434"):
        self.ollama_url = ollama_url
        # If you have 2 Ollama instances running, you could pass different ports here!
        
    def embed_text(self, filepath, text_payload):
        try:
            # 1. Pydantic Verification
            safe_data = SemanticSentence(filepath=filepath, synthesized_text=text_payload)
            
            # 2. Hit Local Ollama Embedding API
            # Make sure you have run: `ollama pull snowflake-arctic-embed` or `nomic-embed-text`
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": "snowflake-arctic-embed", # Or change to nomic-embed-text
                    "prompt": safe_data.synthesized_text
                }
            )
            response.raise_for_status()
            vector = response.json().get('embedding')
            
            return {
                "filepath": safe_data.filepath,
                "text_memory": safe_data.synthesized_text,
                "vector": vector
            }
            
        except ValueError as ve:
            print(f"🛡️ Pydantic Blocked: {ve}")
            return None
        except Exception as e:
            print(f"❌ Ollama Error on {filepath}: {e}")
            return None

# -------------------------------------------------------------
# 3. BUILD THE LANCEDB MEMORY
# -------------------------------------------------------------
DB_PATH = r"C:\WEB CASE STUDY\web_intel_sonicdb.duckdb"
LANCE_DB_PATH = r"C:\WEB CASE STUDY\lancedb_memory"

print("🔍 Synthesizing Natural Language Sentences from DuckDB...")
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
    LIMIT 500 -- Batch size for Chatbot Indexing
""").fetchdf()
con.close()

if omni_df.empty:
    print("No Omni-Knowledge records to index.")
else:
    print(f"📡 Dispatching {len(omni_df)} targets to Local Ollama Swarm...")
    t0 = time.time()
    
    workers = [OllamaEmbeddingWorker.remote() for _ in range(4)]
    futures = []
    
    for i, row in omni_df.iterrows():
        # Synthesize the text block for the LLM
        text_sentence = f"An audio track produced by {row['vendors']} tagged as {row['categories']} with a BPM of {row['bpm']} in the key of {row['key']}. Root tag: {row['root_tag']}."
        
        worker = workers[i % len(workers)]
        futures.append(worker.embed_text.remote(row['filepath'], text_sentence))
        
    results = ray.get(futures)
    valid_results = [r for r in results if r is not None]
    
    if valid_results:
        # Connect to LanceDB and save the Text Vectors
        db = lancedb.connect(LANCE_DB_PATH)
        
        # LanceDB automatically handles the PyArrow schema based on the dict keys
        if "chatbot_memory" in db.table_names():
            table = db.open_table("chatbot_memory")
            table.add(valid_results)
        else:
            table = db.create_table("chatbot_memory", data=valid_results)
            
        print(f"🔥 Successfully generated and injected {len(valid_results)} semantic text vectors into LanceDB in {time.time()-t0:.2f}s!")
