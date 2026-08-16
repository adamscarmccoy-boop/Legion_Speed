# %% [markdown]
# # 🌌 THE OMNI-KNOWLEDGE GRAPH (GLOBAL JOIN)
# This cell establishes the ultimate cognitive map. It joins the physical drive map (computer_fs),
# the semantic tag map (ray_categories.parquet), and the mathematical footprint map (sonic_dna).
# It also ingests Ableton JSONs to map your arrangement logic.

import duckdb
import json
import os
import time

DB_PATH = r"C:\WEB CASE STUDY\web_intel_sonicdb.duckdb"

print("🌌 Fusing the Omni-Knowledge Graph...")
con = duckdb.connect(DB_PATH)

# 1. MOUNT THE SEMANTIC MAP (ray_categories.parquet)
# We create a view directly into the parquet file so DuckDB can query it live
con.execute("""
    CREATE OR REPLACE VIEW semantic_map AS 
    SELECT * FROM read_parquet('C:\WEB CASE STUDY\ray_categories.parquet')
""")

# 2. CREATE THE ARRANGEMENT MAP (ableton_nodes)
con.execute("""
    CREATE TABLE IF NOT EXISTS ableton_nodes (
        project_name VARCHAR,
        tempo VARCHAR,
        tracks_json VARCHAR,
        filepath VARCHAR
    )
""")

# -------------------------------------------------------------
# STEP A: INGEST ABLETON ARRANGEMENTS (THE MIND)
# -------------------------------------------------------------
# Find all unparsed _DNA.json files
dna_files_df = con.execute("""
    SELECT filepath FROM computer_fs 
    WHERE filename LIKE '%_DNA.json'
      AND filepath NOT IN (SELECT filepath FROM ableton_nodes)
    LIMIT 100
""").fetchdf()

dna_targets = dna_files_df['filepath'].tolist()
if dna_targets:
    print(f"🎹 Found {len(dna_targets)} new Ableton projects. Mapping Arrangement DNA...")
    records = []
    for path in dna_targets:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                records.append((
                    data.get('project_name', 'Unknown'),
                    str(data.get('tempo', '')),
                    json.dumps(data.get('tracks', [])),
                    path
                ))
        except Exception:
            pass
    if records:
        con.executemany("INSERT INTO ableton_nodes VALUES (?, ?, ?, ?)", records)

# -------------------------------------------------------------
# STEP B: THE OMNI-QUERY (THE DELTA QUEUE OF THE GODS)
# -------------------------------------------------------------
# This is the ultimate query. It finds files that:
# 1. Physically exist on your drive (computer_fs)
# 2. Have a semantic category/vendor tag (semantic_map)
# 3. Have NOT yet been encoded by the PyTorch/ONNX Swarm (sonic_dna)
omni_queue_df = con.execute("""
    SELECT 
        c.filepath,
        c.size_mb,
        sem.vendors,
        sem.categories,
        sem.bpm,
        sem.key
    FROM computer_fs c
    -- Strict INNER JOIN: We only process audio that has semantic tags!
    INNER JOIN semantic_map sem ON c.filepath = sem.path
    LEFT JOIN sonic_dna s ON c.filepath = s.filepath
    LEFT JOIN failed_ingestion f ON c.filepath = f.filepath
    WHERE c.ext IN ('.wav', '.mp3', '.aif')
      AND s.filepath IS NULL 
      AND f.filepath IS NULL
      AND c.filename NOT LIKE '._%'
    LIMIT 100
""").fetchdf()

if omni_queue_df.empty:
    print("✅ The Omni-Knowledge Graph is 100% synchronized.")
else:
    print(f"📡 Found {len(omni_queue_df)} fully semantically-tagged targets waiting for the Swarm.")
    print("   -> Example Target Context:")
    print(f"      File:   {omni_queue_df.iloc[0]['filepath']}")
    print(f"      Vendor: {omni_queue_df.iloc[0]['vendors']}")
    print(f"      Tags:   {omni_queue_df.iloc[0]['categories']}")
    print(f"      BPM:    {omni_queue_df.iloc[0]['bpm']}")
    
    # You would pass omni_queue_df['filepath'].tolist() to the Ray ONNX Swarm here!

con.close()
