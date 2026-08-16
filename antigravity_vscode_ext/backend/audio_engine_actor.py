import os
import time
import torch
import torchaudio
import librosa
import numpy as np
import ray
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# ==============================================================================
# SOVEREIGN LIFE-CYCLE STABILIZER (AUTO-INJECTED)
# Prevents dangling stdout/stdio pipes and GCS registry locks on Windows exit
# ==============================================================================
import atexit
import signal

def clean_exit_handler(*args, **kwargs):
    import sys
    sys.stderr.write("\n[LMS LIFECYCLE] Exit triggered. Flushing system streams...\n")
    sys.stderr.flush()
    try:
        import ray
        if ray.is_initialized():
            sys.stderr.write("[LMS LIFECYCLE] Active Ray session detected. Disconnecting...\n")
            ray.shutdown()
    except Exception:
        pass
    sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================


# Initialize background Ray environment if it isn't already running
if not ray.is_initialized():
    ray.init(namespace="legion")

# ==========================================
# Pydantic Target Metrics Validation Layer
# ==========================================
class SegmentMetrics(BaseModel):
    segment_name: str
    rms_db: float
    crest_factor: float
    sub_bass_energy: float
    bass_energy: float
    mid_energy: float
    high_energy: float
    spectral_centroid: float

class MasterTrackProfile(BaseModel):
    filename: str
    processing_time_ms: float
    segment_data: List[SegmentMetrics]


# ==========================================
# Headless Audio Engine Ray Actor Definition
# ==========================================
@ray.remote(num_gpus=1 if torch.cuda.is_available() else 0)
class HeadlessAudioEngineActor:
    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"📦 Ray Actor initialized on headless node device: {self.device}")

    def profile_track(self, file_path: str, segment_count: int = 4) -> dict:
        """Loads a file from disk and parses it completely in the background"""
        start_time = time.perf_counter()
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file missing at path: {file_path}")

        # Headless disk ingestion
        waveform, sr = torchaudio.load(file_path)
        
        # Split data into even multi-segment chunks across time-axis
        total_samples = waveform.shape[1]
        chunk_size = total_samples // segment_count
        
        segment_list = []
        
        # Loop through each time slice completely headless
        for i in range(segment_count):
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size
            
            # Slice audio tensor and push to compute target
            chunk = waveform[:, start_idx:end_idx].to(self.device)
            chunk_np = chunk.cpu().numpy()
            
            # Sub-band extraction via manual slice math
            # Calculate Root-Mean-Square energy
            rms = torch.sqrt(torch.mean(chunk ** 2)).item()
            rms_db = 20 * np.log10(rms) if rms > 1e-5 else -80.0
            
            # Calculate Crest Factor (Transient snap)
            peak = torch.max(torch.abs(chunk)).item()
            crest_factor = (peak / rms) if rms > 1e-5 else 1.0
            
            # Basic frequency boundary estimations using absolute array mean variance
            sub_bass_energy = float(np.mean(np.abs(chunk_np[:, :int(chunk_size * 0.05)]))) * 10000
            bass_energy = float(np.mean(np.abs(chunk_np[:, :int(chunk_size * 0.15)]))) * 10000
            mid_energy = float(np.mean(np.abs(chunk_np[:, int(chunk_size * 0.15):int(chunk_size * 0.6)]))) * 10000
            high_energy = float(np.mean(np.abs(chunk_np[:, int(chunk_size * 0.6):]))) * 10000
            
            # Spectral Centroid estimation via Librosa
            try:
                centroid = float(np.mean(librosa.feature.spectral_centroid(y=chunk_np[0], sr=sr)))
            except Exception:
                centroid = 2000.0 # Standard fallback reference
                
            # Compile values into structured segment dictionaries
            segment_list.append(SegmentMetrics(
                segment_name=f"Segment {i+1} / Data Window",
                rms_db=rms_db,
                crest_factor=crest_factor,
                sub_bass_energy=sub_bass_energy,
                bass_energy=bass_energy,
                mid_energy=mid_energy,
                high_energy=high_energy,
                spectral_centroid=centroid
            ))
            
        latency = (time.perf_counter() - start_time) * 1000
        
        # Instantiate master Pydantic schema validation model
        master_profile = MasterTrackProfile(
            filename=os.path.basename(file_path),
            processing_time_ms=latency,
            segment_data=segment_list
        )
        
        # Return standard raw JSON dict to the main thread
        return master_profile.model_dump()