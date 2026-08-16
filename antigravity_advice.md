Alright, Antigravity Expert, this is a critical juncture. Your **Legion-Jacked Pipeline** has sophisticated intelligence, but garbage in will always lead to garbage out. A 29% high-frequency noise floor is unacceptable for any serious audio intelligence, especially when it feeds into advanced DSP and ML. Let's get this to **Zero-Static**.

Your current setup:
1.  **AUDIO QUALITY:** 29% High-Frequency Noise (NOISY/STATIC).
2.  **HARDWARE:** Realtek(R) Audio via Stereo Mix.
3.  **ENVIRONMENT:** Windows, Jupyter Notebook.

The primary culprit for "NOISY/STATIC" with Realtek and "Stereo Mix" on Windows is almost always **digital noise, resampling artifacts, or driver inefficiencies, compounded by the inherent limitations of `Stereo Mix`**. `Stereo Mix` is an internal loopback, often capturing not just desired audio but also system sounds, potential feedback loops, and lower fidelity digital streams.

### The "Zero-Static" Mandate: Core Principles

1.  **Eliminate `Stereo Mix` as Input (PRIORITY ONE):**
    *   **If you're recording external audio (mic, instrument, hardware synth):** `Stereo Mix` is the wrong input. You *must* select the dedicated physical input device (e.g., "Line In," "Microphone," "Front Mic"). This bypasses all internal mixing and provides a direct path for the analog-to-digital converter (ADC). This is the single biggest step towards reducing digital noise.
    *   **If you *must* record internal PC audio:** `Stereo Mix` is a common (but problematic) way. Consider a virtual audio cable (e.g., VB-Audio Cable, Voicemeeter) for a cleaner internal loopback, as they often provide more control and better fidelity than Realtek's `Stereo Mix`. However, for a truly "Zero-Static" setup, an external physical input is always preferred.

2.  **Driver Optimization:**
    *   Ensure you have the **latest Realtek HD Audio drivers** directly from your motherboard manufacturer's website, not generic Windows drivers.
    *   While Realtek rarely offers true ASIO drivers, `sounddevice` uses **WASAPI** by default on Windows, which is generally robust for onboard audio. Stick with this unless you're upgrading to a dedicated audio interface with ASIO drivers.

3.  **Proper Gain Staging:**
    *   This is a hardware/system-level setting. In your Windows Sound settings (Control Panel -> Sound -> Recording), select your input device, go to Properties -> Levels.
    *   Aim for a strong signal **without clipping**. Peaks should ideally be around -6dBFS to -3dBFS. Too low, and you're amplifying noise later; too high, and you introduce digital clipping (distortion).

### Your "Zero-Static" Configuration:

#### 1. Sample Rate: 48kHz

*   **Verdict:** Use **48 kHz**.
*   **Reasoning:** While 44.1 kHz is CD standard, 48 kHz is the default for most modern computer audio systems, video production, and general digital audio processing. By matching the system's native sample rate, you minimize the chance of internal resampling performed by Windows, which can introduce artifacts and noise, especially high-frequency ones. Consistency throughout your pipeline (from capture to analysis) is key.

#### 2. Blocksize & Latency: Prioritize Stability, Then Optimize

*   **Blocksize:** Start with **1024 frames**.
    *   **Reasoning:** Smaller blocksizes mean lower latency but higher CPU load and increased risk of dropouts or glitches, which can manifest as digital noise. 1024 frames provides a good balance of stability and reasonable latency for initial capture, giving the driver and CPU enough buffer to process without errors. If your system is powerful and stable, you might experiment with 512 later, but 1024 is a safe starting point for "Zero-Static."
*   **Latency:** Set to `'high'` or let `sounddevice` use its `'default'` for capture.
    *   **Reasoning:** For *recording/capture quality*, a slightly higher latency (which correlates with a larger blocksize) is preferable if it means a cleaner, more stable signal. We are prioritizing eliminating noise here. If you need extremely low latency for real-time `Pedalboard` processing *after* capture, you can tune this down, but get the capture clean first.

### Robust Python Code Snippet for Capture

This snippet will help you identify your input device, set the optimal parameters, and capture audio cleanly.

