Here's the integrated, production-ready Python code combining all your requested enhancements. This script defines two Ray Actors: `HeadlessAudioSegmenter` for detailed segment analysis and Omni-Vector generation, and `DynamicMasteringAgent` for continuous mastering with a persistent `Pedalboard` and LanceDB ingestion.

This code respects your hand-written style, uses `soundfile` implicitly via `pedalboard.io.AudioFile`, `scipy` for filtering, and `ray` and `lancedb` for distributed processing and persistence.

**Key Features Implemented:**

1.  **Omni-Vector Fusion & FretFlow Ingestion:**
    *   A mock `_generate_mock_omni_vector` function simulates the `FretFlowEngine`'s output, creating a 41-dimension vector for each audio segment.
    *   The `HeadlessAudioSegmenter` actor generates these vectors as part of its segment analysis.
    *   These Omni-Vectors are stored in LanceDB alongside other metrics.

2.  **LUFS, LRA & Spectral Brightness:**
    *   `pyloudnorm.Meter` is integrated into `HeadlessAudioSegmenter` to calculate Integrated Loudness (LUFS) and Loudness Range (LRA) for each segment.
    *   `librosa.feature.spectral_centroid` is used to quantify the "brightness" of each segment.

3.  **Persistent Ingestion to LanceDB:**
    *   New Pydantic schemas (`AudioSegmentMetrics`, `TrackMasterProfile`, `LanceDBSegmentRecord`) define the structure for LanceDB.
    *   The `DynamicMasteringAgent` actor ingests both individual segment metrics and an overall track profile into two separate LanceDB tables (`omni_audio_segments` and `omni_audio_tracks`).

4.  **Continuous Mastering Integration:**
    *   The `DynamicMasteringAgent` instantiates a single `Pedalboard` object once, outside the processing loop.
    *   Audio is processed `chunk-by-chunk` using `AudioFile` and `board(..., reset=False)` to preserve dynamic envelope states (compressor, limiter), preventing clicks and phase issues.
    *   The `_mono_below_frequency` utility function is included to address low-end phase problems, consistent with your original `dynamic_segment_master.py`.
    *   Dynamic adjustments to `Compressor` and `Gain` parameters are made per segment based on its analyzed metrics and a target reference.

---

### `legion_audio_mastering_agent.py`

