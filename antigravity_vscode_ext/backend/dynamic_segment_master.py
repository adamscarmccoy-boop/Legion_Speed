import sys
import os
import numpy as np
import lancedb
from typing import Optional
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import cdist
from scipy import signal
import soundfile as sf # Used implicitly by Pedalboard's AudioFile for reading/writing

from pedalboard import Pedalboard, Compressor, HighpassFilter, Gain, Limiter, Clipping
from pedalboard.io import AudioFile

# Configuration Paths - Completely bundled locally!
LANCEDB_PATH = os.path.join(os.path.dirname(__file__), "lancedb_omni_snowflake_rag")
TABLE_NAME = "omni_semantic_baselines"
BASELINE_TRACK = "Somebody (2024)"
# DOWNLOADS_DIR is a common place for temporary outputs, but best to make it configurable
DOWNLOADS_DIR = r"C:\Users\adams\Downloads" # Default, can be overridden by explicit paths
SEGMENT_SEC = 6.0

def mono_below_frequency(audio, samplerate, cutoff_hz=150.0):
    """
    Converts audio frequencies below a cutoff to mono to prevent phase cancellation.
    Preserves stereo image for higher frequencies.
    """
    # If audio is already mono or has less than 2 channels, return as is.
    if len(audio.shape) < 2 or audio.shape[0] < 2:
        return audio
        
    left = audio[0]
    right = audio[1]
    
    # Mid/Side decomposition
    mid = (left + right) / 2.0
    side = (left - right) / 2.0
    
    # Design high-pass filter for the Side channel to keep only high frequencies in stereo
    nyquist = 0.5 * samplerate
    # Ensure normal_cutoff is within valid range [0, 1]
    normal_cutoff = max(0.01, min(0.99, cutoff_hz / nyquist)) 
    
    # Use 4th order Butterworth filter for a smooth rolloff
    b, a = signal.butter(4, normal_cutoff, btype='high', analog=False)
    
    # Filter the side channel zero-phase using filtfilt to avoid phase distortion
    side_filtered = signal.filtfilt(b, a, side)
    
    # Reconstruct stereo channels
    left_reconstructed = mid + side_filtered
    right_reconstructed = mid - side_filtered
    
    return np.stack([left_reconstructed, right_reconstructed], axis=0)

