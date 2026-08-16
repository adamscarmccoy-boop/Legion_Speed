# pyrefly: ignore [missing-import]
import polars
import os

# ==============================================================================
# 🔍 INTEGRITY VERIFIER: SCARS ARCHITECTURE
# ==============================================================================
def verify_training_index(parquet_path):
    print(f"[🔍] Verifying index at: {parquet_path}")
    
    if not os.path.exists(parquet_path):
        print(f"[❌ ERROR] File not found: {parquet_path}")
        return

    # 1. Load the index
    try:
        df = pl.read_parquet(parquet_path)
        print(f"[✅] Index loaded successfully. Total rows: {len(df)}")
    except Exception as e:
        print(f"[❌ ERROR] Could not read Parquet file: {e}")
        return

    # 2. Check for required columns (assuming your pipeline created 'path')
    required_cols = ["path"]
    if not all(col in df.columns for col in required_cols):
        print(f"[⚠️ WARNING] Missing columns. Found: {df.columns}")
        return

    # 3. Sample Integrity Check (Verify actual files exist)
    missing_files = 0
    sample_count = min(10, len(df)) # Check first 10 paths
    
    print(f"[⚡] Checking integrity of {sample_count} sample paths...")
    for row in df.head(sample_count).iter_rows(named=True):
        if not os.path.exists(row["path"]):
            print(f"    [❌ MISSING] {row['path']}")
            missing_files += 1
        else:
            print(f"    [✅ FOUND]   {os.path.basename(row['path'])}")

    if missing_files == 0:
        print(f"[🎉 SUCCESS] All sampled paths are valid.")
    else:
        print(f"[❌ FAILED] Found {missing_files} missing files in sample check.")

if __name__ == "__main__":
    # Update this path to where your 'dir /s /b' command found the file
    INDEX_FILE = r"C:\WEB CASE STUDY\training_latents\training_index.parquet"
    verify_training_index(INDEX_FILE)