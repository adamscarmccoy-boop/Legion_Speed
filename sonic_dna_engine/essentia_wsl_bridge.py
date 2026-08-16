# essentia_wsl_bridge.py
import os
import sys
import json
import subprocess
import platform
import numpy as np
import librosa
import time
from typing import Dict, Any, List, Union

# Configuration
WSL_PYTHON_PATH = "python3" # Assumes 'python3' is available in WSL's PATH
ESSENTIA_SR = 44100         # Essentia's typical sample rate for feature extraction
LIBROSA_SR = 22050          # Librosa's default for general features
HOP_LENGTH = 512            # Standard hop length for STFT and onset detection

class EssentiaWSLBridge:
    def __init__(self):
        self._wsl_available = self._check_wsl_availability()

    def _check_wsl_availability(self) -> bool:
        if platform.system() != "Windows":
            print("WSL bridge only applicable on Windows.", file=sys.stderr)
            return False
        try:
            subprocess.run(["wsl", "true"], check=True, capture_output=True, text=True, timeout=5)
            print("WSL detected and available.", file=sys.stderr)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            print("WSL not available or not configured correctly. Will fallback to Librosa.", file=sys.stderr)
            return False

    def _run_essentia_in_wsl(self, windows_path: str) -> Dict[str, Any]:
        """
        Executes Essentia in WSL and returns parsed JSON output.
        The WSL Python script performs onset detection and feature extraction.
        """
        # Convert Windows path to WSL path format (e.g., E:\ -> /mnt/e/)
        wsl_path = subprocess.run(["wsl", "wslpath", "-u", windows_path], capture_output=True, text=True, check=True).stdout.strip()
        
        # In-line Python script for WSL execution
        # Using a single-line script to minimize dependencies and temporary files
        wsl_script = f"""
import essentia.standard as es
import numpy as np
import json
import sys

try:
    audio_path = r"{wsl_path}"
    sr = {ESSENTIA_SR}
    
    # Load audio using Essentia's MonoLoader
    loader = es.MonoLoader(filename=audio_path, sampleRate=sr)()
    audio_vector = np.array(loader) # Convert to numpy for easier slicing and math
    
    # Onset Detection (High-Frequency Content)
    onset_detector = es.OnsetDetection(method='hfc')
    windowing = es.Windowing(type='hann')
    fft = es.FFT()
    
    onset_pool = es.Pool()
    for frame in es.FrameGenerator(loader, frameSize=2048, hopSize={HOP_LENGTH}):
        mag_spectrum = fft(windowing(frame))
        onset_score = onset_detector(mag_spectrum, frame)
        onset_pool.add('onset_strength', onset_score)

    onsets = es.Onsets()
    section_timestamps_raw = onsets(onset_pool['onset_strength'], [1.0]) # 1.0 is sensitivity

    # Ensure start and end markers
    timestamps_list = sorted(list(set([0.0] + list(section_timestamps_raw) + [len(audio_vector) / sr])))

    sections_data = []
    
    for i in range(len(timestamps_list) - 1):
        start_sec = timestamps_list[i]
        end_sec = timestamps_list[i+1]
        
        start_idx = int(start_sec * sr)
        end_idx = int(end_sec * sr)
        
        if (end_idx - start_idx) < sr // 4: # Skip very short segments (<0.25 sec)
            continue
        
        chunk = audio_vector[start_idx:end_idx]
        
        rms = float(np.sqrt(np.mean(chunk**2)))
        rms_db = float(20 * np.log10(rms)) if rms > 1e-9 else -80.0
        peak = float(np.max(np.abs(chunk)))
        crest_factor = float(peak / rms) if rms > 1e-9 else 1.0

        sections_data.append({
            "segment_id": i + 1,
            "start_time_sec": round(start_sec, 3),
            "end_time_sec": round(end_sec, 3),
            "rms_db": round(rms_db, 2),
            "crest_factor": round(crest_factor, 2)
        })

    result = {
        "status": "SUCCESS",
        "engine": "Essentia_WSL",
        "total_sections_found": len(sections_data),
        "sections": sections_data
    }
    print(json.dumps(result))

except Exception as e:
    # Print error in a JSON-like format for easier parsing on Windows side
    error_report = {"status": "FAILED", "engine": "Essentia_WSL", "error": str(e), "wsl_path": audio_path if 'audio_path' in locals() else 'N/A'}
    print(json.dumps(error_report))
    sys.exit(1)
"""
        
        cmd = ["wsl", WSL_PYTHON_PATH, "-c", wsl_script]
        
        print(f"Executing Essentia in WSL for: {windows_path}...", file=sys.stderr)
        try:
            process = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=120)
            output = process.stdout.strip()
            return json.loads(output)
        except subprocess.CalledProcessError as e:
            error_output = e.stderr.strip()
            try:
                # Try to parse the WSL's script error output as JSON
                return json.loads(error_output)
            except json.JSONDecodeError:
                return {"status": "FAILED", "engine": "Essentia_WSL", "error": f"WSL execution error (Essentia): {e.stderr}", "wsl_stdout": output}
        except subprocess.TimeoutExpired:
            return {"status": "FAILED", "engine": "Essentia_WSL", "error": "WSL Essentia processing timed out after 120 seconds."}
        except FileNotFoundError:
            return {"status": "FAILED", "engine": "Essentia_WSL", "error": f"WSL Python '{WSL_PYTHON_PATH}' not found. Ensure Essentia is installed in WSL."}
        except json.JSONDecodeError:
            return {"status": "FAILED", "engine": "Essentia_WSL", "error": f"Failed to parse JSON output from WSL. Raw output: {output}"}

    def _run_librosa_fallback(self, file_path: str) -> Dict[str, Any]:
        """
        Fallback to Librosa for onset detection and feature extraction on Windows.
        """
        print(f"Falling back to Librosa for: {file_path} (WSL/Essentia not available)...", file=sys.stderr)
        start_time = time.perf_counter()
        
        try:
            y, sr = librosa.load(file_path, sr=LIBROSA_SR, mono=True)
            
            # Onset Detection
            onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=HOP_LENGTH)
            onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=HOP_LENGTH, backtrack=True)
            
            timestamps_list = librosa.frames_to_time(onset_frames, sr=sr, hop_length=HOP_LENGTH).tolist()
            timestamps_list = sorted(list(set([0.0] + timestamps_list + [librosa.get_duration(y=y, sr=sr)])))
            
            sections_data = []
            
            for i in range(len(timestamps_list) - 1):
                start_sec = timestamps_list[i]
                end_sec = timestamps_list[i+1]
                
                start_idx = int(start_sec * sr)
                end_idx = int(end_sec * sr)
                
                if (end_idx - start_idx) < sr // 4: # Skip very short segments
                    continue
                
                chunk = y[start_idx:end_idx]
                
                rms = float(np.sqrt(np.mean(chunk**2)))
                rms_db = float(20 * np.log10(rms)) if rms > 1e-9 else -80.0
                peak = float(np.max(np.abs(chunk)))
                crest_factor = float(peak / rms) if rms > 1e-9 else 1.0

                sections_data.append({
                    "segment_id": i + 1,
                    "start_time_sec": round(start_sec, 3),
                    "end_time_sec": round(end_sec, 3),
                    "rms_db": round(rms_db, 2),
                    "crest_factor": round(crest_factor, 2)
                })

            latency_ms = (time.perf_counter() - start_time) * 1000
            return {
                "status": "SUCCESS",
                "engine": "Librosa_Fallback",
                "total_sections_found": len(sections_data),
                "librosa_latency_ms": round(latency_ms, 2),
                "sections": sections_data
            }
        except Exception as e:
            return {"status": "FAILED", "engine": "Librosa_Fallback", "error": str(e)}

    def analyze_audio_structural(self, file_path: str) -> Dict[str, Any]:
        """
        Analyzes an audio file for structural segments (onsets, beats) using Essentia via WSL
        or falls back to Librosa if WSL is unavailable/fails.
        """
        if self._wsl_available:
            essentia_result = self._run_essentia_in_wsl(file_path)
            if essentia_result and essentia_result.get("status") == "SUCCESS":
                print(f"Essentia (WSL) analysis successful for {os.path.basename(file_path)}", file=sys.stderr)
                return essentia_result
            else:
                print(f"Essentia (WSL) failed or returned error: {essentia_result.get('error', 'Unknown error')}. Falling back to Librosa...", file=sys.stderr)
        
        # Fallback if WSL is not available or Essentia in WSL failed
        return self._run_librosa_fallback(file_path)

