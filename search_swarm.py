import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

import os
import shutil
import numpy as np
import pyarrow as pa
import ray
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import cdist

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


# Reference features for 'E:\DJSUSAN\LEGION\2 Bass.wav'
TARGET_RMS = -24.764841079711914
TARGET_CREST = 5.588803768157959

def main():
    if not ray.is_initialized():
        try:
            ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        except ConnectionError:
            print("Could not connect to existing Ray cluster. Please ensure the Swarm is running.")
            return
    
    try:
        registry = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
    except ValueError:
        print("SwarmKnowledgeRegistry actor not found. Please ensure ray_arrow_swarm.py is running.")
        return

    all_names = []
    all_features = []
    
    summary = ray.get(registry.get_registered_tables_summary.remote())
    
    print("Gathering PyArrow tables from Swarm memory...")
    for table_name in summary.keys():
        try:
            tbl = ray.get(registry.get_table.remote(table_name))
            df = tbl.to_pandas()
            
            # Find RMS column
            if "rms_db" in df.columns:
                rms_col = "rms_db"
            elif "rms" in df.columns:
                rms_col = "rms"
            else:
                continue
                
            if "crest_factor" not in df.columns:
                continue
                
            # Find name/path column
            name_col = None
            for col in ["filepath", "filename", "segment_name", "track_name"]:
                if col in df.columns:
                    name_col = col
                    break
            if not name_col:
                continue
                
            for _, row in df.iterrows():
                r_val = row[rms_col]
                c_val = row["crest_factor"]
                
                # If RMS is linear, convert to dB (matching DSPAlignmentActor logic)
                if rms_col == "rms":
                    try:
                        r_val = float(20 * np.log10(r_val)) if r_val > 1e-9 else -100.0
                    except:
                        continue
                        
                try:
                    all_features.append([float(r_val), float(c_val)])
                    name_val = row[name_col]
                    # Format name with table name prefix
                    all_names.append(f"[{table_name}] {name_val}")
                except:
                    pass
        except Exception as e:
            print(f"Error reading table {table_name}: {e}")
            
    if not all_features:
        print("No valid acoustic features found in any registered Swarm tables.")
        return
        
    X_base = np.array(all_features, dtype=np.float32)
    scaler = StandardScaler()
    X_base_scaled = scaler.fit_transform(X_base)
    
    target_raw = np.array([[TARGET_RMS, TARGET_CREST]], dtype=np.float32)
    target_scaled = scaler.transform(target_raw)
    
    # Calculate euclidean distance (matching DSPAlignmentActor logic)
    dists = cdist(target_scaled, X_base_scaled, metric="euclidean")[0]
    
    # Get top 10 matches
    top_indices = np.argsort(dists)
    
    print("\n========================================================")
    print(f"🎯 Closest Swarm Matches to '2 Bass.wav'")
    print(f"   Target Signature: RMS={TARGET_RMS:.2f} dB, Crest={TARGET_CREST:.2f}")
    print(f"   Total Records Searched: {len(all_features)}")
    print("========================================================\n")
    
    out_dir = r"C:\Users\adams\Downloads\Matched_Samples"
    os.makedirs(out_dir, exist_ok=True)
    
    matches_found = 0
    for idx in top_indices:
        # Skip the exact match itself
        if "2 Bass.wav" in all_names[idx]:
            continue
            
        dist = float(dists[idx])
        # Calculate alignment score (matching DSPAlignmentActor logic)
        score = max(0.0, 100.0 - (dist * 15.0))
        
        match_rms = X_base[idx][0]
        match_crest = X_base[idx][1]
        
        matches_found += 1
        print(f"#{matches_found} Match (Score: {score:.1f}/100)")
        
        full_path = all_names[idx].split('] ')[1]
        print(f"File: {all_names[idx]}")
        print(f"Features: RMS={match_rms:.2f} dB, Crest={match_crest:.2f}")
        
        try:
            if os.path.exists(full_path):
                shutil.copy2(full_path, os.path.join(out_dir, os.path.basename(full_path)))
                print(f"-> Copied to Downloads\\Matched_Samples")
            else:
                print(f"-> WARNING: Source file not found on disk: {full_path}")
        except Exception as e:
            print(f"-> Error copying file: {e}")
            
        print("-" * 50)
        
        if matches_found >= 10:
            break

if __name__ == "__main__":
    main()