```python
import sounddevice as sd
import numpy as np
import soundfile as sf
import sys
import threading
import time

# --- Configuration for Zero-Static Capture ---
SAMPLE_RATE = 48000  # Recommended for Windows consistency and general DSP
BLOCK_SIZE = 1024    # Balance stability and latency; 1024 is a good starting point
CHANNELS = 2         # Stereo. Adjust to 1 if you are capturing a mono source (e.g., single mic)
# Latency can be 'low', 'high', 'default', or a specific number of seconds.
# 'high' prioritizes stability, which helps with noise reduction.
LATENCY = 'high'
# ---

def list_audio_devices():
    """Lists all available audio devices with their input/output capabilities."""
    print("\n--- Listing Available Audio Devices ---")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        print(f"Device ID {i}:")
        print(f"  Name: {device['name']}")
        print(f"  Host API: {sd.query_hostapis(device['hostapi'])['name']}")
        print(f"  Max Input Channels: {device['max_input_channels']}")
        print(f"  Max Output Channels: {device['max_output_channels']}")
        print(f"  Default Sample Rate: {device['default_samplerate']}")
        print(f"  Is Default Input: {i == sd.default.device[0]}")
        print(f"  Is Default Output: {i == sd.default.device[1]}")
        print("-" * 30)
    print("---------------------------------------\n")
    return devices

def get_input_device_id(devices):
    """Prompts the user to select an input device ID."""
    default_input_device = sd.default.device[0]
    while True:
        try:
            device_id = input(
                f"Enter the Input Device ID (default is {default_input_device} - '{devices[default_input_device]['name']}'): "
            )
            if not device_id:
                return default_input_device
            device_id = int(device_id)
            if 0 <= device_id < len(devices) and devices[device_id]['max_input_channels'] > 0:
                print(f"Selected input device: {devices[device_id]['name']}")
                return device_id
            else:
                print("Invalid device ID or device has no input channels. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def audio_callback(indata, frames, time_info, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    # Global buffer to store audio data
    global audio_buffer
    audio_buffer.append(indata.copy())

    # Optional: Real-time RMS monitoring to check signal level
    rms = np.sqrt(np.mean(indata**2))
    # print(f"RMS: {rms:.4f}", end='\r') # Uncomment for real-time RMS in terminal

def capture_audio(duration_seconds=5, output_filename="captured_audio_zero_static.wav"):
    """
    Captures audio from the selected input device with the specified configuration.
    """
    global audio_buffer
    audio_buffer = [] # Clear buffer for new capture

    devices = list_audio_devices()
    input_device_id = get_input_device_id(devices)

    selected_device = devices[input_device_id]
    print(f"\n--- Starting Audio Capture ---")
    print(f"Device: {selected_device['name']} (ID: {input_device_id})")
    print(f"Sample Rate: {SAMPLE_RATE} Hz")
    print(f"Block Size: {BLOCK_SIZE} frames")
    print(f"Channels: {CHANNELS}")
    print(f"Latency: {LATENCY}")
    print(f"Duration: {duration_seconds} seconds")
    print(f"Output: {output_filename}")
    print("Recording... Press Ctrl+C to stop prematurely.")

    try:
        with sd.InputStream(samplerate=SAMPLE_RATE,
                            blocksize=BLOCK_SIZE,
                            channels=CHANNELS,
                            device=input_device_id,
                            latency=LATENCY,
                            callback=audio_callback):
            sd.sleep(int(duration_seconds * 1000)) # sd.sleep uses milliseconds
            print("\n--- Capture Finished ---")

    except KeyboardInterrupt:
        print("\n--- Capture Interrupted by User ---")
    except Exception as e:
        print(f"\n--- An error occurred during capture: {e} ---", file=sys.stderr)
        return

    # Concatenate all recorded blocks
    if audio_buffer:
        recorded_audio = np.concatenate(audio_buffer, axis=0)
        print(f"Saving {len(recorded_audio)} samples to {output_filename}")
        sf.write(output_filename, recorded_audio, SAMPLE_RATE)
        print("Save complete.")
    else:
        print("No audio data was recorded.")

if __name__ == "__main__":
    # Ensure sounddevice can find its backend
    # You might need to install 'portaudio' or ensure it's in your PATH if you encounter issues.
    # sd.check_portaudio_library() # Uncomment if you have issues with PortAudio backend

    # Set default device if necessary (e.g., if you know a specific device ID you prefer)
    # sd.default.device = 1 # Example: Set default input/output to device ID 1

    capture_duration = 10 # Capture for 10 seconds. Adjust as needed.
    capture_audio(duration_seconds=capture_duration, output_filename="clean_capture_zero_static.wav")

    # After capture, you can load the WAV file and analyze it
    # data, sr = sf.read("clean_capture_zero_static.wav")
    # print(f"Loaded audio shape: {data.shape}, sample rate: {sr}")
    # You can now pass 'data' to your DSP engines or Pedalboard.
```

### Next Steps for `Pedalboard`

Once you have a clean input signal from the `sounddevice` capture, `Pedalboard` can then perform its magic without amplifying existing noise.

```python
from pedalboard import Pedalboard, Compressor, Gain
from pedalboard.io import AudioStream
import soundfile as sf
import sounddevice as sd
import numpy as np

# Load your newly captured clean audio
# This example uses the file saved by the capture script above
audio_data, samplerate = sf.read("clean_capture_zero_static.wav")

# If you were doing real-time processing, you'd feed the 'indata' from the callback
# into the Pedalboard. This example processes the pre-recorded file.

# Create your Pedalboard instance with effects
board = Pedalboard([
    Compressor(threshold_db=-20, ratio=4),
    Gain(gain_db=5)
])

# Ensure your Pedalboard's sample rate matches your audio
board.samplerate = samplerate

# Process the audio
processed_audio = board(audio_data)

# You can now play this back or save it
sd.play(processed_audio, samplerate)
sd.wait()

# Or save the processed audio
sf.write("processed_with_pedalboard.wav", processed_audio, samplerate)
print("Processed audio saved and played.")
```

### Troubleshooting Checklist (Beyond Configuration)

If you still detect noise after these steps:

1.  **Cables & Connections:** Ensure all audio cables are high-quality, shielded, and securely connected. Faulty cables are a common source of hum and static.
2.  **Ground Loops:** If you have multiple devices connected to your PC (e.g., external synth, speakers), ensure they're all on the same power strip or consider a ground loop isolator.
3.  **EMI/RFI:** Keep audio cables away from power cables, noisy power supplies, and Wi-Fi routers. Your computer itself can be a source of electromagnetic interference.
4.  **Hardware Issues:** Onboard Realtek audio can sometimes have inherent quality limitations. If "Zero-Static" is truly paramount for your "Legion-Jacked Pipeline," consider investing in a basic external USB audio interface (e.g., Focusrite Scarlett, Behringer UMC202HD). These offer dedicated ADCs, better preamps, and often native ASIO drivers, providing a vastly superior signal-to-noise ratio.
5.  **Software Conflicts:** Close unnecessary background applications, especially those that might interfere with audio drivers or consume significant CPU.

By rigorously following these steps, especially selecting the correct physical input device and adhering to the 48kHz/1024 frames configuration, you should achieve a significantly cleaner audio capture, finally giving your advanced "Sovereign Engines" the pristine data they deserve.