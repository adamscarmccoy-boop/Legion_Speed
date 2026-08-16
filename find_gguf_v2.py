import duckdb
import os

db_path = r"C:\WEB CASE STUDY\web_intel_sonicdb.duckdb"

def scan_core_paths():
    if not os.path.exists(db_path):
        print(f"DB not found: {db_path}")
        return

    print(f"Scanning core_paths in {db_path}...")
    try:
        conn = duckdb.connect(db_path, read_only=True)
        # Get all unique paths from the core_paths table
        res = conn.execute("SELECT DISTINCT filepath FROM core_paths").fetchall()
        
        ggufs = [row[0] for row in res if row[0] and row[0].lower().endswith('.gguf')]
        
        if ggufs:
            print(f"FOUND {len(ggufs)} GGUF files:")
            for g in ggufs:
                print(g)
        else:
            print("No .gguf files found in core_paths.")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scan_core_paths()
