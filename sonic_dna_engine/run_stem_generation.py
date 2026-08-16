"""  
run_stem_generation.py  
=====================  
Uses full stem folders from E:\OLD ABLETON\ABELTON\HY2ROGEN\bundle house pack\HY2ROGEN - BASS HOUSE TOOLS\HBHT WAV\Bass Loops  
to generate mastered audio via Sonic DNA V5 Neural Master.  

Assumes stem files are named as:  
0 Lead Vocals.wav  
1 Backing Vocals.wav  
2 Drums.wav  
3 Bass.wav  
4 Percussion.wav  
5 Synth.wav  
6 Other.wav  

This script combines stems into a full mix and passes it to the Sonic DNA V5 mastering engine.  
"""  

import sys  
import os  
import time  
import warnings  
import numpy as np  
import soundfile as sf  
import torch  

# Suppress warnings  
warnings.filterwarnings("ignore")  

# Add sonic_dna_engine to path  
sys.path.append(r"C:\WEB CASE STUDY\sonic_dna_engine")  
try:  
    from sonic_dna_batch_master_v5_neural import SonicDNAMaster, process_track, extract_dsp_features  
except ImportError:  
    print("[ERR] Could not import v5 mastering engine.")  
    sys.exit(1)  

# ── Config ─────────────────────────────────────────────────────────────────────  
STEMS_DIR = r"E:\OLD ABLETON\ABELTON\HY2ROGEN\bundle house pack\HY2ROGEN - BASS HOUSE TOOLS\HBHT WAV\Bass Loops"  
TARGET_LUFS = -9.0  
BLOCK_SIZE = 1024  
GLIDE_MS = 150.0  
HIGHPASS_HZ = 30.0  
SUB_BASS_MONO_HZ = 150.0  
LIMITER_CEILING_DB = -0.3  
MODEL_PATH = r"C:\WEB CASE STUDY\sonic_dna_engine\sonic_dna_master_v3.pt"  

# Define expected stem filenames in order  
STEM_NAMES = [  
    "0 Lead Vocals.wav",  
    "1 Backing Vocals.wav",  
    "2 Drums.wav",  
    "3 Bass.wav",  
    "4 Percussion.wav",  
    "5 Synth.wav",  
    "6 Other.wav"  
]  

# ── 1. Load Neural Master Model ────────────────────────────────────────────────  
print(f"[OK] Neural Network Loaded: {MODEL_PATH}")  
model = SonicDNAMaster(MODEL_PATH)  

# ── 2. Find and Validate Stem Folder ───────────────────────────────────────────  
if not os.path.exists(STEMS_DIR):  
    print(f"[ERR] Stem directory not found: {STEMS_DIR}")  
    sys.exit(1)  

# List all directories in STEMS_DIR (each directory is a full stem set)  
stem_sets = [d for d in os.listdir(STEMS_DIR) if os.path.isdir(os.path.join(STEMS_DIR, d))]  

if not stem_sets:  
    print(f"[ERR] No stem sets found in {STEMS_DIR}")  
    sys.exit(1)  

print(f"[OK] Found {len(stem_sets)} stem sets to process.")  

# ── 3. Process Each Stem Set ───────────────────────────────────────────────────  
for stem_set_name in stem_sets:  
    stem_set_path = os.path.join(STEMS_DIR, stem_set_name)  
    print(f"\n[>>] Processing stem set: {stem_set_name}")  

    # Load each stem  
    stems = {}  
    missing_stems = []  
    for stem_name in STEM_NAMES:  
        path = os.path.join(stem_set_path, stem_name)  
        if os.path.exists(path):  
            try:  
                y, sr = sf.read(path, always_2d=True)  
                stems[stem_name] = {"audio": y, "sr": sr}  
            except Exception as e:  
                print(f"[WARN] Failed to load {stem_name}: {e}")  
                missing_stems.append(stem_name)  
        else:  
            missing_stems.append(stem_name)  

    if missing_stems:  
        print(f"[SKIP] Missing stems in {stem_set_name}: {missing_stems}")  
        continue  

    # Verify all stems have same sample rate  
    sample_rates = {stem["sr"] for stem in stems.values()}  
    if len(sample_rates) > 1:  
        print(f"[SKIP] Inconsistent sample rates in {stem_set_name}: {sample_rates}")  
        continue  

    sr = list(sample_rates)[0]  

    # Find the longest stem to determine total length  
    max_length = max(stem["audio"].shape[0] for stem in stems.values())  

    # Pad all stems to match max_length  
    mixed = np.zeros((max_length, 2), dtype=np.float32)  
    for stem_name, data in stems.items():  
        audio = data["audio"]  
        if audio.ndim == 1:  
            audio = np.stack([audio, audio], axis=1)  # Convert mono to stereo  
        elif audio.shape[1] == 1:  
            audio = np.concatenate([audio, audio], axis=1)  # Convert mono to stereo  
        
        # Pad or trim to max_length  
        if audio.shape[0] < max_length:  
            pad = max_length - audio.shape[0]  
            audio = np.pad(audio, ((0, pad), (0, 0)), mode='constant')  
        elif audio.shape[0] > max_length:  
            audio = audio[:max_length]  

        mixed += audio  

    # Normalize mixed signal to prevent clipping  
    peak = np.max(np.abs(mixed))  
    if peak > 0.99:  
        mixed = mixed / peak * 0.99  

    # Save mixed audio as temporary file  
    output_path = os.path.join(stem_set_path, f"{stem_set_name}_FULL_MIX.wav")  
    sf.write(output_path, mixed, sr)  
    print(f"[OK] Full mix saved to: {output_path}")  

    # Master the full mix using Sonic DNA V5 Neural  
    try:  
        process_track(output_path, model)  
        print(f"[SUCCESS] Mastered: {stem_set_name}")  
    except Exception as ex:  
        print(f"[ERR] Mastering failed for {stem_set_name}: {ex}")  

print("\n" + "=" * 70)  
print(" DONE")  
print("=" * 70)