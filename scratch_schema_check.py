import duckdb
import os

db_path = r'C:\WEB CASE STUDY\web_intel_sonicdb.duckdb'
if os.path.exists(db_path):
    print(f'Connecting to {db_path}...')
    con = duckdb.connect(db_path, read_only=True)
    tables = con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchall()
    print('Tables found:', tables)
    
    for t in tables:
        table_name = t[0]
        schema = con.execute(f"DESCRIBE {table_name}").fetchall()
        print(f'\nSchema for {table_name}:')
        for col in schema:
            print(f'  {col[0]} ({col[1]})')
else:
    print('DuckDB file not found at path.')
