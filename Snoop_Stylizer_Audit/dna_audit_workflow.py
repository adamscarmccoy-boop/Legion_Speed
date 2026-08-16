
import numpy as np
import librosa
import os
import json
import soundfile as sf

def extract_acoustic_dna(file_path: str) -> np.ndarray:
    try:
        y, sr = librosa.load(file_path, sr=None)
        if len(y.shape) > 1:
            y = np.mean(y, axis=1)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        dna_vector = np.mean(chroma, axis=1)
        dna_vector = dna_vector / (np.max(dna_vector) + 1e-6)
        return dna_vector
    except Exception as e:
        print(f"Error extracting DNA from {file_path}: {e}")
        return None

def compare_dna(source_dna, target_dna):
    dot_product = np.dot(source_dna, target_dna)
    norm_source = np.linalg.norm(source_dna)
    norm_target = np.linalg.norm(target_dna)
    return dot_product / (norm_source * norm_target + 1e-6)

def run_dna_audit():
    print("=== ACOUSTIC DNA ANALYSIS WORKFLOW ===")
    TGT_FOLDER = r"C:\\WEB CASE STUDY\\Snoop_Stylizer_App\\training_audio"
    WET_FOLDER = r"C:\\WEB CASE STUDY\\Snoop_Stylizer_App\\LAPPED_FINAL_SNOOP"
    
    files = [f for f in os.listdir(TGT_FOLDER) if f.endswith('.wav')]
    target_signatures = []
    for f in files:
        dna = extract_acoustic_dna(os.path.join(TGT_FOLDER, f))
        if dna is not None:
            target_signatures.append(dna)
    
    if not target_signatures:
        print("No target DNA found.")
        return
        
    snoop_baseline_dna = np.mean(target_signatures, axis=0)
    print(f"Target Snoop DNA Baseline extracted from {len(target_signatures)} files.")
    
    wet_files = [f for f in os.listdir(WET_FOLDER) if f.endswith('.wav')]
    print("\\n[ DNA COMPARISON REPORT ]")
    print("File Name                | Match Score (0-1) | Result")
    print("----------------------------------------------------------")
    
    for f in wet_files:
        wet_dna = extract_acoustic_dna(os.path.join(WET_FOLDER, f))
        if wet_dna is not None:
            score = compare_dna(wet_dna, snoop_baseline_dna)
            status = "MATCH" if score > 0.8 else "PARTIAL" if score > 0.6 else "FAIL"
            print(f"{f:<25} | {score:.4f} | {status}")

if __name__ == "__main__":
    run_dna_audit()
