import sounddevice as sd
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import soundfile as sf
import time
import librosa
import json

def run_standard_loopback(duration=30):
    print("DEPLOYING STANDARD WASAPI LOOPBACK (v12.0)")
    
    # 1. USER PROTOCOL SETTINGS
    RATE = 48000
    ID = 9 # AudioBox USB
    CHANNELS = 2
    FILE_PATH = 'sovereign_capture.wav'
    
    try:
        # WASAPI Loopback setup from sovereign_audio_link.py
        wasapi_settings = sd.WasapiSettings(loopback=True)
        
        print(f"Targeting: AudioBox USB (ID 9) | Loopback: ON")
        print(f"Recording {duration}s... PLEASE ENSURE MUSIC IS PLAYING")
        
        # Capture into float32 buffer directly
        recording = sd.rec(
            int(duration * RATE),
            samplerate=RATE,
            channels=CHANNELS,
            dtype='float32',
            device=ID,
            extra_settings=wasapi_settings
        )
        
        # Hard wait for duration
        for i in range(duration):
            time.sleep(1)
            if i % 5 == 0: print(f"Progress: {i}/{duration}s...")
            
        sd.wait()
        
        # 2. SAVE IMMEDIATELY
        sf.write(FILE_PATH, recording, RATE)
        print("✅ Capture saved to disk.")

        # 3. GROUND TRUTH MEASUREMENTS (Read back from file)
        y, sr = librosa.load(FILE_PATH, sr=RATE, mono=True)
        peak = np.max(np.abs(y))
        rms = np.sqrt(np.mean(y**2))
        
        # 4. BRIGHT VISUALIZATION
        f, t, Sxx = signal.spectrogram(y, RATE, nperseg=8192)
        # Log scale for visibility
        Sxx_db = 10 * np.log10(Sxx + 1e-10)
        
        low = np.mean(Sxx_db[(f >= 20) & (f < 250)], axis=0)
        mid = np.mean(Sxx_db[(f >= 250) & (f < 4000)], axis=0)
        high = np.mean(Sxx_db[(f >= 4000) & (f < 20000)], axis=0)
        
        def norm_vis(x):
            return (x - np.min(x)) / (np.max(x) - np.min(x) + 1e-8)
            
        rgb = np.vstack((norm_vis(low), norm_vis(mid), norm_vis(high))).T
        
        plt.figure(figsize=(15, 4))
        plt.imshow(np.expand_dims(rgb, axis=0), aspect='auto', extent=[0, duration, 0, 1])
        plt.axis('off')
        plt.title(f"Sovereign Pro Signature (Peak: {peak:.4f} | RMS: {rms:.4f})")
        plt.savefig('sovereign_signature.png', bbox_inches='tight', pad_inches=0)
        plt.close()

        # 5. DATA PERSISTENCE
        mfccs = librosa.feature.mfcc(y=y, sr=RATE, n_mfcc=13)
        vector_data = {
            "mfcc": np.mean(mfccs, axis=1).tolist(),
            "peak": float(peak),
            "rms": float(rms),
            "engine": "12.0_StandardLoopback"
        }
        with open('sovereign_vectors.json', 'w') as v_file:
            json.dump(vector_data, v_file)

        print("\n" + "="*40)
        print("🎤 FINAL AUDIO MEASUREMENTS:")
        print(f"PEAK: {peak:.4f}")
        print(f"RMS:  {rms:.4f}")
        print(f"FILE: sovereign_capture.wav")
        print("="*40)
        
        return True

    except Exception as e:
        print(f"ENGINE FAILURE: {e}")
        return False

if __name__ == "__main__":
    run_standard_loopback()
