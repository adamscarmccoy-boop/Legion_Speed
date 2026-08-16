import duckdb
import ollama
import json
import logging
import requests
import pyarrow as pa
import pyarrow.parquet as pq
from pydantic import BaseModel, Field
from jinja2 import Template
from typing import List, Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# =====================================================================
# CONFIGURATION
# =====================================================================
OLLAMA_MODEL = "phi3"
LM_STUDIO_EMBEDDING_URL = "http://localhost:1234/v1/embeddings"
EMBEDDING_MODEL = "text-embedding-snowflake-arctic-embed-l-v2.0"
PARQUET_OUTPUT = r"C:\WEB CASE STUDY\prospects.parquet"
HACKER_NEWS_API_BASE = "https://hacker-news.firebaseio.com/v0"

# =====================================================================
# JINJA PROMPT TEMPLATE BLUEPRINT
# =====================================================================
JINJA_PROSPECT_EXAMINER = """
System: You are an expert Job Prospect Analyst.
Read the following raw job post or project request from HackerNews.
You must extract the requested data and output a single JSON object matching the requested schema.

Raw Job Description:
{{ job_text }}

Rules:
1. Identify if the post is explicitly looking for audio processing, DSP, AI, data pipelines, or high-speed data architecture.
2. If budget or salary is mentioned, extract it. Otherwise, set it to "Unknown".
3. Evaluate the fit for our ultra-fast Audio/Data processing agency.
"""

# =====================================================================
# PYDANTIC MUZZLE (FIREWALL)
# =====================================================================
class JobProspectReport(BaseModel):
    """Pydantic Muzzle for LLM Prospect Evaluation"""
    company_name: str = Field(..., description="Name of the company hiring, or 'Unknown'")
    requires_audio_or_data: bool = Field(..., description="True if they need audio processing, DSP, AI, or data pipelines")
    budget_signal: str = Field(..., description="Salary or budget mentioned, otherwise 'Unknown'")
    fit_score: int = Field(..., description="Score from 0 to 100 on how well this matches our high-speed DSP/AI audio agency")
    reasoning: str = Field(..., description="Brief reasoning for the fit score")

# =====================================================================
# 1. THE FETCHER (Scraping Hacker News)
# =====================================================================
def fetch_hn_jobs(limit: int = 5) -> List[dict]:
    """Fetches the latest job postings from Hacker News."""
    logging.info("🌐 Fetching job postings from Hacker News Who is Hiring...")
    try:
        # Get the latest 'Ask HN: Who is hiring?' thread (ID 40846428 is a recent one, or we search)
        # For reliability in testing without complex search, we will fetch random top stories and filter
        # But a safer direct route: fetch top stories
        top_stories_req = requests.get(f"{HACKER_NEWS_API_BASE}/jobstories.json")
        job_ids = top_stories_req.json()[:limit]
        
        jobs = []
        for jid in job_ids:
            item_req = requests.get(f"{HACKER_NEWS_API_BASE}/item/{jid}.json")
            item = item_req.json()
            if item and item.get("type") == "job" and "title" in item:
                # Combine title and text (if any)
                full_text = item.get("title", "") + "\n" + item.get("text", "")
                jobs.append({
                    "id": jid,
                    "url": item.get("url", f"https://news.ycombinator.com/item?id={jid}"),
                    "raw_text": full_text
                })
        return jobs
    except Exception as e:
        logging.error(f"❌ Failed to fetch HN jobs: {e}")
        return []

# =====================================================================
# 2. THE LANGGRAPH PARSER (Jinja + Ollama Phi-3)
# =====================================================================
def parse_prospect_with_llm(job_text: str) -> Optional[JobProspectReport]:
    """Parses raw text into structured JSON using LM Studio and Pydantic."""
    jinja_compiler = Template(JINJA_PROSPECT_EXAMINER)
    fully_rendered_prompt = jinja_compiler.render(job_text=job_text)
    
    # Append schema to prompt to ensure the model knows what to output
    schema_str = json.dumps(JobProspectReport.model_json_schema())
    fully_rendered_prompt += f"\n\nJSON Schema:\n{schema_str}"
    
    logging.info("🧠 Passing raw job post into LM Studio Nemotron-3-Nano...")
    try:
        payload = {
            "model": "nvidia/nemotron-3-nano-4b",
            "messages": [{"role": "user", "content": fully_rendered_prompt}],
            "temperature": 0.0,
            "response_format": {"type": "json_object"}
        }
        res = requests.post("http://localhost:1234/v1/chat/completions", json=payload, timeout=30)
        res.raise_for_status()
        raw_ai_string = res.json()["choices"][0]["message"]["content"]
        
        logging.info("🛡️ Enforcing Pydantic Firewall schema validation...")
        validated_insight = JobProspectReport.model_validate_json(raw_ai_string)
        return validated_insight
    except Exception as e:
        logging.error(f"❌ LLM Parsing Error: {e}")
        return None

