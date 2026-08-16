import duckdb
import os

DB_PATH = r"C:\WEB CASE STUDY\web_intel_sonicdb.duckdb"

if os.path.exists(DB_PATH):
    conn = duckdb.connect(DB_PATH)
    # Check tables
    tables = conn.execute("SHOW TABLES").fetchall()
    print(f"Tables in {DB_PATH}: {tables}")
    
    # Query a sample of the data to prove I am reading the source of truth
    if ('spotify_charts_daily',) in tables:
        sample = conn.execute("SELECT * FROM spotify_charts_daily LIMIT 5").fetchall()
        print(f"\nSample from spotify_charts_daily: {sample}")
    else:
        print("\nTable 'spotify_charts_daily' not found.")
    
    conn.close()
else:
    print(f"Database file not found at {DB_PATH}")
