import pyarrow.parquet as pq
import pyarrow.compute as pc
import pyarrow as pa
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

PARQUET_FILES = [
    r"C:\WEB CASE STUDY\code_notebook_knowledge_audit.parquet",
    r"C:\WEB CASE STUDY\als_master_data.parquet"
]

SEARCH_TERMS = [".cpp", "engine", "sovereign", "wasapi", "pedalboard"]

def direct_parquet_search():
    for file_path in PARQUET_FILES:
        if not os.path.exists(file_path):
            continue
        
        print(f"Scanning: {file_path}")
        try:
            table = pq.read_table(file_path)
            columns = table.schema.names
            
            for term in SEARCH_TERMS:
                found_any = False
                for col_name in columns:
                    col_data = table.column(col_name).cast(pa.string())
                    mask = pc.match_substring(col_data, term, ignore_case=True)
                    filtered = table.filter(mask)
                    
                    if filtered.num_rows > 0:
                        found_any = True
                        print(f"Term: {term} | Col: {col_name} | Hits: {filtered.num_rows}")
                        for row in filtered.to_pylist()[:3]:
                            print(f"  -> {str(row)[:500]}")
                if not found_any:
                    pass
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    direct_parquet_search()
