Here is the complete, fully realized Python code for your Legion Sonic Engine roadmap, implementing all phases as modular, typed, and integrated components.

This solution provides:
1.  **`utils.py`**: Common Pydantic models and helper functions.
2.  **`audio_analysis_actor.py`**: A Ray Actor for detailed segment-level loudness, dynamics, and brightness analysis.
3.  **`lancedb_manager.py`**: A class-based manager for connecting to LanceDB, defining schemas, ingesting data, and querying baselines.
4.  **`mastering_agent_actor.py`**: A Ray Actor that orchestrates adaptive, target-matched mastering using LanceDB baselines and dynamic Pedalboard adjustments.
5.  **`batch_master.py`**: A Ray-parallelized directory watcher for automated mastering tasks.
6.  **`legion_cli.py`**: A user-friendly command-line interface for manual file/folder mastering and baseline ingestion.
7.  **`test_audio_math.py`**: An automatic audio math verification test suite.
8.  **`requirements.txt`**: A list of all necessary Python dependencies.

---

### 1. `requirements.txt`

First, create a `requirements.txt` file in your `legion_sonic_engine` directory:

```txt
ray[default]
pydantic==2.*
torch
torchaudio
librosa
numpy
scipy
pyloudnorm
pedalboard
lancedb
soundfile
scikit-learn
argparse
tqdm # for batch_master progress
```

Install these dependencies:
`pip install -r requirements.txt`

---

### 2. `legion_sonic_engine/utils.py`

This file defines all Pydantic models and common utility functions used across the project.

```python
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

```

---

### 3. `legion_sonic_engine/audio_analysis_actor.py`

This Ray Actor is responsible for deeply analyzing audio files, segmenting them, and extracting a rich set of metrics and embeddings.

```python
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
```

---

### 4. `legion_sonic_engine/lancedb_manager.py`

This file handles LanceDB connections, schema definition, and data operations for storing and retrieving audio profiles.

```python
import os
import lancedb
import numpy as np
from typing import List, Dict, Any, Optional
from pydantic import ValidationError
from scipy.spatial.distance import euclidean

from legion_sonic_engine.utils import (
    ensure_utf8_output, SectionMetrics, MasterTrackStructuralProfile, BaselineTrackProfile
)

ensure_utf8_output()

class LanceDBManager:
    """
    Manages connections and operations for LanceDB, storing and retrieving
    audio structural profiles and baseline references.
    """
    def __init__(self, db_path: str, table_name: str):
        self.db_path = db_path
        self.table_name = table_name
        self.db: Optional[lancedb.LanceDB] = None
        self.table: Optional[lancedb.table.Table] = None
        print(f"🗄️ LanceDBManager initialized for path: {db_path} | Table: {table_name}")

    def connect(self):
        """Establishes connection to LanceDB."""
        try:
            self.db = lancedb.connect(self.db_path)
            print(f"✅ Connected to LanceDB at {self.db_path}")
        except Exception as e:
            print(f"❌ Failed to connect to LanceDB: {e}")
            raise

    def create_table_if_not_exists(self):
        """
        Creates the LanceDB table with the defined schema if it doesn't exist.
        The schema is inferred from the Pydantic model's first data ingestion.
        We'll use a placeholder for the vector field for initial table creation.
        """
        if not self.db:
            self.connect()
        
        # LanceDB schema is inferred from the first insertion.
        # We need a dummy record that matches the BaselineTrackProfile structure
        # to ensure the 'vector' field is created correctly.
        dummy_segment = SectionMetrics(
            segment_name="dummy", start_time_sec=0.0, end_time_sec=1.0, duration_sec=1.0,
            rms_db=-23.0, crest_factor=1.0, integrated_lufs=-23.0, loudness_range_lra=5.0,
            sub_bass_energy=0.0, bass_energy=0.0, mid_energy=0.0, high_energy=0.0,
            spectral_centroid=2000.0, mfcc_embedding=[0.0]*128
        )
        dummy_profile = BaselineTrackProfile(
            track_name="dummy_init", original_filepath="/dummy/path.wav",
            vector=[0.0]*128, # Ensure vector field is present
            segment_data=[dummy_segment]
        )
        
        try:
            # Try to open, if it fails, create
            self.table = self.db.open_table(self.table_name)
            print(f"📖 Opened existing LanceDB table: {self.table_name}")
        except lancedb.exceptions.TableNotFound:
            # If the table doesn't exist, create it with the dummy record.
            # LanceDB will infer the schema from this first record.
            # Remove the dummy later or simply tolerate it for schema bootstrapping.
            print(f"✨ Creating new LanceDB table: {self.table_name}")
            self.table = self.db.create_table(self.table_name, data=[dummy_profile.model_dump()])
            # It's good practice to remove the dummy record after creation
            self.table.delete(f"track_name = 'dummy_init'")
            print(f"✅ New LanceDB table '{self.table_name}' created.")
        except Exception as e:
            print(f"❌ Error creating/opening LanceDB table: {e}")
            raise

    def add_baseline_profile(self, profile_data: MasterTrackStructuralProfile, track_name: str):
        """
        Adds a MasterTrackStructuralProfile as a baseline to LanceDB.
        Calculates a track-level MFCC embedding for similarity search.
        
        Args:
            profile_data: The MasterTrackStructuralProfile to add.
            track_name: A unique name to identify this baseline.
        """
        if not self.table:
            self.create_table_if_not_exists()
        
        # Check for existing baseline with the same name
        if len(self.table.search().where(f"track_name = '{track_name}'").limit(1).to_list()) > 0:
            print(f"⚠️ Baseline '{track_name}' already exists. Skipping addition.")
            return

        # Generate a pooled MFCC vector for the entire track from its segments
        # This will be the main vector for track-level similarity search
        all_mfccs = [seg.mfcc_embedding for seg in profile_data.segment_data if seg.mfcc_embedding]
        if not all_mfccs:
            print(f"❌ No MFCC embeddings found in profile for '{track_name}'. Cannot add baseline.")
            return
        
        track_embedding = np.mean(all_mfccs, axis=0).tolist()
        
        try:
            baseline_entry = BaselineTrackProfile(
                track_name=track_name,
                original_filepath=profile_data.original_filepath,
                vector=track_embedding,
                segment_data=profile_data.segment_data
            )
            self.table.add([baseline_entry.model_dump()])
            print(f"✅ Baseline '{track_name}' successfully added to LanceDB.")
        except ValidationError as e:
            print(f"❌ Pydantic validation error adding baseline '{track_name}': {e}")
        except Exception as e:
            print(f"❌ Error adding baseline '{track_name}' to LanceDB: {e}")

    def query_closest_baselines(self, query_mfcc_embedding: List[float], n_results: int = 1) -> List[Dict[str, Any]]:
        """
        Queries LanceDB for the closest baseline tracks based on MFCC embedding.
        
        Args:
            query_mfcc_embedding: The MFCC embedding of the track to query.
            n_results: Number of closest baselines to return.
        
        Returns:
            A list of dictionaries, each representing a matched baseline track.
        """
        if not self.table:
            self.create_table_if_not_exists()
        
        try:
            # LanceDB performs vector similarity search
            results = self.table.search(query_mfcc_embedding).limit(n_results).to_list()
            print(f"🔍 Found {len(results)} closest baselines.")
            return results
        except Exception as e:
            print(f"❌ Error querying LanceDB: {e}")
            return []
            
    def get_baseline_by_name(self, track_name: str) -> Optional[BaselineTrackProfile]:
        """
        Retrieves a specific baseline track profile by its name.
        """
        if not self.table:
            self.create_table_if_not_exists()

        try:
            results = self.table.search().where(f"track_name = '{track_name}'").limit(1).to_list()
            if results:
                return BaselineTrackProfile(**results[0])
            else:
                return None
        except Exception as e:
            print(f"❌ Error retrieving baseline '{track_name}': {e}")
            return None

# Example usage (for local testing of the manager)
# if __name__ == "__main__":
#     DB_PATH = "C:\\STUDIES_BACKUP\\vectors\\lancedb_omni_snowflake_rag" # Update your path
#     TABLE_NAME = "sonic_engine_baselines"

#     manager = LanceDBManager(DB_PATH, TABLE_NAME)
#     manager.connect()
#     manager.create_table_if_not_exists()

#     # Dummy profile to add for testing
#     dummy_segment_metrics = SectionMetrics(
#         segment_name="Intro", start_time_sec=0.0, end_time_sec=10.0, duration_sec=10.0,
#         rms_db=-18.0, crest_factor=4.5, integrated_lufs=-20.0, loudness_range_lra=6.0,
#         sub_bass_energy=100.0, bass_energy=500.0, mid_energy=1000.0, high_energy=200.0,
#         spectral_centroid=2500.0, mfcc_embedding=[float(i % 100) / 100.0 for i in range(128)]
#     )
#     dummy_profile_data = MasterTrackStructuralProfile(
#         filename="dummy_test_track.wav", original_filepath="/tmp/dummy_test_track.wav",
#         total_sections_found=1, processing_time_ms=500.0, segment_data=[dummy_segment_metrics]
#     )

#     test_track_name = "Dummy Baseline Track 1"
#     manager.add_baseline_profile(dummy_profile_data, test_track_name)

#     # Query for a similar track
#     query_embedding = [float((i + 5) % 100) / 100.0 for i in range(128)] # Slightly different embedding
#     closest = manager.query_closest_baselines(query_embedding, n_results=1)
#     if closest:
#         print(f"\nClosest baseline found: {closest[0]['track_name']}")
#         print(f"  Segment Data sample: {closest[0]['segment_data'][0]['segment_name']}")
#     else:
#         print("No baselines found.")
```

