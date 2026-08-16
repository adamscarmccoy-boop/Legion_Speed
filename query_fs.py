import ray
import pandas as pd

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


ray.init(address="auto", namespace="legion")

# Get the registry actor
registry = ray.get_actor("SwarmKnowledgeRegistry")

# Get the table "computer_fs"
try:
    df = ray.get(registry.get_table.remote("computer_fs"))
    print(f"Loaded computer_fs: {len(df)} rows")
    
    # Let's see the columns
    print("Columns:", df.columns.tolist())
    
    # We are looking for a .py file modified around 2026-06-29 16:19:57
    # Assuming there are columns like 'file_path', 'extension', 'modified_time', etc.
    # Convert whatever time column exists to datetime
    time_col = None
    for col in ['modified_time', 'mtime', 'creation_time', 'ctime', 'timestamp']:
        if col in df.columns:
            time_col = col
            break
            
    if time_col:
        # Convert to datetime
        df['dt'] = pd.to_datetime(df[time_col], unit='s' if df[time_col].dtype in ['float64', 'int64'] else None, errors='coerce')
        
        # Filter for .py files
        py_files = df[df['file_path'].str.endswith('.py', na=False)].copy()
        
        # Filter by date 2026-06-29
        py_files_target = py_files[py_files['dt'].dt.date.astype(str) == '2026-06-29'].copy()
        
        print("\nPython files modified on 2026-06-29:")
        for _, row in py_files_target.sort_values('dt').iterrows():
            print(f"{row['dt']} - {row['file_path']}")
    else:
        print("Could not find a time column. Sample row:")
        print(df.iloc[0])
        
except Exception as e:
    print(f"Error: {e}")