import os
import time
import duckdb
import pyarrow as pa
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Exclude obvious system folders to prevent permission loops and junk
EXCLUDE_DIRS = {'$Recycle.Bin', 'System Volume Information', 'Windows', 'Program Files', 'Program Files (x86)', 'AppData'}

def fast_scan(root_dir):
    """
    Hyper-fast recursive filesystem traversal using os.scandir.
    Returns a list of dictionaries containing file metadata.
    """
    records = []
    
    def _scan(current_path):
        try:
            with os.scandir(current_path) as it:
                for entry in it:
                    if entry.is_symlink():
                        continue
                    if entry.is_dir():
                        if entry.name not in EXCLUDE_DIRS:
                            _scan(entry.path)
                    elif entry.is_file():
                        ext = os.path.splitext(entry.name)[1].lower()
                        # We only care about audio files, project files, and parsed jsons for the Swarm
                        if ext in ['.wav', '.mp3', '.aif', '.flac', '.als', '.adg', '.json', '.xml']:
                            try:
                                stat = entry.stat()
                                records.append({
                                    'filepath': entry.path,
                                    'filename': entry.name,
                                    'size_mb': stat.st_size / (1024 * 1024),
                                    'ext': ext
                                })
                            except OSError:
                                pass
        except PermissionError:
            pass # Skip folders we don't have access to
        except FileNotFoundError:
            pass
            
    print(f"🚀 Scanning {root_dir}...")
    t0 = time.time()
    _scan(root_dir)
    print(f"✅ Indexed {len(records):,} target files in {time.time() - t0:.2f} seconds.")
    return records

def ingest_to_duckdb(records, db_path):
    if not records:
        print("⚠️ No records to ingest.")
        return

    print("💾 Converting to Zero-Copy PyArrow Table...")
    arrow_table = pa.Table.from_pylist(records)
    
    print(f"🔗 Connecting to DuckDB at {db_path}...")
    con = duckdb.connect(db_path)
    
    # Create the computer_fs table if it doesn't exist, otherwise append
    con.execute("""
        CREATE TABLE IF NOT EXISTS computer_fs (
            filepath VARCHAR,
            filename VARCHAR,
            size_mb DOUBLE,
            ext VARCHAR
        )
    """)
    
    print("📥 Inserting records into DuckDB `computer_fs`...")
    con.execute("INSERT INTO computer_fs SELECT filepath, filename, size_mb, ext FROM arrow_table")
    
    # Verification
    count = con.execute("SELECT COUNT(*) FROM computer_fs").fetchone()[0]
    print(f"🎯 Total files now in DuckDB `computer_fs`: {count:,}")
    
    con.close()

if __name__ == "__main__":
    # You can change this to C:\ to scan the whole drive, or a specific folder
    TARGET_DIR = r"C:\WEB CASE STUDY" 
    DB_PATH = r"C:\WEB CASE STUDY\web_intel_sonicdb.duckdb"
    
    # 1. Scan
    records = fast_scan(TARGET_DIR)
    
    # 2. Ingest
    ingest_to_duckdb(records, DB_PATH)
