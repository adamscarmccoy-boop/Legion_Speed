import sounddevice as sd
import numpy as np
import matplotlib.pyplot as plt
import time
import soundfile as sf
from scipy import signal

def capture_and_visualize_rgb(duration=30):
    print(f"--- Sovereign RGB Audio Analysis (30s) ---")
    
    # 1. Identify Input (Stereo Mix)
    devices = sd.query_devices()
    input_dev = None
    for i, d in enumerate(devices):
        if 'Stereo Mix' in d['name'] and d['max_input_channels'] > 0:
            input_dev = i
            break
            
    if input_dev is None:
        print("ERROR: Stereo Mix not found. Falling back to default input.")
        input_dev = sd.default.device[0]

    device_info = sd.query_devices(input_dev)
    samplerate = int(device_info['default_samplerate'])
    
    print(f"Capturing from: {device_info['name']}")
    print(f"Recording for {duration} seconds...")

    # 2. Record
    recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=2, device=input_dev)
    
    # Progress feedback
    start_time = time.time()
    while time.time() - start_time < duration:
        elapsed = int(time.time() - start_time)
        print(f"Progress: [{'=' * elapsed}{' ' * (duration - elapsed)}] {elapsed}/{duration}s", end='\r')
        time.sleep(1)
    
    sd.wait()
    print("\nCapture Complete. Generating RGB Visualization...")

    # 3. Process Mono for analysis
    mono_data = np.mean(recording, axis=1)

    # 4. Generate Spectrogram
    frequencies, times, spectrogram = signal.spectrogram(mono_data, samplerate, nperseg=2048)
    
    # 5. Create RGB Mapping
    # Bass (20-250Hz) -> Red
    # Mids (250-4000Hz) -> Green
    # Highs (4000-20000Hz) -> Blue
    
    low_mask = (frequencies >= 20) & (frequencies < 250)
    mid_mask = (frequencies >= 250) & (frequencies < 4000)
    high_mask = (frequencies >= 4000) & (frequencies < 20000)
    
    low_energy = np.mean(spectrogram[low_mask, :], axis=0) if any(low_mask) else np.zeros(len(times))
    mid_energy = np.mean(spectrogram[mid_mask, :], axis=0) if any(mid_mask) else np.zeros(len(times))
    high_energy = np.mean(spectrogram[high_mask, :], axis=0) if any(high_mask) else np.zeros(len(times))
    
    # Normalize for visualization
    def normalize(x):
        if np.max(x) == 0: return x
        return (x - np.min(x)) / (np.max(x) - np.min(x))

    r = normalize(low_energy)
    g = normalize(mid_energy)
    b = normalize(high_energy)
    
    # 6. Plotting
    plt.figure(figsize=(15, 8))
    
    # Top Plot: Waveform
    plt.subplot(2, 1, 1)
    plt.plot(np.linspace(0, duration, len(mono_data)), mono_data, color='cyan', alpha=0.7)
    plt.title('Sovereign Waveform (30s Capture)')
    plt.ylabel('Amplitude')
    plt.grid(True, alpha=0.3)

    # Bottom Plot: RGB Frequency Distribution
    plt.subplot(2, 1, 2)
    rgb_data = np.vstack((r, g, b)).T
    # We'll plot this as an image strip
    img = np.expand_dims(rgb_data, axis=0)
    plt.imshow(img, aspect='auto', extent=[0, duration, 0, 1])
    plt.title('RGB Frequency Distribution (Red: Bass, Green: Mids, Blue: Highs)')
    plt.xlabel('Time (s)')
    plt.yticks([])

    plt.tight_layout()
    plt.savefig('sovereign_rgb_analysis.png')
    print("Visualization saved as 'sovereign_rgb_analysis.png'")

    # 7. Output Stats
    print("\n--- Audio Statistics ---")
    print(f"Max Amplitude: {np.max(np.abs(mono_data)):.4f}")
    print(f"Avg Energy (RMS): {np.sqrt(np.mean(mono_data**2)):.4f}")
    
    # Save raw capture
    sf.write('sovereign_30s_capture.wav', recording, samplerate)
    print("Raw capture saved as 'sovereign_30s_capture.wav'")

if __name__ == "__main__":
    capture_and_visualize_rgb()