# =====================================================================
# 3. THE VECTORIZER (LM Studio - Snowflake Arctic)
# =====================================================================
def generate_embedding(text: str) -> List[float]:
    """Hits local LM Studio to generate embeddings."""
    logging.info("🧬 Vectorizing job text via LM Studio (Snowflake Arctic)...")
    payload = {
        "input": text,
        "model": EMBEDDING_MODEL
    }
    try:
        res = requests.post(LM_STUDIO_EMBEDDING_URL, json=payload, timeout=10)
        res.raise_for_status()
        data = res.json()
        return data["data"][0]["embedding"]
    except Exception as e:
        logging.error(f"❌ Embedding Generation Failed: {e}")
        # Return a zero vector fallback (1024 dims for Snowflake-L)
        return [0.0] * 1024

# =====================================================================
# 4. THE DATABASE (PyArrow + DuckDB)
# =====================================================================
def store_and_query_results(jobs_data: List[dict]):
    """Stores data into PyArrow/Parquet and queries it via DuckDB."""
    logging.info("💾 Building PyArrow Table for zero-copy memory transport...")
    
    # Flatten the data for Arrow
    flat_data = []
    for job in jobs_data:
        insight = job["insight"]
        flat_data.append({
            "job_id": str(job["id"]),
            "url": job["url"],
            "raw_text": job["raw_text"],
            "company_name": insight.company_name if insight else "Error",
            "requires_audio_data": insight.requires_audio_or_data if insight else False,
            "budget": insight.budget_signal if insight else "Unknown",
            "fit_score": insight.fit_score if insight else 0,
            "reasoning": insight.reasoning if insight else "Error",
            "embedding": job["embedding"]
        })
    
    arrow_table = pa.Table.from_pylist(flat_data)
    
    logging.info(f"📁 Saving to Parquet: {PARQUET_OUTPUT}")
    pq.write_table(arrow_table, PARQUET_OUTPUT)
    
    logging.info("🦆 Launching DuckDB for Zero-Copy PyArrow Query...")
    con = duckdb.connect(database=":memory:")
    
    # We can query the PyArrow table directly in memory!
    # DuckDB will read `arrow_table` directly from the Python variable scope.
    query_result = con.execute("""
        SELECT company_name, fit_score, requires_audio_data, budget
        FROM arrow_table
        ORDER BY fit_score DESC
    """).df()
    
    print("\n" + "="*60)
    print("🏆 DuckDB High-Speed Zero-Copy Query Results:")
    print("="*60)
    print(query_result)
    print("="*60)

# =====================================================================
# PIPELINE EXECUTION
# =====================================================================
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 60)
    print(" 🕸️ Independent Work Finder - Local AI Pipeline")
    print("=" * 60)
    
    # Step 1: Scrape
    jobs = fetch_hn_jobs(limit=3)
    if not jobs:
        print("No jobs found, exiting.")
        sys.exit(0)
        
    for job in jobs:
        print(f"\nProcessing Job ID {job['id']}: {job['url']}")
        # Step 2: Parse (LLM + Pydantic)
        job["insight"] = parse_prospect_with_llm(job["raw_text"])
        if job["insight"]:
            print(f"  -> Extracted Company: {job['insight'].company_name} | Score: {job['insight'].fit_score}")
        
        # Step 3: Vectorize
        job["embedding"] = generate_embedding(job["raw_text"])
        print(f"  -> Generated {len(job['embedding'])} dimensional vector.")
        
    # Step 4: Arrow & DuckDB
    store_and_query_results(jobs)
