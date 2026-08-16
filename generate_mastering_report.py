import os
import glob
import numpy as np
import librosa
import matplotlib.pyplot as plt
import soundfile as sf

GPU_OUT_DIR = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\AI_Logs\gpu_outputs"
ARTIFACT_DIR = r"C:\Users\adams\.gemini\antigravity-ide\brain\4e030647-cd28-49d8-b366-06132364e52c"

def get_stats(wav_path):
    y, sr = librosa.load(wav_path, sr=None, mono=False)
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
    raw_files = [f for f in os.listdir(GPU_OUT_DIR) if f.endswith('.wav') and not f.endswith('_MASTERED.wav')]
    
    results = []
    
    print("Calculating statistics for all tracks...")
    for rf in raw_files:
        raw_path = os.path.join(GPU_OUT_DIR, rf)
        mastered_name = rf.replace('.wav', '_MASTERED.wav')
        mastered_path = os.path.join(GPU_OUT_DIR, mastered_name)
        
        if not os.path.exists(mastered_path):
            continue
            
        raw_rms, raw_crest = get_stats(raw_path)
        mst_rms, mst_crest = get_stats(mastered_path)
        
        results.append({
            'name': rf,
            'raw_rms': raw_rms, 'raw_crest': raw_crest,
            'mst_rms': mst_rms, 'mst_crest': mst_crest
        })
        print(f"Processed: {rf}")
        
    # Generate Plot
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    raw_rms_vals = [r['raw_rms'] for r in results]
    mst_rms_vals = [r['mst_rms'] for r in results]
    raw_crest_vals = [r['raw_crest'] for r in results]
    mst_crest_vals = [r['mst_crest'] for r in results]
    
    # Plot 1: RMS Loudness Shift
    for i in range(len(results)):
        ax1.plot([1, 2], [raw_rms_vals[i], mst_rms_vals[i]], 'o-', color='#00ff88', alpha=0.6, linewidth=2)
    ax1.axhline(-10.0, color='white', linestyle='--', alpha=0.5, label='Target (-10.0 dB)')
    ax1.set_xticks([1, 2])
    ax1.set_xticklabels(['Raw Generation', 'Sovereign Mastered'])
    ax1.set_ylabel('RMS Loudness (dB)')
    ax1.set_title('Dynamic Gain Staging (Loudness Alignment)')
    ax1.grid(True, alpha=0.1)
    ax1.legend()
    
    # Plot 2: Crest Factor Shift
    for i in range(len(results)):
        ax2.plot([1, 2], [raw_crest_vals[i], mst_crest_vals[i]], 'o-', color='#ff00ff', alpha=0.6, linewidth=2)
    ax2.axhline(3.63, color='white', linestyle='--', alpha=0.5, label='Target (3.63)')
    ax2.set_xticks([1, 2])
    ax2.set_xticklabels(['Raw Generation', 'Sovereign Mastered'])
    ax2.set_ylabel('Crest Factor (Dynamics)')
    ax2.set_title('Transient Compression & Glue')
    ax2.grid(True, alpha=0.1)
    ax2.legend()
    
    plt.suptitle('Sovereign DSP Mastering Results (14 GPU Generations)', fontsize=16, color='white')
    plt.tight_layout()
    
    plot_path = os.path.join(ARTIFACT_DIR, "mastering_plot.png")
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"Saved plot to {plot_path}")
    
    # Generate Markdown Table
    md_path = os.path.join(ARTIFACT_DIR, "mastering_results.md")
    with open(md_path, "w", encoding='utf-8') as f:
        f.write("# 🎧 Sovereign DSP Mastering Results\n\n")
        f.write("Here is the visual proof and data calculations for the mastering pass applied to all 14 GPU generated tracks.\n\n")
        f.write("![Mastering Plot](file:///C:/Users/adams/.gemini/antigravity-ide/brain/4e030647-cd28-49d8-b366-06132364e52c/mastering_plot.png)\n\n")
        f.write("### Before vs After Calculations\n\n")
        f.write("| Track ID | Raw RMS (dB) | Mastered RMS | Gain Shift | Raw Crest | Mastered Crest | Dynamics Shift |\n")
        f.write("|----------|--------------|--------------|------------|-----------|----------------|----------------|\n")
        
        for r in results:
            name_short = r['name'].split('_')[-1].replace('.wav', '')
            rms_shift = r['mst_rms'] - r['raw_rms']
            crest_shift = r['mst_crest'] - r['raw_crest']
            
            f.write(f"| `...{name_short}` ")
            f.write(f"| {r['raw_rms']:.2f} ")
            f.write(f"| **{r['mst_rms']:.2f}** ")
            f.write(f"| {rms_shift:+.2f} dB ")
            f.write(f"| {r['raw_crest']:.2f} ")
            f.write(f"| **{r['mst_crest']:.2f}** ")
            f.write(f"| {crest_shift:+.2f} |\n")
            
    print(f"Saved MD report to {md_path}")

if __name__ == "__main__":
    main()
