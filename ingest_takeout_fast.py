import os
import sys
import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
from bs4 import BeautifulSoup
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

TAKEOUT_DIR = r"C:\Users\adams\Downloads\takeout-20260613T032152Z-3-001\Takeout\NotebookLM\LETS MAKE SOME MONEY HONEY\Sources"
RAW_PARQUET = r"C:\WEB CASE STUDY\takeout_raw.parquet"

def extract_html_text(filepath: str) -> str:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, "html.parser")
            return soup.get_text(separator='\n', strip=True)
    except Exception as e:
        return ""

def main():
    print("=" * 60)
    print(" ⚡ Legion Pipeline: Phase 1 (Fast PyArrow Ingestion)")
    print("=" * 60)

    if not os.path.exists(TAKEOUT_DIR):
        print(f"FATAL: Takeout directory not found: {TAKEOUT_DIR}")
        sys.exit(1)

    html_files = [f for f in os.listdir(TAKEOUT_DIR) if f.endswith(".html")]
    print(f"Found {len(html_files)} HTML files in Takeout.")
    
    t0 = time.time()
    records = []
    
    for filename in html_files:
        filepath = os.path.join(TAKEOUT_DIR, filename)
        raw_text = extract_html_text(filepath)
        if raw_text:
            records.append({
                "filename": filename,
                "raw_text": raw_text,
                "char_length": len(raw_text)
            })
            
    # Save to PyArrow
    arrow_table = pa.Table.from_pylist(records)
    pq.write_table(arrow_table, RAW_PARQUET)
    
    elapsed = time.time() - t0
    print(f"\n✅ Slurped {len(records)} files into zero-copy memory in {elapsed:.2f} seconds.")
    print(f"💾 Saved raw dataset to {RAW_PARQUET}")
    
    # Fast DuckDB Query
    print("\n🦆 Firing zero-copy DuckDB query against PyArrow memory...")
    con = duckdb.connect(database=":memory:")
    
    # Query 1: Top longest docs
    top_docs = con.execute("""
        SELECT filename, char_length 
        FROM arrow_table 
        ORDER BY char_length DESC 
        LIMIT 5
    """).df()
    
    print("\n[TOP 5 LONGEST DOCUMENTS IN TAKEOUT]")
    print(top_docs)
    
    # Query 2: Search for 'contractor' or 'freelance'
    hits = con.execute("""
        SELECT filename, char_length
        FROM arrow_table
        WHERE raw_text ILIKE '%contractor%' OR raw_text ILIKE '%freelance%'
        ORDER BY char_length DESC
        LIMIT 5
    """).df()
    
    print("\n[TOP 5 DOCUMENTS MENTIONING 'contractor' OR 'freelance']")
    print(hits)

if __name__ == "__main__":
    main()
