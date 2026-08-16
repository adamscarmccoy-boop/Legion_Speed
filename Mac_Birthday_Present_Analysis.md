This is such a thoughtful and fun birthday gift idea! Your approach of using native PyTorch and Pedalboard for ultra-low latency is brilliant, especially for real-time presentations. Let's make sure this gift is absolutely flawless for her Mac desktop.

After a thorough review of your provided files and project description, I've identified a few key areas to enhance Mac compatibility and ensure a truly foolproof installation and user experience.

---

### 🔍 Mac Compatibility & Ease of Use Analysis

1. **Hardcoded Windows Paths:**
    * **Found:** In `snoop_dolly_test.py` and `snoop_run_test.py`, the `YTDLP_PATH = r"C:\WEB CASE STUDY\.venv\Scripts\yt-dlp.exe"` is a Windows-specific path.
    * **Impact:** These scripts will fail on a Mac. While they are "test" scripts, `snoop_dolly_test.py` is crucial for generating the "Dolly" profile the app expects.
    * **Fix:** We'll update these to use a platform-agnostic way to call `yt-dlp` as a Python module.

2. **Missing Python Dependencies in `install_mac.command`:**
    * **Found:** Your `install_mac.command` currently only installs `pyaudio` and `numpy`.
    * **Missing:** `pedalboard`, `torch`, `librosa`, `soundfile`, and `yt-dlp` are essential. `pedalboard` and `torch` are core to your DSP pipeline, `librosa` and `soundfile` are used for audio processing and profile generation, and `yt-dlp` is used for ingesting source audio.
    * **Impact:** The app and profile generation will fail with "ModuleNotFoundError".
    * **Fix:** We'll add all these to the `pip install` command in `install_mac.command`.

3. **Voice Profile Generation Not Integrated with `install_mac.command`:**
    * **Found:** The `snoop_voice_app.py` relies heavily on `Snoop_pitch_delta.pt` (and potentially `snoop_dna.pt`) to be present. The UI also offers "Dolly", "Drake", and "Michael" profiles, which would require `Dolly_pitch_delta.pt`, etc.
    * **Missing:** `install_mac.command` currently only launches the app, it doesn't run `snoop_voice_engine.ipynb` (or its equivalent `.py` script) or `snoop_dolly_test.py` to generate these crucial `.pt` files. Also, `snoop_voice_engine.ipynb` is a notebook, which isn't directly runnable by a shell script.
    * **Impact:** The app will likely default to an arbitrary `shift_delta` or error, severely impacting the core functionality and "birthday gift" experience.
    * **Fix:** We'll convert the relevant parts of your notebook into a standalone Python script (`snoop_profile_generator.py`) and modify `snoop_dolly_test.py` into `dolly_profile_generator.py`. We'll then add steps to `install_mac.command` to execute these scripts and generate the necessary `.pt` files. I'll also guide you on how to create similar scripts for Drake and Michael.

4. **`sys.stdout.reconfigure` in `snoop_voice_engine.ipynb`:**
    * **Found:** `try: sys.stdout.reconfigure(encoding='utf-8') except: pass` is present.
    * **Impact:** This is primarily a Windows-specific workaround. On macOS, stdout is typically UTF-8 by default, so this block is benign but unnecessary.
    * **Fix:** No action needed, the `try-except` makes it safe.

5. **Project Structure & Paths:**
    * **Found:** Your description mentions `C:\WEB CASE STUDY\Snoop_Stylizer_App`. On Mac, this simply becomes the folder where the app is located.
    * **Impact:** The `install_mac.command` correctly uses relative paths (`cd "$DIR"`), so all `.pt` files and audio downloads will be handled correctly within the project directory.
    * **Fix:** No action needed, it's robust.

---

### ✅ Actionable Fixes for a Perfect Birthday Gift

Here are the precise changes and instructions to make this application shine on her Mac:

#### Step 1: Prepare the Profile Generation Scripts

You'll need two new files in your project directory: `snoop_profile_generator.py` and `dolly_profile_generator.py`.

**A. Create `snoop_profile_generator.py`**
This script will extract the core logic from your `snoop_voice_engine.ipynb` to generate `Snoop_pitch_delta.pt` and `snoop_dna.pt`.

**File: `snoop_profile_generator.py`** (Create this new file)

