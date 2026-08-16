This is an excellent set of enhancements that moves your audio engineering pipeline into a truly intelligent, data-driven domain. By integrating more sophisticated feature extraction, a persistent vector store, and dynamic control over your `Pedalboard`, you're building a system that can understand and react to audio with unprecedented precision.

Let's build out the clean, production-ready Python code in the style of your existing codebase.

---

### **1. New Module: `enhanced_audio_features.py`**
This module will encapsulate all the new and existing segment-level audio feature extraction logic. It ensures reusability and keeps our main scripts clean.

```python
# C:\WEB CASE STUDY\enhanced_audio_features.py

import numpy as np
import librosa
import pyloudnorm as pln
import soundfile as sf # Used for pyloudnorm's meter to read the data correctly
from typing import Dict, Any, List

# Configuration for feature extraction
FFT_WINDOW_SIZE = 2048 # Common for spectral analysis
HOP_LENGTH      = 512  # For spectral features like centroid, MFCC
N_MFCC          = 128  # Number of MFCC coefficients for embedding
LOUDNESS_GATING = 0.5  # pyloudnorm gating for LRA calculation

def extract_segment_features(audio_chunk: np.ndarray, sr: int, chunk_start_sec: float) -> Dict[str, Any]:
    """
    Extracts a comprehensive set of acoustic features from a given stereo audio chunk.
    Assumes audio_chunk is a (num_channels, num_samples) float array.
    """
    if audio_chunk.shape[1] == 0:
        return {
            "rms_db": -100.0, "crest_factor": 1.0, 
            "lufs_integrated": -80.0, "lra": 0.0,
            "spectral_centroid": 0.0,
            "sub_bass_energy": 0.0, "bass_energy": 0.0, "mid_energy": 0.0, "high_energy": 0.0,
            "mfcc_embedding": [0.0] * N_MFCC
        }

    # Ensure audio is float64 for pyloudnorm processing
    if audio_chunk.dtype != np.float64:
        audio_chunk = audio_chunk.astype(np.float64)

    # Convert to mono for most feature extractions
    mono_chunk = audio_chunk.mean(axis=0) if audio_chunk.shape[0] > 1 else audio_chunk[0]

    # --- 1. RMS & Crest Factor ---
    rms_lin = float(np.sqrt(np.mean(mono_chunk ** 2)))
    rms_db = float(20 * np.log10(rms_lin)) if rms_lin > 1e-9 else -100.0
    peak = float(np.max(np.abs(mono_chunk)))
    crest = float(peak / rms_lin) if rms_lin > 1e-9 else 0.0

    # --- 2. LUFS & LRA Loudness Logging (using pyloudnorm) ---
    meter = pln.Meter(sr, block_size=0.400) # 400 ms block size is standard for LUFS
    
    # pyloudnorm expects (num_samples, num_channels)
    audio_for_loudnorm = audio_chunk.T 

    lufs_integrated = meter.integrated_loudness(audio_for_loudnorm)
    
    # LRA requires a longer segment, may return nan for very short chunks
    try:
        lra = meter.loudness_range(audio_for_loudnorm, gating=LOUDNESS_GATING)
    except ValueError: # e.g., if segment is too short for LRA calculation
        lra = 0.0 # Default to 0 if cannot be calculated
    
    # --- 3. Spectral Centroid (Brightness) ---
    # librosa expects mono, float array
    spectral_centroid = float(np.mean(librosa.feature.spectral_centroid(
        y=mono_chunk, sr=sr, n_fft=FFT_WINDOW_SIZE, hop_length=HOP_LENGTH
    )))

    # --- 4. Frequency Band Energies (Sub-bass, Bass, Mid, High) ---
    # Using STFT for more accurate frequency band division
    S = np.abs(librosa.stft(mono_chunk, n_fft=FFT_WINDOW_SIZE, hop_length=HOP_LENGTH))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=FFT_WINDOW_SIZE)

    # Define standard frequency bands
    sub_bass_energy = float(np.sum(S[(freqs >= 20) & (freqs < 60), :]))
    bass_energy = float(np.sum(S[(freqs >= 60) & (freqs < 250), :]))
    mid_energy = float(np.sum(S[(freqs >= 250) & (freqs < 2000), :]))
    high_energy = float(np.sum(S[freqs >= 2000, :]))
    
    # --- 5. MFCC Embedding (128-dimensional vector) ---
    # Mean of MFCCs over time frames to get a single vector per segment
    mfccs = librosa.feature.mfcc(
        y=mono_chunk, sr=sr, n_mfcc=N_MFCC, n_fft=FFT_WINDOW_SIZE, hop_length=HOP_LENGTH
    )
    mfcc_embedding = mfccs.mean(axis=1).tolist() # Average across time frames

    return {
        "rms_db": rms_db,
        "crest_factor": crest,
        "lufs_integrated": lufs_integrated,
        "lra": lra,
        "spectral_centroid": spectral_centroid,
        "sub_bass_energy": sub_bass_energy,
        "bass_energy": bass_energy,
        "mid_energy": mid_energy,
        "high_energy": high_energy,
        "mfcc_embedding": mfcc_embedding
    }

# Example Usage (for testing this module independently)
if __name__ == "__main__":
    print("--- Testing enhanced_audio_features.py ---")
    # Create a dummy audio file for testing
    dummy_sr = 44100
    dummy_duration = 5 # seconds
    dummy_channels = 2
    dummy_samples = dummy_sr * dummy_duration
    
    # Simple sine wave mix
    t = np.linspace(0, dummy_duration, dummy_samples, endpoint=False)
    # Bass sine wave
    bass = 0.5 * np.sin(2 * np.pi * 100 * t) 
    # High-freq sine wave for testing centroid
    high = 0.3 * np.sin(2 * np.pi * 5000 * t) 
    # Adding some noise to test LRA
    noise = np.random.randn(dummy_samples) * 0.1

    # Stereo mix
    dummy_audio_stereo = np.array([bass + noise, high + noise])
    
    # Save to a temp file (pyloudnorm can load from buffer but it's easier to verify with file)
    temp_file = "temp_dummy_audio.wav"
    sf.write(temp_file, dummy_audio_stereo.T, dummy_sr)
    
    # Load back with soundfile to get correct shape (samples, channels) for pyloudnorm later
    audio_data, sr = sf.read(temp_file, dtype='float64') 
    
    # Reshape to (channels, samples) for our internal processing
    audio_chunk = audio_data.T 

    print(f"Loaded dummy audio: shape={audio_chunk.shape}, SR={sr}")
    
    features = extract_segment_features(audio_chunk, sr, 0.0)
    
    print("\nExtracted Features:")
    for k, v in features.items():
        if k == "mfcc_embedding":
            print(f"  {k}: {len(v)}-dim vector (first 5: {v[:5]})")
        else:
            print(f"  {k}: {v:.2f}")

    os.remove(temp_file)
    print("\n--- Test complete ---")
```

