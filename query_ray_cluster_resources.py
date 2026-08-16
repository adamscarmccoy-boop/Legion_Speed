import os
import ray
from ray.util.state import list_actors
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


# Disable version check to avoid environment mismatch errors
os.environ["RAY_DISABLE_VERSION_CHECK"] = "1"

# Connect to the cluster
ray.init(address="auto", namespace="legion", ignore_reinit_error=True)

print("Fetching live actor data from the cluster...")
raw_actors = list_actors()

# Clean the raw API data into flat dictionaries so ray.data can parse it
actor_records = []
for a in raw_actors:
    actor_records.append({
        "actor_id": a.get("actor_id", ""),
        "name": a.get("name", "Unnamed"),
        "class_name": a.get("class_name", ""),
        "state": a.get("state", ""),
        "pid": a.get("pid", 0),
        "namespace": a.get("ray_namespace", "default")
    })

# ==========================================
# RAY DATA PIPELINE
# ==========================================

# 1. INGEST: Convert the raw list into a distributed Ray Dataset
ds = ray.data.from_items(actor_records)

# 2. FILTER: Keep only ALIVE actors using ray.data's native filter
alive_ds = ds.filter(lambda row: row["state"] == "ALIVE")

# 3. TRANSFORM: Use vectorized map_batches (Pandas format) to categorize the data
def categorize_actors(batch: pd.DataFrame) -> pd.DataFrame:
    """
    Categorizes actors based on what we saw in the Dashboard vs the legion namespace.
    """
    def label_type(class_name):
        class_str = str(class_name)
        if "ServeReplica" in class_str:
            return "Serve Deployment (Dashboard)"
        elif "Worker" in class_str or "Engine" in class_str or "Actor" in class_str:
            return "Background AI Model (Legion)"
        else:
            return "System / Other"
            
    batch["category"] = batch["class_name"].apply(label_type)
    return batch

# Apply the transformation across the dataset
processed_ds = alive_ds.map_batches(categorize_actors, batch_format="pandas")

# 4. CONSUME: Print a clean, formatted table of the processed dataset
print("\n--- Processed Ray Data Output (First 15 Rows) ---")
processed_ds.show(limit=15)

# 5. EXPORT: Write the entire processed dataset to disk for analysis
export_path = "C:/WEB CASE STUDY/ray_actors_dataset"
print(f"\nExporting dataset to: {export_path}")
try:
    # This will create a folder with CSV files containing your cluster data
    processed_ds.write_csv(export_path)
    print("✅ Data extraction and export complete!")
except Exception as e:
    print(f"Error during export: {e}")

ray.shutdown()