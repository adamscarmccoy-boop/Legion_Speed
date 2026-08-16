import duckdb
import os
import soundfile as sf
import numpy as np
from pedalboard import Pedalboard, Compressor, HighpassFilter, Gain, Limiter

# ── 1. LOAD TARGETS FROM GROUND TRUTH ───────────────────────
DB_PATH = r"C:\WEB CASE STUDY\web_intel_sonicdb.duckdb"
INPUT_WAV = r"C:\Users\adams\Downloads\Sovereign Anchor V2.wav"
OUTPUT_WAV = r"C:\Users\adams\Downloads\Sovereign Anchor V2_MASTERED.wav"

conn = duckdb.connect(DB_PATH)
# Fetch the Chris Lake target baseline
baseline = conn.execute("SELECT rms_db, crest_factor FROM chris_lake_baseline LIMIT 1").fetchone()
conn.close()

TARGET_RMS = float(baseline[0])
TARGET_CREST = float(baseline[1])

print(f"Sovereign Baseline Loaded: {TARGET_RMS:.2f} dB RMS, {TARGET_CREST:.2f} Crest")

# ── 2. DYNAMIC MASTERING CHAIN ──────────────────────────────
def master_audio(input_path, output_path):
    y, sr = sf.read(input_path)
    
    # Calculate current metrics
    rms = np.sqrt(np.mean(y**2))
    rms_db = 20 * np.log10(rms) if rms > 1e-9 else -100.0
    peak = np.max(np.abs(y))
    crest = peak / rms if rms > 1e-9 else 0.0
    
    print(f"Current Metrics: {rms_db:.2f} dB RMS, {crest:.2f} Crest")
    
    rms_delta = TARGET_RMS - rms_db
    
    # Chain
    board = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=30.0),
        Compressor(threshold_db=rms_db - 2.0, ratio=3.0),
        Gain(gain_db=rms_delta),
        Limiter(threshold_db=-0.3)
    ])
    
    # Apply
    mastered = board(y, sr)
    sf.write(output_path, mastered, sr)
    print(f"Master saved to {output_path}")

master_audio(INPUT_WAV, OUTPUT_WAV)
