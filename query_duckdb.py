import duckdb
import pandas as pd

con = duckdb.connect(r'c:\WEB CASE STUDY\web_intel_sonicdb.duckdb')
tables = con.execute("SHOW TABLES").fetchall()

print("Searching DuckDB tables for 'generator', 'gpu fast', 'lyrics'...")
for t in tables:
    table_name = t[0]
    try:
        df = con.execute(f"SELECT * FROM {table_name}").df()
        string_cols = df.select_dtypes(include=['object']).columns
        
        for col in string_cols:
            mask = df[col].astype(str).str.contains('generator|gpu fast|lyrics', case=False, na=False)
            if mask.any():
                print(f"\n--- MATCH IN {table_name}.{col} ---")
                matched = df[mask][col].astype(str).tolist()
                for m in matched[:3]:
                    print(m[:300])
    except Exception as e:
        print(f"Error reading {table_name}: {e}")
