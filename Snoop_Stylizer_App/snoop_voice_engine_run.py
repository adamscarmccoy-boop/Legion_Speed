import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

import os
import subprocess
import librosa
import soundfile as sf
import numpy as np
import torch
import warnings
warnings.filterwarnings('ignore')

# 1. YT-DLP INGESTION (USING YTSEARCH TO AVOID BROKEN URLS)
def download_clip(query, output_name, duration="00:00:15"):
    print(f"Downloading {output_name} via search: '{query}'...")
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-f", "bestaudio[ext=m4a]",
        "--match-filter", "!is_live",
        "--download-sections", f"*00:01:30-00:01:45", # Rip 15 seconds from the middle of the video
        "-o", output_name + ".m4a",
        f"ytsearch1:{query}"
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

for f in ["snoop1.m4a", "snoop2.m4a", "snoop3.m4a", "instructor_input.m4a"]:
    if os.path.exists(f): os.remove(f)

# Download 3 Snoop Dogg Interviews (Raw Vocals)
download_clip("snoop dogg breakfast club interview", "snoop1")
download_clip("snoop dogg howard stern interview", "snoop2")
download_clip("snoop dogg jimmy kimmel interview", "snoop3")

# Download 1 Medical Instructor (Input)
download_clip("medical instructor cardiovascular lecture", "instructor_input")

print("✅ Data Ingestion Complete!")

# 2. EXTRACT DSP FOOTPRINT
def extract_dsp_footprint(filepath):
    # Try m4a or wav
    if os.path.exists(filepath + ".m4a"):
        y, sr = librosa.load(filepath + ".m4a", sr=22050)
    elif os.path.exists(filepath + ".wav"):
        y, sr = librosa.load(filepath + ".wav", sr=22050)
    else:
        print(f"File {filepath} not found!")
        return 100.0, np.zeros(13), np.zeros(1024), 22050
    
    # Pitch
    f0, voiced_flag, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
    valid_f0 = f0[voiced_flag]
    mean_pitch = np.median(valid_f0) if len(valid_f0) > 0 else 100.0
    
    # Formants / MFCCs
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mean_mfccs = np.mean(mfccs, axis=1)
    
    return mean_pitch, mean_mfccs, y, sr

# Average the Snoop Targets
snoop_pitches = []
snoop_mfccs_list = []
for f in ["snoop1", "snoop2", "snoop3"]:
    p, m, _, _ = extract_dsp_footprint(f)
    snoop_pitches.append(p)
    snoop_mfccs_list.append(m)

snoop_pitch = np.mean(snoop_pitches)
snoop_mfcc = np.mean(snoop_mfccs_list, axis=0)

instructor_pitch, instructor_mfcc, instructor_y, sr = extract_dsp_footprint("instructor_input")

print(f"🎤 Instructor Pitch: {instructor_pitch:.1f} Hz")
print(f"🌿 Snoop Averaged Pitch: {snoop_pitch:.1f} Hz")

pitch_shift_ratio = snoop_pitch / instructor_pitch
semitones_shift = 12 * np.log2(pitch_shift_ratio)
print(f"\\n➡️ Required Math Shift: {semitones_shift:.2f} semitones.")

# 3. THE PYTORCH WEIGHT GENERATOR
delta_mfcc = torch.tensor(snoop_mfcc - instructor_mfcc, dtype=torch.float32)

print("🧠 PyTorch Sovereign Weight Matrix Calculated:")
print(delta_mfcc)
torch.save(delta_mfcc, 'snoop_dna.pt')
torch.save(torch.tensor([semitones_shift], dtype=torch.float32), 'snoop_pitch_delta.pt')

print("✅ Saved to snoop_dna.pt and snoop_pitch_delta.pt")

# 4. PEDALBOARD EXECUTION
from pedalboard import Pedalboard, PitchShift, HighpassFilter, LowpassFilter, Compressor, Delay

shift_amount = float(semitones_shift)
# Bound the shift so we don't destroy the audio if the math is wild
shift_amount = max(-12.0, min(12.0, shift_amount))

snoop_board = Pedalboard([
    Compressor(threshold_db=-15, ratio=3),
    PitchShift(semitones=shift_amount),
    LowpassFilter(cutoff_hz=3500),
    Delay(delay_seconds=0.1, mix=0.1)
])

print("🎛️ Executing C++ Pedalboard DSP...")
processed_y = snoop_board(instructor_y, sample_rate=sr)

sf.write('snoop_output.wav', processed_y, sr)
print("✅ Voice Conversion Complete! Output saved to snoop_output.wav")
