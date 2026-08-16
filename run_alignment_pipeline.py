import os
import sys
import numpy as np
import librosa
import ray
import pandas as pd
from typing import List
from pydantic import BaseModel

# Add project paths
sys.path.append(r"C:\WEB CASE STUDY")
from legion_schema import SegmentPhysics, AlignmentQuery

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


# Add engine paths
sys.path.append(r"C:\WEB CASE STUDY\Acoustic-DNA-Audio-Engine\engine")
from analysis import AcousticDNAEngine

# --- CONFIG ---
LANCEDB_PATH = r"C:\WEB CASE STUDY\lancedb_data"
TABLE_NAME = "omni_semantic_baselines"
SEGMENT_DURATION = 5.0  # seconds per segment

class AlignmentRunner:
    def __init__(self):
        ray.init(ignore_reinit_error=True)
        
        # 1. Initialize Actor
        from dsp_alignment_actor import DSPAlignmentActor
        self.actor = DSPAlignmentActor.remote(LANCEDB_PATH, TABLE_NAME)
        
        # 2. Setup Baseline (Assuming baseline exists in DB)
        # We'll use a dummy batch for now or load from DB if possible
        # In a real run, we'd pull the 'Somebody' track as baseline
        print("[Sovereign] Actor Initialized. Baseline awaiting setup...")

    def extract_physics(self, file_path):
        y, sr = librosa.load(file_path, sr=None)
        engine = AcousticDNAEngine(sample_rate=sr)
        
        samples_per_seg = int(SEGMENT_DURATION * sr)
        segments = []
        
        for i in range(0, len(y) - samples_per_seg, samples_per_seg):
            chunk = y[i : i + samples_per_seg]
            
            # Basic physics extraction
            rms = np.sqrt(np.mean(chunk**2))
            peak = np.max(np.abs(chunk))
            crest = 20 * np.log10(peak / rms) if rms > 1e-9 else 0
            
            # Simple spectral split
            S = np.abs(librosa.stft(chunk))
            freqs = librosa.fft_frequencies(sr=sr)
            
            def get_energy(f_min, f_max):
                mask = (freqs >= f_min) & (freqs <= f_max)
                return np.sum(S[mask, :]) / np.sum(S) if np.sum(S) > 0 else 0
            
            segments.append(SegmentPhysics(
                segment_name=f"seg_{i // samples_per_seg}",
                track_name=os.path.basename(file_path),
                rms_db=float(20 * np.log10(rms + 1e-8)),
                crest_factor=float(crest),
                sub_bass_energy=get_energy(20, 60),
                bass_energy=get_energy(60, 250),
                mid_energy=get_energy(250, 4000),
                high_energy=get_energy(4000, 20000)
            ))
            
        return segments

    def run_alignment(self, file_path):
        print(f"\n--- Aligning: {os.path.basename(file_path)} ---")
        segments = self.extract_physics(file_path)
        
        # Dispatch to Actor
        queries = [
            {"targ_idx": i, "targ_segment": seg.model_dump()} 
            for i, seg in enumerate(segments)
        ]
        
        # Parallel execution via Ray
        results = ray.get([self.actor.align_segment.remote(q) for q in queries])
        
        # Print report
        print(f"{'Segment':<12} | {'Matched Base':<20} | {'Score':<8} | {'Status'}")
        print("-" * 55)
        for r in results:
            print(f"{r['targ_name']:<12} | {r['matched_base']:<20} | {r['alignment_score']:<8} | {r['status']}")

if __name__ == "__main__":
    runner = AlignmentRunner()
    
    # Files to process
    tracks = [
        r"C:\Users\adams\Downloads\GIRL NAME DREAM -  i need that_MASTERED.wav",
        r"C:\Users\adams\Downloads\GIRL NAME DREAM -  i need that Stems\3 Bass.wav",
        r"C:\Users\adams\Downloads\GIRL NAME DREAM -  i need that Stems\5 Synth.wav"
    ]
    
    for t in tracks:
        runner.run_alignment(t)
    
    ray.shutdown()