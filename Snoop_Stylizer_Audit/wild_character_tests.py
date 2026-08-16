
import numpy as np
import librosa
import json
import os
import soundfile as sf
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
# CORE LOGIC
# =============================================================================
def analyze_audio_profile(file_path: str) -> Optional[SpectralProfile]:
    try:
        y, sr = librosa.load(file_path, sr=None)
        if len(y.shape) > 1:
            y = np.mean(y, axis=1)
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
        print(f"Error analyzing {file_path}: {e}")
        return None

def calculate_dynamic_offset(source: SpectralProfile, target: SpectralProfile, base_preset: DSPParams, wild_mode: float = 1.0) -> DSPParams:
    def clamp(n, minn, maxn):
        return max(minn, min(maxn, n))

    adjusted = base_preset.model_copy()
    centroid_delta = target.spectral_centroid / (source.spectral_centroid + 1e-6)
    lowpass_target = base_preset.lowpass_hz * centroid_delta
    if wild_mode > 1.0:
        lowpass_target = lowpass_target * (1.0 - (wild_mode - 1.0) * 0.2)
    adjusted.lowpass_hz = clamp(lowpass_target, 1000.0, 20000.0)
    
    zcr_delta = target.zero_crossing_rate / (source.zero_crossing_rate + 1e-6)
    drive_val = base_preset.drive * zcr_delta * wild_mode
    adjusted.drive = clamp(drive_val, 0.0, 3.0)
    
    rms_delta = target.rms_energy / (source.rms_energy + 1e-6)
    output_gain = base_preset.output_gain * rms_delta * (1.0 + (wild_mode - 1.0) * 0.1)
    adjusted.output_gain = clamp(output_gain, 0.1, 1.5)
    
    freq_diff = abs(target.peak_frequency - source.peak_frequency)
    peak_gain = base_preset.peak_gain * (1.0 + freq_diff/1000.0) * wild_mode
    adjusted.peak_gain = clamp(peak_gain, 0.0, 3.0)
    
    return adjusted

def fast_slew_rate_limit(y, max_delta=0.05):
    # Vectorized approximation of slew rate limiting using a one-pole filter.
    alpha = 0.1 
    return signal.lfilter([alpha], [1, -(1-alpha)], y)

class AudioChainWild:
    def __init__(self, target_profile: SpectralProfile, base_preset: DSPParams):
        self.target_profile = target_profile
        self.base_preset = base_preset
        self.output_gain = base_preset.output_gain

    def process(self, y_raw, sr, wild_mode: float = 1.0) -> np.ndarray:
        source_profile = analyze_audio_profile_array(y_raw, sr)
        params = calculate_dynamic_offset(source_profile, self.target_profile, self.base_preset, wild_mode)
        
        # 1. Peaking Filter
        peak_freq = params.peak_freq
        peak_gain = params.peak_gain
        b, a = signal.iirpeak(peak_freq, 1.0, fs=sr)
        y = signal.lfilter(b, a, y_raw)
        y = y + (y * peak_gain)
        y = fast_slew_rate_limit(y) 
        
        # 2. Low Pass
        sos_lp = signal.butter(10, params.lowpass_hz, 'lp', fs=sr, output='sos')
        y = signal.sosfilt(sos_lp, y)
        y = fast_slew_rate_limit(y) 
        
        # 3. Drive
        y = np.tanh(y * (1.0 + params.drive))
        y = fast_slew_rate_limit(y) 
        
        # 4. Compression
        comp_strength = params.comp_strength
        peak = np.max(np.abs(y))
        if peak > 0:
            y = y * (1.0 - (comp_strength * 0.5))
            
        # 5. Final Safety
        y = fast_slew_rate_limit(y)
        return np.tanh(y * params.output_gain)

def analyze_audio_profile_array(y, sr) -> SpectralProfile:
    if len(y.shape) > 1: y = np.mean(y, axis=1)
    rms = np.mean(librosa.feature.rms(y=y))
    zcr = np.mean(librosa.feature.zero_crossing_rate(y=y))
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

if __name__ == "__main__":
    SRC = r"C:\\WEB CASE STUDY\\Snoop_Stylizer_App\\training_audio\\TED_TALK_SMALL.mp3"
    TGT_FOLDER = r"C:\\WEB CASE STUDY\\Snoop_Stylizer_App\\training_audio"
    PRESET_PATH = "C:\\Users\\adams\\.agents\\skills\\omni-deployment-engine\\golden_preset.json"
    OUT_FOLDER = r"C:\\WEB CASE STUDY\\Snoop_Stylizer_App\\LAPPED_FINAL_OUTPUTS"
    
    if not os.path.exists(OUT_FOLDER):
        os.makedirs(OUT_FOLDER)

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
    
    chain = AudioChainWild(target_avg, base_preset)
    
    wild_levels = {
        "01_Surgical": 1.0,
        "02_Obvious": 1.5,
        "03_Cinematic": 2.0,
        "04_Aggressive": 2.5,
        "05_Cursed": 3.0
    }
    
    for name, level in wild_levels.items():
        print(f"Rendering {name} (Wild Level: {level})...")
        y_wet = chain.process(y, sr, wild_mode=level)
        out_path = os.path.join(OUT_FOLDER, f"{name}_TED_TALK.wav")
        sf.write(out_path, y_wet, sr)
        
        diffs = np.diff(y_wet)
        max_jump = np.max(np.abs(diffs))
        print(f"  -> Binary Stability: {max_jump:.6f} ({'STABLE' if max_jump < 0.1 else 'UNSTABLE'})")
        
    print(f"\\nAll 5 character variations saved to: {OUT_FOLDER}")
