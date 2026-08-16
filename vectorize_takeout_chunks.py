import sys
import os
import logging
import requests
import pyarrow as pa
import pyarrow.parquet as pq
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

RAW_PARQUET = r"C:\WEB CASE STUDY\takeout_raw.parquet"
VECTORIZED_PARQUET = r"C:\WEB CASE STUDY\takeout_vectorized.parquet"
LM_STUDIO_URL = "http://127.0.0.1:1234/v1/embeddings"
EMBEDDING_MODEL = "text-embedding-snowflake-arctic-embed-l-v2.0"

def chunk_text_by_paragraphs(text: str, max_chars=1000, overlap=200, hard_cap=8190) -> list:
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    for p in paragraphs:
        p = p.strip()
        if not p: continue
        
        # If a single paragraph is massive (HTML blob), slice it aggressively
        while len(p) > hard_cap:
            chunks.append(p[:hard_cap])
            p = p[hard_cap:]
            
        if len(current_chunk) + len(p) < max_chars:
            current_chunk += p + " "
        else:
            if current_chunk: 
                # Enforce hard cap before appending just in case
                if len(current_chunk) > hard_cap:
                    current_chunk = current_chunk[:hard_cap]
                chunks.append(current_chunk.strip())
            current_chunk = current_chunk[-overlap:] + " " + p + " " if len(current_chunk) > overlap else p + " "
    if current_chunk:
        if len(current_chunk) > hard_cap:
            current_chunk = current_chunk[:hard_cap]
        chunks.append(current_chunk.strip())
    return chunks

def generate_snowflake_embedding(text: str):
    try:
        payload = {"input": text, "model": EMBEDDING_MODEL}
        res = requests.post(LM_STUDIO_URL, json=payload, timeout=10)
        res.raise_for_status()
        return res.json()["data"][0]["embedding"]
    except Exception as e:
        logging.error(f"Snowflake Embedding Failed: {e}")
        return [0.0] * 1024

def main():
    print("=" * 60)
    print(" 🧬 Legion Pipeline: Phase 2 (Background Vectorization Resume)")
    print("=" * 60)
    
    try:
        raw_table = pq.read_table(RAW_PARQUET)
    except FileNotFoundError:
        print("Raw Parquet not found. Run Phase 1 first.")
        sys.exit(1)
        
    records = raw_table.to_pylist()
    print(f"Loaded {len(records)} raw documents from PyArrow.")
    
    vectorized_chunks = []
    processed_files = set()
    
    if os.path.exists(VECTORIZED_PARQUET):
        try:
            vec_table = pq.read_table(VECTORIZED_PARQUET)
            vectorized_chunks = vec_table.to_pylist()
            processed_files = {doc["filename"] for doc in vectorized_chunks}
            print(f"Resuming: Loaded {len(vectorized_chunks)} existing chunks from {len(processed_files)} files.")
        except Exception as e:
            print(f"Could not load existing vectorized parquet: {e}")
    
    # Process only files mentioning freelance/contractor or audio jobs for speed right now
    target_keywords = ["contractor", "freelance", "vst", "audio", "dsp", "music", "ai"]
    
    for doc in records:
        text = doc["raw_text"]
        filename = doc["filename"]
        
        if filename in processed_files:
            continue
            
        # Fast keyword filter before heavy chunking
        text_lower = text.lower()
        if not any(k in text_lower for k in target_keywords):
            continue
            
        print(f"Chunking & Vectorizing: {filename}")
        chunks = chunk_text_by_paragraphs(text)
        
        for idx, chunk in enumerate(chunks):
            vec = generate_snowflake_embedding(chunk)
            vectorized_chunks.append({
                "filename": filename,
                "chunk_id": idx,
                "text_chunk": chunk,
                "embedding": vec
            })
            
        # Optional: Save checkpoint after every doc
        pq.write_table(pa.Table.from_pylist(vectorized_chunks), VECTORIZED_PARQUET)
        processed_files.add(filename)
            
    print(f"\n✅ Finished! Vectorized {len(vectorized_chunks)} total chunks.")
    print(f"💾 Final vectors saved to {VECTORIZED_PARQUET}")

if __name__ == "__main__":
    main()
