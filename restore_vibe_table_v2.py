import json
import lancedb
import pandas as pd

# Paths
paths = [
    r'C:\STUDIES_BACKUP\vectors\lancedb_store',
    r'C:\WEB CASE STUDY\.vector_cache'
]
JSON_PATH = r'C:\WEB CASE STUDY\data\lancedb_audio_vibe_gpu.json'

def restore_vibe_table():
    print(f"Loading data from {JSON_PATH}...")
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    
    for path in paths:
        try:
            print(f"Restoring to {path}...")
            db = lancedb.connect(path)
            tbl = db.create_table("audio_vibe_gpu", data=df, mode="overwrite")
            print(f"✅ Success: {path} | Rows: {tbl.count_rows()}")
        except Exception as e:
            print(f"❌ Failed: {path} | Error: {e}")

if __name__ == "__main__":
    restore_vibe_table()
