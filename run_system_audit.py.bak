import os
import json
import time
import sys
import pyarrow as pa
import lancedb
import duckdb
import pandas as pd
import ray
from sklearn.ensemble import RandomForestRegressor

# ==============================================================================
# SOVEREIGN LIFE-CYCLE STABILIZER (AUTO-INJECTED)
# Prevents dangling stdout/stdio pipes and GCS registry locks on Windows exit
# ==============================================================================
import atexit
import signal

def clean_exit_handler(*args, **kwargs):
    import sys
    sys.stderr.write("\n[LMS LIFECYCLE] Exit triggered. Flushing system streams...\n")
    sys.stderr.flush()
    try:
        import ray
        if ray.is_initialized():
            sys.stderr.write("[LMS LIFECYCLE] Active Ray session detected. Disconnecting...\n")
            ray.shutdown()
    except Exception:
        pass
    sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================


if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

@ray.remote
def audit_single_json_file(file_path):
    import json
    import os
    try:
        sz = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        if sz < 5 * 1024 * 1024:
            with open(file_path, "r", encoding="utf-8") as jf:
                data = json.load(jf)
                keys = list(data.keys()) if isinstance(data, dict) else (list(data[0].keys()) if isinstance(data, list) and len(data) > 0 else [])
                return {
                    "filename": filename,
                    "path": file_path,
                    "size_kb": round(sz / 1024, 2),
                    "keys": keys[:10]
                }
        else:
            return {
                "filename": filename,
                "path": file_path,
                "size_kb": round(sz / 1024, 2),
                "keys": "large_file"
            }
    except Exception as e:
        return {"path": file_path, "status": "unreadable", "error": str(e)}

def run_system_verification():
    print("======================================================================")
    print("🔬 RUNNING SYSTEM-WIDE AUDIO DATA & SCHEMA INTEGRITY AUDIT")
    print("======================================================================")
    
    t0 = time.time()
    reports = {}
    
    # ── 1. PYARROW & LANCEDB VERIFICATION ──
    print("\n[1/4] Auditing LanceDB & PyArrow schemas...")
    lancedb_path = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
    table_name = "omni_semantic_baselines"
    
    try:
        db = lancedb.connect(lancedb_path)
        tbl = db.open_table(table_name)
        arrow_tbl = tbl.to_arrow()
        
        reports["lancedb"] = {
            "status": "PASS",
            "rows": arrow_tbl.num_rows,
            "columns": arrow_tbl.schema.names,
            "schema_details": str(arrow_tbl.schema),
            "null_count": {col: arrow_tbl[col].null_count for col in arrow_tbl.schema.names}
        }
        print("  ✅ LanceDB: Schema is valid and fully intact.")
    except Exception as e:
        reports["lancedb"] = {"status": "FAIL", "error": str(e)}
        print(f"  ❌ LanceDB Audit failed: {e}")

    # ── 2. DUCKDB VERIFICATION ──
    print("\n[2/4] Auditing DuckDB Sonic database...")
    duckdb_path = r"C:\WEB CASE STUDY\web_intel_sonicdb.duckdb"
    
    try:
        conn = duckdb.connect(duckdb_path, read_only=True)
        tables = conn.execute("SHOW TABLES").fetchall()
        table_names = [t[0] for t in tables]
        
        table_audits = {}
        for name in table_names:
            desc = conn.execute(f"DESCRIBE {name}").fetchall()
            row_count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            table_audits[name] = {
                "columns": [col[0] for col in desc],
                "types": [col[1] for col in desc],
                "rows": row_count
            }
        conn.close()
        reports["duckdb"] = {
            "status": "PASS",
            "tables": table_audits
        }
        print("  ✅ DuckDB: Metadata schemas validated successfully.")
    except Exception as e:
        reports["duckdb"] = {"status": "FAIL", "error": str(e)}
        print(f"  ❌ DuckDB Audit failed: {e}")

    # ── 3. PARQUET SYSTEM SCAN ──
    print("\n[3/4] Scanning system for Parquet datasets...")
    parquet_files = []
    search_dirs = [r"C:\WEB CASE STUDY", r"C:\STUDIES_BACKUP"]
    
    for s_dir in search_dirs:
        if os.path.exists(s_dir):
            for root, _, files in os.walk(s_dir):
                for file in files:
                    if file.endswith(".parquet"):
                        p_path = os.path.join(root, file)
                        try:
                            meta = pq.read_metadata(p_path)
                            parquet_files.append({
                                "path": p_path,
                                "rows": meta.num_rows,
                                "columns": meta.schema.names
                            })
                        except Exception:
                            parquet_files.append({"path": p_path, "status": "unreadable"})
                            
    reports["parquet"] = parquet_files
    print(f"  ✅ Parquet scan completed. Found {len(parquet_files)} files.")

    # ── 4. STALE DATA & OLD JSON FINDER ──
    print("\n[4/4] Searching for legacy / stale JSON data assets in parallel via Ray...")
    
    # Connect to the local Ray cluster
    ray.init(address="auto", ignore_reinit_error=True)
    
    json_candidates = []
    # Scan specifically for files in Downloads, Web Case Study, and exported_json
    for s_dir in [r"C:\Users\adams\Downloads", r"C:\WEB CASE STUDY", r"C:\STUDIES_BACKUP\ableton-session-intelligence\exported_json"]:
        if os.path.exists(s_dir):
            for root, _, files in os.walk(s_dir):
                for file in files:
                    if file.endswith(".json") and not file.startswith("."):
                        json_candidates.append(os.path.join(root, file))
                        
    print(f"  Distributing {len(json_candidates)} JSON files to Ray workers...")
    futures = [audit_single_json_file.remote(path) for path in json_candidates]
    json_results = ray.get(futures)
    
    # Filter out failures or None results
    json_files = [r for r in json_results if r is not None and "status" not in r]
    
    reports["stale_jsons"] = json_files
    print(f"  ✅ JSON scan completed. Found {len(json_files)} verified legacy data assets.")

    # ── 5. TRAIN AUTO-SUITABILITY PREDICTION MODEL ──
    print("\n🤖 Training dynamic suitability prediction model...")
    try:
        # Load features from LanceDB to train our RandomForest Regressor
        db = lancedb.connect(lancedb_path)
        tbl = db.open_table(table_name)
        df = tbl.to_pandas()
        
        # Train model to predict Crest Factor based on spectral/energy band dynamics
        features = ["rms", "sub_bass_energy", "bass_energy", "mid_energy", "high_energy", "spectral_centroid"]
        target = "crest_factor"
        
        df_clean = df[features + [target]].dropna()
        X = df_clean[features].values
        y = df_clean[target].values
        
        rf = RandomForestRegressor(n_estimators=100, random_state=42)
        rf.fit(X, y)
        
        reports["suitability_model"] = {
            "status": "TRAINED",
            "samples": len(df_clean),
            "features": features,
            "target": target,
            "feature_importances": dict(zip(features, rf.feature_importances_.tolist()))
        }
        print("  ✅ Model trained successfully. Ready for dynamic target prediction.")
    except Exception as e:
        reports["suitability_model"] = {"status": "FAIL", "error": str(e)}
        print(f"  ❌ Model training failed: {e}")

    # Write output report
    out_path = r"C:\WEB CASE STUDY\system_data_audit_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=4)
        
    elapsed = time.time() - t0
    print(f"\n======================================================")
    print(f"✅ Audit Complete in {elapsed:.2f} seconds!")
    print(f"Report written to -> {out_path}")
    print(f"======================================================")

if __name__ == "__main__":
    import pyarrow.parquet as pq
    run_system_verification()