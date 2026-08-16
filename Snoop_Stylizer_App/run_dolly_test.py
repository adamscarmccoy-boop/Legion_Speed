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
    print("STARTING DOLLY PARTON END-TO-END TEST")
    
    # 1. Download Dolly Audio
    print("\n[1/4] Pulling Dolly Parton vocals...")
    if os.path.exists("dolly_test.wav"): os.remove("dolly_test.wav")
    subprocess.run(YTDLP_CMD + [
        "ytsearch1:dolly parton isolated vocals",
        "--extract-audio", "--audio-format", "wav", "-o", "dolly_test.%(ext)s"
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 2. Download TED Talk Audio
    print("\n[2/4] Pulling random TED Talk lecture...")
    if os.path.exists("ted_talk_test.wav"): os.remove("ted_talk_test.wav")
    subprocess.run(YTDLP_CMD + [
        "ytsearch1:ted talk science lecture",
        "--extract-audio", "--audio-format", "wav", "-o", "ted_talk_test.%(ext)s"
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 3. Calculate PyTorch Delta
    print("\n[3/4] Calculating Semantic Delta...")
    y_dolly, sr_dolly = librosa.load("dolly_test.wav", sr=22050, duration=15)
    f0_dolly, voiced_dolly, _ = librosa.pyin(y_dolly, fmin=65, fmax=2000)
    v_f0_dolly = f0_dolly[voiced_dolly]
    dolly_pitch = np.median(v_f0_dolly) if len(v_f0_dolly) > 0 else 200.0
    
    y_ted, sr_ted = librosa.load("ted_talk_test.wav", sr=22050, duration=15)
    f0_ted, voiced_ted, _ = librosa.pyin(y_ted, fmin=65, fmax=2000)
    v_f0_ted = f0_ted[voiced_ted]
    ted_pitch = np.median(v_f0_ted) if len(v_f0_ted) > 0 else 120.0
    
    shift_ratio = dolly_pitch / ted_pitch
    semitones_shift = 12 * np.log2(shift_ratio)
    
    # Save the true Dolly weight
    torch.save(torch.tensor([semitones_shift], dtype=torch.float32), 'Dolly_pitch_delta.pt')
    print(f"Dolly Pitch Delta Calculated: {semitones_shift:.2f} semitones")
    
    # 4. Pedalboard Execution (Process first 15 seconds)
    print("\n[4/4] Executing C++ Pedalboard DSP (Deep Faking)...")
    # Take first 15 seconds to be fast
    y_ted_short = y_ted[:int(15 * sr_ted)]
    
    board = Pedalboard([
        Compressor(threshold_db=-15, ratio=3),
        PitchShift(semitones=semitones_shift),
        LowpassFilter(cutoff_frequency_hz=3500),
        Delay(delay_seconds=0.1, mix=0.1)
    ])
    
    processed_y = board(y_ted_short, sample_rate=sr_ted)
    sf.write('Dolly_TED_Talk_Deepfake.wav', processed_y, sr_ted)
    
    print("\nSUCCESS! Listen to Dolly_TED_Talk_Deepfake.wav!")

if __name__ == "__main__":
    run_test()
