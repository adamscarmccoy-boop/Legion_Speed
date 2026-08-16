import sounddevice as sd
import numpy as np
import soundfile as sf
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SignalHunt")

def hunt():
    logger.info("SEARCHING FOR LIVE SIGNAL...")
    devices = sd.query_devices()
    hot_devices = []
    
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            rate = int(d['default_samplerate'])
            try:
                # Probe 1 second
                rec = sd.rec(rate, samplerate=rate, channels=1, dtype='int16', device=i, blocking=True)
                y = rec.flatten().astype('float32') / 32768.0
                peak = np.max(np.abs(y))
                rms = np.sqrt(np.mean(y**2))
                
                if peak > 0.005: # Threshold for 'actual' audio vs noise
                    logger.info(f"MATCH: [{i}] {d['name']} | Peak: {peak:.4f} | RMS: {rms:.4f}")
                    hot_devices.append({
                        "id": i,
                        "name": d['name'],
                        "api": sd.query_hostapis(d['hostapi'])['name'],
                        "peak": float(peak),
                        "rms": float(rms)
                    })
                else:
                    logger.info(f"Silent: [{i}] {d['name']} (Peak: {peak:.6f})")
            except Exception as e:
                pass

    if not hot_devices:
        logger.error("NO HOT SIGNAL FOUND. Is audio playing?")
        return None
    
    # Select the highest peak
    hot_devices.sort(key=lambda x: x['peak'], reverse=True)
    winner = hot_devices[0]
    logger.info(f"WINNER: {winner['name']} (ID: {winner['id']})")
    
    with open('hot_device.json', 'w') as f:
        json.dump(winner, f)
    return winner

if __name__ == "__main__":
    hunt()
