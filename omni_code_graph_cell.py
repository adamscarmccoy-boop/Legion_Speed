# %% [markdown]
# # 🌌 THE CODE OMNI-KNOWLEDGE GRAPH (GLOBAL JOIN)
# This cell establishes the cognitive map for your Code and E-Drive architecture.
# It mounts the newly generated code_knowledge_audit.parquet, ray_exploration_results.json, 
# and the new Snowflake code_vectors table directly into DuckDB.

import duckdb
import json
import os
import time
import sys

# Force output to UTF-8 to prevent Windows crash on emojis
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

DB_PATH = r"C:\WEB CASE STUDY\web_intel_sonicdb.duckdb"

print("🌌 Fusing the Code Omni-Knowledge Graph...")
con = duckdb.connect(DB_PATH)

# 1. MOUNT THE CODE AUDIT MAP (from ray_code_swarm.py)
print("Mounting Code Audit Parquet...")
con.execute("""
    CREATE OR REPLACE VIEW code_audit_map AS 
    SELECT * FROM read_parquet('C:/WEB CASE STUDY/code_knowledge_audit.parquet')
""")

# 2. MOUNT THE RAY EXPLORATION JSON
print("Mounting Ray Exploration JSON...")
con.execute("""
    CREATE OR REPLACE VIEW ray_exploration_map AS 
    SELECT * FROM read_json_auto('C:/WEB CASE STUDY/ray_exploration_results.json')
""")

# 3. MOUNT NOTEBOOK KNOWLEDGE AUDIT
print("Mounting Notebook Knowledge Audit Parquet...")
con.execute("""
    CREATE OR REPLACE VIEW notebook_audit_map AS 
    SELECT * FROM read_parquet('C:/WEB CASE STUDY/notebook_knowledge_audit.parquet')
""")

# 4. MOUNT OMNI WORKER STATES BACKUP
print("Mounting Omni Worker States Backup Parquet...")
con.execute("""
    CREATE OR REPLACE VIEW omni_worker_states AS 
    SELECT * FROM read_parquet('C:/WEB CASE STUDY/omni_worker_states_backup.parquet')
""")

# 5. VERIFY THE CODE VECTORS TABLE
print("Verifying Snowflake Code Vectors...")
con.execute("""
    CREATE TABLE IF NOT EXISTS code_vectors (
        source_table VARCHAR,
        payload VARCHAR,
        lm_vector FLOAT[]
    )
""")

# 6. FUSE THE OMNI-QUERY FOR CODE
# This query joins the Code Audit map with the completed Vectors to find what's missing
code_queue_df = con.execute("""
    SELECT 
        c.filename,
        c.path,
        c.size_kb,
        c.rows,
        v.source_table
    FROM code_audit_map c
    LEFT JOIN code_vectors v ON c.filename = v.source_table
    WHERE c.status = 'SUCCESS'
      AND v.source_table IS NULL
    LIMIT 100
""").fetchdf()

if code_queue_df.empty:
    print("✅ The Code Omni-Knowledge Graph is 100% synchronized and fully vectorized.")
else:
    print(f"📡 Found {len(code_queue_df)} code/JSON targets waiting to be sent to Snowflake LM Studio.")
    print("   -> Example Target Context:")
    print(f"      File: {code_queue_df.iloc[0]['filename']}")
    print(f"      Path: {code_queue_df.iloc[0]['path']}")
    print(f"      Rows: {code_queue_df.iloc[0]['rows']}")

con.close()
print("🔥 Fusion Complete!")
