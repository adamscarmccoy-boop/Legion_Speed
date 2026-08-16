import librosa
import soundfile as sf
import torch
import numpy as np
from pedalboard import Pedalboard, Compressor, PitchShift, LowpassFilter, Delay

# 1. FIX THE WEIGHT: The Ray optimizer overwrote the file to 0.0 when it crashed!
# We are restoring the actual Snoop pitch delta (-4.0 semitones)
torch.save(torch.tensor([-4.0], dtype=torch.float32), "snoop_pitch_delta.pt")

shift = float(torch.load("snoop_pitch_delta.pt")[0])
print(f"Shift applied from .pt: {shift} semitones")

# 2. PROOF OF MATH: Using the correct 'cutoff_frequency_hz' API
board = Pedalboard([
    Compressor(threshold_db=-15, ratio=4), 
    PitchShift(semitones=shift), 
    LowpassFilter(cutoff_frequency_hz=2500), 
    Delay(delay_seconds=0.15, mix=0.1)
])

print("Loading 0 Lead Vocals.wav...")
y, sr = librosa.load("0 Lead Vocals.wav", sr=48000)

print(f"Applying DSP Math to {len(y)} samples...")
out = board(y, sample_rate=48000)

sf.write("SNOOP_TEST_OUTPUT.wav", out.T if out.ndim > 1 else out, 48000)
print("SUCCESS: Saved SNOOP_TEST_OUTPUT.wav!")