```python
import os
import subprocess
import librosa
import soundfile as sf
import numpy as np
import torch
import warnings
import sys
warnings.filterwarnings('ignore')

# Use sys.executable -m yt_dlp for platform independence
YTDLP_CMD = [sys.executable, "-m", "yt_dlp"]

# --- Profile Generation Logic (from snoop_voice_engine.ipynb) ---
def download_clip(query, output_name, duration_segment="*00:01:30-00:01:45"):
    print(f"Downloading {output_name} for '{query}'...")
    cmd = YTDLP_CMD + [
        "-f", "bestaudio[ext=m4a]",
        "--match-filter", "!is_live",
        "--download-sections", duration_segment, # Rip 15 seconds from the middle of the video
        "-o", output_name + ".m4a",
        f"ytsearch1:{query}"
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def extract_dsp_footprint(filepath):
    loaded_filepath = None
    if os.path.exists(filepath + ".m4a"):
        loaded_filepath = filepath + ".m4a"
    elif os.path.exists(filepath + ".wav"):
        loaded_filepath = filepath + ".wav"
    
    if loaded_filepath:
        y, sr = librosa.load(loaded_filepath, sr=22050)
    else:
        print(f"Error: File {filepath} not found for DSP extraction!")
        return 100.0, np.zeros(13), np.zeros(1024), 22050
    
    f0, voiced_flag, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C3'), fmax=librosa.note_to_hz('C6'), sr=sr)
    valid_f0 = f0[voiced_flag]
    mean_pitch = np.median(valid_f0) if len(valid_f0) > 0 else 100.0
    
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mean_mfccs = np.mean(mfccs, axis=1)
    
    return mean_pitch, mean_mfccs, y, sr

def generate_snoop_profile():
    print("\n--- Generating Snoop Dogg Voice Profile ---")
    
    for f in ["snoop1.m4a", "snoop2.m4a", "snoop3.m4a", "base_voice.m4a"]:
        if os.path.exists(f): os.remove(f)

    # Download 3 Snoop Dogg Interviews (Raw Vocals)
    download_clip("snoop dogg breakfast club interview", "snoop1")
    download_clip("snoop dogg howard stern interview", "snoop2")
    download_clip("snoop dogg jimmy kimmel interview", "snoop3")

    # Download 1 Medical Instructor (Input) - Renamed to base_voice for generic use
    download_clip("medical instructor cardiovascular lecture", "base_voice") 

    print("✅ Snoop Profile: Data Ingestion Complete!")

    # Average the Snoop Targets
    snoop_pitches = []
    snoop_mfccs_list = []
    for f in ["snoop1", "snoop2", "snoop3"]:
        p, m, _, _ = extract_dsp_footprint(f)
        snoop_pitches.append(p)
        snoop_mfccs_list.append(m)

    snoop_pitch = np.mean(snoop_pitches)
    snoop_mfcc = np.mean(snoop_mfccs_list, axis=0)

    base_voice_pitch, base_voice_mfcc, _, _ = extract_dsp_footprint("base_voice")

    print(f"🎤 Snoop Profile: Base Voice Pitch: {base_voice_pitch:.1f} Hz")
    print(f"🌿 Snoop Profile: Averaged Snoop Pitch: {snoop_pitch:.1f} Hz")

    pitch_shift_ratio = snoop_pitch / base_voice_pitch
    semitones_shift = 12 * np.log2(pitch_shift_ratio)
    print(f"➡️ Snoop Profile: Required Math Shift: {semitones_shift:.2f} semitones.")

    # Save PyTorch Weights
    delta_mfcc = torch.tensor(snoop_mfcc - base_voice_mfcc, dtype=torch.float32)
    torch.save(delta_mfcc, 'snoop_dna.pt') # Not directly used by app, but good to save
    torch.save(torch.tensor([semitones_shift], dtype=torch.float32), 'Snoop_pitch_delta.pt') # Consistent with app's load_profile

    print("✅ Snoop Profile: Saved 'snoop_dna.pt' and 'Snoop_pitch_delta.pt'")

    # Clean up downloaded files
    for f in ["snoop1.m4a", "snoop2.m4a", "snoop3.m4a", "base_voice.m4a"]:
        if os.path.exists(f): os.remove(f)

if __name__ == "__main__":
    generate_snoop_profile()
```

**B. Create `dolly_profile_generator.py`**
This script will be derived from your `snoop_dolly_test.py`, but with the Windows path fixed and focused on generating `Dolly_pitch_delta.pt`.

**File: `dolly_profile_generator.py`** (Create this new file)

```python
import os
import subprocess
import librosa
import numpy as np
import torch
import sys
import warnings
warnings.filterwarnings('ignore')

YTDLP_CMD = [sys.executable, "-m", "yt_dlp"]

def generate_dolly_profile():
    print("\n--- Generating Dolly Parton Voice Profile ---")
    
    dolly_audio_path = "dolly_target.wav"
    base_audio_path = "base_voice_dolly_profile.wav"

    # Clean up previous downloads if they exist
    for f in [dolly_audio_path, base_audio_path]:
        if os.path.exists(f): os.remove(f)

    # 1. Download Dolly Audio
    print("[1/3] Pulling Dolly Parton vocals...")
    subprocess.run(YTDLP_CMD + [
        "ytsearch1:dolly parton isolated vocals",
        "--extract-audio", "--audio-format", "wav", "-o", dolly_audio_path
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 2. Download a base speaker audio (e.g., a TED Talk)
    print("[2/3] Pulling random TED Talk lecture for base voice...")
    subprocess.run(YTDLP_CMD + [
        "ytsearch1:ted talk science lecture",
        "--extract-audio", "--audio-format", "wav", "-o", base_audio_path
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 3. Calculate PyTorch Delta
    print("[3/3] Calculating Semantic Delta for Dolly...")
    
    def extract_pitch(filepath, duration=15):
        try:
            y, sr = librosa.load(filepath, sr=22050, duration=duration)
            f0, voiced_flag, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C3'), fmax=librosa.note_to_hz('C6'), sr=sr)
            valid_f0 = f0[voiced_flag]
            return np.median(valid_f0) if len(valid_f0) > 0 else 200.0
        except Exception as e:
            print(f"Error extracting pitch from {filepath}: {e}")
            return 200.0 # Fallback

    dolly_pitch = extract_pitch(dolly_audio_path)
    base_pitch = extract_pitch(base_audio_path)
    
    if base_pitch == 0 or dolly_pitch == 0: # Avoid division by zero
        print("Warning: Could not determine pitch for Dolly profile, using default shift.")
        semitones_shift = 0.0 # Or some safe default
    else:
        shift_ratio = dolly_pitch / base_pitch
        semitones_shift = 12 * np.log2(shift_ratio)
    
    # Save the Dolly weight
    torch.save(torch.tensor([semitones_shift], dtype=torch.float32), 'Dolly_pitch_delta.pt')
    print(f"✅ Dolly Profile: Pitch Delta Calculated: {semitones_shift:.2f} semitones")
    
    # Clean up downloaded files
    for f in [dolly_audio_path, base_audio_path]:
        if os.path.exists(f): os.remove(f)

if __name__ == "__main__":
    generate_dolly_profile()
```

**C. (Optional but Recommended) Create `drake_profile_generator.py` and `michael_profile_generator.py`**
To make the "Drake" and "Michael" profiles work flawlessly, you'd create similar scripts. For example, for Drake:

