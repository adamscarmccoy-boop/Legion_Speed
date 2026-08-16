import pandas as pd
import lancedb
from pathlib import Path

PARQUET_DIR = Path(r"C:\STUDIES_BACKUP\data\metadata\parquet_exports")
LANCEDB_PATH = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"

def diagnose_names():
    print("=" * 70)
    print("  NAME ALIGNMENT DIAGNOSIS")
    print("=" * 70)

    # 1. Sample names from Parquet files
    parquet_names = []
    parquet_files = list(PARQUET_DIR.glob("*.parquet"))
    for pf in parquet_files[:10]:
        try:
            df = pd.read_parquet(pf)
            if "track_name" in df.columns:
                parquet_names.append(df["track_name"].iloc[0])
            else:
                parquet_names.append(f"FILE: {pf.name}")
        except Exception as e:
            parquet_names.append(f"ERROR: {e}")

    print("\n[Parquet Samples]:")
    for name in parquet_names:
        print(f"  - {name}")

    # 2. Sample names from LanceDB
    try:
        db = lancedb.connect(LANCEDB_PATH)
        table = db.open_table("omni_semantic_baselines")
        lancedb_names = table.head(10).to_pandas()["track_name"].tolist()
        
        print("\n[LanceDB Samples]:")
        for name in lancedb_names:
            print(f"  - {name}")
    except Exception as e:
        print(f"\n[LanceDB Error]: {e}")

    print("=" * 70)

if __name__ == "__main__":
    diagnose_names()
