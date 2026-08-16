import librosa
import numpy as np
import onnxruntime as ort
import time

print("1. Extracting Acoustic Manifold from Downloads...")
wav_path = r"C:\Users\adams\Downloads\129bpm-ADMIT IT.wav"
y, sr = librosa.load(wav_path, sr=44100, mono=True)

rms_val = float(np.sqrt(np.mean(y ** 2)))
peak = float(np.max(np.abs(y))) + 1e-9
crest_factor = rms_val / peak
zcr = float(np.mean(librosa.feature.zero_crossing_rate(y)))
spectral_centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
spectral_rolloff = float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr)))
spectral_bandwidth = float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr)))
S = np.abs(librosa.stft(y))
spectral_contrast = float(np.mean(librosa.feature.spectral_contrast(S=S, sr=sr)))
onset_env = librosa.onset.onset_strength(y=y, sr=sr)
onset_strength = float(np.mean(onset_env))
transient_density = float(len(librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr))) / (len(y)/sr)

# Extract exactly 11 dims to match audio_llm_v1.onnx
features = np.array([rms_val, crest_factor, spectral_centroid, spectral_rolloff, spectral_bandwidth, spectral_contrast, zcr, onset_strength, transient_density, 0.5, 0.5], dtype=np.float32)

print("2. Piping through pure ONNX C++ Engines...")
t0 = time.time()
# Generative Engine
session_llm = ort.InferenceSession(r"C:\WEB CASE STUDY\sonic_dna_engine\audio_llm_v1.onnx", providers=["CPUExecutionProvider"])
hallucinated = session_llm.run(None, {session_llm.get_inputs()[0].name: features.reshape(1, -1)})[0][0]

# Zero-Pad to 64 dims
padded = np.pad(hallucinated, (0, 64 - len(hallucinated)), mode="constant")

# End DSP Engine
session_dsp = ort.InferenceSession(r"C:\WEB CASE STUDY\sovereign_big_brain_exhaustive.onnx", providers=["CPUExecutionProvider"])
dsp_params = session_dsp.run(None, {session_dsp.get_inputs()[0].name: padded.reshape(1, -1).astype(np.float32)})[0][0]
t1 = time.time()

import soundfile as sf
from pedalboard import Pedalboard, Compressor, HighpassFilter, Gain, Limiter

print("3. Rendering Final Audio with Pedalboard...")
# Map normalized DSP outputs to real physical boundaries
gain_db = float(np.clip(dsp_params[0] * 12.0, -12.0, 12.0))
threshold_db = float(np.clip(-12.0 + (dsp_params[1] * -10.0), -30.0, -2.0))
ratio = float(np.clip(abs(dsp_params[2]) * 6.0, 1.5, 8.0))

board = Pedalboard([
    HighpassFilter(cutoff_frequency_hz=30.0),
    Gain(gain_db=gain_db),
    Compressor(threshold_db=threshold_db, ratio=ratio, attack_ms=10.0, release_ms=100.0),
    Limiter(threshold_db=-0.3, release_ms=100.0)
])

y_stereo, sr_stereo = librosa.load(wav_path, sr=44100, mono=False)
if y_stereo.ndim == 1:
    y_stereo = y_stereo[np.newaxis, :]

t_board_start = time.time()
mastered = board(y_stereo, sample_rate=sr_stereo)
t_board_end = time.time()

out_path = r"C:\Users\adams\.gemini\antigravity-ide\brain\a53f4d8e-f963-4062-a42a-dedddcd50236\ONNX_MASTERED_ADMIT_IT.wav"
sf.write(out_path, mastered.T, sr_stereo)

print(f"\nHeavy lifting complete in {(t1-t0)*1000:.2f} ms (Pure C++ Execution)!")
print(f"Audio Rendered with Pedalboard in {(t_board_end-t_board_start)*1000:.2f} ms")
print(f"Final 12 DSP Parameters: {np.round(dsp_params, 4)}")
print(f"Saved physical audio to: {out_path}")
