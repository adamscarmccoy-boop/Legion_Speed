import os
import subprocess
import librosa
import soundfile as sf
import numpy as np
import torch
import warnings
import sys
warnings.filterwarnings('ignore')

# Use sys.executable -m yt_dlp for platform independence
YTDLP_CMD = [sys.executable, "-m", "yt_dlp"]

# --- Profile Generation Logic (from snoop_voice_engine.ipynb) ---
def download_clip(query, output_name, duration_segment="*00:01:30-00:01:45"):
    print(f"Downloading {output_name} for '{query}'...")
    cmd = YTDLP_CMD + [
        "-f", "bestaudio[ext=m4a]",
        "--match-filter", "!is_live",
        "--download-sections", duration_segment, # Rip 15 seconds from the middle of the video
        "-o", output_name + ".m4a",
        f"ytsearch1:{query}"
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def extract_dsp_footprint(filepath):
    loaded_filepath = None
    if os.path.exists(filepath + ".m4a"):
        loaded_filepath = filepath + ".m4a"
    elif os.path.exists(filepath + ".wav"):
        loaded_filepath = filepath + ".wav"
    
    if loaded_filepath:
        y, sr = librosa.load(loaded_filepath, sr=22050)
    else:
        print(f"Error: File {filepath} not found for DSP extraction!")
        return 100.0, np.zeros(13), np.zeros(1024), 22050
    
    f0, voiced_flag, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C3'), fmax=librosa.note_to_hz('C6'), sr=sr)
    valid_f0 = f0[voiced_flag]
    mean_pitch = np.median(valid_f0) if len(valid_f0) > 0 else 100.0
    
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mean_mfccs = np.mean(mfccs, axis=1)
    
    return mean_pitch, mean_mfccs, y, sr

def generate_snoop_profile():
    print("\n--- Generating Snoop Dogg Voice Profile ---")
    
    for f in ["snoop1.m4a", "snoop2.m4a", "snoop3.m4a", "base_voice.m4a"]:
        if os.path.exists(f): os.remove(f)

    # Download 3 Snoop Dogg Interviews (Raw Vocals)
    download_clip("snoop dogg breakfast club interview", "snoop1")
    download_clip("snoop dogg howard stern interview", "snoop2")
    download_clip("snoop dogg jimmy kimmel interview", "snoop3")

    # Download 1 Medical Instructor (Input) - Renamed to base_voice for generic use
    download_clip("medical instructor cardiovascular lecture", "base_voice") 

    print("✅ Snoop Profile: Data Ingestion Complete!")

    # Average the Snoop Targets
    snoop_pitches = []
    snoop_mfccs_list = []
    for f in ["snoop1", "snoop2", "snoop3"]:
        p, m, _, _ = extract_dsp_footprint(f)
        snoop_pitches.append(p)
        snoop_mfccs_list.append(m)

    snoop_pitch = np.mean(snoop_pitches)
    snoop_mfcc = np.mean(snoop_mfccs_list, axis=0)

    base_voice_pitch, base_voice_mfcc, _, _ = extract_dsp_footprint("base_voice")

    print(f"🎤 Snoop Profile: Base Voice Pitch: {base_voice_pitch:.1f} Hz")
    print(f"🌿 Snoop Profile: Averaged Snoop Pitch: {snoop_pitch:.1f} Hz")

    pitch_shift_ratio = snoop_pitch / base_voice_pitch
    semitones_shift = 12 * np.log2(pitch_shift_ratio)
    print(f"➡️ Snoop Profile: Required Math Shift: {semitones_shift:.2f} semitones.")

    # Save PyTorch Weights
    delta_mfcc = torch.tensor(snoop_mfcc - base_voice_mfcc, dtype=torch.float32)
    torch.save(delta_mfcc, 'snoop_dna.pt') # Not directly used by app, but good to save
    torch.save(torch.tensor([semitones_shift], dtype=torch.float32), 'Snoop_pitch_delta.pt') # Consistent with app's load_profile

    print("✅ Snoop Profile: Saved 'snoop_dna.pt' and 'Snoop_pitch_delta.pt'")

    # Clean up downloaded files
    for f in ["snoop1.m4a", "snoop2.m4a", "snoop3.m4a", "base_voice.m4a"]:
        if os.path.exists(f): os.remove(f)

if __name__ == "__main__":
    generate_snoop_profile()
