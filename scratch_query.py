import lancedb
import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 100)

# Connect to the fully populated database on the backup drive
db = lancedb.connect(r'C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag')

try:
    table = db.open_table('mined_code_vectors')
    results = table.search('ray[serve]').limit(5).to_pandas()
    print("\n--- RAG RESULTS FOR 'ray[serve]' ---\n")
    if not results.empty:
        print(results[['source_file', 'symbol_name', 'lines_of_code']])
    else:
        print("No results found.")
except Exception as e:
    print(f"Error querying table: {e}")