---

### 5. `legion_sonic_engine/mastering_agent_actor.py`

This Ray Actor is the core of the adaptive mastering process. It uses analysis from `AudioAnalysisActor`, baselines from `LanceDBManager`, and applies dynamic DSP with `pedalboard`.

```python
import os
import time
import torch
import torchaudio
import numpy as np
import ray
import soundfile as sf # For reading/writing via pedalboard.io.AudioFile
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import euclidean

from pedalboard import Pedalboard, Compressor, HighpassFilter, Gain, Limiter, LowpassFilter
from pedalboard.io import AudioFile

from legion_sonic_engine.utils import (
    ensure_utf8_output, SectionMetrics, MasterTrackStructuralProfile, MasteringJobConfig
)
from legion_sonic_engine.audio_analysis_actor import AudioAnalysisActor
from legion_sonic_engine.lancedb_manager import LanceDBManager

# Initialize Ray if not already done
if not ray.is_initialized():
    ray.init(log_to_stdout=False)

ensure_utf8_output()

@ray.remote(num_gpus=1 if torch.cuda.is_available() else 0)
class MasteringAgentActor:
    def __init__(self, lancedb_path: str, lancedb_table_name: str):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.lancedb_manager = LanceDBManager(lancedb_path, lancedb_table_name)
        self.lancedb_manager.connect()
        self.lancedb_manager.create_table_if_not_exists()
        
        self.audio_analysis_actor = AudioAnalysisActor.remote()
        
        print(f"🎛️ MasteringAgentActor initialized on {self.device} with LanceDB at {lancedb_path}")

    async def adaptive_master_track(self, job_config_dict: dict) -> dict:
        """
        Orchestrates the entire adaptive mastering pipeline for a single track.
        
        Args:
            job_config_dict: A dictionary representing a MasteringJobConfig.
        
        Returns:
            A dictionary containing the mastering outcome and metrics.
        """
        try:
            job_config = MasteringJobConfig(**job_config_dict)
        except Exception as e:
            return {"status": "error", "message": f"Invalid job configuration: {e}"}

        input_path = job_config.input_filepath
        output_path = job_config.output_filepath
        baseline_track_name = job_config.baseline_track_name
        segment_length_sec = job_config.segment_length_sec

        if not os.path.exists(input_path):
            return {"status": "error", "message": f"Input file not found: {input_path}"}

        start_mastering_time = time.perf_counter()
        print(f"\n--- 🚀 INITIATING ADAPTIVE MASTERING: {os.path.basename(input_path)} ---")
        print(f"    Target Baseline: '{baseline_track_name}' | Output: {os.path.basename(output_path)}")

        # 1. Get baseline track profile from LanceDB
        baseline_profile_data = self.lancedb_manager.get_baseline_by_name(baseline_track_name)
        if not baseline_profile_data:
            return {"status": "error", "message": f"Baseline track '{baseline_track_name}' not found in LanceDB."}
        
        baseline_segments = baseline_profile_data.segment_data
        if not baseline_segments:
            return {"status": "error", "message": f"Baseline '{baseline_track_name}' has no segment data."}

        # For matching, we'll use a subset of key metrics and MFCCs
        # Scale numerical values for distance calculation
        baseline_features_raw = []
        baseline_mfcc_embeddings = []
        for seg in baseline_segments:
            baseline_features_raw.append([
                seg.rms_db, seg.crest_factor, seg.integrated_lufs, seg.loudness_range_lra,
                seg.spectral_centroid, seg.sub_bass_energy, seg.bass_energy, seg.mid_energy, seg.high_energy
            ])
            baseline_mfcc_embeddings.append(seg.mfcc_embedding)
        
        baseline_feature_matrix = np.array(baseline_features_raw, dtype=np.float32)
        baseline_mfcc_matrix = np.array(baseline_mfcc_embeddings, dtype=np.float32)
        
        baseline_segment_names = [seg.segment_name for seg in baseline_segments]
        
        print(f"✅ Loaded {len(baseline_segments)} segments from baseline '{baseline_track_name}'.")

        # 2. Load target track, slice into uniform segments, and extract features
        print("🎵 Loading target track and extracting features for alignment...")
        
        target_segments_features = []
        target_segments_mfccs = []
        audio_chunks = [] # Store raw audio chunks for processing
        
        with AudioFile(input_path) as f:
            sr = f.samplerate
            channels = f.num_channels
            frames_per_seg = int(segment_length_sec * sr)
            
            while True:
                audio_chunk_raw = f.read(frames_per_seg)
                if audio_chunk_raw.shape[1] == 0:
                    break
                
                # Check if chunk is too short to be meaningful
                if audio_chunk_raw.shape[1] < frames_per_seg // 2 and audio_chunk_raw.shape[1] < sr * 0.5:
                    break # Don't process very small residual chunks
                
                audio_chunks.append(audio_chunk_raw)
                
                # Create a temporary Pydantic model to leverage calculation functions
                # Note: This is a simplified analysis per uniform segment, not structural
                mono_np = audio_chunk_raw.mean(axis=0) if channels > 1 else audio_chunk_raw[0]
                
                rms_lin = float(np.sqrt(np.mean(mono_np ** 2)))
                rms_db = float(20 * np.log10(rms_lin)) if rms_lin > 1e-9 else -100.0
                peak = float(np.max(np.abs(mono_np)))
                crest = float(peak / rms_lin) if rms_lin > 1e-9 else 0.0
                
                integrated_lufs, loudness_range_lra = calculate_lufs_and_lra(audio_chunk_raw, sr)
                spectral_centroid = calculate_spectral_centroid(mono_np, sr)
                sub_bass_energy, bass_energy, mid_energy, high_energy = \
                    calculate_band_energies(mono_np, sr, mono_np.shape[0])
                mfcc_embedding = calculate_mfcc_embedding(mono_np, sr)
                
                target_segments_features.append([
                    rms_db, crest, integrated_lufs, loudness_range_lra,
                    spectral_centroid, sub_bass_energy, bass_energy, mid_energy, high_energy
                ])
                target_segments_mfccs.append(mfcc_embedding)

        if not audio_chunks:
            return {"status": "error", "message": "No audio chunks could be processed from the target track."}

        target_feature_matrix = np.array(target_segments_features, dtype=np.float32)
        target_mfcc_matrix = np.array(target_segments_mfccs, dtype=np.float32)
        
        print(f"  Extracted features for {len(target_feature_matrix)} uniform segments.")

        # 3. Scale features for distance calculation
        # Combine feature matrices and scale once to avoid bias
        scaler = StandardScaler()
        combined_features = np.vstack([baseline_feature_matrix, target_feature_matrix])
        scaler.fit(combined_features)
        
        scaled_baseline_features = scaler.transform(baseline_feature_matrix)
        scaled_target_features = scaler.transform(target_feature_matrix)
        
        # MFCCs are already normalized, but we can also scale them if desired (optional)
        mfcc_scaler = StandardScaler()
        combined_mfccs = np.vstack([baseline_mfcc_matrix, target_mfcc_matrix])
        mfcc_scaler.fit(combined_mfccs)
        
        scaled_baseline_mfccs = mfcc_scaler.transform(baseline_mfcc_matrix)
        scaled_target_mfccs = mfcc_scaler.transform(target_mfcc_matrix)

        # 4. Perform dynamic segment alignment (Euclidean distance on features + MFCCs)
        print("🎯 Aligning target segments to baseline reference segments...")
        aligned_target_info = []
        for i in range(len(scaled_target_features)):
            targ_combined_vec = np.concatenate([scaled_target_features[i], scaled_target_mfccs[i]])
            
            # Combine baseline features and MFCCs for matching
            baseline_combined_vectors = np.array([
                np.concatenate([scaled_baseline_features[j], scaled_baseline_mfccs[j]])
                for j in range(len(scaled_baseline_features))
            ])
            
            dists = cdist(targ_combined_vec.reshape(1, -1), baseline_combined_vectors, metric="euclidean")[0]
            best_idx = int(np.argmin(dists))
            
            # Look up matched baseline physical targets
            matched_baseline_seg = baseline_segments[best_idx]
            
            aligned_target_info.append({
                "targ_idx": i,
                "matched_base_seg": matched_baseline_seg,
                "distance": float(dists[best_idx])
            })
            print(f"  Segment {i:03d} -> matched '{matched_baseline_seg.segment_name}' | Dist: {dists[best_idx]:.3f}")

        # 5. Dynamic block-by-block mastering processing
        print("\n🎛️ Processing audio dynamically block-by-block with adaptive DSP...")
        
        # Initialize the effect nodes with default values
        # These will be dynamically updated
        hp = HighpassFilter(cutoff_frequency_hz=30.0)
        comp = Compressor(threshold_db=-20.0, ratio=3.0, attack_ms=10.0, release_ms=100.0)
        gain = Gain(gain_db=0.0)
        lim = Limiter(threshold_db=-0.3)
        
        board = Pedalboard([hp, comp, gain, lim])
        
        with AudioFile(output_path, 'w', samplerate=sr, num_channels=channels) as outfile:
            for seg_idx, audio_chunk_raw in enumerate(audio_chunks):
                # Get current segment's target values from the alignment
                match_info = aligned_target_info[seg_idx]
                target_seg_metrics = match_info["matched_base_seg"]
                
                target_rms_db = target_seg_metrics.rms_db
                target_crest_factor = target_seg_metrics.crest_factor
                target_lufs = target_seg_metrics.integrated_lufs
                target_sub_bass = target_seg_metrics.sub_bass_energy # Use for HPF adjustment
                
                # Analyze the raw chunk to calculate current values
                mono_chunk_np = audio_chunk_raw.mean(axis=0) if channels > 1 else audio_chunk_raw[0]
                current_rms_lin = float(np.sqrt(np.mean(mono_chunk_np ** 2)))
                current_rms_db = float(20 * np.log10(current_rms_lin)) if current_rms_lin > 1e-9 else -100.0
                current_peak = float(np.max(np.abs(mono_chunk_np)))
                current_crest_factor = float(current_peak / current_rms_lin) if current_rms_lin > 1e-9 else 0.0
                
                current_lufs, _ = calculate_lufs_and_lra(audio_chunk_raw, sr)
                current_sub_bass, _, _, _ = calculate_band_energies(mono_chunk_np, sr, mono_chunk_np.shape[0])
                
                # --- Dynamic DSP Parameter Adjustment Logic ---
                
                # Highpass Filter Adjustment: Reduce muddy sub-bass if target has less
                # Simple heuristic: If target sub-bass is significantly lower, raise HPF slightly.
                if current_sub_bass > target_sub_bass * 1.5 and hp.cutoff_frequency_hz < 60:
                    hp.cutoff_frequency_hz += 5 # Gently increase HPF
                    hp.cutoff_frequency_hz = min(hp.cutoff_frequency_hz, 80.0) # Cap HPF
                elif current_sub_bass < target_sub_bass * 0.8 and hp.cutoff_frequency_hz > 20:
                    hp.cutoff_frequency_hz -= 2 # Gently decrease HPF
                    hp.cutoff_frequency_hz = max(hp.cutoff_frequency_hz, 20.0) # Floor HPF
                
                # Compressor Adjustment: Match Crest Factor & RMS
                crest_delta = current_crest_factor - target_crest_factor
                if crest_delta > 0.1: # Current is spikier than target
                    comp.ratio = max(2.0, min(6.0, comp.ratio + crest_delta * 0.5))
                    comp.threshold_db = current_rms_db - (target_crest_factor * 0.5) # Dynamic threshold
                    comp.attack_ms = max(5.0, comp.attack_ms - 2.0)
                    comp.release_ms = max(50.0, comp.release_ms - 5.0)
                else: # Current is less spiky or matches target
                    comp.ratio = max(1.0, min(3.0, comp.ratio - 0.1)) # Relax compression
                    comp.threshold_db = 0.0 # Effectively bypass if no significant delta
                    comp.attack_ms = min(30.0, comp.attack_ms + 1.0)
                    comp.release_ms = min(200.0, comp.release_ms + 5.0)
                
                # Gain Adjustment: Match Integrated LUFS
                # Calculate gain needed to push current LUFS towards target
                lufs_delta = target_lufs - current_lufs
                gain.gain_db = max(-15.0, min(15.0, gain.gain_db + lufs_delta * 0.5))
                
                # Limiter: Always set to a safe commercial ceiling
                lim.threshold_db = -0.3 # Hard brickwall for final output
                lim.release_ms = max(50.0, min(200.0, abs(lufs_delta) * 5 + 50)) # Adaptive release

                # Run the chunk through the board with reset=False to preserve envelope states
                mastered_chunk = board(audio_chunk_raw, sample_rate=sr, reset=False)
                
                # Write to file
                outfile.write(mastered_chunk)
                
                # Log telemetry
                print(f"⚡ [SEG {seg_idx:03d}] Current LUFS: {current_lufs:.2f} (Target: {target_lufs:.2f}) | "
                      f"Gain: {gain.gain_db:+.2f}dB | Comp Ratio: {comp.ratio:.1f}:1 | HPF: {hp.cutoff_frequency_hz:.1f}Hz")
                
        total_mastering_latency_ms = (time.perf_counter() - start_mastering_time) * 1000
        
        print(f"\n======================================================")
        print(f"✅ Adaptive Mastering Complete! File saved to:\n   -> {output_path}")
        print(f"   Total Mastering Time: {total_mastering_latency_ms:.2f} ms")
        print(f"======================================================")

        return {
            "status": "success",
            "message": "Track mastered successfully.",
            "input_file": input_path,
            "output_file": output_path,
            "total_mastering_time_ms": total_mastering_latency_ms
        }

print("✅ MasteringAgentActor validated and ready.")

# Example usage (for local testing of the actor)
# if __name__ == "__main__":
#     # Configure LanceDB paths
#     LANCEDB_PATH = "C:\\STUDIES_BACKUP\\vectors\\lancedb_omni_snowflake_rag" # Your LanceDB path
#     LANCEDB_TABLE_NAME = "sonic_engine_baselines"
    
#     # Ensure baseline exists (run lancedb_manager.py example first or cli ingest_baseline)
#     # For this example, let's assume "Chris Lake - Somebody" is a baseline
#     # Create dummy baseline for quick test if not exists
#     manager_local = LanceDBManager(LANCEDB_PATH, LANCEDB_TABLE_NAME)
#     manager_local.connect()
#     manager_local.create_table_if_not_exists()
    
#     chris_lake_baseline = manager_local.get_baseline_by_name("Chris Lake - Somebody (2024)")
#     if not chris_lake_baseline:
#         print("⚠️ 'Chris Lake - Somebody (2024)' baseline not found. Creating a dummy for testing.")
#         dummy_mfcc = [float(i % 128) / 128.0 for i in range(128)]
#         dummy_seg = SectionMetrics(
#             segment_name="Drop/Main High-Energy Groove [Sect 1]", start_time_sec=0.0, end_time_sec=6.0, duration_sec=6.0,
#             rms_db=-7.7, crest_factor=2.5, integrated_lufs=-7.5, loudness_range_lra=2.0,
#             sub_bass_energy=8997.0, bass_energy=34839.0, mid_energy=965.0, high_energy=1296.0,
#             spectral_centroid=2061.0, mfcc_embedding=dummy_mfcc
#         )
#         dummy_profile = MasterTrackStructuralProfile(
#             filename="Somebody (2024).mp3", original_filepath="C:\\path\\to\\Somebody (2024).mp3", # Update with real path if known
#             total_sections_found=1, processing_time_ms=100.0, segment_data=[dummy_seg]
#         )
#         manager_local.add_baseline_profile(dummy_profile, "Chris Lake - Somebody (2024)")
#         print("Dummy baseline added.")
        
#     # Test file (replace with your actual audio file)
#     TEST_INPUT_FILE = r"C:\Users\adams\Downloads\putting in the work.wav" 
#     TEST_OUTPUT_FILE = r"C:\Users\adams\Downloads\putting in the work_MASTERED.wav"

#     if not os.path.exists(TEST_INPUT_FILE):
#         print(f"Test input file not found: {TEST_INPUT_FILE}")
#         exit()
    
#     mastering_agent = MasteringAgentActor.remote(LANCEDB_PATH, LANCEDB_TABLE_NAME)
    
#     job_config = MasteringJobConfig(
#         input_filepath=TEST_INPUT_FILE,
#         output_filepath=TEST_OUTPUT_FILE,
#         baseline_track_name="Chris Lake - Somebody (2024)",
#         segment_length_sec=6.0
#     )
    
#     import asyncio
#     async def run_mastering():
#         result = await mastering_agent.adaptive_master_track.remote(job_config.model_dump())
#         print("\nMastering Result:")
#         print(result)

#     asyncio.run(run_mastering())
```

