import glob, os, duckdb

print("=== CHECKING DUCKDB / DB FILES ===")
db_files = [f for f in glob.glob("**/*", recursive=True) if f.endswith((".duckdb", ".db", ".parquet", ".lance", ".npy", ".npz"))]
total_rows = 0
for f in db_files:
    if f.endswith((".duckdb", ".db")):
        try:
            con = duckdb.connect(f, read_only=True)
            tables = con.execute("SHOW TABLES").fetchall()
            print(f"\n[DuckDB] {f}:")
            for t in tables:
                cnt = con.execute(f'SELECT count(*) FROM "{t[0]}"').fetchone()[0]
                total_rows += cnt
                print(f"  Table '{t[0]}': {cnt:,} records")
            con.close()
        except Exception as e:
            print(f"  Error reading {f}: {e}")
    elif f.endswith(".parquet"):
        try:
            cnt = duckdb.execute(f"SELECT count(*) FROM read_parquet('{f}')").fetchone()[0]
            total_rows += cnt
            print(f"\n[Parquet] {f}: {cnt:,} rows")
        except Exception as e:
            pass

print(f"\nTotal Tabular / Vector DB Record Count: {total_rows:,}")
