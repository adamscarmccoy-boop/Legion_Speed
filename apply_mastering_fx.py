import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import json
import soundfile as sf
import numpy as np
import librosa
from pedalboard import Pedalboard, Compressor, HighpassFilter, Gain, Limiter

# Paths
DOWNLOADS_DIR = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\AI_Logs\gpu_outputs"
ASSETS_DIR = r"C:\WEB CASE STUDY\Acoustic-DNA-Audio-Engine\assets"

# Target Sovereign reference bounds (Calibrated to Chris Lake Somebody (2024))
TARGET_RMS = -10.007
TARGET_CREST = 3.632

def dynamic_mastering_processor(input_wav_name):
    input_path = os.path.join(DOWNLOADS_DIR, input_wav_name)
    if not os.path.exists(input_path):
        print(f"[ERROR] Input WAV not found at: {input_path}")
        return None
        
    print(f"\n" + "=" * 50)
    print(f"  SOVEREIGN CONTINUOUS DSP MASTERING: {input_wav_name}")
    print("=" * 50)
    
    # 1. READ RAW PROPERTIES IN FULL STEREO (Preserves Phase Integrity)
    print("Reading raw mix properties (stereo-independent)...")
    y, sr = librosa.load(input_path, sr=None, mono=False)
    
    # Extract raw parameters
    if y.ndim > 1:
        peak = np.max(np.abs(y))
        rms_left = librosa.feature.rms(y=y[0])
        rms_right = librosa.feature.rms(y=y[1])
        avg_rms = (np.mean(rms_left) + np.mean(rms_right)) / 2
    else:
        peak = np.max(np.abs(y))
        avg_rms = np.mean(librosa.feature.rms(y=y))
        
    current_rms_db = 20 * np.log10(avg_rms) if avg_rms > 0 else -100.0
    current_crest = peak / avg_rms if avg_rms > 0 else 0.0
    
    print(f"  - Raw Loudness: {current_rms_db:.2f} dB RMS")
    print(f"  - Raw Crest Factor: {current_crest:.2f}")
    
    # 2. CALCULATE MASTERING DELTAS VS COMMERCIAL TARGETS
    rms_delta = TARGET_RMS - current_rms_db  # how much gain we need to reach target RMS
    crest_delta = TARGET_CREST - current_crest
    
    print(f"\nCalculating DSP adjustments to match targets:")
    print(f"  - Target RMS   : {TARGET_RMS:.2f} dB (Delta: {rms_delta:+.2f} dB)")
    print(f"  - Target Crest : {TARGET_CREST:.2f} (Delta: {crest_delta:+.2f})")
    
    # 3. BUILD STATEFUL PEDALBOARD CHAIN DYNAMICALLY (Gain staging BEFORE Compressor)
    dsp_chain = []
    
    # Clean sub-sonics to prevent headroom choke
    dsp_chain.append(HighpassFilter(cutoff_frequency_hz=30.0))
    
    # Gain boost goes BEFORE the compressor so the compressor glues the gain-makeup!
    target_gain_boost = min(15.0, max(-12.0, rms_delta))
    print(f"  - Adding Gain Boost: {target_gain_boost:+.2f} dB (Gain Staging)")
    dsp_chain.append(Gain(gain_db=target_gain_boost))
    
    # Compressor controls peak-to-average dynamics (transient control)
    if current_crest > TARGET_CREST:
        ratio = max(1.8, min(4.5, 2.0 + (current_crest - TARGET_CREST) * 0.5))
        threshold = TARGET_RMS - 2.5  # Glue dynamic transients
        print(f"  - Adding Compressor (Threshold: {threshold:.1f} dB, Ratio: {ratio:.1f}:1) to glue mix")
        dsp_chain.append(Compressor(threshold_db=threshold, ratio=ratio, attack_ms=10.0, release_ms=100.0))
    else:
        # Subtle glue compressor
        dsp_chain.append(Compressor(threshold_db=-18.0, ratio=1.5, attack_ms=15.0, release_ms=150.0))
        
    # Safe brickwall limiter to prevent any digital clipping (Ceiling at -0.3dB)
    print("  - Adding Lookahead Brickwall Limiter (Ceiling: -0.3 dB) for safe peak levels")
    dsp_chain.append(Limiter(threshold_db=-0.3, release_ms=100.0))
    
    board = Pedalboard(dsp_chain)
    
    # 4. PROCESS AUDIO VIA PEDALBOARD (Reads entire file at once for perfect lookahead limiting)
    output_wav_name = os.path.splitext(input_wav_name)[0] + "_MASTERED.wav"
    output_wav_path = os.path.join(DOWNLOADS_DIR, output_wav_name)
    
    print(f"\nProcessing full track at once for perfect transient lookahead...")
    # Read entire file at once preserving original stereo channels
    y_full, sr_full = sf.read(input_path)
    
    # Process through Pedalboard in one gorgeous, click-free pass
    processed_full = board(y_full, sr_full)
    
    # Write entire file at once
    sf.write(output_wav_path, processed_full, sr_full)
    print(f"🎉 Beautiful Mastered WAV saved to: {output_wav_path}")
    
    # 5. POST-MASTER AUDIT CHECK
    print(f"\nRunning post-master validation audit...")
    y_mst, sr_mst = librosa.load(output_wav_path, sr=None, mono=False)
    
    if y_mst.ndim > 1:
        peak_mst = np.max(np.abs(y_mst))
        rms_mst_l = librosa.feature.rms(y=y_mst[0])
        rms_mst_r = librosa.feature.rms(y=y_mst[1])
        avg_rms_mst = (np.mean(rms_mst_l) + np.mean(rms_mst_r)) / 2
    else:
        peak_mst = np.max(np.abs(y_mst))
        avg_rms_mst = np.mean(librosa.feature.rms(y=y_mst))
        
    rms_db_mst = 20 * np.log10(avg_rms_mst) if avg_rms_mst > 0 else -100.0
    crest_mst = peak_mst / avg_rms_mst if avg_rms_mst > 0 else 0.0
    clipping_samples = np.sum(np.abs(y_mst) >= 0.99)
    
    print("=" * 50)
    print("  POST-MASTER AUDIT RESULTS:")
    print("=" * 50)
    print(f"  - Loudness: {rms_db_mst:.2f} dB RMS (Target: {TARGET_RMS:.2f} dB)")
    print(f"  - Crest Factor: {crest_mst:.2f} (Target: {TARGET_CREST:.2f})")
    print(f"  - Peak Amplitude: {peak_mst:.4f} (Ceiling: -0.3dB)")
    print(f"  - Clipping Samples: {clipping_samples} (Safe Headroom)")
    print(f"  - Verdict: {'PASS - CLEAN & READY' if clipping_samples == 0 else 'WARNING - CLIPPING'}")
    print("=" * 50)
    
    return output_wav_name

