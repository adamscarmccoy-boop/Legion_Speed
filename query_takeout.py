import sys
import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RAW_PARQUET = r"C:\WEB CASE STUDY\takeout_raw.parquet"
VECTORIZED_PARQUET = r"C:\WEB CASE STUDY\takeout_vectorized.parquet"

def main():
    con = duckdb.connect(database=":memory:")
    
    print("=" * 60)
    print(" 🦆 Legion DuckDB: Querying NotebookLM Takeout Data")
    print("=" * 60)
    
    # Check RAW Schema
    print("\n--- SCHEMA FOR takeout_raw.parquet ---")
    raw_schema = con.execute(f"DESCRIBE SELECT * FROM '{RAW_PARQUET}'").df()
    print(raw_schema[['column_name', 'column_type']])
    
    # Check VECTORIZED Schema
    print("\n--- SCHEMA FOR takeout_vectorized.parquet ---")
    try:
        vec_schema = con.execute(f"DESCRIBE SELECT * FROM '{VECTORIZED_PARQUET}'").df()
        print(vec_schema[['column_name', 'column_type']])
    except Exception as e:
        print(f"Failed to read vectorized schema: {e}")

    # Perform a fast keyword search on the vector chunks
    print("\n--- SEARCHING VECTORIZED DATA FOR 'Ableton' ---")
    try:
        hits = con.execute(f"""
            SELECT filename, chunk_id, substring(text_chunk, 1, 80) as snippet 
            FROM '{VECTORIZED_PARQUET}' 
            WHERE text_chunk ILIKE '%Ableton%'
            LIMIT 5
        """).df()
        print(hits)
    except Exception as e:
        print(f"Search failed: {e}")

if __name__ == "__main__":
    main()