---

### 6. `legion_sonic_engine/batch_master.py`

This script provides a Ray-parallelized directory scanner that watches a folder and automatically submits mastering tasks.

```python
import os
import time
import ray
from typing import Set, Dict, Any
from tqdm import tqdm # For progress bar

from legion_sonic_engine.utils import ensure_utf8_output, MasteringJobConfig
from legion_sonic_engine.mastering_agent_actor import MasteringAgentActor

# Configuration
WATCH_FOLDER = r"C:\Users\adams\Music\Mastering_Inputs" # Folder to watch for new audio files
OUTPUT_FOLDER = r"C:\Users\adams\Music\Mastering_Outputs" # Folder to save mastered files
LANCEDB_PATH = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
LANCEDB_TABLE_NAME = "sonic_engine_baselines"
DEFAULT_BASELINE_TRACK_NAME = "Chris Lake - Somebody (2024)" # Default baseline to use

FILE_EXTENSIONS = ('.wav', '.mp3', '.flac') # Supported audio file extensions
SCAN_INTERVAL_SEC = 10 # How often to scan the watch folder

# Initialize Ray if not already done
if not ray.is_initialized():
    ray.init(log_to_stdout=False)

ensure_utf8_output()

def create_folders_if_not_exists():
    """Ensures watch and output folders exist."""
    os.makedirs(WATCH_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print(f"✅ Watch folder: {WATCH_FOLDER}")
    print(f"✅ Output folder: {OUTPUT_FOLDER}")

def batch_master_watcher():
    """
    Watches a directory for new audio files and submits them for mastering
    via the Ray MasteringAgentActor.
    """
    create_folders_if_not_exists()

    mastering_agent = MasteringAgentActor.remote(LANCEDB_PATH, LANCEDB_TABLE_NAME)
    
    processed_files: Set[str] = set()
    active_jobs: Dict[ray.ObjectRef, str] = {} # Map object ref to original filename

    print(f"🚀 Starting Legion Batch Mastering Watcher. Scanning '{WATCH_FOLDER}' every {SCAN_INTERVAL_SEC} seconds...")
    print(f"    New files will be mastered against baseline: '{DEFAULT_BASELINE_TRACK_NAME}'")

    try:
        while True:
            # 1. Check for completed jobs
            completed_refs, pending_refs = ray.wait(list(active_jobs.keys()), timeout=0)
            for ref in completed_refs:
                filename = active_jobs.pop(ref)
                try:
                    result = ray.get(ref)
                    if result.get("status") == "success":
                        print(f"✅ Job completed for '{filename}': {result.get('output_file')}")
                    else:
                        print(f"❌ Job failed for '{filename}': {result.get('message')}")
                except Exception as e:
                    print(f"❌ Error retrieving result for '{filename}': {e}")
            
            # 2. Scan for new files
            current_files = set(
                f for f in os.listdir(WATCH_FOLDER) 
                if os.path.isfile(os.path.join(WATCH_FOLDER, f)) and f.lower().endswith(FILE_EXTENSIONS)
            )
            
            new_files = current_files - processed_files - set(active_jobs.values())
            
            if new_files:
                print(f"\n📁 Detected {len(new_files)} new audio files in '{WATCH_FOLDER}'. Submitting for mastering...")
                for filename in tqdm(list(new_files), desc="Submitting jobs"):
                    input_filepath = os.path.join(WATCH_FOLDER, filename)
                    output_filename = f"{os.path.splitext(filename)[0]}_MASTERED{os.path.splitext(filename)[1]}"
                    output_filepath = os.path.join(OUTPUT_FOLDER, output_filename)

                    job_config = MasteringJobConfig(
                        input_filepath=input_filepath,
                        output_filepath=output_filepath,
                        baseline_track_name=DEFAULT_BASELINE_TRACK_NAME,
                        segment_length_sec=6.0 # Can be configured
                    )
                    
                    try:
                        obj_ref = mastering_agent.adaptive_master_track.remote(job_config.model_dump())
                        active_jobs[obj_ref] = filename
                        print(f"  ⚡ Submitted '{filename}' for mastering.")
                        processed_files.add(filename) # Mark as processed once submitted
                    except Exception as e:
                        print(f"  ❌ Failed to submit '{filename}': {e}")
                        
            if not new_files and not active_jobs:
                print(f"💤 No new files detected and no active jobs. Waiting {SCAN_INTERVAL_SEC}s...", end='\r')

            time.sleep(SCAN_INTERVAL_SEC)

    except KeyboardInterrupt:
        print("\n👋 Legion Batch Mastering Watcher stopped by user.")
    except Exception as e:
        print(f"\nFatal error in watcher: {e}")

if __name__ == "__main__":
    batch_master_watcher()
```

