import sounddevice as sd
import numpy as np
import time
from pedalboard import Pedalboard, Compressor, Reverb
import soundfile as sf

def test_capture():
    print("--- Sovereign Audio Link Diagnostic ---")
    # 1. Find Stereo Mix or Loopback device
    devices = sd.query_devices()

    loopback_dev = None
    # Look for 'Stereo Mix' first
    for i, d in enumerate(devices):
        if 'Stereo Mix' in d['name'] and d['max_input_channels'] > 0:
            loopback_dev = i
            break

    # Fallback to any device with input channels that isn't a microphone if possible
    if loopback_dev is None:
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0 and 'Microphone' not in d['name']:
                loopback_dev = i
                break

    if loopback_dev is None:
        # Final fallback to first input device
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                loopback_dev = i
                break

    if loopback_dev is None:
        print("ERROR: No input device found.")
        return

    device_info = sd.query_devices(loopback_dev)
    samplerate = int(device_info['default_samplerate'])

    # 2. Capture buffer
    duration = 5 # seconds

    print(f"Targeting Input: {device_info['name']}")
    print(f"Sample Rate: {samplerate}Hz")
    print("Capturing 5 seconds of audio... PLEASE PLAY AUDIO NOW.")

    recording = sd.rec(
        int(duration * samplerate), 
        samplerate=samplerate, 
        channels=2, 
        device=loopback_dev
    )

    
    # Progress bar simulation
    for i in range(duration):
        print(f"Listening... {duration - i}s remaining")
        time.sleep(1)
    
    sd.wait() # Wait for recording to finish
    
    # 3. Analyze signal
    peak = np.max(np.abs(recording))
    rms = np.sqrt(np.mean(recording**2))
    
    print("\n--- Analysis Results ---")
    print(f"Peak Level: {peak:.4f}")
    print(f"RMS Level:  {rms:.4f}")
    
    if peak > 0.001:
        print("SUCCESS: Audio signal detected!")
        sf.write('test_capture_output.wav', recording, samplerate)
        print("Saved capture to 'test_capture_output.wav' for manual review.")
    else:
        print("FAILURE: Silence detected. Check if your browser is outputting to the selected device.")

if __name__ == "__main__":
    test_capture()
