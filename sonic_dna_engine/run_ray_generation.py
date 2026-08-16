import os
import sys
import json
import librosa
import numpy as np
import pandas as pd
import onnxruntime as ort

# Reconfigure stdout for emoji printing in Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Import the DSP extraction function from the user's neural master script
from sonic_dna_batch_master_v5_neural import extract_dsp_features

STEMS_DIR = r"E:\OLD ABLETON\ABELTON\HY2ROGEN\bundle house pack\HY2ROGEN - BASS HOUSE TOOLS\HBHT WAV\Bass Loops"
ONNX_PATH = r"C:\WEB CASE STUDY\sonic_dna_engine\audio_llm_v1.onnx"
SIDECAR_PATH = ONNX_PATH + ".data"

def main():
    print("=" * 70)
    print("  AUDIO LLM: STEM-DRIVEN HALLUCINATION ENGINE (ONNX C++)")
    print("=" * 70)

    # 1. Load ONNX Model & Sidecar
    print("🔥 Booting Neural ONNX Engine...")
    session = ort.InferenceSession(ONNX_PATH, providers=['CPUExecutionProvider'])
    input_name = session.get_inputs()[0].name
    
    dsp_cols = [
        "Bass_Energy_Predicted", "High_Energy_Predicted", "Sub_Bass_Predicted", 
        "Mid_Energy_Predicted", "Crest_Factor_Predicted", "RMS_Target_Predicted",
        "Spectral_Centroid", "Spectral_Bandwidth", "Spectral_Rolloff", 
        "Zero_Crossing_Rate", "LRA_Target"
    ]
    
    # 2. Find Stems
    stem_files = [os.path.join(STEMS_DIR, f) for f in os.listdir(STEMS_DIR) if f.endswith(".wav")]
    if not stem_files:
        print("❌ No stems found in directory.")
        return
        
    print(f"✅ Found {len(stem_files)} stems. Extracting DSP DNA...")

    results = []

    # 3. Process each stem
    for stem_path in stem_files:
        stem_name = os.path.basename(stem_path).replace(".wav", "")
        print(f"   => Analyzing: {stem_name}")
        
        # Load audio (extract first 5 seconds to grab the initial sonic profile)
        y, sr = librosa.load(stem_path, sr=44100, mono=True, duration=5.0)
        
        if len(y) == 0:
            continue
            
        # Extract 11-dimensional input DNA
        dna_dict = extract_dsp_features(y, sr)
        dna_vector = [
            dna_dict["rms_db"], dna_dict["crest_factor"], dna_dict["sub_bass_energy"],
            dna_dict["bass_energy"], dna_dict["mid_energy"], dna_dict["high_energy"],
            dna_dict["spectral_centroid"], dna_dict["spectral_bandwidth"],
            dna_dict["spectral_rolloff"], dna_dict["spectral_contrast"],
            dna_dict["zero_crossing_rate"]
        ]
        
        # Format for ONNX (batch_size=1, in_dim=11)
        input_tensor = np.array(dna_vector, dtype=np.float32).reshape(1, 11)
        
        # 4. Hallucinate the target (Bass/Mastering Profile)
        out = session.run(None, {input_name: input_tensor})[0][0]
        
        # Package the result
        result_row = {"Stem": stem_name}
        for i, col in enumerate(dsp_cols):
            result_row[f"Gen_{col}"] = out[i]
            
        results.append(result_row)

    # 5. Display the Hallucinations
    print("\n" + "=" * 70)
    print(" 🚀 HALLUCINATED DNA PROFILES (THE SOVEREIGN OUTPUT)")
    print("=" * 70)
    
    df = pd.DataFrame(results)
    
    # Clean up column names for display
    df.columns = [c.replace("Gen_Predicted", "Gen").replace("Gen_", "") for c in df.columns]
    
    # Print the DataFrame nicely
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(df.to_string(index=False))
    
    print("\n✅ Successfully ran inference across all stems!")

if __name__ == "__main__":
    main()
