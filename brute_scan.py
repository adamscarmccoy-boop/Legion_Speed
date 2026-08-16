import sounddevice as sd
import numpy as np
import soundfile as sf
import os
import json

def brute_force_scan():
    print("🚀 STARTING BRUTE FORCE AUDIO SCAN...")
    devices = sd.query_devices()
    input_indices = [i for i, d in enumerate(devices) if d['max_input_channels'] > 0]
    
    if not os.path.exists('probes'):
        os.makedirs('probes')
        
    results = []
    
    for idx in input_indices:
        name = devices[idx]['name']
        api = sd.query_hostapis(devices[idx]['hostapi'])['name']
        rate = int(devices[idx]['default_samplerate'])
        
        print(f"Probing [{idx}] {name} ({api})...", end='', flush=True)
        
        try:
            # Capture 2 seconds
            # Use int16 for maximum compatibility
            rec = sd.rec(int(rate * 2), samplerate=rate, channels=1, dtype='int16', device=idx, blocking=True)
            y = rec.flatten().astype('float32') / 32768.0
            
            # Binary Clean
            y = np.nan_to_num(y)
            peak = np.max(np.abs(y))
            rms = np.sqrt(np.mean(y**2))
            
            filename = f"probes/probe_{idx}.wav"
            sf.write(filename, y, rate)
            
            print(f" DONE. Peak: {peak:.4f}")
            results.append({
                "id": idx,
                "name": name,
                "api": api,
                "peak": float(peak),
                "rms": float(rms),
                "file": filename
            })
        except Exception as e:
            print(f" FAILED: {e}")

    print("\n--- SCAN RESULTS ---")
    results.sort(key=lambda x: x['peak'], reverse=True)
    
    for r in results[:5]:
        status = "🔥 HOT" if r['peak'] > 0.01 else "❄️ COLD"
        print(f"[{r['id']}] {r['name']} | {status} | Peak: {r['peak']:.4f}")

    with open('scan_results.json', 'w') as f:
        json.dump(results, f, indent=4)
        
    if results and results[0]['peak'] > 0.001:
        return results[0]['id']
    return None

if __name__ == "__main__":
    brute_force_scan()
