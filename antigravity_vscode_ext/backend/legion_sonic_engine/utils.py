import os
import numpy as np
import torch
import torchaudio
import librosa
import pyloudnorm as ln
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ValidationError

# --- Pydantic Models for Audio Analysis and Mastering ---

class SectionMetrics(BaseModel):
    """
    Detailed metrics for an audio segment.
    All energy values (sub_bass_energy, bass_energy, mid_energy, high_energy)
    are scaled by 10000 for better numerical representation as discussed in chat.
    """
    segment_name: str = Field(..., description="Descriptive name for the audio segment (e.g., 'Drop', 'Build').")
    start_time_sec: float = Field(..., ge=0.0, description="Start time of the segment in seconds.")
    end_time_sec: float = Field(..., ge=0.0, description="End time of the segment in seconds.")
    duration_sec: float = Field(..., ge=0.0, description="Duration of the segment in seconds.")
    rms_db: float = Field(..., description="Root Mean Square (RMS) loudness in dBFS.")
    crest_factor: float = Field(..., ge=1.0, description="Ratio of peak to RMS, indicating dynamic range.")
    integrated_lufs: float = Field(..., description="Integrated Loudness Units Full Scale (LUFS) for the segment.")
    loudness_range_lra: float = Field(..., ge=0.0, description="Loudness Range (LRA) for the segment, in LU.")
    sub_bass_energy: float = Field(..., ge=0.0, description="Energy in the sub-bass frequency band (e.g., 20-60Hz).")
    bass_energy: float = Field(..., ge=0.0, description="Energy in the bass frequency band (e.g., 60-250Hz).")
    mid_energy: float = Field(..., ge=0.0, description="Energy in the mid frequency band (e.g., 250-4000Hz).")
    high_energy: float = Field(..., ge=0.0, description="Energy in the high frequency band (e.g., 4000-20000Hz).")
    spectral_centroid: float = Field(..., ge=0.0, description="Weighted mean of the frequencies present in the sound, indicating 'brightness'.")
    mfcc_embedding: List[float] = Field(..., description="128-dimensional MFCC embedding vector for the segment.")
    
    # Optional field to store the matched baseline segment's name
    matched_baseline_segment: Optional[str] = Field(None, description="Name of the baseline segment this segment was matched against.")


class MasterTrackStructuralProfile(BaseModel):
    """
    Comprehensive structural and metric profile for an entire audio track,
    broken down into segments.
    """
    filename: str = Field(..., description="Original filename of the track.")
    original_filepath: str = Field(..., description="Absolute path to the original audio file.")
    total_sections_found: int = Field(..., ge=0, description="Total number of structural sections identified.")
    processing_time_ms: float = Field(..., ge=0.0, description="Time taken to process the track and extract metrics in milliseconds.")
    segment_data: List[SectionMetrics] = Field(..., description="List of detailed metrics for each identified segment.")
    mastering_params_applied: Optional[dict] = Field(None, description="Dictionary of global mastering parameters applied (if any).")


class BaselineTrackProfile(BaseModel):
    """
    Schema for storing a baseline track's structural profile in LanceDB.
    Adds a 'vector' field for similarity search.
    """
    track_name: str = Field(..., description="User-friendly name for the baseline track (e.g., 'Chris Lake - Somebody').")
    original_filepath: str = Field(..., description="Absolute path to the original baseline audio file.")
    vector: List[float] = Field(..., description="Pooled MFCC embedding vector for the entire track, used for track-level similarity.")
    segment_data: List[SectionMetrics] = Field(..., description="List of detailed metrics for each identified segment.")
    # LanceDB requires primary key or index field. We can use track_name for uniqueness
    # though it's not explicitly a LanceDB requirement here, good for logical indexing.
    # A dedicated unique ID might be better for production if track names aren't always unique.


class MasteringJobConfig(BaseModel):
    """
    Configuration for a single mastering job.
    """
    input_filepath: str = Field(..., description="Absolute path to the input audio file for mastering.")
    output_filepath: str = Field(..., description="Absolute path where the mastered audio file will be saved.")
    baseline_track_name: str = Field(..., description="Name of the baseline track in LanceDB to match against.")
    segment_length_sec: float = Field(6.0, gt=0.0, description="Length of segments for dynamic mastering in seconds.")


