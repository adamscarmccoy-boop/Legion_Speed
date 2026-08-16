
import numpy as np
import librosa
import soundfile as sf
import os
import json
from scipy import signal
from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, List, Optional

# =============================================================================
# SCHEMAS
# =============================================================================
class SpectralProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mean_energy: float
    spectral_centroid: float
    spectral_bandwidth: float
    zero_crossing_rate: float
    rms_energy: float
    peak_frequency: float

class DSPParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    drive: float = 0.0
    lowpass_hz: float = 20000.0
    comp_strength: float = 0.0
    peak_freq: float = 441.0
    peak_gain: float = 0.0
    output_gain: float = 0.9

# =============================================================================
# THE "SNOOP" MORPHING ENGINE
# =============================================================================
def shift_pitch(y, sr, n_steps):
    # Shifts pitch without changing duration.
    return librosa.effects.pitch_shift(y, sr=sr, n_steps=n_steps)

def warp_formants(y, sr, shift_factor=0.85):
    # Simulates formant shifting by time-stretching the signal, 
    # pitch-shifting it back, and re-sampling.
    # Shift factor < 1.0 = Deeper/Larger throat (Snoop).
    y_stretched = librosa.effects.time_stretch(y, rate=shift_factor)
    n_steps = 12 * np.log2(1.0 / shift_factor)
    y_morphed = librosa.effects.pitch_shift(y_stretched, sr=sr, n_steps=n_steps)
    
    if len(y_morphed) > len(y):
        return y_morphed[:len(y)]
    else:
        return np.pad(y_morphed, (0, len(y) - len(y_morphed)))

def slew_rate_limit(y, max_delta=0.05):
    smoothed = np.zeros_like(y)
    last_val = 0.0
    for i in range(len(y)):
        diff = y[i] - last_val
        smoothed[i] = last_val + np.clip(diff, -max_delta, max_delta)
        last_val = smoothed[i]
    return smoothed

class SnoopDeepEngine:
    def __init__(self, target_profile: SpectralProfile, base_preset: DSPParams):
        self.target_profile = target_profile
        self.base_preset = base_preset

    def process(self, y_raw, sr, wild_mode=1.0):
        # 1. PITCH SHIFT (The Depth)
        pitch_drop = -3.0 * wild_mode 
        y = shift_pitch(y_raw, sr, pitch_drop)
        
        # 2. FORMANT WARP (The Throat)
        warp_factor = 0.9 - (0.1 * (wild_mode - 1.0))
        y = warp_formants(y, sr, warp_factor)
        
        # 3. THE WILD ZONE (Saturate the Morph)
        drive = self.base_preset.drive * wild_mode
        y = np.tanh(y * (1.0 + drive))
        
        # Low Pass (Tame the highs of the shift)
        sos_lp = signal.butter(10, self.base_preset.lowpass_hz, 'lp', fs=sr, output='sos')
        y = signal.sosfilt(sos_lp, y)
        
        # 4. SAFETY GUARD (Lapped-Binary Exit)
        y = slew_rate_limit(y)
        y = np.tanh(y * self.base_preset.output_gain)
        
        return y

def analyze_audio_profile(file_path: str) -> Optional[SpectralProfile]:
    try:
        y, sr = librosa.load(file_path, sr=None)
        if len(y.shape) > 1: y = np.mean(y, axis=1)
        rms = np.mean(librosa.feature.rms(y=y))
        zcr = np.mean(librosa.feature.zero_crossing_rate(y))
        stft = np.abs(librosa.stft(y))
        centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
        bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))
        frequencies = librosa.fft_frequencies(sr=sr)
        magnitude = np.mean(stft, axis=1)
        peak_freq = frequencies[np.argmax(magnitude)]
        return SpectralProfile(
            mean_energy=float(np.mean(np.abs(y))),
            spectral_centroid=float(centroid),
            spectral_bandwidth=float(bandwidth),
            zero_crossing_rate=float(zcr),
            rms_energy=float(rms),
            peak_frequency=float(peak_freq)
        )
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    SRC = r"C:\\WEB CASE STUDY\\Snoop_Stylizer_App\\training_audio\\TED_TALK_SMALL.mp3"
    TGT_FOLDER = r"C:\\WEB CASE STUDY\\Snoop_Stylizer_App\\training_audio"
    PRESET_PATH = "C:\\Users\\adams\\.agents\\skills\\omni-deployment-engine\\golden_preset.json"
    OUT_FOLDER = r"C:\\WEB CASE STUDY\\Snoop_Stylizer_App\\LAPPED_FINAL_SNOOP"
    
    if not os.path.exists(OUT_FOLDER): os.makedirs(OUT_FOLDER)

    files = [f for f in os.listdir(TGT_FOLDER) if f.endswith('.wav')]
    profiles = [analyze_audio_profile(os.path.join(TGT_FOLDER, f)) for f in files if analyze_audio_profile(os.path.join(TGT_FOLDER, f))]
    target_avg = SpectralProfile(
        mean_energy=float(np.mean([p.mean_energy for p in profiles])),
        spectral_centroid=float(np.mean([p.spectral_centroid for p in profiles])),
        spectral_bandwidth=float(np.mean([p.spectral_bandwidth for p in profiles])),
        zero_crossing_rate=float(np.mean([p.zero_crossing_rate for p in profiles])),
        rms_energy=float(np.mean([p.rms_energy for p in profiles])),
        peak_frequency=float(np.mean([p.peak_frequency for p in profiles]))
    )
    with open(PRESET_PATH, 'r') as f:
        base_preset = DSPParams(**json.load(f))

    y, sr = librosa.load(SRC, sr=None)
    if len(y.shape) > 1: y = np.mean(y, axis=1)
    
    engine = SnoopDeepEngine(target_avg, base_preset)
    
    wild_levels = {
        "01_Surgical": 1.0,
        "02_Obvious": 1.5,
        "03_Cinematic": 2.0,
        "04_Aggressive": 2.5,
        "05_Cursed": 3.0
    }
    
    for name, level in wild_levels.items():
        print(f"Morphed Rendering: {name}...")
        y_wet = engine.process(y, sr, wild_mode=level)
        out_path = os.path.join(OUT_FOLDER, f"{name}_SNOOP_TED.wav")
        sf.write(out_path, y_wet, sr)
        print(f"  -> Saved to {out_path}")
