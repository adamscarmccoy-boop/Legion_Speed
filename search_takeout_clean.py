import duckdb
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except:
    pass

PARQUET_FILE = r"C:\WEB CASE STUDY\takeout_vectorized.parquet"
con = duckdb.connect()

print("ray serve gemma onnx")

query = f"""
    SELECT filename, chunk_id, text_chunk 
    FROM '{PARQUET_FILE}'
    WHERE text_chunk ILIKE '%ray%' 
       or text_chunk ILIKE '%onnx%'
       or text_chunk ILIKE '%gemma%'
"""
df = con.execute(query).df()

for idx, row in df.iterrows():
    text = row['text_chunk']
    upper_text = text.upper()
    if ('DNA' in upper_text) and ('RAY' in upper_text or 'onnx' in upper_text or 'gemma' in upper_text):
        print(f"\n--- MATCH IN {row['filename']} (Chunk {row['chunk_id']}) ---")
        import re
        for m in re.finditer(r'.{0,150}(?:ray|onnx|gemma).{0,150}', text, flags=re.IGNORECASE|re.DOTALL):
            print("..." + m.group(0).replace('\n', ' ') + "...")