if __name__ == "__main__":
    # --- DEMO ---
    # Ensure a test WAV file exists in a known location
    # E.g., copy "what a waste-2 (Edit).wav" to your Downloads or a test folder
    TEST_AUDIO_FILE = r"E:\DJSUSAN\LEGION\what a waste-2 (Edit).wav" # Adjust path as needed

    if not os.path.exists(TEST_AUDIO_FILE):
        print(f"ERROR: Test audio file not found at '{TEST_AUDIO_FILE}'. Please create it.")
        sys.exit(1)

    bridge = EssentiaWSLBridge()
    print("\n--- Running Audio Structural Analysis Demo ---")
    
    start_time = time.perf_counter()
    analysis_report = bridge.analyze_audio_structural(TEST_AUDIO_FILE)
    end_time = time.perf_counter()
    
    total_time_ms = (end_time - start_time) * 1000

    print(f"\n--- Analysis Report for {os.path.basename(TEST_AUDIO_FILE)} ---")
    print(f"Engine Used: {analysis_report.get('engine', 'N/A')}")
    print(f"Status: {analysis_report.get('status', 'N/A')}")
    print(f"Total Sections Found: {analysis_report.get('total_sections_found', 0)}")
    print(f"Total Analysis Time: {total_time_ms:.2f} ms")
    if analysis_report.get("error"):
        print(f"Error: {analysis_report['error']}")
    
    if analysis_report.get("sections"):
        print("\nSample Sections (first 3):")
        for section in analysis_report["sections"][:3]:
            print(f"  - Seg {section['segment_id']} ({section['start_time_sec']:.2f}s-{section['end_time_sec']:.2f}s): RMS={section['rms_db']:.2f}dB, Crest={section['crest_factor']:.2f}")

    print("\n--- WSL/Essentia Setup (if not already done) ---")
    print("1. Install WSL:
