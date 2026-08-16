import os
import subprocess
import json
import time
import librosa
import numpy as np

# --- Configuration ---
# Set to True if you have WSL installed and essentia is available in its python3 environment
USE_WSL_ESSENTIA = True 
WSL_PYTHON_PATH = "python3" # The command to invoke Python inside WSL (e.g., 'python3' or '/usr/bin/python3')

def _run_wsl_command(command: str) -> str:
    """Executes a command inside WSL and returns stdout."""
    try:
        # Use 'wsl -e' to execute a command without an interactive shell
        result = subprocess.run(['wsl', '-e'] + command.split(), capture_output=True, text=True, check=True, encoding='utf-8')
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"WSL command failed with exit code {e.returncode}: {e.stderr}", flush=True)
        raise
    except FileNotFoundError:
        print("WSL is not installed or not in PATH.", flush=True)
        raise
    except Exception as e:
        print(f"An unexpected error occurred while calling WSL: {e}", flush=True)
        raise

def _get_essentia_script(audio_filepath: str) -> str:
    """Generates the Python script to be run inside WSL for Essentia analysis."""
    # Note: Essentia expects POSIX paths within WSL
    # We must double all curly braces to escape them in the Python f-string!
    wsl_filepath = audio_filepath.replace("C:", "/mnt/c").replace("D:", "/mnt/d").replace("E:", "/mnt/e").replace("\\", "/")

    script = f"""
import essentia.standard as es
import numpy as np
import json
import os

try:
    if not os.path.exists('{wsl_filepath}'):
        raise FileNotFoundError(f"Essentia WSL: Audio file not found at {{'{wsl_filepath}'}}")

    loader = es.MonoLoader(filename='{wsl_filepath}', sampleRate=44100)
    audio_vector = loader()

    # Onset Detection (High-Frequency Content method)
    onset_detector = es.OnsetDetection(method='hfc')
    windowing = es.Windowing(type='hann')
    fft = es.FFT()

    pool = es.Pool()
    for frame in es.FrameGenerator(audio_vector, frameSize=1024, hopSize=512):
        mag_spectrum = fft(windowing(frame))
        onset_score = onset_detector(mag_spectrum, frame)
        pool.add('onset_strength', onset_score)

    onsets_alg = es.Onsets()
    section_timestamps = onsets_alg(pool['onset_strength'], [1.0])

    # Append start and end markers
    timestamps_list = sorted(list(set([0.0] + list(section_timestamps) + [len(audio_vector) / 44100.0])))

    sections_data = []
    for i in range(len(timestamps_list) - 1):
        start_sec = timestamps_list[i]
        end_sec = timestamps_list[i+1]
        
        # Ensure minimum chunk size to avoid errors
        if (end_sec - start_sec) < 0.05: # minimum 50ms
            continue

        start_idx = int(start_sec * 44100)
        end_idx = int(end_sec * 44100)
        
        chunk = audio_vector[start_idx:end_idx]
        
        # Basic feature extraction (simplified for speed)
        rms = np.sqrt(np.mean(chunk**2)) if len(chunk) > 0 else 0.0
        rms_db = float(20 * np.log10(rms)) if rms > 1e-9 else -80.0
        peak = float(np.max(np.abs(chunk))) if len(chunk) > 0 else 0.0
        crest_factor = float(peak / rms) if rms > 1e-9 else 0.0

        sections_data.append({{
            "segment_id": i + 1,
            "start_time_sec": round(start_sec, 3),
            "end_time_sec": round(end_sec, 3),
            "rms_db": rms_db,
            "crest_factor": crest_factor
        }})

    print(json.dumps({{
        "status": "SUCCESS",
        "sections": sections_data,
        "total_sections": len(sections_data),
        "engine": "Essentia_C++"
    }}))

except Exception as e:
    print(json.dumps({{
        "status": "FAILED",
        "error": str(e),
        "engine": "Essentia_C++"
    }}))
"""
    return script