---

### **2. Script for Persistent Segment Ingestion to LanceDB (`ingest_to_lancedb.py`)**

This script will take an input audio file, segment it, extract all the enhanced features using the module above, and store them in your `omni_semantic_baselines` LanceDB table.

```python
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
    TEST_AUDIO_FILE = r"C:\Users\adams\Downloads\putting in the work.wav" 
    
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

```

---

### **3. Enhanced `dynamic_segment_master.py` for Continuous Mastering**

This is where we integrate the new features for alignment and dynamic `Pedalboard` control. We will extend the feature vector for `StandardScaler` and `cdist` to use LUFS, LRA, and Spectral Centroid, and discuss how MFCCs could provide a different type of alignment if needed.

```python
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import time
import numpy as np
import pandas as pd
import lancedb
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import cdist
import soundfile as sf # Used for pyloudnorm's meter and AudioFile

from pedalboard import Pedalboard, Compressor, HighpassFilter, Gain, Limiter
from pedalboard.io import AudioFile

# Import our new feature extraction module
from enhanced_audio_features import extract_segment_features, N_MFCC

# --- Configuration Paths ---
LANCEDB_PATH = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
TABLE_NAME = "omni_semantic_baselines"
BASELINE_TRACK = "Somebody (2024)" # Our reference baseline (Chris Lake)
DOWNLOADS_DIR = r"C:\Users\adams\Downloads"
SEGMENT_SEC = 6.0 # Must be consistent with ingestion for matching

def dynamic_segment_master(input_filename: str, custom_output: str = None, reference_track_name: str = BASELINE_TRACK):
    """
    Dynamically masters an audio track segment-by-segment by aligning its
    acoustic features to a reference baseline in LanceDB.
    Updates Pedalboard parameters on the fly without clicks or phase issues.
    """
    input_path = os.path.join(DOWNLOADS_DIR, input_filename)
    if custom_output:
        output_filename = custom_output
    else:
        output_filename = os.path.splitext(input_filename)[0] + "_DYNAMIC_MASTERED_ENHANCED.wav"
    output_path = os.path.join(DOWNLOADS_DIR, output_filename)
    
    if not os.path.exists(input_path):
        print(f"❌ Input file not found: {input_path}")
        return

    print("======================================================================")
    print(f"🚀 INITIATING ENHANCED DYNAMIC SEGMENT MASTERING FOR: {input_filename}")
    print(f"  Reference Baseline: '{reference_track_name}'")
    print("======================================================================")

    # 1. Connect to LanceDB & retrieve baseline segments (now with more features)
    print("Connecting to LanceDB...")
    db = lancedb.connect(LANCEDB_PATH)
    table = db.open_table(TABLE_NAME)
    df_all = table.to_pandas()
    
    # Filter for the specified baseline track segments
    df_base = df_all[df_all["track_name"].str.contains(reference_track_name, case=False, regex=False, na=False)].copy()
    if df_base.empty:
        print(f"❌ Baseline track '{reference_track_name}' not found in database.")
        print("  Please ingest the baseline track first using lancedb_ingestion.py.")
        return
        
    print(f"Loaded {len(df_base)} reference baseline segments for '{reference_track_name}'.")
    
    # Sort reference segments numerically (assuming segment_idx exists and is reliable)
    df_base = df_base.sort_values("segment_idx").reset_index(drop=True)
    
    # Define the features to use for alignment (Extended Feature Vector)
    # MFCCs could be used for advanced vector search, but for direct cdist with scalar features,
    # it's usually better to use the primary perceptual scalars.
    ALIGNMENT_FEATURES = [
        "rms_db", "crest_factor", "lufs_integrated", "lra", "spectral_centroid",
        "sub_bass_energy", "bass_energy", "mid_energy", "high_energy"
    ]
    
    # Handle potential NaNs in baseline data
    X_base_raw = df_base[ALIGNMENT_FEATURES].fillna(0.0).values.astype(np.float32)
    names_base = df_base["segment_name"].tolist()

    # 2. Load target track, slice into segments & extract ENHANCED features
    print("\nExtracting enhanced features from target track for alignment...")
    target_segments_features_raw = []
    
    # Use AudioFile for consistent reading
    with AudioFile(input_path) as f_read:
        sr = f_read.samplerate
        channels = f_read.num_channels
        frames_per_seg = int(SEGMENT_SEC * sr)
        
        current_frame = 0
        while True:
            audio_chunk = f_read.read(frames_per_seg) # Returns (num_channels, num_samples)
            if audio_chunk.shape[1] < frames_per_seg // 2:
                break
            
            chunk_start_time_sec = current_frame / sr
            extracted_features = extract_segment_features(audio_chunk, sr, chunk_start_time_sec)
            
            # Append only the features used for alignment
            target_segments_features_raw.append([extracted_features[f] for f in ALIGNMENT_FEATURES])
            
            current_frame += audio_chunk.shape[1]

    X_targ_raw = np.array(target_segments_features_raw, dtype=np.float32)
    print(f"Extracted {len(X_targ_raw)} segments from target track.")

    # 3. Fit StandardScaler on combined space for normalized alignment
    scaler = StandardScaler()
    combined = np.vstack([X_base_raw, X_targ_raw])
    scaler.fit(combined)
    
    X_base_scaled = scaler.transform(X_base_raw)
    X_targ_scaled = scaler.transform(X_targ_raw)

    # 4. Perform dynamic segment alignment using Euclidean distance
    print("\nAligning segments to baseline reference (using RMS, Crest, LUFS, LRA, Centroid, Band Energies)...")
    aligned_targets = []
    for i in range(len(X_targ_scaled)):
        targ_vec = X_targ_scaled[i].reshape(1, -1)
        dists = cdist(targ_vec, X_base_scaled, metric="euclidean")[0]
        best_idx = int(np.argmin(dists))
        best_dist = float(dists[best_idx])
        
        # Look up matched baseline physical targets (all features for dynamic control)
        matched_baseline_segment = df_base.loc[best_idx].to_dict()
        
        aligned_targets.append({
            "targ_idx": i,
            "matched_base_name": names_base[best_idx],
            "matched_base_features": matched_baseline_segment # Store all features
        })
        print(f"  Segment {i:03d} -> matched {names_base[best_idx]:<30} | Match Dist: {best_dist:.2f}")

    # 5. Dynamic block-by-block mastering processing
    print("\nProcessing audio dynamically block-by-block with a persistent Pedalboard...")
    
    # Initialize the effect nodes with starting parameters
    hp = HighpassFilter(cutoff_frequency_hz=30.0)
    
    # Compressor initial parameters will be updated dynamically
    comp = Compressor(threshold_db=-20.0, ratio=3.0, attack_ms=10.0, release_ms=100.0)
    
    # Gain initial to 0.0, will be updated dynamically
    gain = Gain(gain_db=0.0)
    
    lim = Limiter(threshold_db=-0.3, release_ms=100.0) # Limiter is usually more static
    
    # Create the Pedalboard instance *outside* the loop (CRITICAL for state preservation)
    board = Pedalboard([hp, comp, gain, lim])
    
    with AudioFile(input_path) as infile:
        sr = infile.samplerate
        channels = infile.num_channels
        total_frames = infile.frames
        frames_per_seg = int(SEGMENT_SEC * sr)
        
        # Open output file in write mode
        with AudioFile(output_path, 'w', samplerate=sr, num_channels=channels) as outfile:
            seg_idx = 0
            current_frame_for_write = 0 # Track position for output file
            
            while current_frame_for_write < total_frames:
                audio_chunk_raw = infile.read(frames_per_seg) # Returns (num_channels, num_samples)
                if audio_chunk_raw.shape[1] == 0:
                    break
                    
                # Get matched baseline features for the current segment
                if seg_idx < len(aligned_targets):
                    match_info = aligned_targets[seg_idx]["matched_base_features"]
                else:
                    match_info = aligned_targets[-1]["matched_base_features"] # fallback to last match
                
                # Extract *target* values from the matched baseline segment
                target_rms_db = float(match_info["rms_db"])
                target_crest = float(match_info["crest_factor"])
                target_lufs = float(match_info["lufs_integrated"])
                
                # Analyze the *current raw audio chunk* to calculate its current values
                # This ensures feedback loop is based on the actual incoming audio
                current_chunk_features = extract_segment_features(audio_chunk_raw, sr, current_frame_for_write / sr)
                current_rms_db = current_chunk_features["rms_db"]
                current_crest = current_chunk_features["crest_factor"]
                current_lufs = current_chunk_features["lufs_integrated"]
                
                # --- Dynamic Compressor Update Logic ---
                # Aim to match target crest factor and a 'tighter' LUFS if needed
                # More aggressive compression if current crest is higher than target
                if current_crest > target_crest * 1.05: # Apply compression if current is much more dynamic
                    # Dynamically compute compression ratio and threshold based on target & current
                    ratio_diff = (current_crest - target_crest) * 0.75 # Scale difference
                    ratio = max(1.5, min(5.0, 2.0 + ratio_diff)) # Min 1.5:1, Max 5:1
                    
                    # Set threshold relative to the target LUFS for pre-compression gain staging
                    threshold = target_lufs - 2.0 # Target -2dB below LUFS
                    
                    comp.threshold_db = threshold
                    comp.ratio = ratio
                    comp.attack_ms = 10.0 # Keep fast attack for transients
                    comp.release_ms = 100.0
                else:
                    # Less aggressive or no compression if dynamics already match or are too low
                    comp.threshold_db = 0.0 # Effectively bypass threshold if no dynamic issue
                    comp.ratio = 1.0        # No ratio
                
                # --- Dynamic Gain Makeup Logic ---
                # Adjust gain to bring the *post-compression* (but pre-limiter) perceived loudness
                # closer to the target LUFS. This is a common practice.
                
                # First, estimate how much gain is needed to hit target LUFS
                # This is a simplification; a more precise feedback loop would run the chunk
                # through compressor and then re-measure LUFS
                gain_val = target_lufs - current_lufs
                
                # Clamp gain boost to prevent extreme volume spikes or cuts
                gain.gain_db = max(-15.0, min(15.0, gain_val))
                
                # Run the chunk through the board with reset=False to preserve envelope states
                # This is CRITICAL for smooth, click-free dynamic processing
                mastered_chunk = board(audio_chunk_raw, sample_rate=sr, reset=False)
                
                # Write the processed chunk to the output file
                outfile.write(mastered_chunk)
                
                # Log telemetry
                print(f"⚡ [BLK {seg_idx:03d}] Raw RMS: {current_rms_db:.2f}dB (Target: {target_rms_db:.2f}dB) | "
                      f"Raw LUFS: {current_lufs:.2f} (Target: {target_lufs:.2f}) | "
                      f"Gain: {gain.gain_db:+.2f}dB | Comp Ratio: {comp.ratio:.1f}:1")
                
                seg_idx += 1
                current_frame_for_write += audio_chunk_raw.shape[1] # Update for next read

    print(f"\n======================================================")
    print(f"✅ Enhanced Dynamic Mastered file successfully saved to:\n   -> {output_path}")
    print(f"======================================================")

if __name__ == "__main__":
    # Test on a sample track
    TEST_INPUT_TRACK = "putting in the work.wav" # Ensure this file exists in C:\Users\adams\Downloads\
    
    if not os.path.exists(os.path.join(DOWNLOADS_DIR, TEST_INPUT_TRACK)):
        print(f"TEST ERROR: Input stereo mix not found at {os.path.join(DOWNLOADS_DIR, TEST_INPUT_TRACK)}. Please update the path.")
        print("Make sure 'Somebody (2024)' is ingested into LanceDB first via lancedb_ingestion.py.")
    else:
        # First, ensure your baseline track (e.g., Chris Lake's "Somebody (2024)") is in LanceDB
        # You'd run `python lancedb_ingestion.py` on that track first.
        # Then, run this dynamic mastering on your target track.
        dynamic_segment_master(TEST_INPUT_TRACK, reference_track_name=BASELINE_TRACK)

```