# --- Helper Functions ---

def ensure_utf8_output():
    """Ensures stdout encoding is UTF-8 for proper emoji/special character display."""
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

def calculate_lufs_and_lra(audio_mono_np: np.ndarray, sr: int, block_size: float = 0.4) -> (float, float):
    """
    Calculates Integrated LUFS and Loudness Range (LRA) using pyloudnorm.
    Args:
        audio_mono_np: Mono audio waveform as a NumPy array (float).
        sr: Sample rate.
        block_size: Window size in seconds for loudness measurement.
    Returns:
        (integrated_lufs, loudness_range_lra)
    """
    try:
        meter = ln.LoudnessMeter(sr, block_size=block_size)
        integrated_lufs = meter.integrated_loudness(audio_mono_np)
        loudness_range_lra = meter.loudness_range(audio_mono_np)
        return float(integrated_lufs), float(loudness_range_lra)
    except Exception as e:
        print(f"⚠️ Error calculating LUFS/LRA: {e}. Falling back to default values.")
        return -23.0, 5.0 # EBU R128 default integrated LUFS, and a typical LRA


def calculate_spectral_centroid(audio_mono_np: np.ndarray, sr: int, n_fft: int = 2048, hop_length: int = 512) -> float:
    """
    Calculates the spectral centroid for a mono audio segment.
    Args:
        audio_mono_np: Mono audio waveform as a NumPy array (float).
        sr: Sample rate.
        n_fft: FFT window size.
        hop_length: Hop length for STFT.
    Returns:
        Mean spectral centroid.
    """
    try:
        # Avoid issues with too short audio chunks for librosa
        if len(audio_mono_np) < n_fft:
            # Pad with zeros if chunk is too short for meaningful STFT
            padded_chunk = np.pad(audio_mono_np, (0, n_fft - len(audio_mono_np)), 'constant')
            centroid = librosa.feature.spectral_centroid(y=padded_chunk, sr=sr, n_fft=n_fft, hop_length=hop_length)
        else:
            centroid = librosa.feature.spectral_centroid(y=audio_mono_np, sr=sr, n_fft=n_fft, hop_length=hop_length)
        return float(np.mean(centroid))
    except Exception as e:
        print(f"⚠️ Error calculating spectral centroid: {e}. Falling back to 2000.0.")
        return 2000.0 # Standard fallback reference


def calculate_mfcc_embedding(audio_mono_np: np.ndarray, sr: int, n_mfcc: int = 128, n_fft: int = 2048, hop_length: int = 512) -> List[float]:
    """
    Calculates MFCCs and returns a pooled embedding vector.
    Pooling is done by taking the mean across time.
    Args:
        audio_mono_np: Mono audio waveform as a NumPy array (float).
        sr: Sample rate.
        n_mfcc: Number of MFCC coefficients.
        n_fft: FFT window size.
        hop_length: Hop length for STFT.
    Returns:
        128-dimensional MFCC embedding vector as a list of floats.
    """
    try:
        # Ensure minimum length for STFT
        if len(audio_mono_np) < n_fft:
            padded_chunk = np.pad(audio_mono_np, (0, n_fft - len(audio_mono_np)), 'constant')
            mfccs = librosa.feature.mfcc(y=padded_chunk, sr=sr, n_mfcc=n_mfcc, n_fft=n_fft, hop_length=hop_length)
        else:
            mfccs = librosa.feature.mfcc(y=audio_mono_np, sr=sr, n_mfcc=n_mfcc, n_fft=n_fft, hop_length=hop_length)
        
        # Take the mean across time frames to get a single vector
        pooled_mfcc = np.mean(mfccs, axis=1)
        # Ensure it's 128-dimensional, pad or truncate if n_mfcc was different
        if len(pooled_mfcc) < n_mfcc:
            pooled_mfcc = np.pad(pooled_mfcc, (0, n_mfcc - len(pooled_mfcc)), 'constant')
        elif len(pooled_mfcc) > n_mfcc:
            pooled_mfcc = pooled_mfcc[:n_mfcc]

        return pooled_mfcc.tolist()
    except Exception as e:
        print(f"⚠️ Error calculating MFCC embedding: {e}. Returning zero vector.")
        return [0.0] * n_mfcc # Return a zero vector on failure


