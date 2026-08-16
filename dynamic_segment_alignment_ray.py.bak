import os
import sys
import re
import json
import time
import numpy as np
import pandas as pd
import lancedb
import ray
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import euclidean_distances

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


# Ensure standard output is UTF-8 to prevent console encode crashes
sys.stdout.reconfigure(encoding='utf-8')

LANCEDB_PATH = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
TABLE_NAME = "omni_semantic_baselines"

print("=================================================================")
print("  RAY-PARALLELIZED DYNAMIC DSP AUDIO SEGMENT ALIGNMENT")
print("=================================================================")

# 1. Connect to LanceDB
if not os.path.exists(LANCEDB_PATH):
    print(f"Error: LanceDB path does not exist at {LANCEDB_PATH}")
    sys.exit(1)

db = lancedb.connect(LANCEDB_PATH)
try:
    tbl = db.open_table(TABLE_NAME)
except Exception as e:
    print(f"Error opening table '{TABLE_NAME}': {e}")
    sys.exit(1)

df = tbl.to_pandas()

# Filter for Chris Lake and Sam Shure
df_base = df[df['track_name'].str.contains("Somebody (2024)", case=False, regex=False, na=False)].copy()
df_targ = df[df['track_name'].str.contains("Shine", case=False, regex=False, na=False)].copy()

if df_base.empty or df_targ.empty:
    print("Error: Could not find segments for one of the tracks.")
    sys.exit(1)

# Helper function to sort segments by index extracted from their name
def sort_segments(track_df):
    track_df['seg_idx'] = track_df['segment_name'].str.extract(r'(\d+)').astype(float).fillna(0).astype(int)
    return track_df.sort_values('seg_idx').reset_index(drop=True)

df_base = sort_segments(df_base)
df_targ = sort_segments(df_targ)

# 2. Regex parser to extract ONLY RMS and Crest Factor (to match CPPSectionMetrics)
def parse_text_features(text):
    flat_features = []
    
    # Restrict to strictly 'rms_db' and 'crest_factor' as output by the C++ engine
    for pattern in [
        r"RMS Loudness:\s*([\d\.-]+)",
        r"Crest Factor[^:]*:\s*([\d\.-]+)"
    ]:
        match = re.search(pattern, text)
        val = float(match.group(1)) if match else 0.0
        
        # Convert raw RMS loudness value to dB if it's a linear scale representation
        # (LanceDB contains raw linear RMS values like 0.3408, we map to dB)
        if pattern == r"RMS Loudness:\s*([\d\.-]+)" and val > 0:
            val = 20 * np.log10(val)
            
        flat_features.append(val)
        
    return flat_features

def extract_dsp_features(track_df):
    features = []
    names = []
    for _, row in track_df.iterrows():
        text = row['semantic_text']
        flat = parse_text_features(text)
        features.append(flat)
        names.append(row['segment_name'])
    return np.array(features), names

X_base_raw, names_base = extract_dsp_features(df_base)
X_targ_raw, names_targ = extract_dsp_features(df_targ)

# Standardize the combined feature space to ensure equal weights
scaler = StandardScaler()
X_combined = np.vstack([X_base_raw, X_targ_raw])
scaler.fit(X_combined)

X_base = scaler.transform(X_base_raw)
X_targ = scaler.transform(X_targ_raw)

print(f"\n[BASELINE (Chris Lake)]: Somebody (2024) ({len(X_base)} segments)")
print(f"[TARGET (Sam Shure)]:   Shine ({len(X_targ)} segments)")

# 3. Ray remote task for parallel segment-level comparisons
@ray.remote
def align_single_segment_ray(targ_idx, targ_vec, X_base, names_base, threshold=85.0):
    best_align = -999.0
    best_base_name = ""
    
    # Compare this target segment against all reference segments in parallel
    for j in range(len(X_base)):
        base_vec = X_base[j].reshape(1, -1)
        dist = float(euclidean_distances(targ_vec.reshape(1, -1), base_vec)[0][0])
        # Scale to 0-100% alignment score
        alignment = float(np.clip(100 - (dist * 15), 0, 100))
        if alignment > best_align:
            best_align = alignment
            best_base_name = names_base[j]
            
    status = "passed" if best_align >= threshold else "fallback"
    
    return {
        "targ_idx": targ_idx,
        "matched_base_segment": best_base_name,
        "alignment_score": best_align,
        "status": status
    }

# Initialize local Ray cluster
print("\n📡 Launching local Ray cluster...")
ray.init(ignore_reinit_error=True, log_to_driver=False)

start_time = time.perf_counter()

# Launch all segment comparisons in parallel
# Using an 85% threshold check since we are comparing a focused 2D (RMS + Crest) feature space.
ray_tasks = []
for i in range(len(X_targ)):
    task_ref = align_single_segment_ray.remote(i, X_targ[i], X_base, names_base, threshold=85.0)
    ray_tasks.append(task_ref)

# Gather results
results = ray.get(ray_tasks)
results.sort(key=lambda x: x["targ_idx"])

elapsed_ms = (time.perf_counter() - start_time) * 1000
ray.shutdown()

print(f"\n⚡ RAY EXECUTION COMPLETED IN: {elapsed_ms:.2f} ms")
print("\n--- 🧭 DYNAMIC DSP ALIGNMENT WITH FALLBACK GUARD ---")
print(f"{'Target Segment (Shine)':<25} | {'Matched Base (Somebody)':<25} | {'Acoustic Match':<14} | {'Status'}")
print("-" * 84)

passed_count = 0
fallback_count = 0

for r in results:
    targ_name = names_targ[r["targ_idx"]]
    best_base_name = r["matched_base_segment"]
    best_align = r["alignment_score"]
    
    if r["status"] == "passed":
        status_str = "PASSED (Apply Dynamic Multipliers)"
        passed_count += 1
    else:
        status_str = "FAILED (Fallback to Node 0 Target)"
        fallback_count += 1
        
    print(f"{targ_name:<25} | {best_base_name:<25} | {best_align:<12.1f}% | {status_str}")

print("\n=================================================================")
print("                   ALIGNMENT REPORT SUMMARY")
print("=================================================================")
print(f"Total Segments Audited : {len(results)}")
print(f"Dynamic Matches Passed  : {passed_count} ({passed_count / len(results) * 100:.1f}%)")
print(f"Failsafe Fallbacks      : {fallback_count} ({fallback_count / len(results) * 100:.1f}%)")
print("=================================================================")