---

### **Integration Notes and How to Use:**

1.  **Install New Dependencies:**
    Make sure you have all necessary libraries:
    ```bash
    pip install pyloudnorm librosa lancedb pyarrow pandas scikit-learn scipy pedalboard soundfile numpy
    ```

2.  **Save the New Files:**
    *   Save the `enhanced_audio_features.py` content to `C:\WEB CASE STUDY\enhanced_audio_features.py`.
    *   Save the `lancedb_ingestion.py` content to `C:\WEB CASE STUDY\lancedb_ingestion.py`.
    *   Replace your existing `dynamic_segment_master.py` content with the enhanced version above.

3.  **Ingest Your Baseline Track:**
    Before you can master your own tracks dynamically, you need to populate your LanceDB with data from a reference track (like Chris Lake's "Somebody (2024)").
    *   Make sure you have `Somebody (2024).mp3` (or `.wav`) in your `C:\Users\adams\Downloads` folder.
    *   Edit `lancedb_ingestion.py`'s `TEST_AUDIO_FILE` to point to `Somebody (2024).mp3` (or `.wav`).
    *   Run it:
        ```powershell
        & "C:\WEB CASE STUDY\.venv\Scripts\python.exe" C:\WEB CASE STUDY\lancedb_ingestion.py
        ```
    This will extract features for each 6-second segment of the Chris Lake track and store them in your `omni_semantic_baselines` LanceDB table.

4.  **Run the Enhanced Dynamic Mastering:**
    Now, you can master your own track (`putting in the work.wav` in this example) against the newly ingested Chris Lake baseline.
    *   Ensure `putting in the work.wav` is in `C:\Users\adams\Downloads`.
    *   Run the enhanced `dynamic_segment_master.py`:
        ```powershell
        & "C:\WEB CASE STUDY\.venv\Scripts\python.exe" C:\WEB CASE STUDY\dynamic_segment_master.py
        ```
    This will output `putting in the work_DYNAMIC_MASTERED_ENHANCED.wav` to your Downloads folder, with dynamic adjustments based on the Chris Lake reference.

---

### **How These Enhancements Address Your Requirements:**

1.  **LUFS & LRA Loudness Logging:**
    *   Integrated into `enhanced_audio_features.py` using `pyloudnorm.Meter`.
    *   These values (`lufs_integrated`, `lra`) are now stored in LanceDB and used as part of the alignment feature vector in `dynamic_segment_master.py`.
    *   The dynamic gain adjustment in `dynamic_segment_master.py` specifically uses `target_lufs - current_lufs` for more accurate loudness matching.

2.  **Spectral Centroid Brightness:**
    *   Integrated into `enhanced_audio_features.py` using `librosa.feature.spectral_centroid`.
    *   `spectral_centroid` is stored in LanceDB and also included in the alignment feature vector, allowing the system to match the *brightness profile* of your target track to the reference.

3.  **Persistent Segment Ingestion to LanceDB:**
    *   The `lancedb_ingestion.py` script provides a complete solution.
    *   It uses `enhanced_audio_features.py` to extract all the required metrics (RMS, Crest, LUFS, LRA, Spectral Centroid, Band Energies, and a 128-dimensional MFCC embedding).
    *   These metrics are structured into a Pandas DataFrame and efficiently added to the `omni_semantic_baselines` LanceDB table, with `mfcc_embedding` correctly handled as a vector type.

4.  **Continuous Mastering Integration:**
    *   The `dynamic_segment_master.py` script now uses a much richer `ALIGNMENT_FEATURES` vector (RMS, Crest, LUFS, LRA, Spectral Centroid, Band Energies) to find the closest matching segment in your LanceDB baseline.
    *   The `Pedalboard` is instantiated once outside the loop, and crucial parameters (`comp.threshold_db`, `comp.ratio`, `gain.gain_db`) are updated *per segment* inside the loop.
    *   By continuously passing the audio chunks through `board(audio_chunk_raw, sample_rate=sr, reset=False)`, the compressor and limiter's envelope states are preserved across chunks, eliminating clicks and phase issues inherent in re-initializing effects.
    *   The dynamic logic for compression and gain is more nuanced, reacting to `current_crest` vs. `target_crest` and `current_lufs` vs. `target_lufs` to apply more intelligent, feedback-driven mastering adjustments.

This comprehensive set of changes provides a powerful, data-driven foundation for your dynamic audio mastering workflow.