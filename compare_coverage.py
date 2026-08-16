import os
import glob
import json
import duckdb

def main():
    print("=== Analyzing System-Wide Audio Coverage ===")
    
    # 1. Load the processed tracks from DuckDB
    db_path = r"c:\STUDIES_BACKUP\Legion-Jacked-Pipeline\AI_Logs\sonic_core_v2.duckdb"
    processed_paths = set()
    if os.path.exists(db_path):
        conn = duckdb.connect(db_path, read_only=True)
        try:
            df = conn.execute("SELECT filepath FROM audio_features").fetchdf()
            processed_paths = set(df['filepath'].str.lower().tolist())
            print(f"Loaded {len(processed_paths)} processed tracks from DuckDB.")
        except Exception as e:
            print(f"Error reading DuckDB: {e}")
        finally:
            conn.close()
    else:
        print(f"Warning: DuckDB not found at {db_path}")

    # 2. Load the total catalog from the JSONL shards
    shard_dir = r"C:\WEB CASE STUDY\ray_cat_shards"
    shard_files = glob.glob(os.path.join(shard_dir, "*.jsonl"))
    
    catalog_by_shard = {}
    total_catalog_tracks = 0
    total_unprocessed_tracks = 0
    
    print(f"Scanning {len(shard_files)} catalog shards...")
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
            print(f"Error reading {shard_name}: {e}")
            
        covered = catalog_paths.intersection(processed_paths)
        uncovered = catalog_paths - processed_paths
        
        catalog_by_shard[shard_name] = {
            "total": len(catalog_paths),
            "covered": len(covered),
            "uncovered": len(uncovered),
            "coverage_pct": (len(covered) / len(catalog_paths) * 100) if catalog_paths else 0.0
        }
        
        total_catalog_tracks += len(catalog_paths)
        total_unprocessed_tracks += len(uncovered)

    # 3. Print report
    print("\n" + "="*80)
    print(f"{'Catalog Shard':<40} | {'Total':<8} | {'Covered':<8} | {'Uncovered':<9} | {'Coverage %':<10}")
    print("-"*80)
    for name, stats in catalog_by_shard.items():
        print(f"{name[:40]:<40} | {stats['total']:<8} | {stats['covered']:<8} | {stats['uncovered']:<9} | {stats['coverage_pct']:>9.2f}%")
    print("="*80)
    
    overall_coverage = (total_catalog_tracks - total_unprocessed_tracks)
    overall_pct = (overall_coverage / total_catalog_tracks * 100) if total_catalog_tracks else 0.0
    
    print(f"OVERALL SUMMARY:")
    print(f"  Total Tracks in Catalog:   {total_catalog_tracks:,}")
    print(f"  Total Processed (Covered): {overall_coverage:,}")
    print(f"  Total Unprocessed (Gap):   {total_unprocessed_tracks:,}")
    print(f"  Overall Swarm Coverage:    {overall_pct:.4f}%")
    print("="*80)

if __name__ == "__main__":
    main()
