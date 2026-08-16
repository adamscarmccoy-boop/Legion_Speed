import os
import subprocess
import librosa
import numpy as np
import torch
import sys
import warnings
warnings.filterwarnings('ignore')

YTDLP_CMD = [sys.executable, "-m", "yt_dlp"]

def generate_dolly_profile():
    print("\n--- Generating Dolly Parton Voice Profile ---")
    
    dolly_audio_path = "dolly_target.wav"
    base_audio_path = "base_voice_dolly_profile.wav"

    # Clean up previous downloads if they exist
    for f in [dolly_audio_path, base_audio_path]:
        if os.path.exists(f): os.remove(f)

    # 1. Download Dolly Audio
    print("[1/3] Pulling Dolly Parton vocals...")
    subprocess.run(YTDLP_CMD + [
        "ytsearch1:dolly parton isolated vocals",
        "--extract-audio", "--audio-format", "wav", "-o", dolly_audio_path
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 2. Download a base speaker audio (e.g., a TED Talk)
    print("[2/3] Pulling random TED Talk lecture for base voice...")
    subprocess.run(YTDLP_CMD + [
        "ytsearch1:ted talk science lecture",
        "--extract-audio", "--audio-format", "wav", "-o", base_audio_path
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 3. Calculate PyTorch Delta
    print("[3/3] Calculating Semantic Delta for Dolly...")
    
    def extract_pitch(filepath, duration=15):
        try:
            y, sr = librosa.load(filepath, sr=22050, duration=duration)
            f0, voiced_flag, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C3'), fmax=librosa.note_to_hz('C6'), sr=sr)
            valid_f0 = f0[voiced_flag]
            return np.median(valid_f0) if len(valid_f0) > 0 else 200.0
        except Exception as e:
            print(f"Error extracting pitch from {filepath}: {e}")
            return 200.0 # Fallback

    dolly_pitch = extract_pitch(dolly_audio_path)
    base_pitch = extract_pitch(base_audio_path)
    
    if base_pitch == 0 or dolly_pitch == 0: # Avoid division by zero
        print("Warning: Could not determine pitch for Dolly profile, using default shift.")
        semitones_shift = 0.0 # Or some safe default
    else:
        shift_ratio = dolly_pitch / base_pitch
        semitones_shift = 12 * np.log2(shift_ratio)
    
    # Save the Dolly weight
    torch.save(torch.tensor([semitones_shift], dtype=torch.float32), 'Dolly_pitch_delta.pt')
    print(f"✅ Dolly Profile: Pitch Delta Calculated: {semitones_shift:.2f} semitones")
    
    # Clean up downloaded files
    for f in [dolly_audio_path, base_audio_path]:
        if os.path.exists(f): os.remove(f)

if __name__ == "__main__":
    generate_dolly_profile()
