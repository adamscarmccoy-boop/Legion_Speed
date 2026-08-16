import os
import json
import sys
import time

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

from audit_and_score_downloads import (
    extract_audio_features,
    DOWNLOADS_DIR,
    ASSETS_DIR
)

def main():
    print("=" * 80)
    print("  🏆 SOVEREIGN DOWNLOADS AUDIT LEADERBOARD — SECTIONED & ESSENTIA-DRIVEN")
    print("=" * 80)
    print(f"Scanning Directory: {DOWNLOADS_DIR}...\n")
    
    if not os.path.exists(DOWNLOADS_DIR):
        print(f"❌ Downloads directory not found: {DOWNLOADS_DIR}")
        return
        
    # The perfect, symmetric head-to-head comparison list (10 raw vs 10 masters)
    target_files = [
        # --- 10 NEW DYNAMIC ENHANCED MASTERS ---
        "boys can't stop or get up off the ground_DYNAMIC_MASTERED_ENHANCED.wav",
        "7l-melodic-progressive-tech-house_DYNAMIC_MASTERED_ENHANCED.wav",
        "2-Lets Go We Win_DYNAMIC_MASTERED_ENHANCED.wav",
        "1-Lets Go We Win_DYNAMIC_MASTERED_ENHANCED.wav",
        "DADDY LOOK BACK (Edit)_DYNAMIC_MASTERED_ENHANCED.wav",
        "DADDY LOOK BACK (Edit) (1)_DYNAMIC_MASTERED_ENHANCED.wav",
        "DADDY LOOK BACK (1)_DYNAMIC_MASTERED_ENHANCED.wav",
        "come n get it_DYNAMIC_MASTERED_ENHANCED.wav",
        "come n get it mastered_DYNAMIC_MASTERED_ENHANCED.wav",
        "bass killler - parking lot gang_DYNAMIC_MASTERED_ENHANCED.wav",
        
        # --- 10 ORIGINAL RAW MIXES ---
        "boys can't stop or get up off the ground.mp3",
        "7l-melodic-progressive-tech-house.mp3",
        "2-Lets Go We Win.mp3",
        "1-Lets Go We Win.mp3",
        "DADDY LOOK BACK (Edit).mp3",
        "DADDY LOOK BACK (Edit) (1).mp3",
        "DADDY LOOK BACK (1).mp3",
        "come n get it.wav",
        "come n get it mastered.wav",
        "bass killler - parking lot gang.mp3"
    ]
    
    # Filter for targeted files that actually exist in your Downloads folder right now
    all_files = os.listdir(DOWNLOADS_DIR)
    audio_files = [f for f in target_files if f in all_files]
    
    if not audio_files:
        print("❌ None of the targeted files were found in Downloads.")
        return
        
    print(f"🔊 Found {len(audio_files)} targeted files to audit side-by-side.")
    
    report_data = []
    
    for idx, filename in enumerate(audio_files):
        file_path = os.path.join(DOWNLOADS_DIR, filename)
        print(f"[{idx+1}/{len(audio_files)}] Processing {filename}...")
        try:
            # Extract features and scores dynamically in our new Essentia-divided, phase-preserving core!
            feats, scores = extract_audio_features(file_path)
            
            track_report = {
                "filename": filename,
                "duration": feats["duration"],
                "tempo": feats.get("tempo", 126.0),
                "rms_db": feats["rms_db"],
                "crest_factor": feats["crest_factor"],
                "sub_bass_energy": feats["sub_bass_energy"],
                "bass_energy": feats["bass_energy"],
                "mid_energy": feats["mid_energy"],
                "high_energy": feats["high_energy"],
                "spectral_centroid": feats["spectral_centroid"],
                "fidelity_score": scores["fidelity_score"],
                "sonic_fit_score": scores["sonic_fit_score"],
                "market_score": scores["market_score"],
                "verdict": scores["verdict"],
                "deltas": scores["deltas"]
            }
            report_data.append(track_report)
        except Exception as e:
            print(f"⚠️ Failed to analyze {filename}: {str(e)}")
            
    if not report_data:
        print("❌ No tracks were successfully audited.")
        return
        
    # Rank tracks from BEST to WORST based on Sonic Fit Score (perceptual similarity to Chris Lake)
    ranked_tracks = sorted(report_data, key=lambda x: x["sonic_fit_score"], reverse=True)
    
    # Save ranked JSON report
    output_path = os.path.join(ASSETS_DIR, "market_score_audit_report_ranked.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ranked_tracks, f, indent=4)
        
    # Print Beautiful Leaderboard
    print("\n" + "=" * 105)
    print(f"  🥇 SOVEREIGN PEER LEADERBOARD — RAW MIXES VS DYNAMIC ENHANCED MASTERS  ")
    print("=" * 105)
    print(f"  {'Rank':<4} | {'Track Name':<45} | {'Sonic Fit':<9} | {'Market Score':<12} | {'Crest':<5} | {'RMS dB':<7}")
    print("-" * 105)
    
    for r_idx, track in enumerate(ranked_tracks):
        name_trunc = track["filename"]
        if len(name_trunc) > 45:
            name_trunc = name_trunc[:42] + "..."
            
        print(f"  #{r_idx+1:<3} | {name_trunc:<45} | {track['sonic_fit_score']:>8.1f}% | {track['market_score']:>11.1f}% | {track['crest_factor']:>5.2f} | {track['rms_db']:>7.2f}")
        
    print("=" * 105)
    print(f"💾 Full ranked report saved to: {output_path}\n")

if __name__ == "__main__":
    main()
