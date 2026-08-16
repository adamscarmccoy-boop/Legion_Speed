import os
import sys
import re
import json
import numpy as np
import pandas as pd
import lancedb
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import euclidean_distances

# Ensure standard output is UTF-8 to prevent console encode crashes
sys.stdout.reconfigure(encoding='utf-8')

LANCEDB_PATH = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
TABLE_NAME = "omni_semantic_baselines"

print("=================================================================")
print("       DYNAMIC DSP VECTOR-SPACE AUDIO SEGMENT ALIGNMENT")
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

# 2. Regex parser to extract numerical features from structured text
def parse_text_features(text):
    flat_features = []
    
    # Scalars
    for pattern in [
        r"RMS Loudness:\s*([\d\.-]+)",
        r"Crest Factor[^:]*:\s*([\d\.-]+)",
        r"Sub Bass Energy[^:]*:\s*([\d\.-]+)",
        r"Bass Energy[^:]*:\s*([\d\.-]+)",
        r"Mid Energy[^:]*:\s*([\d\.-]+)",
        r"High Energy[^:]*:\s*([\d\.-]+)",
        r"Spectral Centroid:\s*([\d\.-]+)",
        r"Spectral Bandwidth:\s*([\d\.-]+)",
        r"Spectral Rolloff:\s*([\d\.-]+)",
        r"Spectral Flatness:\s*([\d\.-]+)",
        r"Spectral Contrast:\s*([\d\.-]+)",
        r"Zero Crossing Rate:\s*([\d\.-]+)"
    ]:
        match = re.search(pattern, text)
        val = float(match.group(1)) if match else 0.0
        flat_features.append(val)
        
    # Arrays (Chroma and MFCC)
    arrays = re.findall(r"-\s*\[([\d\.,\s-]+)\]", text)
    
    # First array is Chroma (12 elements)
    if len(arrays) >= 1:
        chroma = [float(x.strip()) for x in arrays[0].split(",") if x.strip()]
        if len(chroma) == 12:
            flat_features.extend(chroma)
        else:
            flat_features.extend([0.0]*12)
    else:
        flat_features.extend([0.0]*12)
        
    # Second array is MFCC (13 elements)
    if len(arrays) >= 2:
        mfcc = [float(x.strip()) for x in arrays[1].split(",") if x.strip()]
        if len(mfcc) == 13:
            flat_features.extend(mfcc)
        else:
            flat_features.extend([0.0]*13)
    else:
        flat_features.extend([0.0]*13)
        
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

# Define physical alignment check
# 100 - dist * 15 threshold. 50% alignment is our threshold limit.
BACKUP_ALIGNMENT_THRESHOLD = 50.0

print("\n--- 🧭 DYNAMIC DSP ALIGNMENT WITH FALLBACK GUARD ---")
print(f"{'Target Segment (Shine)':<25} | {'Matched Base (Somebody)':<25} | {'Acoustic Match':<14} | {'Status'}")
print("-" * 84)

aligned_records = []

for i in range(len(X_targ)):
    targ_vec = X_targ[i].reshape(1, -1)
    targ_name = names_targ[i]
    
    best_align = -999.0
    best_base_idx = -1
    best_base_name = ""
    best_dist = 999.0
    
    # Dynamically find the base segment with the smallest Euclidean distance (best alignment)
    for j in range(len(X_base)):
        base_vec = X_base[j].reshape(1, -1)
        dist = euclidean_distances(targ_vec, base_vec)[0][0]
        alignment = float(np.clip(100 - (dist * 15), 0, 100))
        if alignment > best_align:
            best_align = alignment
            best_dist = dist
            best_base_idx = j
            best_base_name = names_base[j]
            
    # Apply backup check threshold
    if best_align >= BACKUP_ALIGNMENT_THRESHOLD:
        status = "PASSED (Apply Dynamic Multipliers)"
    else:
        status = f"FAILED (Fallback to Node 0 Target)"
        
    print(f"{targ_name:<25} | {best_base_name:<25} | {best_align:<12.1f}% | {status}")
    
    aligned_records.append({
        "target_segment": targ_name,
        "matched_base_segment": best_base_name,
        "alignment_score": best_align,
        "status": "passed" if best_align >= BACKUP_ALIGNMENT_THRESHOLD else "fallback"
    })

passed_count = sum(1 for r in aligned_records if r["status"] == "passed")
fallback_count = sum(1 for r in aligned_records if r["status"] == "fallback")

print("\n=================================================================")
print("                   ALIGNMENT REPORT SUMMARY")
print("=================================================================")
print(f"Total Segments Audited : {len(aligned_records)}")
print(f"Dynamic Matches Passed  : {passed_count} ({passed_count / len(aligned_records) * 100:.1f}%)")
print(f"Failsafe Fallbacks      : {fallback_count} ({fallback_count / len(aligned_records) * 100:.1f}%)")
print("=================================================================")
