import os
import json
import numpy as np
import librosa

DOWNLOADS_DIR = r"C:\Users\adams\Downloads"
TRACKS = ["feed this desire", "jumpy jumpy"]

def extract_metrics(file_path):
    y, sr = librosa.load(file_path, sr=22050, mono=True)
    
    # Calculate RMS per second
    hop_length = sr  # 1 second windows
    rms = librosa.feature.rms(y=y, frame_length=sr, hop_length=hop_length)[0]
    rms_db = 20 * np.log10(np.maximum(1e-9, rms))
    
    # Calculate crest factor per second
    peaks = []
    for i in range(0, len(y), hop_length):
        chunk = y[i:i+hop_length]
        if len(chunk) == 0: continue
        peak = np.max(np.abs(chunk))
        peaks.append(peak)
    
    peaks = np.array(peaks[:len(rms)])
    crest_factor = peaks / np.maximum(1e-9, rms)
    
    return {
        "rms_db": np.round(rms_db, 2).tolist(),
        "crest_factor": np.round(crest_factor, 2).tolist()
    }

results = {}

for track in TRACKS:
    orig_path = os.path.join(DOWNLOADS_DIR, f"{track}.wav")
    mastered_path = os.path.join(DOWNLOADS_DIR, f"{track}_DYNAMIC_MASTERED.wav")
    
    if os.path.exists(orig_path) and os.path.exists(mastered_path):
        orig_metrics = extract_metrics(orig_path)
        mastered_metrics = extract_metrics(mastered_path)
        
        results[track] = {
            "original": orig_metrics,
            "mastered": mastered_metrics
        }
    else:
        print(f"Missing files for {track}")

with open(r"c:\WEB CASE STUDY\scratch\audio_metrics.json", "w") as f:
    json.dump(results, f)

print("Metrics successfully extracted to audio_metrics.json")
