import duckdb
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

con = duckdb.connect(r'C:\WEB CASE STUDY\web_intel_sonicdb.duckdb', read_only=True)
query = "SELECT filepath FROM computer_fs WHERE filename LIKE '%_DNA.json' LIMIT 1"
df = con.execute(query).fetchdf()

if not df.empty:
    path = df.iloc[0]['filepath']
    print('Found DNA JSON:', path)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            print(json.dumps(json.load(f), indent=2)[:800])
    except Exception as e:
        print('Error reading:', e)
else:
    print('No DNA JSON found in DuckDB.')