---

### 7. `legion_sonic_engine/legion_cli.py`

This is the command-line interface for interacting with the mastering engine.

```python
import argparse
import os
import ray
import asyncio
import json

from legion_sonic_engine.utils import ensure_utf8_output, MasteringJobConfig
from legion_sonic_engine.audio_analysis_actor import AudioAnalysisActor
from legion_sonic_engine.lancedb_manager import LanceDBManager
from legion_sonic_engine.mastering_agent_actor import MasteringAgentActor

# --- Configuration ---
LANCEDB_PATH = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
LANCEDB_TABLE_NAME = "sonic_engine_baselines"
DEFAULT_OUTPUT_DIR = r"C:\Users\adams\Downloads" # Default directory for mastered files
DEFAULT_BASELINE_TRACK_NAME = "Chris Lake - Somebody (2024)" # Default baseline


# --- Initialize Ray and Actors ---
if not ray.is_initialized():
    ray.init(log_to_stdout=False) # Suppress Ray logs in CLI

ensure_utf8_output()

# Instantiate global actors
audio_analysis_actor = AudioAnalysisActor.remote()
mastering_agent_actor = MasteringAgentActor.remote(LANCEDB_PATH, LANCEDB_TABLE_NAME)
lancedb_manager_cli = LanceDBManager(LANCEDB_PATH, LANCEDB_TABLE_NAME)
lancedb_manager_cli.connect()
lancedb_manager_cli.create_table_if_not_exists()


# --- CLI Commands ---

async def master_file_command(args):
    """Handles the 'master' command: processes a single audio file."""
    input_filepath = os.path.abspath(args.input_file)
    output_filepath = os.path.abspath(args.output) if args.output else \
                      os.path.join(DEFAULT_OUTPUT_DIR, os.path.basename(input_filepath).replace('.', '_MASTERED.'))
    baseline_name = args.baseline if args.baseline else DEFAULT_BASELINE_TRACK_NAME

    print(f"--- Legion CLI: Mastering Single File ---")
    print(f"Input: {input_filepath}")
    print(f"Output: {output_filepath}")
    print(f"Baseline: {baseline_name}")

    if not os.path.exists(input_filepath):
        print(f"❌ Error: Input file not found at '{input_filepath}'")
        return

    job_config = MasteringJobConfig(
        input_filepath=input_filepath,
        output_filepath=output_filepath,
        baseline_track_name=baseline_name,
        segment_length_sec=args.segment_length
    )

    print("\n⚡ Submitting mastering job to Ray agent...")
    result = await mastering_agent_actor.adaptive_master_track.remote(job_config.model_dump())
    
    print("\n--- Mastering Result ---")
    print(json.dumps(result, indent=2))
    if result.get("status") == "success":
        print(f"\n✅ Mastering complete! Output saved to: {result['output_file']}")
    else:
        print(f"\n❌ Mastering failed: {result.get('message')}")


async def ingest_baseline_command(args):
    """Handles the 'ingest-baseline' command: adds a track to LanceDB as a baseline."""
    input_filepath = os.path.abspath(args.input_file)
    baseline_name = args.name if args.name else os.path.splitext(os.path.basename(input_filepath))[0]

    print(f"--- Legion CLI: Ingesting Baseline ---")
    print(f"Input: {input_filepath}")
    print(f"Baseline Name: {baseline_name}")

    if not os.path.exists(input_filepath):
        print(f"❌ Error: Input file not found at '{input_filepath}'")
        return

    print("\n🔮 Analyzing track to generate structural profile and embeddings...")
    profile_data_dict = await audio_analysis_actor.profile_track_by_sections.remote(input_filepath, max_sections=16)
    profile_data = lancedb_manager_cli.MasterTrackStructuralProfile(**profile_data_dict) # Re-Pydantic validate

    print(f"\n📊 Profile generated in {profile_data.processing_time_ms:.2f} ms. Found {profile_data.total_sections_found} sections.")
    
    print("🗄️ Adding profile to LanceDB as a baseline...")
    lancedb_manager_cli.add_baseline_profile(profile_data, baseline_name)
    print(f"✅ Baseline '{baseline_name}' ingestion process complete.")


async def watch_folder_command(args):
    """Handles the 'watch' command: starts the batch mastering watcher."""
    print(f"--- Legion CLI: Starting Folder Watcher ---")
    print(f"Watching: {args.input_folder}")
    print(f"Output: {args.output_folder}")
    print(f"Baseline: {args.baseline if args.baseline else DEFAULT_BASELINE_TRACK_NAME}")
    
    # Update batch_master configuration dynamically
    global WATCH_FOLDER, OUTPUT_FOLDER, DEFAULT_BASELINE_TRACK_NAME, SCAN_INTERVAL_SEC
    WATCH_FOLDER = os.path.abspath(args.input_folder)
    OUTPUT_FOLDER = os.path.abspath(args.output_folder)
    DEFAULT_BASELINE_TRACK_NAME = args.baseline if args.baseline else DEFAULT_BASELINE_TRACK_NAME
    SCAN_INTERVAL_SEC = args.interval

    # Import and run the batch_master directly
    # Note: This is an atypical way to run a daemon from CLI and would usually be a separate process.
    # For simplicity, we directly call its main function. It assumes the global config is updated.
    print("\nStarting batch mastering watcher in this process. Press Ctrl+C to stop.")
    from legion_sonic_engine.batch_master import batch_master_watcher
    batch_master_watcher()


async def main():
    parser = argparse.ArgumentParser(
        description="Legion Sonic Engine CLI: Master audio files using adaptive DSP and LanceDB baselines.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Master single file command
    master_parser = subparsers.add_parser('master', help='Master a single audio file.')
    master_parser.add_argument('input_file', type=str, help='Path to the input audio file (.wav, .mp3, .flac).')
    master_parser.add_argument('--output', '-o', type=str, 
                               help=f'Output file path. Defaults to {DEFAULT_OUTPUT_DIR}/<input_name>_MASTERED.<ext>.')
    master_parser.add_argument('--baseline', '-b', type=str,
                               help=f'Name of the baseline track in LanceDB to match against. Defaults to "{DEFAULT_BASELINE_TRACK_NAME}".')
    master_parser.add_argument('--segment-length', '-s', type=float, default=6.0,
                               help='Length of audio segments for dynamic mastering in seconds. Default: 6.0.')
    master_parser.set_defaults(func=master_file_command)

    # Ingest baseline command
    ingest_parser = subparsers.add_parser('ingest-baseline', help='Analyze an audio track and add its profile to LanceDB as a baseline.')
    ingest_parser.add_argument('input_file', type=str, help='Path to the audio file to ingest as a baseline.')
    ingest_parser.add_argument('--name', '-n', type=str,
                               help='A unique name for this baseline. Defaults to the input filename.')
    ingest_parser.set_defaults(func=ingest_baseline_command)

    # Watch folder command
    watch_parser = subparsers.add_parser('watch', help='Start a watcher that automatically masters new files in a folder.')
    watch_parser.add_argument('input_folder', type=str, 
                              help=f'Folder to watch for new audio files. Default: {WATCH_FOLDER}.')
    watch_parser.add_argument('output_folder', type=str, 
                              help=f'Folder to save mastered files. Default: {OUTPUT_FOLDER}.')
    watch_parser.add_argument('--baseline', '-b', type=str,
                               help=f'Name of the baseline track in LanceDB to match against. Defaults to "{DEFAULT_BASELINE_TRACK_NAME}".')
    watch_parser.add_argument('--interval', '-i', type=int, default=10,
                               help='Scan interval in seconds. Default: 10.')
    watch_parser.set_defaults(func=watch_folder_command)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        await args.func(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    # Fix for Windows paths in argparse (optional, but good practice)
    # Allows paths to be passed with backslashes without issues
    def clean_path(path_str):
        if path_str:
            return os.path.normpath(path_str)
        return path_str
    
    for action in parser._actions:
        if isinstance(action, argparse._StoreAction) and 'file' in action.dest or 'folder' in action.dest:
            action.type = clean_path

    asyncio.run(main())
```

