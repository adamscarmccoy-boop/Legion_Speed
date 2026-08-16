import os
import sys

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


# Disable version check to allow connecting to existing cluster with different Ray version
os.environ["RAY_DISABLE_VERSION_CHECK"] = "1"

try:
    import ray
except ImportError:
    print("Error: Ray is not installed. Please install it by running: pip install ray")
    sys.exit(1)

# Shutdown any existing Ray instance and start a new one to avoid version conflicts
ray.shutdown()
ray.init(ignore_reinit_error=True)

# Define base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define directories to search for parquet files
SEARCH_DIRS = [
    os.path.join(BASE_DIR, "AI_Logs", "parquet_exports"),
    os.path.join(BASE_DIR, "lancedb_data"),  # Sometimes parquet files might be here
    os.path.join(BASE_DIR, "vectors"),       # Another possible location
    BASE_DIR,                                # Root directory
]

# Collect all parquet files from search directories
parquet_files = []
for search_dir in SEARCH_DIRS:
    if os.path.exists(search_dir):
        for f in os.listdir(search_dir):
            if f.endswith('.parquet'):
                full_path = os.path.join(search_dir, f)
                parquet_files.append((f, full_path, search_dir))

if not parquet_files:
    print(f"No parquet files found in search directories:")
    for d in SEARCH_DIRS:
        print(f"  - {d} (exists: {os.path.exists(d)})")
    print("\nPlease check the paths or run the data export process first.")
    ray.shutdown()
    sys.exit(0)

print(f"Found {len(parquet_files)} parquet file(s):")
for filename, filepath, search_dir in parquet_files:
    print(f"  - {filename} (in {os.path.relpath(search_dir, BASE_DIR)})")

print("\n" + "="*60)
print("INSPECTING EACH PARQUET FILE WITH RAY.DATA")
print("="*60)

# Inspect each parquet file
for filename, filepath, search_dir in parquet_files:
    print(f"\n🔍 Inspecting: {filename}")
    print(f"   Location: {os.path.relpath(filepath, BASE_DIR)}")
    print("-" * 50)
    
    try:
        # Read the parquet file with Ray Data
        ds = ray.data.read_parquet(filepath)
        
        # Basic info
        print(f"📊 Number of rows: {ds.count():,}")
        print(f"📋 Schema:")
        for field in ds.schema():
            print(f"   - {field.name}: {field.type}")
        
        # Show first 3 rows as a sample
        print(f"\n👀 First 3 rows:")
        rows = ds.take(3)
        for i, row in enumerate(rows, 1):
            print(f"   Row {i}: {row}")
        
        # Try to compute basic statistics for numeric columns
        print(f"\n📈 Basic statistics (for numeric columns):")
        try:
            # Get statistics using Ray's experimental stats method
            stats = ds.stats()
            # stats is a dictionary; we can print it in a readable way
            for col, col_stats in stats.items():
                if isinstance(col_stats, dict) and col_stats:
                    print(f"   Column '{col}':")
                    for stat_name, stat_value in col_stats.items():
                        if stat_value is not None:
                            print(f"     {stat_name}: {stat_value}")
                else:
                    print(f"   Column '{col}': {col_stats}")
        except Exception as e:
            print(f"   Could not compute statistics: {e}")
            # Fallback: show data types and suggest using SQL-like queries
            print("   Tip: You can use ds.sql() to run queries on this dataset.")
            
    except Exception as e:
        print(f"❌ Error reading {filename}: {e}")
    
    print()

# Shutdown Ray
ray.shutdown()
print("✅ Inspection complete. Ray session shut down.")