def dynamic_segment_master(input_filename: str, custom_output_filepath: Optional[str] = None) -> Optional[str]:
    """
    Performs dynamic segment mastering on an audio file by aligning its segments
    to a baseline reference from LanceDB and applying Pedalboard effects.

    Args:
        input_filename: The name or absolute path of the input WAV file.
        custom_output_filepath: Optional. The absolute path for the output mastered file.
                                If None, a default path in DOWNLOADS_DIR is generated.
    Returns:
        The absolute path of the mastered audio file if successful, None otherwise.
    """
    
    input_path = input_filename # Assume input_filename can be an absolute path
    if not os.path.isabs(input_path): # If it's just a filename, prepend DOWNLOADS_DIR
        input_path = os.path.join(DOWNLOADS_DIR, input_filename)

    if custom_output_filepath:
        output_path = custom_output_filepath
    else:
        # Generate default output path
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_filename = f"{base_name}_DYNAMIC_MASTERED.wav"
        output_path = os.path.join(DOWNLOADS_DIR, output_filename)
    
    if not os.path.exists(input_path):
        print(f"❌ Input file not found: {input_path}")
        return None

    print("======================================================================")
    print(f"🚀 INITIATING DYNAMIC SEGMENT MASTERING FOR: {os.path.basename(input_path)}")
    print("======================================================================")

    # 1. Connect to LanceDB & retrieve baseline segments
    print("Connecting to LanceDB...")
    try:
        db = lancedb.connect(LANCEDB_PATH)
        table = db.open_table(TABLE_NAME)
        df_all = table.to_pandas()
    except Exception as e:
        print(f"❌ Failed to connect to LanceDB or open table: {e}")
        return None
    
    # Filter for Chris Lake baseline segments
    df_base = df_all[df_all["track_name"].str.contains(BASELINE_TRACK, case=False, regex=False, na=False)].copy()
    if df_base.empty:
        print(f"❌ Baseline track '{BASELINE_TRACK}' not found in database.")
        return None
        
    print(f"Loaded {len(df_base)} reference baseline segments.")
    
    # Sort reference segments numerically
    df_base["seg_idx"] = df_base["segment_name"].str.extract(r"(\d+)").astype(float).fillna(0).astype(int)
    df_base = df_base.sort_values("seg_idx").reset_index(drop=True)
    
    # Convert linear rms in LanceDB to dB
    def to_db(v):
        return float(20 * np.log10(v)) if v > 1e-9 else -100.0
    
    df_base["rms_db"] = df_base["rms"].apply(to_db)
    
    # Baseline raw features matrix (RMS dB + Crest Factor)
    X_base_raw = df_base[["rms_db", "crest_factor"]].fillna(0.0).values.astype(np.float32)
    names_base = df_base["segment_name"].tolist()

    # 2. Load target track, apply mono sub-bass lock, slice into segments & extract features
    print("Extracting features from target track...")
    target_segments_features = []
    
    try:
        with AudioFile(input_path) as f:
            sr = f.samplerate
            channels = f.num_channels
            total_frames = f.frames
            print(f"Loading {total_frames} frames into memory for Phase Lock...")
            audio = f.read(total_frames)
    except Exception as e:
        print(f"❌ Failed to load audio file {input_path}: {e}")
        return None
        
    # Apply Mono Sub-Bass lock to the entire continuous array to prevent boundary clicks
    print("Applying Mono Phase Lock (<150Hz) to sub-bass...")
    audio_locked = mono_below_frequency(audio, sr, cutoff_hz=150.0)
    
    frames_per_seg = int(SEGMENT_SEC * sr)
    
    for i in range(0, audio_locked.shape[1], frames_per_seg):
        audio_chunk = audio_locked[:, i:i+frames_per_seg]
        if audio_chunk.shape[1] < frames_per_seg // 2: # Don't process very short trailing chunks
            break
        
        # Ensure mono_chunk is 1D array for RMS/peak calculations
        mono_chunk = audio_chunk.mean(axis=0) if channels > 1 else audio_chunk[0]
        
        rms_lin = float(np.sqrt(np.mean(mono_chunk ** 2)))
        rms_db = float(20 * np.log10(rms_lin)) if rms_lin > 1e-9 else -100.0
        peak = float(np.max(np.abs(mono_chunk)))
        crest = float(peak / rms_lin) if rms_lin > 1e-9 else 0.0
        
        target_segments_features.append([rms_db, crest])

    X_targ_raw = np.array(target_segments_features, dtype=np.float32)
    print(f"Extracted {len(X_targ_raw)} segments from target track.")

    if len(X_targ_raw) == 0:
        print("❌ No segments extracted from target track for analysis.")
        return None

    # 3. Fit StandardScaler on combined space
    scaler = StandardScaler()
    combined = np.vstack([X_base_raw, X_targ_raw])
    scaler.fit(combined)
    
    X_base_scaled = scaler.transform(X_base_raw)
    X_targ_scaled = scaler.transform(X_targ_raw)

    # 4. Perform dynamic segment alignment
    print("Aligning segments to baseline reference...")
    aligned_targets = []
    for i in range(len(X_targ_scaled)):
        targ_vec = X_targ_scaled[i].reshape(1, -1)
        dists = cdist(targ_vec, X_base_scaled, metric="euclidean")[0]
        best_idx = int(np.argmin(dists))
        
        # Look up matched baseline physical targets
        target_rms = float(df_base.loc[best_idx, "rms_db"])
        target_crest = float(df_base.loc[best_idx, "crest_factor"])
        
        aligned_targets.append({
            "targ_idx": i,
            "matched_base": names_base[best_idx],
            "target_rms": target_rms,
            "target_crest": target_crest
        })
        print(f"  Segment {i:03d} -> matched {names_base[best_idx]:<30} | Targets: RMS={target_rms:.2f}dB, Crest={target_crest:.2f}")

    # 5. Dynamic block-by-block mastering processing
    print("\nProcessing audio dynamically block-by-block...")
    
    # Initialize the effect nodes with the Two-Stage Peak Control
    hp = HighpassFilter(cutoff_frequency_hz=30.0)
    comp = Compressor(threshold_db=-20.0, ratio=3.0, attack_ms=10.0, release_ms=100.0)
    gain = Gain(gain_db=0.0)
    # Stage 1: Soft clip strays that get blown up by the Gain
    clip = Clipping(threshold_db=-1.0) # threshold in dBFS
    # Stage 2: Final safety brickwall
    lim = Limiter(threshold_db=-0.3) # threshold in dBFS
    
    board = Pedalboard([hp, comp, gain, clip, lim])
    
    try:
        with AudioFile(output_path, 'w', samplerate=sr, num_channels=channels) as outfile:
            seg_idx = 0
            
            for i in range(0, audio_locked.shape[1], frames_per_seg):
                audio_chunk = audio_locked[:, i:i+frames_per_seg]
                if audio_chunk.shape[1] == 0:
                    break
                    
                # Get current segment's target values from the alignment
                if seg_idx < len(aligned_targets):
                    match_info = aligned_targets[seg_idx]
                else:
                    match_info = aligned_targets[-1] # fallback to last match
                    
                target_rms = match_info["target_rms"]
                target_crest = match_info["target_crest"]
                    
                # Analyze the raw chunk to calculate current values
                mono_chunk = audio_chunk.mean(axis=0) if channels > 1 else audio_chunk[0]
                rms_lin = float(np.sqrt(np.mean(mono_chunk ** 2)))
                rms_db = float(20 * np.log10(rms_lin)) if rms_lin > 1e-9 else -100.0
                peak = float(np.max(np.abs(mono_chunk)))
                crest = float(peak / rms_lin) if rms_lin > 1e-9 else 0.0
                
                # Dynamic Compressor update
                if crest > target_crest:
                    # Dynamically compute compression ratio and threshold
                    ratio = max(2.0, min(6.0, 2.0 + (crest - target_crest) * 0.75)) # More aggressive ratio up to 6:1
                    threshold = rms_db - (target_crest - crest + 3.0) # Adjust threshold based on crest difference
                    comp.threshold_db = threshold
                    comp.ratio = ratio
                else:
                    # Minimal compression if dynamics already match
                    comp.threshold_db = 0.0 # Effectively bypass
                    comp.ratio = 1.0 # No compression
                        
                # Dynamic Gain Makeup
                # Adjust gain to hit target RMS
                gain_val = target_rms - rms_db
                # Clamp gain boost to prevent extreme volume spikes and preserve headroom
                gain.gain_db = max(-10.0, min(10.0, gain_val)) # Clamped between -10dB and +10dB
                    
                # Run the chunk through the board with reset=False to preserve envelope states
                mastered_chunk = board(audio_chunk, sample_rate=sr, reset=False)
                    
                # Write to file
                outfile.write(mastered_chunk)
                    
                # Log telemetry
                print(f"⚡ [BLK {seg_idx:03d}] Raw RMS: {rms_db:.2f}dB (Target: {target_rms:.2f}dB) | Gain Boost: {gain.gain_db:+.2f}dB | Comp Ratio: {comp.ratio:.2f}:1")
                    
                seg_idx += 1
        print(f"✅ Dynamic Mastered file successfully saved to:\n   -> {output_path}")
        print(f"======================================================")
        return output_path
    except Exception as e:
        print(f"❌ Error during dynamic block-by-block mastering: {e}")
        return None

if __name__ == "__main__":
    # Test on putting in the work.wav
    # Ensure this file exists in your C:\Users\adams\Downloads directory
    output_path = dynamic_segment_master("putting in the work.wav")
    if output_path:
        print(f"Test mastering completed. Output: {output_path}")
    else:
        print("Test mastering failed.")
