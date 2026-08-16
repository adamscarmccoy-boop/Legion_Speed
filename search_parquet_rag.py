import pyarrow.parquet as pq
import pyarrow.compute as pc
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

parquet_path = r'C:\WEB CASE STUDY\omni_worker_states_backup.parquet'
if not os.path.exists(parquet_path):
    print(f"Parquet file not found at {parquet_path}")
    sys.exit(1)

print(f"Reading {parquet_path}...")
table = pq.read_table(parquet_path)

print(f"Loaded Parquet file with {table.num_rows} rows.")
print(f"Columns: {table.schema.names}")

# Search for 'rllib' and 'vision' in any string column
hits = []
search_cols = [c for c in table.schema.names if c in ["value", "raw_value", "key", "text", "content"]]

# If no common text columns, search all string columns
if not search_cols:
    import pyarrow as pa
    search_cols = [c.name for c in table.schema if pa.types.is_string(c.type) or pa.types.is_large_string(c.type)]

for col in search_cols:
    try:
        col_data = table.column(col)
        
        combined_mask = pc.match_substring(col_data, "onnx", ignore_case=True)
        filtered_table = table.filter(combined_mask)
        
        for record in filtered_table.to_pylist():
            hits.append({"column": col, "record": record})
    except Exception as e:
        print(f"Error searching column {col}: {e}")

print(f"\n=== PYARROW PARQUET SEARCH RESULTS ===")
print(f"Found {len(hits)} hits for 'rllib' + 'vision'.")

if hits:
    for i, h in enumerate(hits[:5]):
        print(f"\n  [HIT {i+1}] Column: {h['column']}")
        val = str(h['record'])
        if len(val) > 1000:
            val = val[:1000] + "... [TRUNCATED]"
        print(f"    {val}")
else:
    print("  Zero instances found in the Parquet backup.")
