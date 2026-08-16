import os
import time
from dynamic_segment_master import dynamic_segment_master
from audit_and_score_downloads import run_auditor_pipeline

def run_batch_pipeline():
    downloads_dir = r"C:\Users\adams\Downloads"
    files = os.listdir(downloads_dir)
    wav_files = [f for f in files if f.endswith(".wav") and not f.endswith("_DYNAMIC_MASTERED.wav") and not f.endswith("mastered.wav") and not f.endswith("mastered mono.wav")]
    
    print(f"Found {len(wav_files)} raw WAV files to master:")
    for w in wav_files:
        print(f"  - {w}")
        
    t_start = time.time()
    for w in wav_files:
        try:
            dynamic_segment_master(w)
        except Exception as e:
            print(f"Error mastering {w}: {e}")
            
    t_end = time.time()
    elapsed = t_end - t_start
    print(f"\n==============================================")
    print(f"Mastered {len(wav_files)} tracks in {elapsed:.2f} seconds!")
    print(f"==============================================")
    
    # Run the auditor again to score the new files
    print("\nRunning Audit Scorer Pipeline on the newly mastered files...")
    run_auditor_pipeline()

if __name__ == "__main__":
    run_batch_pipeline()
