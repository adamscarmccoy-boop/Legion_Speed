import sounddevice as sd
import numpy as np
import time

def find_the_hot_signal():
    print("SCANNING ALL INPUTS FOR LIVE SIGNAL...")
    devices = sd.query_devices()
    input_devices = [i for i, d in enumerate(devices) if d['max_input_channels'] > 0]
    
    results = []
    
    for idx in input_devices:
        name = devices[idx]['name']
        sr = int(devices[idx]['default_samplerate'])
        print(f"Checking [{idx}] {name}...", end='', flush=True)
        
        try:
            # Capture 1 second
            rec = sd.rec(int(sr), samplerate=sr, channels=1, device=idx, blocking=True)
            peak = np.max(np.abs(rec))
            rms = np.sqrt(np.mean(rec**2))
            print(f" PEAK: {peak:.4f} | RMS: {rms:.4f}")
            results.append((idx, name, peak, rms))
        except Exception as e:
            print(f" ERROR: {e}")
            
    print("\n--- SCAN COMPLETE ---")
    results.sort(key=lambda x: x[2], reverse=True)
    
    if results and results[0][2] > 0.001:
        winner = results[0]
        print(f"WINNER: [{winner[0]}] {winner[1]} (Peak: {winner[2]:.4f})")
        return winner[0]
    else:
        print("NO LIVE SIGNAL DETECTED ON ANY INPUT.")
        return None

if __name__ == "__main__":
    find_the_hot_signal()