def batch_master_raw_files():
    print("\n" + "=" * 80)
    print("  🚀 SOVEREIGN BATCH MASTERING INITIATED — ALIGNING RAW TRACKS TO 90%+")
    print("=" * 80)
    
    # Find all MP3 and WAV files in Downloads folder
    all_files = os.listdir(DOWNLOADS_DIR)
    
    # Exclude files that are already mastered or references
    raw_files = [
        f for f in all_files 
        if f.lower().endswith(('.mp3', '.wav')) 
        and os.path.isfile(os.path.join(DOWNLOADS_DIR, f))
        and not f.lower().endswith(('_dynamic_mastered_enhanced.wav', '_dynamic_mastered.wav', '_mastered.wav', 'mastered mono.wav'))
    ]
    
    if not raw_files:
        print("❌ No raw audio files found in Downloads directory.")
        return
        
    print(f"🔊 Found {len(raw_files)} raw, unmastered tracks to process:")
    for f in raw_files:
        print(f"  - {f}")
        
    mastered_count = 0
    for filename in raw_files:
        try:
            output_name = dynamic_mastering_processor(filename)
            if output_name:
                mastered_count += 1
        except Exception as e:
            print(f"❌ Failed to master {filename}: {str(e)}")
            
    print("\n" + "=" * 80)
    print(f"  🏆 BATCH MASTERING COMPLETED! SUCCESSFULLY MASTERED {mastered_count} TRACKS!")
    print("=" * 80)

if __name__ == "__main__":
    # Run batch mastering on all raw files in Downloads
    batch_master_raw_files()
