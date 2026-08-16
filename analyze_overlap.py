import duckdb
import pandas as pd
import json
import os
import glob

db_path = r'c:\STUDIES_BACKUP\Legion-Jacked-Pipeline\AI_Logs\sonic_core_v2.duckdb'
print('Loading duckdb...')
try:
    if os.path.exists(db_path):
        conn = duckdb.connect(db_path, read_only=True)
        db_paths = conn.execute('SELECT filepath FROM audio_features').fetchdf()['filepath'].str.lower().tolist()
        conn.close()
        db_paths_set = set(db_paths)
        print(f'DuckDB total rows: {len(db_paths_set)}')
    else:
        print('DuckDB not found at path.')
        db_paths_set = set()
except Exception as e:
    print(f'Error loading DuckDB: {e}')
    db_paths_set = set()

shard_files = glob.glob(r'C:\WEB CASE STUDY\ray_cat_shards\*.jsonl')

total_shard_rows = 0
total_overlap = 0

for shard_file in shard_files:
    print(f'\nChecking {os.path.basename(shard_file)}...')
    shard_paths = set()
    try:
        with open(shard_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                shard_paths.add(data.get('path', '').lower())
    except Exception as e:
        print(f"Error reading {shard_file}: {e}")
        
    overlap = shard_paths.intersection(db_paths_set)
    print(f'Shard unique paths: {len(shard_paths)}')
    print(f'Overlap with DuckDB: {len(overlap)}')
    total_shard_rows += len(shard_paths)
    total_overlap += len(overlap)

print(f'\n--- SUMMARY ---')
print(f'Total unique paths across all shards: {total_shard_rows}')
print(f'Total overlap with existing DuckDB data: {total_overlap}')
