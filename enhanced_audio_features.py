# C:\WEB CASE STUDY\enhanced_audio_features.py

import numpy as np
import librosa
import pyloudnorm as pln
import soundfile as sf # Used for pyloudnorm's meter to read the data correctly
from typing import Dict, Any, List

# Configuration for feature extraction
FFT_WINDOW_SIZE = 2048 # Common for spectral analysis
HOP_LENGTH      = 512  # For spectral features like centroid, MFCC
N_MFCC          = 128  # Number of MFCC coefficients for embedding
LOUDNESS_GATING = 0.5  # pyloudnorm gating for LRA calculation

def extract_segment_features(audio_chunk: np.ndarray, sr: int, chunk_start_sec: float) -> Dict[str, Any]:
    """
    Extracts a comprehensive set of acoustic features from a given stereo audio chunk.
    Assumes audio_chunk is a (num_channels, num_samples) float array.
    """
    if audio_chunk.shape[1] == 0:
        return {
            "rms_db": -100.0, "crest_factor": 1.0, 
            "lufs_integrated": -80.0, 
            "spectral_centroid": 0.0,
            "sub_bass_energy": 0.0, "bass_energy": 0.0, "mid_energy": 0.0, "high_energy": 0.0,
            "mfcc_embedding": [0.0] * N_MFCC
        }

    # Ensure audio is float64 for pyloudnorm processing
    if audio_chunk.dtype != np.float64:
        audio_chunk = audio_chunk.astype(np.float64)

    # Convert to mono for most feature extractions
    mono_chunk = audio_chunk.mean(axis=0) if audio_chunk.shape[0] > 1 else audio_chunk[0]

    # --- 1. RMS & Crest Factor ---
    rms_lin = float(np.sqrt(np.mean(mono_chunk ** 2)))
    rms_db = float(20 * np.log10(rms_lin)) if rms_lin > 1e-9 else -100.0
    peak = float(np.max(np.abs(mono_chunk)))
    crest = float(peak / rms_lin) if rms_lin > 1e-9 else 0.0

    # --- 2. LUFS & LRA Loudness Logging (using pyloudnorm) ---
    meter = pln.Meter(sr, block_size=0.400) # 400 ms block size is standard for LUFS
    
    # pyloudnorm expects (num_samples, num_channels)
    audio_for_loudnorm = audio_chunk.T 

    lufs_integrated = meter.integrated_loudness(audio_for_loudnorm)
    

    
    # --- 3. Spectral Centroid (Brightness) ---
    # librosa expects mono, float array
    spectral_centroid = float(np.mean(librosa.feature.spectral_centroid(
        y=mono_chunk, sr=sr, n_fft=FFT_WINDOW_SIZE, hop_length=HOP_LENGTH
    )))

    # --- 4. Frequency Band Energies (Sub-bass, Bass, Mid, High) ---
    # Using STFT for more accurate frequency band division
    S = np.abs(librosa.stft(mono_chunk, n_fft=FFT_WINDOW_SIZE, hop_length=HOP_LENGTH))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=FFT_WINDOW_SIZE)

    # Define standard frequency bands
    sub_bass_energy = float(np.sum(S[(freqs >= 20) & (freqs < 60), :]))
    bass_energy = float(np.sum(S[(freqs >= 60) & (freqs < 250), :]))
    mid_energy = float(np.sum(S[(freqs >= 250) & (freqs < 2000), :]))
    high_energy = float(np.sum(S[freqs >= 2000, :]))
    
    # --- 5. MFCC Embedding (128-dimensional vector) ---
    # Mean of MFCCs over time frames to get a single vector per segment
    mfccs = librosa.feature.mfcc(
        y=mono_chunk, sr=sr, n_mfcc=N_MFCC, n_fft=FFT_WINDOW_SIZE, hop_length=HOP_LENGTH
    )
    mfcc_embedding = mfccs.mean(axis=1).tolist() # Average across time frames

    return {
        "rms_db": rms_db,
        "crest_factor": crest,
        "lufs_integrated": lufs_integrated,
        "spectral_centroid": spectral_centroid,
        "sub_bass_energy": sub_bass_energy,
        "bass_energy": bass_energy,
        "mid_energy": mid_energy,
        "high_energy": high_energy,
        "mfcc_embedding": mfcc_embedding
    }

# Example Usage (for testing this module independently)
if __name__ == "__main__":
    print("--- Testing enhanced_audio_features.py ---")
    # Create a dummy audio file for testing
    dummy_sr = 44100
    dummy_duration = 5 # seconds
    dummy_channels = 2
    dummy_samples = dummy_sr * dummy_duration
    
    # Simple sine wave mix
    t = np.linspace(0, dummy_duration, dummy_samples, endpoint=False)
    # Bass sine wave
    bass = 0.5 * np.sin(2 * np.pi * 100 * t) 
    # High-freq sine wave for testing centroid
    high = 0.3 * np.sin(2 * np.pi * 5000 * t) 
    # Adding some noise to test LRA
    noise = np.random.randn(dummy_samples) * 0.1

    # Stereo mix
    dummy_audio_stereo = np.array([bass + noise, high + noise])
    
    # Save to a temp file (pyloudnorm can load from buffer but it's easier to verify with file)
    temp_file = "temp_dummy_audio.wav"
    sf.write(temp_file, dummy_audio_stereo.T, dummy_sr)
    
    # Load back with soundfile to get correct shape (samples, channels) for pyloudnorm later
    audio_data, sr = sf.read(temp_file, dtype='float64') 
    
    # Reshape to (channels, samples) for our internal processing
    audio_chunk = audio_data.T 

    print(f"Loaded dummy audio: shape={audio_chunk.shape}, SR={sr}")
    
    features = extract_segment_features(audio_chunk, sr, 0.0)
    
    print("\nExtracted Features:")
    for k, v in features.items():
        if k == "mfcc_embedding":
            print(f"  {k}: {len(v)}-dim vector (first 5: {v[:5]})")
        else:
            print(f"  {k}: {v:.2f}")

    os.remove(temp_file)
    print("\n--- Test complete ---")