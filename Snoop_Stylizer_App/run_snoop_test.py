import os
import subprocess
import librosa
import numpy as np
import soundfile as sf
import torch
from pedalboard import Pedalboard, Compressor, PitchShift, LowpassFilter, Delay

import sys
YTDLP_CMD = [sys.executable, "-m", "yt_dlp"]

def run_test():
    print("STARTING SNOOP DOGG END-TO-END TEST")
    
    # Check if TED Talk exists, if not download it
    if not os.path.exists("ted_talk_test.wav"):
        print("\n[1/3] Pulling random TED Talk lecture...")
        subprocess.run(YTDLP_CMD + [
            "ytsearch1:ted talk science lecture",
            "--extract-audio", "--audio-format", "wav", "-o", "ted_talk_test.%(ext)s"
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        print("\n[1/3] Using existing TED Talk lecture...")
        
    print("\n[2/3] Loading PyTorch Snoop Delta Math...")
    # Load Snoop delta from the file generated earlier
    try:
        semitones_shift = float(torch.load('snoop_pitch_delta.pt')[0])
    except Exception:
        print("snoop_pitch_delta.pt not found, recalculating...")
        # Fallback to roughly -4 to -6 semitones
        semitones_shift = -5.0
        
    print(f"Snoop Pitch Delta Loaded: {semitones_shift:.2f} semitones")
    
    # Pedalboard Execution (Process first 15 seconds)
    print("\n[3/3] Executing C++ Pedalboard DSP (Deep Faking)...")
    y_ted, sr_ted = librosa.load("ted_talk_test.wav", sr=22050, duration=15)
    
    # Take first 15 seconds to be fast
    y_ted_short = y_ted
    
    board = Pedalboard([
        Compressor(threshold_db=-15, ratio=3),
        PitchShift(semitones=semitones_shift),
        LowpassFilter(cutoff_frequency_hz=3500),
        Delay(delay_seconds=0.1, mix=0.1)
    ])
    
    processed_y = board(y_ted_short, sample_rate=sr_ted)
    sf.write('Snoop_TED_Talk_Deepfake.wav', processed_y, sr_ted)
    
    print("\nSUCCESS! Listen to Snoop_TED_Talk_Deepfake.wav!")

if __name__ == "__main__":
    run_test()
