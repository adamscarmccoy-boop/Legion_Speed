import os
import sys
import subprocess

# ==============================================================================
# SOVEREIGN LAUNCHPAD
# ==============================================================================
# This is the same "Zero-Copy" mindset. 
# No complex configs. Just: Input -> Sovereign Engine -> Output.

INPUT_SAMPLES_DIR = r"C:\WEB CASE STUDY\samples"
OUTPUT_MASTERS_DIR = r"C:\WEB CASE STUDY\sovereign_masters"

os.makedirs(INPUT_SAMPLES_DIR, exist_ok=True)
os.makedirs(OUTPUT_MASTERS_DIR, exist_ok=True)

def launch_sovereign(input_file):
    output_file = os.path.join(OUTPUT_MASTERS_DIR, f"SOVEREIGN_{os.path.basename(input_file)}")
    
    print(f"🚀 Launching Sovereign-Flow-X for: {input_file}")
    
    # We call the engine script directly using the venv python
    cmd = [
        r"C:\WEB CASE STUDY\.venv\Scripts\python.exe",
        r"C:\WEB CASE STUDY\sovereign_flow_x.py",
        "--input", input_file,
        "--output", output_file
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Successfully Sculpted: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Sovereign Engine Failure: {e}")

if __name__ == "__main__":
    files = [f for f in os.listdir(INPUT_SAMPLES_DIR) if f.endswith(".wav")]
    if not files:
        print(f"📂 No .wav files found in {INPUT_SAMPLES_DIR}. Please drop some samples there!")
    else:
        for f in files:
            launch_sovereign(os.path.join(INPUT_SAMPLES_DIR, f))
