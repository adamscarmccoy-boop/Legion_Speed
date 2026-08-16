import os
import sys
import duckdb

# --- CONFIGURATION ---
TARGET_DIR = r"C:\WEB CASE STUDY"
DB_PATH = r"C:\STUDIES\data\metadata\sonic_core.duckdb"
DB_FALLBACK_PATH = r"C:\STUDIES\sonic_core.duckdb"

PARQUET_FILES = {
    "code_ui_forest_audit": os.path.join(TARGET_DIR, "code_ui_forest_audit.parquet"),
    "notebook_knowledge_audit": os.path.join(TARGET_DIR, "code_notebook_knowledge_audit.parquet"),
    "knowledge_audit": os.path.join(TARGET_DIR, "code_knowledge_audit.parquet")
}

def verify_files():
    """
    Verifies that the required Parquet files exist in the TARGET_DIR.
    Prints descriptive diagnostics for any missing files.
    """
    print("[*] Stage 1: Verifying Parquet Files...")
    all_exist = True
    for view_name, path in PARQUET_FILES.items():
        if os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            print(f"  [+] Found '{view_name}' -> {path} ({size_mb:.2f} MB)")
        else:
            print(f"  [-] MISSING: '{view_name}' is not found at: {path}")
            print(f"      -> Why: The Knowledge Actor expects this shard to be mined and placed in the case study folder.")
            all_exist = False
    return all_exist

def create_duckdb_views(db_file):
    """
    Connects to the DuckDB database and registers the Parquet files as views.
    Using views allows zero-copy, real-time querying directly on the Parquet files.
    """
    print(f"\n[*] Stage 2: Registering Views in DuckDB database: {db_file}")
    try:
        # Connect to DuckDB database (or create if it doesn't exist)
        db_dir = os.path.dirname(db_file)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
            
        con = duckdb.connect(db_file)
        
        for view_name, path in PARQUET_FILES.items():
            if os.path.exists(path):
                # Escape backslashes for SQL compatibility
                escaped_path = path.replace("\\", "\\\\")
                query = f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM read_parquet('{escaped_path}');"
                con.execute(query)
                print(f"  [+] Registered View '{view_name}' successfully!")
            else:
                print(f"  [!] Skipped '{view_name}' because the source file was missing.")
                
        # Validate views
        print("\n[*] Stage 3: Validating Registered Views...")
        tables = con.execute("SHOW TABLES;").fetchall()
        print(f"  [+] Active Database Tables/Views: {[t[0] for t in tables]}")
        
        con.close()
        print("\n✅ Success! Parquet-to-Knowledge mapping completed.")
        return True
    except Exception as e:
        print(f"  [-] DuckDB View Registration Failed: {e}", file=sys.stderr)
        return False

def main():
    print("=" * 80)
    print("💎 LEGION SHARD SYNCHRONIZER: PARQUET TO DUCKDB VIEW ENGINE")
    print("=" * 80)
    
    # Check physical paths
    files_ok = verify_files()
    
    # Resolve correct DuckDB path
    active_db = DB_PATH
    if not os.path.exists(os.path.dirname(DB_PATH)):
        if os.path.exists(os.path.dirname(DB_FALLBACK_PATH)):
            active_db = DB_FALLBACK_PATH
        else:
            active_db = "sonic_core.duckdb" # Fallback local database
            
    success = create_duckdb_views(active_db)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
