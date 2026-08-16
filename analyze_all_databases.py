import os
import glob
import json
import duckdb
import lancedb
import pandas as pd

def main():
    print("=== Multi-Database Coverage Aggregation ===")
    
    all_processed_paths = set()

    # 1. Query DuckDB
    duckdb_paths = [
        r"c:\STUDIES_BACKUP\Legion-Jacked-Pipeline\AI_Logs\sonic_core_v2.duckdb",
        r"C:\WEB CASE STUDY\web_intel_sonicdb.duckdb"
    ]
    
    for db in duckdb_paths:
        if os.path.exists(db):
            print(f"Loading DuckDB: {db}")
            try:
                conn = duckdb.connect(db, read_only=True)
                tables = conn.execute("SHOW TABLES").fetchall()
                for (tbl_name,) in tables:
                    try:
                        # Check if it has path or filepath columns
                        cols = [c[0].lower() for c in conn.execute(f"DESCRIBE {tbl_name}").fetchall()]
                        path_col = None
                        for c in ["filepath", "path", "source_file"]:
                            if c in cols:
                                path_col = c
                                break
                        if path_col:
                            df = conn.execute(f"SELECT {path_col} FROM {tbl_name}").fetchdf()
                            paths = set(df[path_col].dropna().astype(str).str.lower().tolist())
                            all_processed_paths.update(paths)
                            print(f"  -> Table '{tbl_name}': loaded {len(paths)} paths.")
                    except Exception as e:
                        pass
                conn.close()
            except Exception as e:
                print(f"  Error querying DuckDB: {e}")

    # 2. Query LanceDB
    lancedb_paths = [
        r"C:\WEB CASE STUDY\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag",
        r"C:\WEB CASE STUDY\lancedb_web_intel_rag",
        r"c:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag"
    ]
    
    for db_path in lancedb_paths:
        if os.path.exists(db_path):
            print(f"Loading LanceDB: {db_path}")
            try:
                db = lancedb.connect(db_path)
                for tbl_name in db.table_names():
                    try:
                        table = db.open_table(tbl_name)
                        df = table.to_pandas()
                        path_col = None
                        for c in ["filepath", "path", "source_file", "filename"]:
                            if c in df.columns:
                                path_col = c
                                break
                        if path_col:
                            paths = set(df[path_col].dropna().astype(str).str.lower().tolist())
                            # Clean up relative or local paths if needed
                            all_processed_paths.update(paths)
                            print(f"  -> Table '{tbl_name}': loaded {len(paths)} paths.")
                    except Exception as e:
                        pass
            except Exception as e:
                print(f"  Error querying LanceDB: {e}")

    print(f"\nTotal unique paths identified in all databases: {len(all_processed_paths)}")

    # 3. Cross-reference with Shards
    shard_dir = r"C:\WEB CASE STUDY\ray_cat_shards"
    shard_files = glob.glob(os.path.join(shard_dir, "*.jsonl"))
    
    total_catalog_tracks = 0
    total_covered = 0
    
    for shard in shard_files:
        shard_name = os.path.basename(shard)
        catalog_paths = set()
        
        try:
            with open(shard, "r", encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line)
                    path = data.get("path")
                    if path:
                        catalog_paths.add(path.lower())
        except Exception as e:
            pass
            
        covered = catalog_paths.intersection(all_processed_paths)
        total_catalog_tracks += len(catalog_paths)
        total_covered += len(covered)
        print(f"Shard '{shard_name}': {len(catalog_paths)} total, {len(covered)} covered.")

    print("\n" + "="*80)
    print(f"COMBINED SUMMARY (DuckDB + LanceDB):")
    print(f"  Total Unique Catalog Files: {total_catalog_tracks:,}")
    print(f"  Total Covered Files:        {total_covered:,}")
    print(f"  Total Unprocessed Gap:      {total_catalog_tracks - total_covered:,}")
    print(f"  Combined Swarm Coverage:     {(total_covered / total_catalog_tracks * 100) if total_catalog_tracks else 0.0:.4f}%")
    print("="*80)

if __name__ == "__main__":
    main()
