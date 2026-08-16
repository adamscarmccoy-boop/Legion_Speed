import urllib.request
import os
import torch
import librosa
import numpy as np
import json
from pedalboard import Pedalboard, Compressor, HighpassFilter, Limiter
from pedalboard.io import AudioFile

URL = "https://upload.wikimedia.org/wikipedia/commons/4/40/Tuning_fork_440_Hz.wav"
OUT_WAV = r"C:\WEB CASE STUDY\mastered_output\online_test_sample.wav"
MASTERED_WAV = r"C:\WEB CASE STUDY\mastered_output\online_sample_MASTERED.wav"

def main():
    print("=" * 60)
    print(" LIVE TEST WITH NEW PUBLIC ONLINE AUDIO ASSET ")
    print("=" * 60)
    
    os.makedirs(os.path.dirname(OUT_WAV), exist_ok=True)
    
    print(f"[*] Fetching online audio from: {URL}")
    urllib.request.urlretrieve(URL, OUT_WAV)
    print(f"[+] Downloaded audio sample -> {OUT_WAV}")
    
    # Extract real audio features
    y, sr = librosa.load(OUT_WAV, sr=None, mono=True)
    beats = librosa.beat.beat_track(y=y, sr=sr)[0]
    tempo = float(beats.flat[0]) if len(beats) > 0 else 120.0
    rms_val = float(np.sqrt(np.mean(y**2)))
    rms_db = float(20 * np.log10(max(rms_val, 1e-9)))
    crest = float(np.max(np.abs(y)) / (rms_val + 1e-9))
    
    print(f"[+] Real DSP Analysis:")
    print(f"    - Sample Rate: {sr} Hz")
    print(f"    - Duration: {len(y)/sr:.2f} seconds")
    print(f"    - RMS Loudness: {rms_db:.2f} dB")
    print(f"    - Crest Factor: {crest:.2f}")

    # Run Pedalboard DSP mastering
    board = Pedalboard([
        Compressor(threshold_db=-16, ratio=3.0),
        HighpassFilter(cutoff_frequency_hz=100),
        Limiter(threshold_db=-0.5)
    ])
    
    with AudioFile(OUT_WAV) as f_in:
        with AudioFile(MASTERED_WAV, 'w', f_in.samplerate, f_in.num_channels) as f_out:
            while f_in.tell() < f_in.frames:
                chunk = f_in.read(f_in.samplerate)
                processed = board(chunk, f_in.samplerate)
                f_out.write(processed)
                
    print(f"[+] Pedalboard DSP Mastering Complete -> {MASTERED_WAV}")
    print("=" * 60)

if __name__ == "__main__":
    main()
