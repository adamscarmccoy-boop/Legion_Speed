import duckdb
import os

db_paths = [
    r"C:\STUDIES_BACKUP\data\metadata\sonic_core_v2.duckdb",
    r"C:\WEB CASE STUDY\web_intel_sonicdb.duckdb"
]

def find_gguf_in_db(db_path):
    if not os.path.exists(db_path):
        print(f"DB not found: {db_path}")
        return

    print(f"Checking DB: {db_path}")
    try:
        conn = duckdb.connect(db_path, read_only=True)
        tables = conn.execute("SHOW TABLES").fetchall()
        
        for table in tables:
            table_name = table[0]
            print(f"  Scanning table: {table_name}")
            # Search for any column that might contain a path with .gguf
            # We use a generic query to check all columns for the string '.gguf'
            # Since we don't know the columns, we'll try to find columns with 'path' or 'file' in the name first
            cols = conn.execute(f"DESCRIBE {table_name}").fetchall()
            path_cols = [c[0] for c in cols if 'path' in c[0].lower() or 'file' in c[0].lower() or 'name' in c[0].lower()]
            
            for col in path_cols:
                res = conn.execute(f"SELECT {col} FROM {table_name} WHERE {col} LIKE '%.gguf%'").fetchall()
                for row in res:
                    print(f"    FOUND: {row[0]}")
        conn.close()
    except Exception as e:
        print(f"  Error accessing {db_path}: {e}")

if __name__ == "__main__":
    for path in db_paths:
        find_gguf_in_db(path)
