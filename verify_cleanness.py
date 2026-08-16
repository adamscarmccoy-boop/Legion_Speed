import librosa
import numpy as np
import json

def objective_audit(file_path):
    # Load audio
    y, sr = librosa.load(file_path, sr=None)
    
    # 1. SPECTRAL FLATNESS (The Noise Detector)
    # 0.0 = Pure Tone (Clear), 1.0 = White Noise (Static)
    flatness = librosa.feature.spectral_flatness(y=y)
    avg_flatness = float(np.mean(flatness))
    
    # 2. CHROMA ENERGY (The Clarity Detector)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chroma_std = float(np.std(chroma))
    
    # 3. RMS ENERGY
    rms = librosa.feature.rms(y=y)
    avg_rms = float(np.mean(rms))
    
    # 4. CHROMA ANALYSIS (Note distribution)
    # If the signal is clear music, we should see strong energy in specific bins.
    chroma_sum = np.sum(chroma, axis=1)
    normalized_chroma = chroma_sum / (np.sum(chroma_sum) + 1e-9)
    top_note_strength = float(np.max(normalized_chroma))

    # VERDICT LOGIC
    # Clean music usually has Flatness < 0.01 and Note Strength > 0.15
    is_static_present = avg_flatness > 0.03
    is_signal_clear = top_note_strength > 0.12
    
    results = {
        "avg_spectral_flatness": avg_flatness,
        "chroma_distinctness": chroma_std,
        "top_note_strength": top_note_strength,
        "avg_rms_energy": avg_rms,
        "verdict": "CLEAN" if not is_static_present and is_signal_clear else "STILL HAS STATIC",
        "clarity_confidence": float(1.0 - avg_flatness)
    }
    
    print(json.dumps(results, indent=4))
    return results

if __name__ == "__main__":
    objective_audit("sovereign_capture.wav")
