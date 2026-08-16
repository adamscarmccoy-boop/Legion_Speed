# C:\WEB CASE STUDY\lancedb_ingestion.py

import os
import sys
import time
import numpy as np
import pandas as pd
import lancedb
import pyarrow as pa
from typing import List, Dict, Any

# Ensure UTF-8 output for console (important for Windows)
sys.stdout.reconfigure(encoding='utf-8')

# Import our new feature extraction module
from enhanced_audio_features import extract_segment_features, N_MFCC
from pedalboard.io import AudioFile # Using AudioFile for consistent loading

# --- Configuration ---
LANCEDB_PATH   = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
TABLE_NAME     = "omni_semantic_baselines"
SEGMENT_DURATION_SEC = 6.0 # Standard segment length (consistent with dynamic_segment_master.py)

def ingest_track_segments_to_lancedb(audio_filepath: str, segment_sec: float = SEGMENT_DURATION_SEC):
    """
    Processes an audio track, extracts comprehensive features for each segment,
    and ingests them into the LanceDB 'omni_semantic_baselines' table.
    """
    if not os.path.exists(audio_filepath):
        print(f"❌ Error: Audio file not found at {audio_filepath}")
        return

    track_name = os.path.splitext(os.path.basename(audio_filepath))[0]
    print(f"🚀 Starting ingestion for track: '{track_name}'")
    print(f"  Segment duration: {segment_sec} seconds")
    print(f"  LanceDB Path: {LANCEDB_PATH}")

    all_segment_data: List[Dict[str, Any]] = []
    start_pipeline_time = time.perf_counter()

    with AudioFile(audio_filepath) as f:
        sr = f.samplerate
        frames_per_segment = int(segment_sec * sr)
        total_frames = f.frames

        seg_idx = 0
        current_frame = 0

        while current_frame < total_frames:
            # Read stereo audio chunk
            audio_chunk = f.read(frames_per_segment) # Returns (num_channels, num_samples)
            if audio_chunk.shape[1] < frames_per_segment // 2: # Stop if chunk is too small
                break

            chunk_start_time_sec = current_frame / sr
            chunk_end_time_sec   = (current_frame + audio_chunk.shape[1]) / sr

            # Extract all features using our new module
            features = extract_segment_features(audio_chunk, sr, chunk_start_time_sec)
            
            # Prepare data for LanceDB
            segment_entry = {
                "track_name": track_name,
                "segment_name": f"{track_name}_seg{seg_idx:03d}",
                "segment_idx": seg_idx,
                "start_time_sec": chunk_start_time_sec,
                "end_time_sec": chunk_end_time_sec,
                **features, # Unpack all extracted features
            }
            all_segment_data.append(segment_entry)
            print(f"  Extracted segment {seg_idx:03d} (RMS: {features['rms_db']:.2f}dB, LUFS: {features['lufs_integrated']:.2f})")

            seg_idx += 1
            current_frame += audio_chunk.shape[1] # Move pointer by actual frames read

    if not all_segment_data:
        print("⚠️ No segments extracted. Check input file or segment duration.")
        return

    # Convert to Pandas DataFrame for easier LanceDB ingestion
    df = pd.DataFrame(all_segment_data)
    
    # Ensure MFCCs are stored as FixedSizeList (vector type) for LanceDB
    # If the column already exists and is not a vector, LanceDB might error or require schema migration.
    # For a fresh table, this will ensure correct type.
    df["mfcc_embedding"] = df["mfcc_embedding"].apply(np.array) # Convert list to numpy array for LanceDB vector type

    print(f"\nConnecting to LanceDB at: {LANCEDB_PATH}")
    db = lancedb.connect(LANCEDB_PATH)

    # Define the schema explicitly for LanceDB, ensuring correct vector type for MFCCs
    # LanceDB infers schema from pandas, but being explicit is safer.
    
    # If table exists, append. If not, create with full schema.
    try:
        table = db.open_table(TABLE_NAME)
        print(f"Table '{TABLE_NAME}' exists. Appending {len(df)} new segments.")
        table.add(df)
    except Exception as e:
        print(f"Table '{TABLE_NAME}' not found or schema mismatch. Attempting to create new table.")
        # Define LanceDB schema explicitly including vector for MFCCs
        # LanceDB's add method can handle numpy arrays for vector columns,
        # but defining schema ensures consistency.
        
        # Example schema for LanceDB if we were creating explicitly:
        # from lancedb.pydantic import Vector, LanceModel
        # class SegmentBaseline(LanceModel):
        #     track_name: str
        #     segment_name: str = pa.Field(unique=True) # or just unique_id field
        #     segment_idx: int
        #     start_time_sec: float
        #     end_time_sec: float
        #     rms_db: float
        #     crest_factor: float
        #     lufs_integrated: float
        #     lra: float
        #     spectral_centroid: float
        #     sub_bass_energy: float
        #     bass_energy: float
        #     mid_energy: float
        #     high_energy: float
        #     mfcc_embedding: Vector(N_MFCC) # Define as vector with correct dimension
        # db.create_table(TABLE_NAME, schema=pa.Schema.from_pandas(df.drop(columns=["mfcc_embedding"])).append(pa.field("mfcc_embedding", pa.list_(pa.float32(), N_MFCC))))
        # table = db.create_table(TABLE_NAME, data=df, schema=SegmentBaseline.to_arrow_schema())
        
        # Simpler approach: let LanceDB infer schema from first write if it doesn't exist.
        # This works if the pandas DataFrame columns are already numpy arrays for vectors.
        table = db.create_table(TABLE_NAME, data=df)
        print(f"Created new table '{TABLE_NAME}' with {len(df)} segments.")


    total_time = time.perf_counter() - start_pipeline_time
    print(f"✅ Ingestion complete for '{track_name}'. Total {len(all_segment_data)} segments ingested in {total_time:.2f} seconds.")
    print(f"Current table size: {table.to_pandas().shape[0]} segments.")

# --- Main execution block for testing ---
if __name__ == "__main__":
    # --- IMPORTANT: Update this path to a real WAV file you want to ingest ---
    TEST_AUDIO_FILE = r"C:\Users\adams\Downloads\what a waste-2.wav" 
    
    if not os.path.exists(TEST_AUDIO_FILE):
        print(f"ERROR: Test audio file not found at {TEST_AUDIO_FILE}. Please update path.")
    else:
        ingest_track_segments_to_lancedb(TEST_AUDIO_FILE)
        
        # Verify ingestion by querying the table
        print("\n--- Verifying LanceDB Ingestion ---")
        db = lancedb.connect(LANCEDB_PATH)
        table = db.open_table(TABLE_NAME)
        
        # Example query: Find segments similar to the average MFCC of the last ingested track
        df_all = table.to_pandas()
        track_segments = df_all[df_all["track_name"] == os.path.splitext(os.path.basename(TEST_AUDIO_FILE))[0]]
        if not track_segments.empty:
            avg_mfcc = np.mean(np.array(track_segments["mfcc_embedding"].tolist()), axis=0)
            print(f"Querying for segments similar to the average MFCC of '{track_segments['track_name'].iloc[0]}'...")
            # Query LanceDB using vector search for MFCCs
            results = table.search(avg_mfcc).limit(3).to_pandas()
            print("Top 3 similar segments:")
            print(results[["track_name", "segment_name", "rms_db", "lufs_integrated", "_distance"]].to_string())
        else:
            print("No segments found for the test track after ingestion.")