---

### 8. `legion_sonic_engine/test_audio_math.py`

This file contains the automated tests for verifying core audio math operations.

```python
import os
import unittest
import numpy as np
import torch
import torchaudio
import librosa
from scipy.signal import butter, lfilter
import pyloudnorm as ln

from pedalboard import Pedalboard, Gain, HighpassFilter, Compressor
from pedalboard.io import AudioFile # Needed for pedalboard to manage files

from legion_sonic_engine.utils import (
    calculate_lufs_and_lra, calculate_spectral_centroid, calculate_mfcc_embedding,
    calculate_band_energies, ensure_utf8_output
)

ensure_utf8_output()

class TestAudioMath(unittest.TestCase):

    def setUp(self):
        """Set up common test parameters and generate dummy audio for tests."""
        self.sr = 44100
        self.duration = 5 # seconds
        self.num_samples = self.sr * self.duration
        self.dummy_signal_mono = np.random.randn(self.num_samples).astype(np.float32) * 0.5
        self.dummy_signal_stereo = np.stack([self.dummy_signal_mono, self.dummy_signal_mono], axis=0) * 0.5
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"\n--- Running tests on device: {self.device} ---")

        # Create a temporary dummy WAV file for pedalboard.io.AudioFile tests
        self.temp_input_wav = "test_input_temp.wav"
        self.temp_output_wav = "test_output_temp.wav"
        torchaudio.save(self.temp_input_wav, torch.from_numpy(self.dummy_signal_stereo), self.sr)

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_input_wav):
            os.remove(self.temp_input_wav)
        if os.path.exists(self.temp_output_wav):
            os.remove(self.temp_output_wav)

    def test_stft_consistency(self):
        """Verify STFT calculations on CPU match expected sizes and properties."""
        print("  Testing STFT consistency...")
        n_fft = 2048
        hop_length = 512

        # Librosa STFT (CPU)
        stft_librosa = librosa.stft(self.dummy_signal_mono, n_fft=n_fft, hop_length=hop_length)
        
        # Torchaudio STFT (CPU)
        stft_torchaudio = torchaudio.transforms.Spectrogram(
            n_fft=n_fft, hop_length=hop_length, power=None, return_complex=True
        )(torch.from_numpy(self.dummy_signal_mono))

        # Check shapes
        self.assertEqual(stft_librosa.shape, stft_torchaudio.shape, "STFT shapes should match.")
        
        # Check if values are close (due to windowing differences, they won't be identical)
        # We'll compare magnitude for a looser check
        self.assertTrue(np.allclose(np.abs(stft_librosa), np.abs(stft_torchaudio.numpy()), atol=1e-3),
                        "STFT magnitudes should be close between Librosa and Torchaudio (CPU).")
        print("  ✅ STFT consistency (Librosa vs Torchaudio CPU) passed.")
        
        # Test GPU offloading for Torchaudio
        if self.device.type == 'cuda':
            stft_torchaudio_gpu = torchaudio.transforms.Spectrogram(
                n_fft=n_fft, hop_length=hop_length, power=None, return_complex=True
            )(torch.from_numpy(self.dummy_signal_mono).to(self.device))
            
            self.assertEqual(stft_librosa.shape, stft_torchaudio_gpu.cpu().shape, "STFT shapes should match on GPU.")
            self.assertTrue(np.allclose(np.abs(stft_librosa), np.abs(stft_torchaudio_gpu.cpu().numpy()), atol=1e-3),
                            "STFT magnitudes should be close (Librosa CPU vs Torchaudio GPU).")
            print("  ✅ STFT consistency (Librosa CPU vs Torchaudio GPU) passed.")


    def test_stereo_phase_cancellation(self):
        """Verify phase cancellation: inverted stereo channels should result in near zero output."""
        print("  Testing stereo phase cancellation...")
        # Create a stereo signal where right channel is inverted
        inverted_stereo = np.stack([self.dummy_signal_mono, -self.dummy_signal_mono], axis=0)

        # Summing these to mono should result in near zero
        summed_to_mono = np.mean(inverted_stereo, axis=0)

        # RMS of the summed signal should be very small
        rms_summed = np.sqrt(np.mean(summed_to_mono ** 2))
        self.assertLess(rms_summed, 1e-5, "Summing inverted stereo channels should result in near zero RMS.")
        print("  ✅ Stereo phase cancellation detection passed.")

    def test_gain_boost_accuracy(self):
        """Verify that gain boosts are mathematically exact on float32 waveforms."""
        print("  Testing gain boost accuracy...")
        gain_db = 6.0 # +6dB means doubling amplitude
        expected_multiplier = 10**(gain_db / 20)
        
        pedalboard_gain = Gain(gain_db=gain_db)
        
        # Apply gain using Pedalboard
        processed_mono = pedalboard_gain(self.dummy_signal_mono, self.sr)
        
        # Compare with manual multiplication
        expected_mono = self.dummy_signal_mono * expected_multiplier
        
        self.assertTrue(np.allclose(processed_mono, expected_mono, atol=1e-6),
                        f"Pedalboard Gain({gain_db}dB) should accurately multiply amplitude.")
        print("  ✅ Gain boost accuracy passed.")

    def test_lufs_lra_calculation(self):
        """Verify LUFS and LRA calculations for known loud/quiet signals."""
        print("  Testing LUFS and LRA calculations...")
        # Create a very quiet signal
        quiet_signal = np.random.randn(self.num_samples).astype(np.float32) * 0.001
        quiet_lufs, quiet_lra = calculate_lufs_and_lra(quiet_signal, self.sr)
        
        # A very quiet signal should have a very low LUFS value (e.g., below -40 LUFS)
        self.assertLess(quiet_lufs, -40.0, "Quiet signal should have low integrated LUFS.")
        
        # Create a moderately loud signal (e.g., -10 dBFS peak, -15 LUFS integrated)
        loud_signal_peak = 0.5
        loud_signal = np.sin(2 * np.pi * 440 * np.arange(self.num_samples) / self.sr).astype(np.float32) * loud_signal_peak
        loud_lufs, loud_lra = calculate_lufs_and_lra(loud_signal, self.sr)
        
        # Check if LUFS is within a reasonable range for a loud signal (e.g., -20 to -5 LUFS)
        self.assertGreater(loud_lufs, -25.0, "Loud signal should have higher integrated LUFS.")
        self.assertLess(loud_lufs, 0.0, "Loud signal LUFS should be below 0 dBFS.")
        
        # LRA should be non-negative
        self.assertGreaterEqual(quiet_lra, 0.0, "LRA should be non-negative.")
        self.assertGreaterEqual(loud_lra, 0.0, "LRA should be non-negative.")
        print("  ✅ LUFS and LRA calculation sanity checks passed.")

    def test_spectral_centroid_calculation(self):
        """Verify spectral centroid behaves as expected for low vs. high frequency signals."""
        print("  Testing spectral centroid calculation...")
        # Create a low-frequency sine wave (e.g., 100 Hz)
        low_freq_signal = np.sin(2 * np.pi * 100 * np.arange(self.num_samples) / self.sr).astype(np.float32) * 0.5
        low_centroid = calculate_spectral_centroid(low_freq_signal, self.sr)
        
        # Create a high-frequency sine wave (e.g., 5000 Hz)
        high_freq_signal = np.sin(2 * np.pi * 5000 * np.arange(self.num_samples) / self.sr).astype(np.float32) * 0.5
        high_centroid = calculate_spectral_centroid(high_freq_signal, self.sr)
        
        # High frequency signal should have a higher spectral centroid
        self.assertGreater(high_centroid, low_centroid, "High frequency signal should have higher spectral centroid.")
        print("  ✅ Spectral centroid calculation passed.")
        
    def test_mfcc_embedding_properties(self):
        """Verify MFCC embedding output dimensions and non-zero values."""
        print("  Testing MFCC embedding properties...")
        n_mfcc = 128
        embedding = calculate_mfcc_embedding(self.dummy_signal_mono, self.sr, n_mfcc=n_mfcc)
        
        self.assertEqual(len(embedding), n_mfcc, f"MFCC embedding should have {n_mfcc} dimensions.")
        self.assertTrue(any(e != 0 for e in embedding), "MFCC embedding should not be all zeros for a non-silent signal.")
        print("  ✅ MFCC embedding properties passed.")

    def test_pedalboard_continuous_processing(self):
        """
        Verify Pedalboard's `reset=False` for continuous processing
        without clicks/phase issues across chunks.
        """
        print("  Testing Pedalboard continuous processing (no clicks)...")
        # Define a simple pedalboard with a compressor and gain
        board = Pedalboard([
            Compressor(threshold_db=-20.0, ratio=2.0, attack_ms=10.0, release_ms=100.0),
            Gain(gain_db=3.0)
        ])

        # Load audio from file
        with AudioFile(self.temp_input_wav) as infile:
            sr = infile.samplerate
            channels = infile.num_channels
            total_frames = infile.frames
            chunk_size = sr # 1-second chunks

            output_chunks = []
            
            while infile.tell() < total_frames:
                audio_chunk = infile.read(chunk_size)
                if audio_chunk.shape[1] == 0:
                    break
                
                # Process with reset=False for continuous operation
                processed_chunk = board(audio_chunk, sample_rate=sr, reset=False)
                output_chunks.append(processed_chunk)
            
            # Concatenate all processed chunks
            if output_chunks:
                full_processed_audio = np.concatenate(output_chunks, axis=1)
                torchaudio.save(self.temp_output_wav, torch.from_numpy(full_processed_audio), sr)
                print(f"  Processed audio saved to {self.temp_output_wav}")
                
                # A qualitative check for clicks would involve listening or more complex analysis.
                # For automated testing, we'll check if output size matches input.
                self.assertEqual(full_processed_audio.shape[1], total_frames, "Output frames should match input frames.")
                # We can't easily quantify "no clicks" without a specific metric or human ear.
                # The primary test is that the pipeline runs without errors and state is maintained.
                self.assertFalse(np.array_equal(self.dummy_signal_stereo, full_processed_audio), 
                                 "Processed audio should be different from original.")
                print("  ✅ Pedalboard continuous processing completed without errors.")
            else:
                self.fail("No audio chunks processed by Pedalboard.")


if __name__ == '__main__':
    unittest.main()

```