import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import time
import numpy as np
import pandas as pd
import lancedb
import librosa # Fixed: added missing librosa import!
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import cdist
import soundfile as sf

from pedalboard import Pedalboard, Compressor, HighpassFilter, Gain, Limiter
from pedalboard.io import AudioFile

# Import Essentia WSL/Python Bridge for structural sectioning
from essentia_wsl_bridge import get_structural_audio_analysis
# Import our phase-preserving feature extractor
from audit_and_score_downloads import extract_section_features

# --- Configuration Paths ---
LANCEDB_PATH = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
TABLE_NAME = "omni_semantic_baselines"
BASELINE_TRACK = "Somebody (2024)" # Our reference baseline (Chris Lake)
DOWNLOADS_DIR = r"C:\Users\adams\Downloads"

def dynamic_segment_master(input_filename: str, custom_output: str = None, reference_track_name: str = BASELINE_TRACK):
    """
    Dynamically masters an audio track by slicing it into structural musical sections
    detected by Essentia, aligning each section to a LanceDB reference,
    and updating Pedalboard parameters seamlessly at section boundaries.
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
    print(f"🚀 INITIATING ESSENTIA-SECTIONED DYNAMIC MASTERING FOR: {input_filename}")
    print(f"  Reference Baseline: '{reference_track_name}'")
    print("======================================================================")

    # 1. Connect to LanceDB & retrieve baseline segments
    print("Connecting to LanceDB...")
    db = lancedb.connect(LANCEDB_PATH)
    table = db.open_table(TABLE_NAME)
    df_all = table.to_pandas()
    
    df_base = df_all[df_all["track_name"].str.contains(reference_track_name, case=False, regex=False, na=False)].copy()
    if df_base.empty:
        print(f"❌ Baseline track '{reference_track_name}' not found in database.")
        return
        
    print(f"Loaded {len(df_base)} reference baseline segments for '{reference_track_name}'.")
    
    # Sort reference segments numerically
    df_base["seg_idx"] = df_base["segment_name"].str.extract(r"(\d+)").astype(float).fillna(0).astype(int)
    df_base = df_base.sort_values("seg_idx").reset_index(drop=True)
    
    # Convert linear rms in LanceDB to dB
    if "rms" in df_base.columns and "rms_db" not in df_base.columns:
        df_base["rms_db"] = df_base["rms"].apply(lambda v: float(20 * np.log10(v)) if v > 1e-9 else -100.0)
        
    # Feature vector definition
    ALIGNMENT_FEATURES = ["rms_db", "crest_factor", "sub_bass_energy", "bass_energy", "mid_energy", "high_energy"]
    X_base_raw = df_base[ALIGNMENT_FEATURES].fillna(0.0).values.astype(np.float32)
    names_base = df_base["segment_name"].tolist()

    # 2. Get structural musical boundaries using Essentia
    print("\nRunning structural analysis with Essentia C++...")
    analysis = get_structural_audio_analysis(input_path)
    sections = analysis.get("sections", [])
    
    if not sections:
        print("⚠️ Essentia sectioning returned empty. Falling back to default chunks.")
        return
        
    print(f"Successfully divided target track into {len(sections)} dynamic sections!")

    # 3. Load full stereo target track (mono=False preserves phase!)
    print("\nLoading full stereo track...")
    y, sr = librosa.load(input_path, sr=None, mono=False)
    
    # Extract features for each dynamic musical section
    print("Extracting stereo-independent features for each musical section...")
    target_sections_features = []
    
    for sect in sections:
        start_sec = sect["start_time_sec"]
        end_sec = sect["end_time_sec"]
        
        start_samp = int(start_sec * sr)
        end_samp = int(end_sec * sr)
        
        if y.ndim > 1:
            y_sect = y[:, start_samp:end_samp]
        else:
            y_sect = y[start_samp:end_samp]
            
        sect_feats = extract_section_features(y_sect, sr)
        target_sections_features.append([sect_feats[f] for f in ALIGNMENT_FEATURES])

    X_targ_raw = np.array(target_sections_features, dtype=np.float32)

    # 4. Fit StandardScaler on combined space for normalized alignment
    scaler = StandardScaler()
    combined = np.vstack([X_base_raw, X_targ_raw])
    scaler.fit(combined)
    
    X_base_scaled = scaler.transform(X_base_raw)
    X_targ_scaled = scaler.transform(X_targ_raw)

    # 5. Perform dynamic segment alignment using Euclidean distance
    print("\nAligning sections to reference baseline...")
    aligned_targets = []
    for i in range(len(X_targ_scaled)):
        targ_vec = X_targ_scaled[i].reshape(1, -1)
        dists = cdist(targ_vec, X_base_scaled, metric="euclidean")[0]
        best_idx = int(np.argmin(dists))
        best_dist = float(dists[best_idx])
        
        matched_baseline_segment = df_base.loc[best_idx].to_dict()
        
        aligned_targets.append({
            "targ_idx": i,
            "matched_base_name": names_base[best_idx],
            "matched_base_features": matched_baseline_segment
        })
        print(f"  Section {i+1:02d} ({sections[i]['start_time_sec']:.1f}s - {sections[i]['end_time_sec']:.1f}s) -> "
              f"matched {names_base[best_idx]:<30} | Match Dist: {best_dist:.2f}")

    # 6. Dynamic block-by-block mastering processing
    print("\nProcessing audio dynamically section-by-section...")
    
    # Initialize Pedalboard effect nodes
    hp = HighpassFilter(cutoff_frequency_hz=30.0)
    comp = Compressor(threshold_db=-20.0, ratio=3.0, attack_ms=10.0, release_ms=100.0)
    gain = Gain(gain_db=0.0)
    lim = Limiter(threshold_db=-0.3, release_ms=100.0)
    
    board = Pedalboard([hp, gain, comp, lim])
    
    # Read full audio file for block-processing (sf.read preserves original stereo)
    y_full, sr_full = sf.read(input_path)
    is_stereo = (y_full.ndim > 1)
    
    mastered_full = np.zeros_like(y_full)
    
    for i, sect in enumerate(sections):
        start_sec = sect["start_time_sec"]
        end_sec = sect["end_time_sec"]
        
        start_samp = int(start_sec * sr_full)
        end_samp = int(end_sec * sr_full)
        
        # Extract original chunk
        if is_stereo:
            audio_chunk = y_full[start_samp:end_samp, :]
        else:
            audio_chunk = y_full[start_samp:end_samp]
            
        if len(audio_chunk) == 0:
            continue
            
        # Get matching reference features
        match_info = aligned_targets[i]["matched_base_features"]
        target_rms = float(match_info["rms_db"])
        target_crest = float(match_info["crest_factor"])
        
        # Analyze current raw section features
        if is_stereo:
            # Transpose to (channels, samples) for librosa feature extractor compatibility
            sect_feats = extract_section_features(audio_chunk.T, sr_full)
        else:
            sect_feats = extract_section_features(audio_chunk, sr_full)
            
        current_rms = sect_feats["rms_db"]
        current_crest = sect_feats["crest_factor"]
        
        # --- Upgraded Parameter Mapping for 90% Target Score ---
        # 1. Compressor update (Dynamic glue)
        if current_crest > target_crest * 1.05:
            # Compress more aggressively to hit the commercial target Crest factor
            ratio = max(1.8, min(4.5, 2.0 + (current_crest - target_crest) * 0.75))
            threshold = current_rms - 3.0 # Clamp top transients
            comp.threshold_db = threshold
            comp.ratio = ratio
        else:
            # Minimal compression
            comp.threshold_db = 0.0
            comp.ratio = 1.0
            
        # 2. Gain makeup update (Target Loudness Alignment)
        # Smoothly bridge the gap to match the commercial baseline RMS db exactly
        gain_val = target_rms - current_rms
        gain.gain_db = max(-12.0, min(12.0, gain_val))
        
        # Process this section through Pedalboard with state preservation (reset=False)
        # This keeps the compressor release and limiter lookup click-free and continuous!
        processed_chunk = board(audio_chunk, sample_rate=sr_full, reset=False)
        
        if is_stereo:
            mastered_full[start_samp:end_samp, :] = processed_chunk
        else:
            mastered_full[start_samp:end_samp] = processed_chunk
            
        # Telemetry
        print(f"⚡ [Section {i+1:02d}] Gain Makeup: {gain.gain_db:+.1f}dB | Comp Ratio: {comp.ratio:.1f}:1 (RMS: {current_rms:.1f}dB -> Ref: {target_rms:.1f}dB)")
        
    # Write full mastered audio file
    sf.write(output_path, mastered_full, sr_full)
    
    print(f"\n======================================================")
    print(f"✅ Musically Sectioned Master successfully saved to:\n   -> {output_path}")
    print(f"======================================================")

if __name__ == "__main__":
    # Test on a raw mix
    dynamic_segment_master("GIRL NAME DREAM -  i need that.mp3")
