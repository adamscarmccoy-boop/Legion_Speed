import os
import numpy as np
import soundfile as sf
from scipy.signal import butter, lfilter

# =========================
# PATHS
# =========================
BASE = r"C:\WEB CASE STUDY\Snoop_Stylizer_App\confirm_outputs"

FILES = [
    "output_raw.wav",
    "output_smooth.wav",
    "output_slow.wav"
]

# =========================
# DSP FUNCTIONS
# =========================

def highpass(audio, sr, cutoff=70):
    b, a = butter(2, cutoff / (sr / 2), btype='high')
    return lfilter(b, a, audio)

def compress(audio, threshold=0.2, ratio=4.0):
    abs_audio = np.abs(audio)
    over = abs_audio > threshold

    audio = audio.copy()

    audio[over] = np.sign(audio[over]) * (
        threshold + (abs_audio[over] - threshold) / ratio
    )

    return audio

def normalize_rms(audio, target=0.1):
    rms = np.sqrt(np.mean(audio**2) + 1e-8)
    return audio * (target / rms)

def soft_limiter(audio):
    return np.tanh(audio)

# =========================
# MASTERING CHAIN
# =========================
def master(audio, sr):
    audio = highpass(audio, sr)
    audio = compress(audio)
    audio = normalize_rms(audio)
    audio = soft_limiter(audio)
    return audio

# =========================
# PROCESS FILES
# =========================
print("\n=== MASTERING OUTPUT FILES ===\n")

for fname in FILES:
    in_path = os.path.join(BASE, fname)

    if not os.path.exists(in_path):
        print(f"Skipping missing: {fname}")
        continue

    audio, sr = sf.read(in_path)

    print(f"Processing: {fname}")

    mastered = master(audio, sr)

    out_name = fname.replace(".wav", "_mastered.wav")
    out_path = os.path.join(BASE, out_name)

    sf.write(out_path, mastered, sr)

    print(f"Saved: {out_name}")

print("\n✔ DONE")