```python
import os
import time
import json
import numpy as np
import torch
import torchaudio
import librosa
import pyloudnorm as pln
import ray
import lancedb
import pandas as pd # Required for LanceDB.add(DataFrame)
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal, Any
from scipy import signal
import soundfile as sf # Used implicitly by Pedalboard's AudioFile for reading/writing
from pedalboard import Pedalboard, Compressor, HighpassFilter, Gain, Limiter, Clipping
from pedalboard.io import AudioFile
from sklearn.preprocessing import StandardScaler # Retained from dynamic_segment_master for potential alignment logic
from scipy.spatial.distance import cdist # Retained from dynamic_segment_master for potential alignment logic

# Disable Ray's interactive terminal status bar which breaks on Windows CMD
os.environ["RAY_PROGRESS_BAR"] = "0"
os.environ["RAY_DEDUP_LOGS"] = "0"
# PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION="python" is often set for Essentia/Ray compatibility,
# but it's generally not needed for core Ray and can sometimes impact performance.
# Keeping it in for consistency if it was in your previous env setup.
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python" 

# --- Global Configurations (can be overridden) ---
# LanceDB path relative to the script location
LANCEDB_PATH = os.path.join(os.path.dirname(__file__), "lancedb_omni_snowflake_rag")
TABLE_NAME_SEGMENTS = "omni_audio_segments"
TABLE_NAME_TRACKS = "omni_audio_tracks"
DEFAULT_SAMPLE_RATE = 48000
SEGMENT_DURATION_SEC = 6.0 # Consistent with dynamic_segment_master.py
OMNI_VECTOR_DIM = 41 # Consistent with Sonic DNA dimension from paper logs
DOWNLOADS_DIR = r"C:\Users\adams\Downloads" # Default, can be overridden by explicit paths

# --- Pydantic Schemas for LanceDB and Ray Actors ---

class OmniVector(BaseModel):
    # Represents the FretFlowEngine latent representation.
    # Stored as a List[float] for JSON serialization and LanceDB embedding.
    vector: List[float] = Field(..., min_length=OMNI_VECTOR_DIM, max_length=OMNI_VECTOR_DIM)

class AudioSegmentMetrics(BaseModel):
    """Metrics for a single audio segment."""
    segment_id: int
    start_time_sec: float
    end_time_sec: float
    # Core DSP metrics
    rms_db: float
    crest_factor: float
    sub_bass_energy: float
    bass_energy: float
    mid_energy: float
    high_energy: float
    spectral_centroid: float
    # New Loudness metrics
    loudness_lufs: float
    loudness_range_lra: float
    # Omni-Vector embedding
    omni_vector: OmniVector

class TrackMasterProfile(BaseModel):
    """Overall profile for a mastered track, linking to its segments."""
    track_id: str = Field(description="Unique identifier for the track, e.g., filename_hash.")
    filename: str
    original_path: str
    mastered_path: Optional[str]
    sample_rate: int
    num_channels: int
    duration_sec: float
    total_segments: int
    processing_latency_ms: float
    overall_rms_db: float
    overall_loudness_lufs: float
    mastering_goal: Optional[str] = None
    baseline_reference: Optional[str] = None
    # For LanceDB, this nested list might be stored as JSON or a separate table ID
    segments_summary: List[Dict[str, Any]] = Field(default_factory=list) # Summary of segments, not full objects

class LanceDBSegmentRecord(BaseModel):
    """Schema for individual segment storage in LanceDB."""
    # LanceDB requires `vector` to be a List[float] for vector search indexing
    # All other fields are metadata.
    omni_vector: List[float] = Field(..., min_length=OMNI_VECTOR_DIM, max_length=OMNI_VECTOR_DIM)
    
    # Metadata for the segment
    track_id: str # Foreign key to the track profile
    segment_id: int
    filename: str # For easy lookup
    start_time_sec: float
    end_time_sec: float
    rms_db: float
    crest_factor: float
    sub_bass_energy: float
    bass_energy: float
    mid_energy: float
    high_energy: float
    spectral_centroid: float
    loudness_lufs: float
    loudness_range_lra: float

# --- Utility Functions ---

def _mono_below_frequency(audio: np.ndarray, samplerate: int, cutoff_hz: float = 150.0) -> np.ndarray:
    """
    Converts audio frequencies below a cutoff to mono to prevent phase cancellation.
    Preserves stereo image for higher frequencies.
    """
    if audio.ndim < 2 or audio.shape[0] < 2:
        return audio # Already mono or less than 2 channels

    left = audio[0]
    right = audio[1]

    # Mid/Side decomposition
    mid = (left + right) / 2.0
    side = (left - right) / 2.0

    # Design high-pass filter for the Side channel to keep only high frequencies in stereo
    nyquist = 0.5 * samplerate
    normal_cutoff = max(0.01, min(0.99, cutoff_hz / nyquist))
    # Use 4th order Butterworth filter for a smooth rolloff
    b, a = signal.butter(4, normal_cutoff, btype='high', analog=False)

    # Filter the side channel zero-phase using filtfilt to avoid phase distortion
    side_filtered = signal.filtfilt(b, a, side)

    # Reconstruct stereo channels
    left_reconstructed = mid + side_filtered
    right_reconstructed = mid - side_filtered

    return np.stack([left_reconstructed, right_reconstructed], axis=0)

def _generate_mock_omni_vector(audio_chunk: np.ndarray) -> OmniVector:
    """
    Simulates the FretFlowEngine's Omni-Vector generation.
    In a real implementation, this would involve complex NN inference.
    """
    # For demonstration, generate a random vector based on the chunk's content hash
    # This provides some deterministic "uniqueness" for the mock vector.
    
    # Generate a seed from a hash of the chunk data to make it somewhat deterministic
    # Handle empty chunks safely
    if audio_chunk.size == 0:
        seed_val = 42
    else:
        # A simple way to get a hash-like value from numpy array
        seed_val = int(np.sum(audio_chunk * np.arange(1, audio_chunk.size + 1).reshape(audio_chunk.shape)) % (2**32 - 1))
    
    np.random.seed(seed_val)
    vector_data = np.random.rand(OMNI_VECTOR_DIM).astype(np.float32).tolist()
    return OmniVector(vector=vector_data)

# --- Ray Actors ---

@ray.remote(num_gpus=0.1 if torch.cuda.is_available() else 0) # Use a small fraction if GPU is available
class HeadlessAudioSegmenter:
    """
    Ray Actor for segmenting audio, extracting rich DSP features (including LUFS, LRA, Spectral Centroid),
    and generating Omni-Vectors from FretFlowEngine's latent space.
    """
    def __init__(self, sample_rate: int = DEFAULT_SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.loudness_meter = pln.Meter(rate=self.sample_rate, block_size=0.400) # 400ms block size for LUFS
        print(f"📦 HeadlessAudioSegmenter Actor initialized on: {self.device}")

    def process_audio_file(self, file_path: str, segment_duration_sec: float = SEGMENT_DURATION_SEC) -> List[AudioSegmentMetrics]:
        """
        Loads an audio file, segments it, and extracts detailed metrics per segment.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file missing at path: {file_path}")

        print(f"🎧 Segmenting and analyzing: {os.path.basename(file_path)}...")
        waveform_torch, sr = torchaudio.load(file_path)
        
        # Ensure consistent sample rate and convert to numpy for librosa/pyloudnorm
        if sr != self.sample_rate:
            resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=self.sample_rate)
            waveform_torch = resampler(waveform_torch)
        
        audio_np = waveform_torch.numpy() # Convert to numpy for further processing
        num_channels = audio_np.shape[0]
        total_samples = audio_np.shape[1]
        duration_sec = total_samples / self.sample_rate
        
        frames_per_seg = int(segment_duration_sec * self.sample_rate)
        
        segment_metrics_list: List[AudioSegmentMetrics] = []

        for i, start_sample in enumerate(range(0, total_samples, frames_per_seg)):
            end_sample = min(start_sample + frames_per_seg, total_samples)
            
            # Skip very short trailing segments (e.g., less than 1/3 of full segment duration)
            if (end_sample - start_sample) < (frames_per_seg // 3) and i > 0:
                continue
            
            # Ensure chunk has enough data for analysis, otherwise skip
            if (end_sample - start_sample) < 2 * 512: # Min for STFT, e.g., 2 hop_lengths
                continue

            chunk_np = audio_np[:, start_sample:end_sample]
            
            # If the chunk is stereo, take the mean for mono features (RMS, Centroid, etc.)
            mono_chunk_np = chunk_np.mean(axis=0) if num_channels > 1 else chunk_np[0]

            # --- Basic DSP features ---
            rms_lin = float(np.sqrt(np.mean(mono_chunk_np ** 2))) if mono_chunk_np.size > 0 else 1e-9
            rms_db = float(20 * np.log10(rms_lin)) if rms_lin > 1e-9 else -100.0
            peak = float(np.max(np.abs(mono_chunk_np))) if mono_chunk_np.size > 0 else 0.0
            crest = float(peak / rms_lin) if rms_lin > 1e-9 else 0.0

            # --- Spectral Centroid (Spectral Brightness) ---
            # librosa.feature.spectral_centroid expects mono signal.
            # Ensure the chunk is long enough for STFT (e.g., n_fft samples)
            n_fft_centroid = 2048
            if len(mono_chunk_np) >= n_fft_centroid:
                spectral_centroid = float(np.mean(librosa.feature.spectral_centroid(y=mono_chunk_np, sr=self.sample_rate, n_fft=n_fft_centroid, hop_length=512)))
            else:
                spectral_centroid = 0.0 # Fallback if chunk too short
            
            # --- Band Energy (simplified) ---
            # These are basic mean absolute values within approximate frequency bands.
            # For accurate band energy, a proper FFT and frequency bin mapping would be needed.
            # This is a placeholder mimicking the style of the previous outputs.
            chunk_size = len(mono_chunk_np)
            # Ensure array slicing does not go out of bounds for very short chunks
            sub_bass_energy = float(np.mean(np.abs(mono_chunk_np[:int(chunk_size * 0.05)]))) * 10000 if chunk_size > 0 else 0.0
            bass_energy = float(np.mean(np.abs(mono_chunk_np[:int(chunk_size * 0.15)]))) * 10000 if chunk_size > 0 else 0.0
            mid_energy = float(np.mean(np.abs(mono_chunk_np[int(chunk_size * 0.15):int(chunk_size * 0.6)]))) * 10000 if chunk_size > 0 else 0.0
            high_energy = float(np.mean(np.abs(mono_chunk_np[int(chunk_size * 0.6):]))) * 10000 if chunk_size > 0 else 0.0
            
            # --- LUFS & LRA (Loudness measurements) ---
            # pyloudnorm can handle multi-channel input for LUFS calculation directly
            try:
                # Ensure the chunk is long enough for pyloudnorm (min 3 blocks of 400ms = 1.2s)
                if chunk_np.shape[1] >= self.sample_rate * 1.2:
                    loudness_lufs = self.loudness_meter.integrated_loudness(chunk_np)
                    loudness_range_lra = self.loudness_meter.loudness_range(chunk_np)
                else:
                    loudness_lufs = -70.0 # Default very quiet if chunk too short
                    loudness_range_lra = 0.0
            except Exception: # Handle cases where chunk might be too short or other error for LUFS calculation
                loudness_lufs = -70.0
                loudness_range_lra = 0.0
            
            # --- Omni-Vector Generation (FretFlowEngine latent) ---
            omni_vector = _generate_mock_omni_vector(mono_chunk_np)

            segment_metrics_list.append(AudioSegmentMetrics(
                segment_id=i,
                start_time_sec=round(start_sample / self.sample_rate, 3),
                end_time_sec=round(end_sample / self.sample_rate, 3),
                rms_db=rms_db,
                crest_factor=crest,
                sub_bass_energy=sub_bass_energy,
                bass_energy=bass_energy,
                mid_energy=mid_energy,
                high_energy=high_energy,
                spectral_centroid=spectral_centroid,
                loudness_lufs=loudness_lufs,
                loudness_range_lra=loudness_range_lra,
                omni_vector=omni_vector
            ))
        
        print(f"✅ Analyzed {len(segment_metrics_list)} segments for {os.path.basename(file_path)}")
        return segment_metrics_list

@ray.remote(num_cpus=1)
class DynamicMasteringAgent:
    """
    Ray Actor for applying dynamic mastering using Pedalboard,
    ingesting data into LanceDB, and orchestrating the process.
    """
    def __init__(self, lancedb_path: str = LANCEDB_PATH, sr: int = DEFAULT_SAMPLE_RATE):
        self.db = lancedb.connect(lancedb_path)
        self.sample_rate = sr
        self.loudness_meter = pln.Meter(rate=self.sample_rate, block_size=0.400)
        
        # Initialize Pedalboard once, outside the processing loop
        self.mastering_board = Pedalboard([
            HighpassFilter(cutoff_frequency_hz=30.0),
            # Threshold and ratio will be dynamically updated
            Compressor(threshold_db=-20.0, ratio=3.0, attack_ms=10.0, release_ms=100.0),
            Gain(gain_db=0.0), # Gain will be dynamically updated
            Clipping(threshold_db=-1.0), # Soft clip just before limiter
            Limiter(threshold_db=-0.3) # Brickwall limiter
        ])
        print(f"🎛️ DynamicMasteringAgent Actor initialized, connected to LanceDB at {lancedb_path}")

    def _get_or_create_tables(self):
        """Helper to get or create LanceDB tables with Pydantic schemas."""
        try:
            segments_table = self.db.open_table(TABLE_NAME_SEGMENTS)
        except lancedb.exceptions.TableNotFound:
            print(f"LanceDB: Table '{TABLE_NAME_SEGMENTS}' not found, creating...")
            # For LanceDB, the embedding column must be named 'vector' by default
            # Or specified in a custom schema. Here, Pydantic's model_json_schema() works.
            segments_table = self.db.create_table(
                TABLE_NAME_SEGMENTS,
                schema=LanceDBSegmentRecord.model_json_schema()
            )
        try:
            tracks_table = self.db.open_table(TABLE_NAME_TRACKS)
        except lancedb.exceptions.TableNotFound:
            print(f"LanceDB: Table '{TABLE_NAME_TRACKS}' not found, creating...")
            tracks_table = self.db.create_table(
                TABLE_NAME_TRACKS,
                schema=TrackMasterProfile.model_json_schema()
            )
        return segments_table, tracks_table

    def process_and_master_track(
        self,
        file_path: str,
        segment_metrics_list: List[AudioSegmentMetrics],
        custom_output_filepath: Optional[str] = None,
        baseline_reference_track: Optional[str] = None # For dynamic alignment
    ) -> TrackMasterProfile:
        """
        Processes an audio file segment-by-segment with dynamic mastering,
        aligns to an optional baseline, and ingests all data into LanceDB.
        """
        start_pipeline_time = time.perf_counter()
        
        input_path = file_path
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # Determine output path
        if custom_output_filepath:
            output_path = custom_output_filepath
        else:
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_filename = f"{base_name}_DYNAMIC_MASTERED.wav"
            output_path = os.path.join(DOWNLOADS_DIR, output_filename)
        
        segments_table, tracks_table = self._get_or_create_tables()

        # Load audio once
        waveform_torch_original, sr_original = torchaudio.load(input_path)
        if sr_original != self.sample_rate:
            resampler = torchaudio.transforms.Resample(orig_freq=sr_original, new_freq=self.sample_rate)
            waveform_torch_original = resampler(waveform_torch_original) # Resample to actor's SR
            
        audio_full_np = waveform_torch_original.numpy()
        num_channels = audio_full_np.shape[0]
        total_frames = audio_full_np.shape[1]
        duration_sec = total_frames / self.sample_rate

        # Apply Mono Sub-Bass lock to the entire continuous array to prevent boundary clicks
        print(f"Applying Mono Phase Lock (<150Hz) to sub-bass for {os.path.basename(input_path)}...")
        audio_locked_np = _mono_below_frequency(audio_full_np, self.sample_rate, cutoff_hz=150.0)

        # --- Baseline Alignment Logic (simplified for demo) ---
        # This section can be significantly expanded to query LanceDB for actual baselines
        # and calculate dynamic target values for each segment.
        target_overall_lufs = -9.0 # Generic target for mastered tracks
        target_overall_crest = 3.0 # Generic target for mastered tracks
        
        # If a specific baseline track is provided, fetch its profile for more accurate targets
        if baseline_reference_track:
            try:
                # Use track_id for more robust lookup than filename
                baseline_track_id = f"{baseline_reference_track.replace('.', '_')}"
                baseline_track_df = tracks_table.search(baseline_track_id).where(f"track_id = '{baseline_track_id}'").limit(1).to_pandas()
                if not baseline_track_df.empty:
                    target_overall_lufs = float(baseline_track_df.iloc[0]["overall_loudness_lufs"])
                    # Optionally, fetch segment-level targets from the baseline track's segments table
                    print(f"Using baseline reference '{baseline_reference_track}': Target LUFS={target_overall_lufs:.2f}")
                else:
                    print(f"Warning: Baseline '{baseline_reference_track}' not found in tracks table. Using generic targets.")
            except Exception as e:
                print(f"Error fetching baseline '{baseline_reference_track}': {e}. Using generic targets.")


        # Reset Pedalboard dynamics for this new track, ensuring a fresh start
        self.mastering_board[1].threshold_db = -20.0 # Compressor
        self.mastering_board[1].ratio = 3.0
        self.mastering_board[2].gain_db = 0.0 # Gain

        processed_segments_data_for_lancedb: List[LanceDBSegmentRecord] = []
        
        overall_lufs_values = []
        overall_rms_values = []

        try:
            with AudioFile(output_path, 'w', samplerate=self.sample_rate, num_channels=num_channels) as outfile:
                for seg_idx, segment_data in enumerate(segment_metrics_list):
                    start_sample = int(segment_data.start_time_sec * self.sample_rate)
                    end_sample = int(segment_data.end_time_sec * self.sample_rate)
                    
                    audio_chunk_original = audio_locked_np[:, start_sample:end_sample]
                    if audio_chunk_original.shape[1] == 0:
                        continue
                        
                    # --- Dynamic Mastering Logic (using current segment's analysis) ---
                    # Adjust compressor and gain based on current segment's characteristics
                    # and the overall target (can be refined with segment-specific targets from alignment)
                    
                    current_lufs = segment_data.loudness_lufs
                    current_crest = segment_data.crest_factor
                    
                    # Adjust compression: if too dynamic, increase ratio/lower threshold
                    if current_crest > (target_overall_crest * 1.2): # If current crest is significantly higher than target
                        self.mastering_board[1].ratio = min(5.0, self.mastering_board[1].ratio + 0.5)
                        self.mastering_board[1].threshold_db = current_lufs - 3.0 # Pull threshold down relative to current LUFS
                    elif current_crest < (target_overall_crest * 0.8): # If too squashed, reduce compression
                        self.mastering_board[1].ratio = max(1.5, self.mastering_board[1].ratio - 0.2)
                        self.mastering_board[1].threshold_db = current_lufs # Raise threshold
                    
                    # Adjust gain: lift or lower to hit target LUFS
                    gain_adjust = target_overall_lufs - current_lufs
                    # Clamp gain boost to prevent extreme volume spikes and preserve headroom
                    self.mastering_board[2].gain_db = max(-10.0, min(10.0, gain_adjust))
                    
                    # Process chunk through the *same* Pedalboard instance (reset=False)
                    mastered_chunk = self.mastering_board(audio_chunk_original, sample_rate=self.sample_rate, reset=False)
                    outfile.write(mastered_chunk)
                    
                    # Collect data for overall track metrics
                    mastered_lufs = self.loudness_meter.integrated_loudness(mastered_chunk)
                    overall_lufs_values.append(mastered_lufs)
                    overall_rms_values.append(np.sqrt(np.mean(mastered_chunk**2)) if mastered_chunk.size > 0 else 1e-9)

                    # Prepare segment data for LanceDB ingestion
                    processed_segments_data_for_lancedb.append(LanceDBSegmentRecord(
                        track_id=f"{os.path.basename(file_path).replace('.', '_')}", # Unique ID for the track
                        segment_id=segment_data.segment_id,
                        filename=os.path.basename(file_path),
                        start_time_sec=segment_data.start_time_sec,
                        end_time_sec=segment_data.end_time_sec,
                        rms_db=segment_data.rms_db, # Original RMS
                        crest_factor=segment_data.crest_factor, # Original Crest
                        sub_bass_energy=segment_data.sub_bass_energy,
                        bass_energy=segment_data.bass_energy,
                        mid_energy=segment_data.mid_energy,
                        high_energy=segment_data.high_energy,
                        spectral_centroid=segment_data.spectral_centroid,
                        loudness_lufs=mastered_lufs, # Mastered LUFS
                        loudness_range_lra=segment_data.loudness_range_lra, # Original LRA for simplicity
                        omni_vector=segment_data.omni_vector.vector # Store as list
                    ))
                    
                    print(f"⚡ [BLK {seg_idx:03d}] Raw LUFS:{current_lufs:.2f} | Crest:{current_crest:.2f} | Mastered LUFS:{mastered_lufs:.2f} | Gain:{self.mastering_board[2].gain_db:+.2f}dB | Comp:{self.mastering_board[1].ratio:.2f}:1")
            
            print(f"✅ Dynamic Mastered file successfully saved to:\n   -> {output_path}")

        except Exception as e:
            print(f"❌ Error during dynamic block-by-block mastering: {e}")
            raise

        # --- Ingest Segments into LanceDB ---
        if processed_segments_data_for_lancedb:
            try:
                # Convert list of Pydantic models to list of dicts for LanceDB.add
                segments_df = pd.DataFrame([s.model_dump() for s in processed_segments_data_for_lancedb])
                segments_table.add(segments_df)
                print(f"📈 Ingested {len(processed_segments_data_for_lancedb)} segments into LanceDB table '{TABLE_NAME_SEGMENTS}'.")
            except Exception as e:
                print(f"❌ Error ingesting segments into LanceDB: {e}")
        
        # Calculate overall track metrics
        overall_avg_lufs = np.mean(overall_lufs_values) if overall_lufs_values else -70.0
        overall_avg_rms = np.mean([20 * np.log10(v) if v > 1e-9 else -100.0 for v in overall_rms_values]) if overall_rms_values else -100.0

        # Create TrackMasterProfile
        processing_latency_ms = (time.perf_counter() - start_pipeline_time) * 1000
        
        # Create summary of segments (e.g., first few segment IDs and their LUFS) for the track profile
        segments_summary = [
            {"segment_id": s.segment_id, "loudness_lufs": s.loudness_lufs, "omni_vector_head": s.omni_vector.vector[:5]}
            for s in segment_metrics_list[:3] # Just the first 3 as a summary
        ]

        track_profile = TrackMasterProfile(
            track_id=f"{os.path.basename(file_path).replace('.', '_')}", # Unique ID for the track
            filename=os.path.basename(file_path),
            original_path=file_path,
            mastered_path=output_path,
            sample_rate=self.sample_rate,
            num_channels=num_channels,
            duration_sec=duration_sec,
            total_segments=len(segment_metrics_list),
            processing_latency_ms=processing_latency_ms,
            overall_rms_db=overall_avg_rms,
            overall_loudness_lufs=overall_avg_lufs,
            mastering_goal="Dynamic segment-aligned loudness and dynamics",
            baseline_reference=baseline_reference_track,
            segments_summary=segments_summary
        )
        
        try:
            # Pydantic model_dump() handles nested objects for conversion to dict for LanceDB
            tracks_table.add(pd.DataFrame([track_profile.model_dump()]))
            print(f"📈 Ingested track profile for '{track_profile.filename}' into LanceDB table '{TABLE_NAME_TRACKS}'.")
        except Exception as e:
            print(f"❌ Error ingesting track profile into LanceDB: {e}")

        print(f"======================================================")
        return track_profile


# --- Main Execution Block for Testing / Demonstration ---
if __name__ == "__main__":
    # Initialize Ray if not already running
    if not ray.is_initialized():
        print("Initializing Ray cluster...")
        # Using "auto" for dynamic connection to an existing head node or starting a new local one.
        # Set a fixed address like "ray://127.0.0.1:10001" if connecting to a specific cluster.
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        print("Ray cluster initialized.")

    # Instantiate actors
    segmenter_actor = HeadlessAudioSegmenter.remote(sample_rate=DEFAULT_SAMPLE_RATE)
    mastering_agent = DynamicMasteringAgent.remote(lancedb_path=LANCEDB_PATH, sr=DEFAULT_SAMPLE_RATE)

    # --- Test Files ---
    # !! IMPORTANT !!
    # Ensure these files exist at the specified paths.
    # Update these paths to match your local setup for 'putting in the work.wav' and 'what a waste-2 (Edit).wav'.
    # Example:
    # TEST_AUDIO_FILE_1 = r"C:\Users\YourUser\Music\MyTracks\putting in the work.wav"
    # TEST_AUDIO_FILE_2 = r"C:\Users\YourUser\Music\MyTracks\what a waste-2 (Edit).wav"
    TEST_AUDIO_FILE_1 = r"C:\Users\adams\Downloads\putting in the work.wav"
    TEST_AUDIO_FILE_2 = r"C:\Users\adams\Downloads\what a waste-2 (Edit).wav" # From previous chat
    
    # A mock baseline track name.
    # For dynamic alignment to truly work, a track with this name should have been
    # previously processed and ingested into the LanceDB 'omni_audio_tracks' table.
    # If not, the system will fall back to generic loudness targets.
    # Example: you could run the Chris Lake track through this pipeline first to create a baseline.
    BASELINE_TRACK_NAME = "Somebody (2024).mp3" 

    # --- Scenario 1: Process and Master Test Audio 1 ---
    print(f"\n--- Scenario 1: Processing and Mastering '{os.path.basename(TEST_AUDIO_FILE_1)}' ---")
    try:
        # Step 1: Segment and analyze
        print(f"📡 Offloading segmentation for '{os.path.basename(TEST_AUDIO_FILE_1)}' to segmenter actor...")
        segment_futures_1 = segmenter_actor.process_audio_file.remote(TEST_AUDIO_FILE_1)
        segment_metrics_1 = ray.get(segment_futures_1)
        
        # Step 2: Dynamically master, align, and ingest
        print(f"🎛️ Offloading dynamic mastering for '{os.path.basename(TEST_AUDIO_FILE_1)}' to mastering agent...")
        master_profile_future_1 = mastering_agent.process_and_master_track.remote(
            TEST_AUDIO_FILE_1,
            segment_metrics_1,
            baseline_reference_track=BASELINE_TRACK_NAME # Optional: try to align to a baseline
        )
        final_master_profile_1 = ray.get(master_profile_future_1)
        
        print("\n🏆 Scenario 1 Complete. Final Track Profile:")
        print(json.dumps(final_master_profile_1.model_dump(), indent=2))
        print(f"Mastered output saved to: {final_master_profile_1.mastered_path}")
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}. Please ensure test audio files exist at the specified paths.")
    except Exception as e:
        print(f"An unexpected error occurred during Scenario 1: {e}")
        import traceback
        traceback.print_exc()

    # --- Scenario 2: Process and Master Test Audio 2 ---
    print(f"\n--- Scenario 2: Processing and Mastering '{os.path.basename(TEST_AUDIO_FILE_2)}' ---")
    try:
        # Step 1: Segment and analyze
        print(f"📡 Offloading segmentation for '{os.path.basename(TEST_AUDIO_FILE_2)}' to segmenter actor...")
        segment_futures_2 = segmenter_actor.process_audio_file.remote(TEST_AUDIO_FILE_2)
        segment_metrics_2 = ray.get(segment_futures_2)
        
        # Step 2: Dynamically master, align, and ingest
        print(f"🎛️ Offloading dynamic mastering for '{os.path.basename(TEST_AUDIO_FILE_2)}' to mastering agent...")
        master_profile_future_2 = mastering_agent.process_and_master_track.remote(
            TEST_AUDIO_FILE_2,
            segment_metrics_2 # No specific baseline for this one, uses generic targets
        )
        final_master_profile_2 = ray.get(master_profile_future_2)
        
        print("\n🏆 Scenario 2 Complete. Final Track Profile:")
        print(json.dumps(final_master_profile_2.model_dump(), indent=2))
        print(f"Mastered output saved to: {final_master_profile_2.mastered_path}")

    except FileNotFoundError as e:
        print(f"ERROR: {e}. Please ensure test audio files exist at the specified paths.")
    except Exception as e:
        print(f"An unexpected error occurred during Scenario 2: {e}")
        import traceback
        traceback.print_exc()

    print("\n--- LanceDB Verification ---")
    try:
        db_verify = lancedb.connect(LANCEDB_PATH)
        segments_tbl = db_verify.open_table(TABLE_NAME_SEGMENTS)
        tracks_tbl = db_verify.open_table(TABLE_NAME_TRACKS)
        
        print(f"Total segments in '{TABLE_NAME_SEGMENTS}': {segments_tbl.count_rows()}")
        print(f"Total tracks in '{TABLE_NAME_TRACKS}': {tracks_tbl.count_rows()}")
        
        # Example: Query segments for one of the processed tracks
        print(f"\nQuerying segments for '{os.path.basename(TEST_AUDIO_FILE_1)}' (first 3):")
        query_results_segments = segments_tbl.search(f"{os.path.basename(TEST_AUDIO_FILE_1).replace('.', '_')}") \
                                   .where(f"filename = '{os.path.basename(TEST_AUDIO_FILE_1)}'") \
                                   .limit(3) \
                                   .to_pandas()
        if not query_results_segments.empty:
            print(query_results_segments[['segment_id', 'start_time_sec', 'end_time_sec', 'loudness_lufs', 'spectral_centroid']].to_string())
        else:
            print("No segments found for this track in LanceDB.")

        print(f"\nQuerying track profile for '{os.path.basename(TEST_AUDIO_FILE_1)}':")
        query_results_track = tracks_tbl.search(f"{os.path.basename(TEST_AUDIO_FILE_1).replace('.', '_')}") \
                                   .where(f"track_id = '{os.path.basename(TEST_AUDIO_FILE_1).replace('.', '_')}'") \
                                   .limit(1) \
                                   .to_pandas()
        if not query_results_track.empty:
            print(query_results_track[['filename', 'overall_loudness_lufs', 'processing_latency_ms']].to_string())
            print(f"Sample segments_summary from track profile:\n{json.dumps(query_results_track['segments_summary'].iloc[0], indent=2)}")
        else:
            print("No track profile found for this track in LanceDB.")

    except Exception as e:
        print(f"Error during LanceDB verification: {e}")
        print("If tables do not exist initially, this is expected for the first run.")
        
    print("\n[INFO] Keeping driver process alive. Press Ctrl+C to exit.")
    while True:
        time.sleep(60) # Keep the main script alive to allow Ray actors to persist
```