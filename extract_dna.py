import librosa
import numpy as np
import json
import sys
import os

def extract_chroma_dna(file_path):
    try:
        # Load audio
        y, sr = librosa.load(file_path, sr=None)
        
        # Extract CQT-chroma features
        # n_chroma=12 for the 12-note chromatic scale
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        
        # Average across time to get a global signature vector
        dna_vector = np.mean(chroma, axis=1)
        
        # Normalize vector to sum to 1
        if np.sum(dna_vector) > 0:
            dna_vector = dna_vector / np.sum(dna_vector)
        
        return dna_vector.tolist()
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No file path provided"}, indent=4))
        sys.exit(1)
    
    target_file = sys.argv[1]
    dna = extract_chroma_dna(target_file)
    
    print(json.dumps({
        "filename": target_file,
        "dna_vector": dna
    }, indent=4))
