import os
import sys
import json
import logging
import requests
import pyarrow as pa
import pyarrow.parquet as pq
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from jinja2 import Template
from typing import List, Optional

# Force UTF-8 to prevent windows unicode crashes
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# =====================================================================
# CONFIGURATION
# =====================================================================
TAKEOUT_DIR = r"C:\Users\adams\Downloads\takeout-20260613T032152Z-3-001\Takeout\NotebookLM\LETS MAKE SOME MONEY HONEY\Sources"
PARQUET_OUTPUT = r"C:\WEB CASE STUDY\takeout_leads.parquet"
LM_STUDIO_URL = "http://localhost:1234/v1"
NEMOTRON_MODEL = "nvidia/nemotron-3-nano-4b"
EMBEDDING_MODEL = "text-embedding-snowflake-arctic-embed-l-v2.0"

# =====================================================================
# PYDANTIC MUZZLE
# =====================================================================
class JobProspectReport(BaseModel):
    title: str = Field(..., description="Title of the job, project or resource")
    requires_audio_or_data: bool = Field(..., description="True if related to DSP, Audio Programming, ML, or Data pipelines")
    budget_signal: str = Field(..., description="Salary or budget mentioned, otherwise 'Unknown'")
    fit_score: int = Field(..., description="Score from 0 to 100 on how well this matches our DSP/Audio agency")
    reasoning: str = Field(..., description="Brief reasoning for the fit score")

JINJA_PROSPECT_EXAMINER = """
System: You are an expert Audio/DSP Agency Analyst.
Read the following scraped resource/job post from my private knowledge base.
Output ONLY a JSON object matching the requested schema.

Resource Content:
{{ job_text }}

Rules:
1. Identify if this is explicitly looking for audio processing, DSP, VST development, or high-speed data.
2. Evaluate the fit for our ultra-fast Audio/Data processing agency.
"""

# =====================================================================
# PIPELINE FUNCTIONS
# =====================================================================

def chunk_text_by_paragraphs(text: str, max_chars=1000, overlap=200) -> List[str]:
    """Chunks text by paragraphs (~1000 chars) with overlap to adhere to AGENTS.md rule."""
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if len(current_chunk) + len(p) < max_chars:
            current_chunk += p + " "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # Start new chunk with overlap
            current_chunk = current_chunk[-overlap:] + " " + p + " " if len(current_chunk) > overlap else p + " "
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

def extract_html_text(filepath: str) -> str:
    """Extracts raw text from an HTML file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, "html.parser")
            return soup.get_text(separator='\n', strip=True)
    except Exception as e:
        logging.error(f"Failed to read {filepath}: {e}")
        return ""

def evaluate_with_nemotron(text: str) -> Optional[JobProspectReport]:
    """Evaluates text with Nemotron-3-Nano to confirm if it's a fit."""
    jinja_compiler = Template(JINJA_PROSPECT_EXAMINER)
    # Truncate text for the LLM evaluation to avoid context window blowouts
    truncated_text = text[:4000] 
    prompt = jinja_compiler.render(job_text=truncated_text)
    
    schema_str = json.dumps(JobProspectReport.model_json_schema())
    prompt += f"\n\nJSON Schema:\n{schema_str}"
    
    try:
        payload = {
            "model": NEMOTRON_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0
        }
        res = requests.post(f"{LM_STUDIO_URL}/chat/completions", json=payload, timeout=45)
        res.raise_for_status()
        raw_ai_string = res.json()["choices"][0]["message"]["content"]
        
        return JobProspectReport.model_validate_json(raw_ai_string)
    except Exception as e:
        logging.error(f"Nemotron Parsing Error: {e}")
        return None

def generate_snowflake_embedding(text: str) -> List[float]:
    """Generates embedding using Snowflake Arctic only for confirmed targets."""
    try:
        payload = {"input": text, "model": EMBEDDING_MODEL}
        res = requests.post(f"{LM_STUDIO_URL}/embeddings", json=payload, timeout=10)
        res.raise_for_status()
        return res.json()["data"][0]["embedding"]
    except Exception as e:
        logging.error(f"Snowflake Embedding Failed: {e}")
        return [0.0] * 1024

# =====================================================================
# MAIN EXECUTION
# =====================================================================
def main():
    print("=" * 60)
    print(" 🚀 Legion Pipeline: Dual LLM+RAG Ingestion (Nemotron -> Snowflake)")
    print("=" * 60)
    
    if not os.path.exists(TAKEOUT_DIR):
        print(f"FATAL: Takeout directory not found: {TAKEOUT_DIR}")
        sys.exit(1)
        
    html_files = [os.path.join(TAKEOUT_DIR, f) for f in os.listdir(TAKEOUT_DIR) if f.endswith(".html")]
    print(f"Found {len(html_files)} HTML files in NotebookLM Takeout.\n")
    
    validated_records = []
    
    for count, filepath in enumerate(html_files[:10]): # Limit to first 10 for testing
        filename = os.path.basename(filepath)
        print(f"[{count+1}/10] Processing: {filename}")
        
        # 1. Extract
        raw_text = extract_html_text(filepath)
        if not raw_text:
            continue
            
        # 2. Evaluate (Nemotron)
        print("  -> Asking Nemotron to evaluate...")
        insight = evaluate_with_nemotron(raw_text)
        
        if not insight:
            print("  -> [SKIP] Parsing failed.")
            continue
            
        print(f"  -> Nemotron Fit Score: {insight.fit_score} | DSP/Audio: {insight.requires_audio_or_data}")
        print(f"  -> Title: {insight.title}")
        print(f"  -> Reasoning: {insight.reasoning}")
        
        # 3. Vectorize ONLY IF Fit
        if insight.fit_score > 50 or insight.requires_audio_or_data:
            print("  -> 🎯 HIGH VALUE TARGET IDENTIFIED. Chunking and Embedding via Snowflake...")
            chunks = chunk_text_by_paragraphs(raw_text)
            print(f"  -> Split into {len(chunks)} chunks based on AGENTS.md rule.")
            
            for chunk_idx, chunk in enumerate(chunks):
                vec = generate_snowflake_embedding(chunk)
                validated_records.append({
                    "source_file": filename,
                    "title": insight.title,
                    "fit_score": insight.fit_score,
                    "budget": insight.budget_signal,
                    "reasoning": insight.reasoning,
                    "chunk_id": chunk_idx,
                    "text_chunk": chunk,
                    "embedding": vec
                })
        else:
            print("  -> [SKIP] Low fit score. Bypassing embedding to save resources.")
            
    # 4. Save to Parquet
    if validated_records:
        print(f"\n💾 Saving {len(validated_records)} high-value embedded chunks to {PARQUET_OUTPUT}")
        arrow_table = pa.Table.from_pylist(validated_records)
        pq.write_table(arrow_table, PARQUET_OUTPUT)
        print("✅ Pipeline Complete.")
    else:
        print("\nNo high-value records found to embed.")

if __name__ == "__main__":
    try:
        import bs4
    except ImportError:
        print("Please run: pip install beautifulsoup4 lxml")
        sys.exit(1)
    main()