**File: `drake_profile_generator.py`** (Example, you'll need to adapt the `ytsearch1` query)

```python
# ... (Similar imports and YTDLP_CMD as dolly_profile_generator.py) ...

def generate_drake_profile():
    print("\n--- Generating Drake Voice Profile ---")
    drake_audio_path = "drake_target.wav"
    base_audio_path = "base_voice_drake_profile.wav"
    for f in [drake_audio_path, base_audio_path]:
        if os.path.exists(f): os.remove(f)

    print("[1/3] Pulling Drake vocals...")
    subprocess.run(YTDLP_CMD + [
        "ytsearch1:drake interview vocals only", # Adjust query for good source
        "--extract-audio", "--audio-format", "wav", "-o", drake_audio_path
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print("[2/3] Pulling random TED Talk lecture for base voice...")
    subprocess.run(YTDLP_CMD + [
        "ytsearch1:ted talk business lecture", # Another generic base voice
        "--extract-audio", "--audio-format", "wav", "-o", base_audio_path
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print("[3/3] Calculating Semantic Delta for Drake...")
    def extract_pitch(filepath, duration=15): # ... (same function as above) ...
        try:
            y, sr = librosa.load(filepath, sr=22050, duration=duration)
            f0, voiced_flag, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C3'), fmax=librosa.note_to_hz('C6'), sr=sr)
            valid_f0 = f0[voiced_flag]
            return np.median(valid_f0) if len(valid_f0) > 0 else 120.0 # Drake's pitch is generally lower than Dolly's
        except Exception as e:
            print(f"Error extracting pitch from {filepath}: {e}")
            return 120.0

    drake_pitch = extract_pitch(drake_audio_path)
    base_pitch = extract_pitch(base_audio_path)
    
    if base_pitch == 0 or drake_pitch == 0:
        print("Warning: Could not determine pitch for Drake profile, using default shift.")
        semitones_shift = 0.0
    else:
        shift_ratio = drake_pitch / base_pitch
        semitones_shift = 12 * np.log2(shift_ratio)
    
    torch.save(torch.tensor([semitones_shift], dtype=torch.float32), 'Drake_pitch_delta.pt')
    print(f"✅ Drake Profile: Pitch Delta Calculated: {semitones_shift:.2f} semitones")
    
    for f in [drake_audio_path, base_audio_path]:
        if os.path.exists(f): os.remove(f)

if __name__ == "__main__":
    generate_drake_profile()
```

*Do the same for `michael_profile_generator.py` by finding suitable "Michael" (e.g., Michael Jackson, Michael Bublé, depending on your target) audio and adjusting the `ytsearch1` query.*

#### Step 2: Update `install_mac.command`

This is the most critical change for ease of use. It will now install all dependencies and generate the voice profiles automatically.

**File: `install_mac.command`** (Replace your existing file with this)

```bash
#!/bin/bash
echo "==========================================="
echo "🎙️ Installing Medical Voice Stylizer (Mac)"
echo "==========================================="

# 1. Install Homebrew if not found
if ! command -v brew &> /dev/null
then
    echo "🍺 Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add brew to PATH for Apple Silicon just in case
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    echo "✅ Homebrew is already installed."
fi

# 2. Install System Dependencies
echo "🎧 Installing PortAudio (required for PyAudio)..."
brew install portaudio

echo "🎛️ Installing BlackHole Virtual Audio Cable (for PowerPoint/Zoom)..."
brew install --cask blackhole-2ch

# 3. Setup Python Virtual Environment
echo "🐍 Setting up Python environment..."
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$DIR"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

echo "📦 Installing Python packages (this might take a few minutes)..."
pip install --upgrade pip
# Install all required Python packages
pip install pyaudio numpy pedalboard torch librosa soundfile yt-dlp

# 4. Generate Voice Profiles (Crucial for the app's functionality!)
echo "🧬 Generating initial voice profiles (Snoop, Dolly)... This will download audio clips and calculate math. Please be patient."

# Ensure profile generation scripts are present (you'll create these files)
if [ -f "snoop_profile_generator.py" ]; then
    python snoop_profile_generator.py
else
    echo "❗ Warning: snoop_profile_generator.py not found. Snoop Dogg profile might not be available."
fi

if [ -f "dolly_profile_generator.py" ]; then
    python dolly_profile_generator.py
else
    echo "❗ Warning: dolly_profile_generator.py not found. Dolly Parton profile might not be available."
fi

# (Optional: Add similar checks and calls for Drake and Michael if you create their scripts)
# if [ -f "drake_profile_generator.py" ]; then
#     python drake_profile_generator.py
# fi
# if [ -f "michael_profile_generator.py" ]; then
#     python michael_profile_generator.py
# fi

echo "==========================================="
echo "✅ Installation & Profile Generation Complete!"
echo "🚀 Launching Voice Stylizer..."
echo "==========================================="

python snoop_voice_app.py
```

#### Step 3: Update `snoop_dolly_test.py` and `snoop_run_test.py`

These are primarily test scripts, but fixing the `YTDLP_PATH` ensures they are also Mac-compatible if you decide to use them later.

**A. Update `snoop_dolly_test.py`** (if you keep it, otherwise it's replaced by `dolly_profile_generator.py`)
If you decide to keep `snoop_dolly_test.py` as a separate test script (and not rename it to `dolly_profile_generator.py`):

```python
import os
import subprocess
import librosa
import numpy as np
import soundfile as sf
import torch
from pedalboard import Pedalboard, Compressor, PitchShift, LowpassFilter, Delay
import sys # <--- ADD THIS

# YTDLP_PATH = r"C:\WEB CASE STUDY\.venv\Scripts\yt-dlp.exe" # <--- REMOVE OR COMMENT OUT THIS LINE
YTDLP_CMD = [sys.executable, "-m", "yt_dlp"] # <--- ADD THIS LINE

def run_test():
    print("STARTING DOLLY PARTON END-TO-END TEST")
    
    # 1. Download Dolly Audio
    print("\n[1/4] Pulling Dolly Parton vocals...")
    if os.path.exists("dolly_test.wav"): os.remove("dolly_test.wav")
    subprocess.run(YTDLP_CMD + [ # <--- USE YTDLP_CMD HERE
        "ytsearch1:dolly parton isolated vocals",
        "--extract-audio", "--audio-format", "wav", "-o", "dolly_test.%(ext)s"
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # ... (rest of the script remains the same) ...
    # Ensure the final torch.save is 'Dolly_pitch_delta.pt' for consistency
    torch.save(torch.tensor([semitones_shift], dtype=torch.float32), 'Dolly_pitch_delta.pt') 
    # ...
```

**B. Update `snoop_run_test.py`**

```python
import os
import subprocess
import librosa
import numpy as np
import soundfile as sf
import torch
from pedalboard import Pedalboard, Compressor, PitchShift, LowpassFilter, Delay
import sys # <--- ADD THIS

# YTDLP_PATH = r"C:\WEB CASE STUDY\.venv\Scripts\yt-dlp.exe" # <--- REMOVE OR COMMENT OUT THIS LINE
YTDLP_CMD = [sys.executable, "-m", "yt_dlp"] # <--- ADD THIS LINE

def run_test():
    print("STARTING SNOOP DOGG END-TO-END TEST")
    
    ted_talk_path = "ted_talk_test.wav" # Define path explicitly
    if not os.path.exists(ted_talk_path):
        print("\n[1/3] Pulling random TED Talk lecture...")
        subprocess.run(YTDLP_CMD + [ # <--- USE YTDLP_CMD HERE
            "ytsearch1:ted talk science lecture",
            "--extract-audio", "--audio-format", "wav", "-o", ted_talk_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        print("\n[1/3] Using existing TED Talk lecture...")
        
    print("\n[2/3] Loading PyTorch Snoop Delta Math...")
    try:
        # Load the correct file name
        semitones_shift = float(torch.load('Snoop_pitch_delta.pt')[0]) 
    except Exception as e:
        print(f"Snoop_pitch_delta.pt not found, recalculating or using fallback: {e}")
        semitones_shift = -5.0 # Fallback
        
    # ... (rest of the script remains the same) ...
```

#### Step 4: Final Check of `snoop_voice_app.py`

* The `load_profile` function in `snoop_voice_app.py` expects files named `Snoop_pitch_delta.pt`, `Dolly_pitch_delta.pt`, etc. The profile generation scripts provided above ensure this naming convention is followed.
* The `build_board` function uses `shift_delta`, which is updated by `load_profile`. This is correct.
* All other aspects of `snoop_voice_app.py` (PyAudio, Tkinter, Pedalboard) are Mac-compatible.

---

### 🎁 Making it a Perfect Birthday Gift

Here’s how you package this up:

1. **Organize the Folder:** Ensure all your `.py` files (the app, the new profile generators) and the `install_mac.command` are in the main `Snoop_Stylizer_App` directory.
2. **Add Instructions (for her!):** Include a simple `README.txt` file with instructions like:
    * "Hi [Girlfriend's Name]! Happy Birthday! I made this special app for you. It lets you change your voice in real-time for presentations, inspired by your favorite voices!"
    * "**How to Use:**x
        1. Double-click the `install_mac.command` file. A terminal window will pop up and do its magic – just let it run until it says 'Installation & Profile Generation Complete!' and the app launches automatically.
        2. In the app, set your **Input** to your physical microphone (e.g., `MacBook Pro Microphone`).
        3. Set the **Output** to `BlackHole 2ch`.
        4. In PowerPoint, Zoom, or Teams, change your microphone setting to `BlackHole 2ch`.
        5. Choose your desired voice profile (Snoop Dogg, Dolly Parton!) and adjust the sliders for extra fun.
        6. Click **START STYLIZER** and start talking!
    * "If anything looks weird, just restart your Mac and try again! Enjoy!"
3. **Encouragement:** Tell her how much effort you put into it! Emphasize the real-time, no-latency aspect.

---

With these changes, the `install_mac.command` will be robust, install all necessary components, automatically generate the crucial voice profiles, and then launch the fully functional application. She'll have a truly seamless and magical experience on her Mac!

Good luck, and Happy Birthday to her!
