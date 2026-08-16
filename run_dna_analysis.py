import os
import sys
import numpy as np
import librosa
import json
from typing import List
from pydantic import BaseModel

# Add engine path to sys.path for import
sys.path.append(r"C:\WEB CASE STUDY\Acoustic-DNA-Audio-Engine\engine")
from analysis import AcousticDNAEngine

# Import project schemas
sys.path.append(r"C:\WEB CASE STUDY")
from legion_schema import TrackPhysics

class DNAResult(BaseModel):
    filename: str
    dna_vector: List[float]
    physics: TrackPhysics

def analyze_track_dna(file_path):
    # 1. Initialize Engine
    # The engine defaults to 44100, but we should match the file's SR
    y, sr = librosa.load(file_path, sr=None)
    engine = AcousticDNAEngine(sample_rate=sr, buffer_size=1024)
    
    # 2. Process in buffers
    buffer_size = engine.buffer_size
    all_dna = []
    
    # Process the whole file in chunks of 1024
    for i in range(0, len(y) - buffer_size, buffer_size):
        buffer = y[i : i + buffer_size].astype(np.float32)
        dna_frame = engine.process_buffer(buffer)
        all_dna.append(dna_frame)
    
    # 3. Aggregate to get global signature
    global_dna = np.mean(all_dna, axis=0).tolist()
    
    # 4. Extract basic physics for the schema
    # Using basic librosa for physics as the engine focuses on DNA
    rms = np.mean(librosa.feature.rms(y=y))
    
    physics = TrackPhysics(
        filename=os.path.basename(file_path),
        rms_db=float(20 * np.log10(rms + 1e-8))
    )
    
    return DNAResult(
        filename=os.path.basename(file_path),
        dna_vector=global_dna,
        physics=physics
    )

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_dna_analysis.py <file_path>")
        sys.exit(1)
    
    target = sys.argv[1]
    result = analyze_track_dna(target)
    print(result.model_dump_json(indent=4))