def _librosa_fallback_analysis(audio_filepath: str, sr: int = 22050) -> dict:
    """Performs structural analysis using Librosa macro-blocks (10s) as a fallback."""
    print(f"⚠️ Slicing track into clean 10-second musical macro-blocks for: {os.path.basename(audio_filepath)}", flush=True)
    start_time = time.perf_counter()
    
    try:
        y, sr_load = librosa.load(audio_filepath, sr=sr, mono=True)
        duration = len(y) / sr
        
        # Slices by 10-second blocks for perfect dynamic compression glue!
        block_sec = 10.0
        num_blocks = int(np.ceil(duration / block_sec))
        
        sections_data = []
        for i in range(num_blocks):
            start_sec = i * block_sec
            end_sec = min(duration, (i + 1) * block_sec)
            
            if (end_sec - start_sec) < 0.1:
                continue

            start_sample = int(start_sec * sr)
            end_sample = int(end_sec * sr)
            chunk = y[start_sample:end_sample]
            
            rms = np.sqrt(np.mean(chunk**2)) if len(chunk) > 0 else 0.0
            rms_db = float(20 * np.log10(rms)) if rms > 1e-9 else -80.0
            peak = float(np.max(np.abs(chunk))) if len(chunk) > 0 else 0.0
            crest_factor = float(peak / rms) if rms > 1e-9 else 0.0

            sections_data.append({
                "segment_id": i + 1,
                "start_time_sec": round(start_sec, 3),
                "end_time_sec": round(end_sec, 3),
                "rms_db": rms_db,
                "crest_factor": crest_factor
            })

        latency_ms = (time.perf_counter() - start_time) * 1000
        return {
            "status": "SUCCESS",
            "sections": sections_data,
            "total_sections": len(sections_data),
            "engine": "Librosa_MacroBlocks_Python",
            "latency_ms": latency_ms
        }
    except Exception as e:
        print(f"❌ Librosa fallback failed: {e}", flush=True)
        return {
            "status": "FAILED",
            "error": str(e),
            "engine": "Librosa_MacroBlocks_Python"
        }

def get_structural_audio_analysis(audio_filepath: str) -> dict:
    """
    Analyzes an audio file to extract structural section boundaries (onsets/beats)
    and basic DSP features for each section. Prioritizes Essentia via WSL for speed,
    falls back to Librosa if WSL is unavailable or fails.
    Returns a dictionary with section data and analysis metadata.
    """
    if not os.path.exists(audio_filepath):
        return {"status": "FAILED", "error": f"Audio file not found: {audio_filepath}"}

    if USE_WSL_ESSENTIA:
        print(f"🔥 Attempting Essentia C++ analysis via WSL for: {os.path.basename(audio_filepath)}", flush=True)
        start_time = time.perf_counter()
        
        try:
            # Pass the Essentia script as a string to WSL Python
            wsl_command = f"{WSL_PYTHON_PATH} -c \"{_get_essentia_script(audio_filepath).replace('\"', '\\\"')}\""
            # Need to escape the script content for shell execution inside WSL
            
            wsl_output = _run_wsl_command(wsl_command)
            
            result = json.loads(wsl_output)
            result["latency_ms"] = (time.perf_counter() - start_time) * 1000
            
            if result.get("status") == "SUCCESS":
                return result
            else:
                print(f"Essentia C++ reported failure: {result.get('error', 'Unknown error')}. Falling back.", flush=True)
                return _librosa_fallback_analysis(audio_filepath)
                
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
            print(f"WSL/Essentia bridge error: {e}. Falling back to Librosa.", flush=True)
            return _librosa_fallback_analysis(audio_filepath)
        except Exception as e:
            print(f"Unhandled error in WSL/Essentia bridge: {e}. Falling back to Librosa.", flush=True)
            return _librosa_fallback_analysis(audio_filepath)
    else:
        return _librosa_fallback_analysis(audio_filepath)
