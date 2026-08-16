import os
import glob
import numpy as np
import librosa
import json
from tqdm import tqdm

DOWNLOADS_DIR = r"C:\Users\adams\Downloads"
GPU_OUT_DIR = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\AI_Logs\gpu_outputs"
ARTIFACT_DIR = r"C:\Users\adams\.gemini\antigravity-ide\brain\4e030647-cd28-49d8-b366-06132364e52c"

def get_stats(wav_path):
    # Load first 30 seconds only to drastically speed up analysis on massive 50MB files
    y, sr = librosa.load(wav_path, sr=None, mono=False, duration=30.0)
    if y.ndim > 1:
        peak = np.max(np.abs(y))
        rms_left = librosa.feature.rms(y=y[0])
        rms_right = librosa.feature.rms(y=y[1])
        avg_rms = (np.mean(rms_left) + np.mean(rms_right)) / 2
    else:
        peak = np.max(np.abs(y))
        avg_rms = np.mean(librosa.feature.rms(y=y))
        
    rms_db = 20 * np.log10(avg_rms) if avg_rms > 0 else -100.0
    crest = peak / avg_rms if avg_rms > 0 else 0.0
    return rms_db, crest

def main():
    print("Finding Reference Mastered Tracks in Downloads...")
    all_files = os.listdir(DOWNLOADS_DIR)
    ref_files = [
        f for f in all_files 
        if f.lower().endswith('.wav') and 'master' in f.lower()
    ]
    
    print(f"Found {len(ref_files)} reference mastered tracks. Calculating target profile...")
    ref_rms_list = []
    ref_crest_list = []
    
    for rf in tqdm(ref_files[:10], desc="Analyzing References"):  # Limit to 10 for speed
        path = os.path.join(DOWNLOADS_DIR, rf)
        try:
            r, c = get_stats(path)
            ref_rms_list.append(r)
            ref_crest_list.append(c)
        except Exception as e:
            pass
            
    target_rms = np.mean(ref_rms_list)
    target_crest = np.mean(ref_crest_list)
    print(f"TARGET PROFILE: RMS {target_rms:.2f} dB, Crest {target_crest:.2f}")
    
    print("\nGrading 14 Mastered GPU Generations...")
    gen_files = [f for f in os.listdir(GPU_OUT_DIR) if f.endswith('_MASTERED.wav')]
    
    grades = []
    for gf in tqdm(gen_files, desc="Grading Generations"):
        path = os.path.join(GPU_OUT_DIR, gf)
        r, c = get_stats(path)
        
        # Calculate Euclidean distance / delta score (lower is better)
        rms_error = abs(r - target_rms)
        crest_error = abs(c - target_crest)
        
        # Weighted error (RMS is heavily weighted)
        total_error = rms_error + (crest_error * 2.0)
        score = 100 - (total_error * 5) # Convert to a 100-point scale
        score = max(0, min(100, score))
        
        grades.append({
            'name': gf,
            'rms': r,
            'crest': c,
            'rms_error': rms_error,
            'crest_error': crest_error,
            'score': score
        })
        
    # Sort by highest score first (Most Ready)
    grades.sort(key=lambda x: x['score'], reverse=True)
    
    # Generate Markdown Table
    md_path = os.path.join(ARTIFACT_DIR, "generation_grades.md")
    with open(md_path, "w", encoding='utf-8') as f:
        f.write("# 🏆 Generation Readiness Grades\n\n")
        f.write("These 14 tracks have been graded against the acoustic profile of the actual mastered tracks sitting in your `Downloads` folder.\n\n")
        f.write(f"**Target Reference Profile (Calculated from Downloads):**\n")
        f.write(f"- **RMS Loudness:** {target_rms:.2f} dB\n")
        f.write(f"- **Crest Factor:** {target_crest:.2f}\n\n")
        
        f.write("### Rankings (Most Ready to Least Ready)\n\n")
        f.write("| Rank | Track | Readiness Score | RMS (dB) | Crest Factor | Grade |\n")
        f.write("|------|-------|-----------------|----------|--------------|-------|\n")
        
        for i, g in enumerate(grades):
            rank = i + 1
            name_short = g['name'].replace('_MASTERED.wav', '').replace('SCARS_GPU_Output_', '')
            score = g['score']
            
            if score >= 90: grade_let = "S-Tier 👑"
            elif score >= 80: grade_let = "A-Tier 🔥"
            elif score >= 70: grade_let = "B-Tier ✅"
            else: grade_let = "Needs Mix 🛠️"
            
            f.write(f"| {rank} ")
            f.write(f"| `...{name_short}` ")
            f.write(f"| **{score:.1f}/100** ")
            f.write(f"| {g['rms']:.2f} ")
            f.write(f"| {g['crest']:.2f} ")
            f.write(f"| {grade_let} |\n")
            
    print(f"\nSaved Grades to {md_path}")

if __name__ == "__main__":
    main()
