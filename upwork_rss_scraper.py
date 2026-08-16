import sys
import logging
import requests
import pyarrow as pa
import pyarrow.parquet as pq
from bs4 import BeautifulSoup
import feedparser

# Re-use functions from takeout extractor
from takeout_contractor_extractor import (
    evaluate_with_nemotron, 
    generate_snowflake_embedding, 
    chunk_text_by_paragraphs
)

# Force UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

PARQUET_OUTPUT = r"C:\WEB CASE STUDY\upwork_leads.parquet"
UPWORK_RSS_URL = "https://www.upwork.com/ab/feed/jobs/rss?q=audio+DSP+OR+audio+programmer+OR+machine+learning"

def main():
    print("=" * 60)
    print(" 🚀 Legion Pipeline: Upwork RSS Live Ingestion")
    print("=" * 60)
    
    print(f"Fetching RSS Feed: {UPWORK_RSS_URL}")
    feed = feedparser.parse(UPWORK_RSS_URL)
    
    if not feed.entries:
        print("No jobs found in RSS feed. Check URL or try again later.")
        sys.exit(0)
        
    print(f"Found {len(feed.entries)} potential jobs in the RSS feed.\n")
    validated_records = []
    
    for count, entry in enumerate(feed.entries[:10]):
        print(f"[{count+1}/10] Processing: {entry.title}")
        
        # Clean HTML from RSS description
        soup = BeautifulSoup(entry.description, "html.parser")
        clean_desc = soup.get_text(separator='\n', strip=True)
        
        raw_text = f"Title: {entry.title}\nLink: {entry.link}\nDescription:\n{clean_desc}"
        
        # Evaluate
        print("  -> Asking Nemotron to evaluate...")
        insight = evaluate_with_nemotron(raw_text)
        
        if not insight:
            print("  -> [SKIP] Parsing failed.")
            continue
            
        print(f"  -> Nemotron Fit Score: {insight.fit_score} | DSP/Audio: {insight.requires_audio_or_data}")
        print(f"  -> Title: {insight.title}")
        print(f"  -> Budget: {insight.budget_signal}")
        
        if insight.fit_score > 50 or insight.requires_audio_or_data:
            print("  -> 🎯 HIGH VALUE TARGET IDENTIFIED. Chunking and Embedding...")
            chunks = chunk_text_by_paragraphs(raw_text)
            
            for chunk_idx, chunk in enumerate(chunks):
                vec = generate_snowflake_embedding(chunk)
                validated_records.append({
                    "source_url": entry.link,
                    "title": insight.title,
                    "fit_score": insight.fit_score,
                    "budget": insight.budget_signal,
                    "reasoning": insight.reasoning,
                    "chunk_id": chunk_idx,
                    "text_chunk": chunk,
                    "embedding": vec
                })
        else:
            print("  -> [SKIP] Low fit score.")
            
    if validated_records:
        print(f"\n💾 Saving {len(validated_records)} high-value embedded chunks to {PARQUET_OUTPUT}")
        arrow_table = pa.Table.from_pylist(validated_records)
        pq.write_table(arrow_table, PARQUET_OUTPUT)
        print("✅ Pipeline Complete.")
    else:
        print("\nNo high-value records found to embed.")

if __name__ == "__main__":
    try:
        import feedparser
    except ImportError:
        print("Please run: pip install feedparser beautifulsoup4")
        sys.exit(1)
    main()