def calculate_sub_bass_energy(mono_chunk_np: np.ndarray, sr: int, chunk_size: int) -> float:
    # A simple approach is to use a low-pass filter to isolate sub-bass,
    # then calculate energy. Here we use a simpler statistical approach based on array mean variance
    # which was referenced in previous interactions. For a production system,
    # a proper band-pass filter would be more accurate.
    # The previous implementation used mean of absolute values across early samples.
    # Let's refine it with some frequency range estimation.
    # This is a proxy for proper frequency analysis.
    try:
        # For a truly accurate frequency-band energy, we'd need STFT and filter banks.
        # Given the previous context, we use a heuristic based on array variance for "energy".
        # This is not frequency-accurate in a DSP sense but provides a relative measure.
        # A more robust approach would involve scipy.signal.butter and scipy.signal.lfilter.
        
        # As per chat, "sub_bass_energy = float(np.mean(np.abs(chunk_np[:, :int(chunk_size * 0.05)]))) * 10000"
        # Let's simulate a rough bandpass for 20-60Hz by looking at lower frequency content
        # of the spectrum if possible, or use a heuristic.
        # For now, sticking to the heuristic from previous chat to avoid deep DSP diversion.
        
        # Fallback to the heuristic for consistency with previous discussion
        # This scales energy to a more readable number as per previous chat
        return float(np.mean(np.abs(mono_chunk_np[:min(chunk_size, sr // 2)]))) * 10000 
    except Exception as e:
        print(f"⚠️ Error calculating sub-bass energy: {e}. Falling back to 0.0.")
        return 0.0

def calculate_band_energies(mono_chunk_np: np.ndarray, sr: int, chunk_size: int) -> (float, float, float, float):
    """
    Calculates sub-bass, bass, mid, and high energy using a simplified statistical approach.
    These values are scaled by 10000 as per previous chat interactions for display.
    For precise frequency band energy, full STFT and band-pass filtering is required.
    """
    
    # We'll use a simple heuristic based on frequency regions derived from STFT,
    # then calculate energy. This is a common simplification for quick feature extraction.
    try:
        # Perform STFT to get frequency information
        n_fft = 2048 # Standard FFT window size
        hop_length = 512 # Standard hop length
        
        # Pad if chunk is too short for STFT
        if len(mono_chunk_np) < n_fft:
            padded_mono = np.pad(mono_chunk_np, (0, n_fft - len(mono_chunk_np)), 'constant')
        else:
            padded_mono = mono_chunk_np

        S = librosa.stft(padded_mono, n_fft=n_fft, hop_length=hop_length)
        magnitude = np.abs(S)
        
        # Convert frequency bins to Hz
        freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

        # Define frequency bands (approximate)
        band_ranges = {
            "sub_bass": (20, 60),
            "bass": (60, 250),
            "mid": (250, 4000),
            "high": (4000, 20000)
        }
        
        energies = {}
        for band_name, (low_hz, high_hz) in band_ranges.items():
            # Find indices for the frequency band
            low_idx = np.searchsorted(freqs, low_hz)
            high_idx = np.searchsorted(freqs, high_hz)
            
            # Extract the magnitude for this band and calculate mean energy
            band_magnitude = magnitude[low_idx:high_idx, :]
            
            if band_magnitude.size > 0:
                # Sum of squares of magnitudes for energy, then mean across time frames
                energy = np.mean(np.sum(band_magnitude**2, axis=0))
            else:
                energy = 0.0
            
            energies[band_name] = energy * 10000 # Scale as per chat for display
            
        return (float(energies.get("sub_bass", 0.0)),
                float(energies.get("bass", 0.0)),
                float(energies.get("mid", 0.0)),
                float(energies.get("high", 0.0)))

    except Exception as e:
        print(f"⚠️ Error calculating band energies: {e}. Falling back to 0.0 for all.")
        return 0.0, 0.0, 0.0, 0.0
