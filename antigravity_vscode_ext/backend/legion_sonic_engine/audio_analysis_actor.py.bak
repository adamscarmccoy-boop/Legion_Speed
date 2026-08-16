import os
import time
import torch
import torchaudio
import librosa
import numpy as np
import ray
from typing import List
from pydantic import ValidationError

from legion_sonic_engine.utils import (
    ensure_utf8_output, SectionMetrics, MasterTrackStructuralProfile,
    calculate_lufs_and_lra, calculate_spectral_centroid, calculate_mfcc_embedding,
    calculate_band_energies
)

# Initialize background Ray environment if it isn't already running
if not ray.is_initialized():
    ray.init(log_to_stdout=False) # Suppress Ray logs to keep output clean

ensure_utf8_output()

@ray.remote(num_gpus=1 if torch.cuda.is_available() else 0)
class AudioAnalysisActor:
    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"📦 AudioAnalysisActor initialized on device: {self.device}")
        
        # Ensure librosa backend for faster processing
        os.environ['LIBROSA_FFT_BACKEND'] = 'scipy' # Can also be 'numpy', 'mkl', etc.

    def profile_track_by_sections(self, file_path: str, max_sections: int = 16) -> dict:
        """
        Dynamically computes authentic transient/beat section boundaries and profiles them,
        extracting detailed metrics including LUFS, LRA, Spectral Centroid, and MFCC embeddings.
        
        Args:
            file_path: Absolute path to the audio file.
            max_sections: Maximum number of major sections to detect.
                          Librosa can find many micro-segments; this filters to macro-structures.
        
        Returns:
            A dictionary representing MasterTrackStructuralProfile.
        """
        start_time = time.perf_counter()
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Target track missing at path: {file_path}")

        print(f"🎵 Processing track for structural analysis: {os.path.basename(file_path)} on {self.device}")
        
        # 1. Ingest asset directly to array memory
        waveform, sr = torchaudio.load(file_path)
        
        # If stereo, convert to mono for librosa's onset detection and most feature extraction
        mono_waveform = torch.mean(waveform, dim=0, keepdim=False)
        
        total_samples = mono_waveform.shape[0]
        duration_sec = total_samples / sr
        
        mono_y_np = mono_waveform.cpu().numpy() # Transfer to CPU for librosa processing
        
        print("🔮 Processing math layer: Extracting rhythmic onset boundaries...")
        
        # 2. Extract transient peaks via spectral novelty envelope calculation
        # Use a consistent hop_length and n_fft for feature extraction
        n_fft_librosa = 2048
        hop_length_librosa = 512
        
        onset_env = librosa.onset.onset_strength(y=mono_y_np, sr=sr, hop_length=hop_length_librosa)
        onset_frames = librosa.onset.onset_detect(
            onset_envelope=onset_env, 
            sr=sr, 
            hop_length=hop_length_librosa, 
            backtrack=True  # Pull slice indices back to preceding energy minima to protect transients
        )
        
        # 3. Dynamic Section Slicing Math
        onset_samples = librosa.frames_to_samples(onset_frames, hop_length=hop_length_librosa)
        
        # Filter down boundaries to select major macro changes if there are too many micro clicks
        # Adjusting step calculation for robustness
        step = max(1, len(onset_samples) // max_sections)
        selected_boundaries = list(onset_samples[::step])
        
        # Append absolute boundaries (start and end of file)
        if 0 not in selected_boundaries:
            selected_boundaries.insert(0, 0)
        if total_samples not in selected_boundaries:
            selected_boundaries.append(total_samples)
            
        selected_boundaries = sorted(list(set(selected_boundaries)))
        
        segment_list = []
        total_detected_sections = len(selected_boundaries) - 1
        
        print(f"📊 Found {total_detected_sections} potential structural sections. Analyzing metrics...")

        # 4. Loop over authentic array slice blocks and extract detailed metrics
        for i in range(total_detected_sections):
            start_sample = selected_boundaries[i]
            end_sample = selected_boundaries[i+1]
            
            # Map sample boundaries to precise time values
            sec_start = round(start_sample / sr, 3)
            sec_end = round(end_sample / sr, 3)
            segment_duration = round(sec_end - sec_start, 3)
            
            # Extract raw audio array slice and offload directly to GPU core VRAM
            # Using the original stereo waveform for accurate RMS/Peak if channels > 1
            chunk_stereo = waveform[:, start_sample:end_sample].to(self.device)
            chunk_mono = mono_waveform[start_sample:end_sample].to(self.device)
            
            chunk_stereo_np = chunk_stereo.cpu().numpy() # For pyloudnorm (needs stereo or mono depending on function)
            chunk_mono_np = chunk_mono.cpu().numpy() # For librosa features
            chunk_size_samples = chunk_mono.shape[0]
            
            if chunk_size_samples < sr * 0.1: # Skip very short segments (less than 100ms) for meaningful analysis
                # print(f"  Skipping very short segment {i+1} ({segment_duration:.2f}s)")
                continue
                
            # 5. Core Algorithmic Feature Mapping
            # RMS and Crest Factor from raw stereo chunk (or mono if only one channel)
            rms_lin = np.sqrt(np.mean(chunk_stereo_np ** 2))
            rms_db = 20 * np.log10(rms_lin) if rms_lin > 1e-9 else -100.0
            peak_val = np.max(np.abs(chunk_stereo_np))
            crest_factor = (peak_val / rms_lin) if rms_lin > 1e-9 else 1.0
            
            # Integrated LUFS and Loudness Range (requires float array, often mono for measurement)
            integrated_lufs, loudness_range_lra = calculate_lufs_and_lra(chunk_stereo_np, sr)
            
            # Spectral Centroid (from mono numpy array)
            spectral_centroid = calculate_spectral_centroid(chunk_mono_np, sr)
            
            # Band Energies (from mono numpy array)
            sub_bass_energy, bass_energy, mid_energy, high_energy = \
                calculate_band_energies(chunk_mono_np, sr, chunk_size_samples)
            
            # MFCC Embedding (from mono numpy array)
            mfcc_embedding = calculate_mfcc_embedding(chunk_mono_np, sr)

            # Dynamic naming label based on data properties (heuristic from previous chat)
            if rms_db > -9.0 and crest_factor < 3.0:
                sec_type = "Drop / Main High-Energy Groove"
            elif rms_db < -15.0:
                sec_type = "Breakdown / Low-Energy Melodic Window"
            else:
                sec_type = "Build / Transition Sequence"

            try:
                segment_list.append(SectionMetrics(
                    segment_name=f"{sec_type} [Sect {i+1}]",
                    start_time_sec=sec_start,
                    end_time_sec=sec_end,
                    duration_sec=segment_duration,
                    rms_db=rms_db,
                    crest_factor=crest_factor,
                    integrated_lufs=integrated_lufs,
                    loudness_range_lra=loudness_range_lra,
                    sub_bass_energy=sub_bass_energy,
                    bass_energy=bass_energy,
                    mid_energy=mid_energy,
                    high_energy=high_energy,
                    spectral_centroid=spectral_centroid,
                    mfcc_embedding=mfcc_embedding
                ))
            except ValidationError as e:
                print(f"Pydantic validation error for segment {i+1}: {e}")
                # Decide how to handle: skip segment, fill with defaults, or raise
                continue

        latency = (time.perf_counter() - start_time) * 1000
        
        try:
            profile_schema = MasterTrackStructuralProfile(
                filename=os.path.basename(file_path),
                original_filepath=os.path.abspath(file_path),
                total_sections_found=len(segment_list),
                processing_time_ms=latency,
                segment_data=segment_list
            )
            return profile_schema.model_dump()
        except ValidationError as e:
            print(f"Pydantic validation error for track profile: {e}")
            raise

print("✅ Headless AudioAnalysisActor validated and ready.")

# Example usage (for local testing of the actor if needed, usually called by other actors)
# if __name__ == "__main__":
#     test_file = r"E:\DJSUSAN\LEGION\what a waste-2 (Edit).wav" # Replace with a real path
#     if not os.path.exists(test_file):
#         print(f"Test file not found: {test_file}")
#         exit()

#     engine_actor = AudioAnalysisActor.remote()
#     print(f"📡 Offloading track to AudioAnalysisActor...")
#     async_ref = engine_actor.profile_track_by_sections.remote(test_file, max_sections=12)
#     print("⏳ Crunching onset boundaries and generating sectional matrix slices...")
#     structural_json_report = ray.get(async_ref)

#     import json
#     print("\n🏆 Asynchronous Background Extraction Complete:")
#     print(json.dumps(structural_json_report, indent=2))
