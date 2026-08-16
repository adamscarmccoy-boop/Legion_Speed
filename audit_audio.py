import librosa
import numpy as np
import json
import os

def audit_audio_fidelity(file_path):
    if not os.path.exists(file_path):
        return {"error": "File not found"}

    # Load audio
    y, sr = librosa.load(file_path, sr=None)
    
    # 1. PEAK & CLIPPING CHECK
    peak = np.max(np.abs(y))
    clipping_count = np.sum(np.abs(y) >= 0.99)
    
    # 2. NOISE FLOOR & STATIC DETECTION (Spectral Flatness)
    # High flatness (> 0.1) across the whole spectrum usually indicates static/noise
    flatness = librosa.feature.spectral_flatness(y=y)
    avg_flatness = np.mean(flatness)
    
    # 3. HIGH-FREQUENCY ENERGY (Static often lives here)
    # Compare energy above 8kHz to total energy
    S = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)
    high_freq_mask = freqs > 8000
    high_freq_energy = np.sum(S[high_freq_mask, :])
    total_energy = np.sum(S)
    hf_ratio = high_freq_energy / total_energy if total_energy > 0 else 0
    
    # 4. DC OFFSET
    dc_offset = np.mean(y)
    
    # 5. RMS ENERGY (Consistency)
    rms = librosa.feature.rms(y=y)
    avg_rms = np.mean(rms)
    
    audit_results = {
        "filename": file_path,
        "sample_rate": sr,
        "peak_amplitude": float(peak),
        "clipping_samples": int(clipping_count),
        "avg_spectral_flatness": float(avg_flatness),
        "high_frequency_ratio": float(hf_ratio),
        "dc_offset": float(dc_offset),
        "avg_rms_energy": float(avg_rms),
        "verdict": "CLEAN" if avg_flatness < 0.05 and hf_ratio < 0.1 else "NOISY/STATIC"
    }
    
    return audit_results

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No file path provided"}, indent=4))
        sys.exit(1)
    
    target_file = sys.argv[1]
    results = audit_audio_fidelity(target_file)
    print(json.dumps(results, indent=4))
