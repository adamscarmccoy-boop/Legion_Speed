import json
# pyrefly: ignore [missing-import]
import ray

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


# 1. Re-attach to your active running 24-replica cluster
ray.init(address="auto", namespace="legion")

def auto_inspect_and_scan(jsonl_path=r"C:\WEB CASE STUDY\e_gdu_full.json"):
    print("🧬 === AUTO-CORRECTING DATASET SCAN INITIALIZED ===")
    
    # --- PHASE 1: LIVE METADATA KEY INSPECTION ---
    try:
        with open(jsonl_path, "r", encoding="utf-8", errors="ignore") as f:
            first_line = f.readline()
            if not first_line:
                print("❌ File is empty.")
                return
            sample_record = json.loads(first_line)
            print("\n🔍 Detectable Row Matrix Keys Found:")
            print(f"   {list(sample_record.keys())}\n")
    except Exception as e:
        print(f"❌ Failed to parse data header layout: {e}")
        return

    # --- PHASE 2: PARALLELIZED KEY-AGNOSTIC SCAN ---
    @ray.remote
    def parse_jsonl_chunk_flexible(line_batch):
        parsed_records = []
        for line in line_batch:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                
                # Turn all dictionary keys lowercase to instantly bypass capitalization errors
                normalized_record = {k.lower(): v for k, v in record.items()}
                
                # Check all possible tracking key variables automatically
                filename = (
                    normalized_record.get("filename") or 
                    normalized_record.get("name") or 
                    normalized_record.get("fullname") or 
                    normalized_record.get("path", "")
                )
                
                # If the value is an absolute path string, isolate the file name
                isolated_name = filename.split("\\")[-1].split("/")[-1]
                
                if isolated_name.lower().endswith(".ps1"):
                    # Pull size metadata dynamically across multiple potential columns
                    size_bytes = (
                        normalized_record.get("size") or 
                        normalized_record.get("length") or 
                        normalized_record.get("filesize") or 
                        len(str(normalized_record.get("content", "")))
                    )
                    
                    path = (
                        normalized_record.get("path") or 
                        normalized_record.get("filepath") or 
                        normalized_record.get("fullname") or 
                        "Embedded inside matrix"
                    )
                    
                    parsed_records.append({
                        "name": isolated_name,
                        "size_kb": round(float(size_bytes) / 1024, 2),
                        "path": path
                    })
            except Exception:
                pass
        return parsed_records

    # --- PHASE 3: DISTRIBUTE THE 714,545 RECORDS ---
    try:
        with open(jsonl_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"❌ Read failure: {e}")
        return

    chunk_size = max(1, len(lines) // 24)
    line_chunks = [lines[i:i + chunk_size] for i in range(0, len(lines), chunk_size)]
    
    print(f"📡 Distributing {len(lines)} file tracking records into {len(line_chunks)} cluster chunks...")
    
    futures = [parse_jsonl_chunk_flexible.remote(chunk) for chunk in line_chunks]
    worker_outputs = ray.get(futures)
    
    consolidated_inventory = [item for sublist in worker_outputs for item in sublist]

    # Sort results layout by size descending
    sorted_inventory = sorted(consolidated_inventory, key=lambda x: x["size_kb"], reverse=True)
    top_10_scripts = sorted_inventory[:10]

    # --- PHASE 4: ANALYTICS DASHBOARD OUTPUT ---
    if not top_10_scripts:
        print("\n⚠️  Scan finished successfully, but zero files ended with '.ps1'.")
        print("   If your files are stored as plain text, try searching for the script content string instead.")
        return

    print(f"\n🎯 SUCCESS: EXTRACTED TOP {len(top_10_scripts)} POWERSHELL FILES FROM 714,545 MATRIX RECORDS:")
    print(f"{'Index':<5} | {'File Name':<35} | {'Size (KB)':<12} | {'Original Infrastructure Location'}")
    print("-" * 115)
    for idx, item in enumerate(top_10_scripts, 1):
        print(f"{idx:<5} | {item['name']:<35} | {item['size_kb']:<10} KB | {item['path']}")

if __name__ == "__main__":
    auto_inspect_and_scan()