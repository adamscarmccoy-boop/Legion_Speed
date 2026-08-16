import os
import sys
import argparse
import numpy as np
import pandas as pd
import torch
import onnxruntime as ort
import librosa
import soundfile as sf
from pedalboard import Pedalboard, Compressor, HighpassFilter, Gain, Limiter
from sklearn.preprocessing import StandardScaler
from scipy.interpolate import interp1d

# Force UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ==============================================================================
# SOVEREIGN CONFIGURATION
# ==============================================================================
DNA_BRAIN_PATH = r"C:\WEB CASE STUDY\dna_brain.onnx"
LATENT_BRAIN_PATH = r"C:\WEB CASE STUDY\fretflow_omni_v4.onnx"
PARAM_BRAIN_PATH = r"C:\WEB CASE STUDY\real_data_brain.onnx"

# The "Sovereign" Baseline
TARGET_BPM = 128.0 
TARGET_STYLE_ID = 0 

# ==============================================================================
# THE SOVEREIGN ENGINE
# ==============================================================================
class SovereignFlowX:
    def __init__(self):
        print("🌌 Initializing Sovereign-Flow-X Engine...")
        self.dna_sess = ort.InferenceSession(DNA_BRAIN_PATH)
        self.latent_sess = ort.InferenceSession(LATENT_BRAIN_PATH)
        self.param_sess = ort.InferenceSession(PARAM_BRAIN_PATH)
        
        # Auto-detect input names to prevent ValueError
        self.dna_in = self.dna_sess.get_inputs()[0].name
        self.latent_in = self.latent_sess.get_inputs()[0].name
        self.param_in = self.param_sess.get_inputs()[0].name
        
        print(f"  [+] DNA Input: {self.dna_in}")
        print(f"  [+] Latent Input: {self.latent_in}")
        print(f"  [+] Param Input: {self.param_in}")
        
        # Setup DSP Chain
        self.hp = HighpassFilter(cutoff_frequency_hz=30.0)
        self.comp = Compressor(threshold_db=-20.0, ratio=3.0, attack_ms=10.0, release_ms=100.0)
        self.gain = Gain(gain_db=0.0)
        self.lim = Limiter(threshold_db=-0.3, release_ms=100.0)
        self.board = Pedalboard([self.hp, self.gain, self.comp, self.lim])

    def get_dna(self, audio_chunk):
        # simplified for flow - in real mode, this uses the dna_sess
        # For now, we maintain the vector shape expected by the next brain
        return np.random.randn(1, 64).astype(np.float32)

    def get_params(self, dna_vector):
        # Chain: DNA -> Latent -> Params
        # Using the auto-detected input names
        latent = self.latent_sess.run(None, {self.latent_in: dna_vector})[0]
        params = self.param_sess.run(None, {self.param_in: latent})[0]
        return params[0] 

    def process(self, input_path, output_path):
        print(f"🚀 Sculpting: {input_path} -> {output_path}")
        
        y, sr = librosa.load(input_path, sr=None, mono=False)
        if y.ndim == 1: y = y[np.newaxis, :]
        
        duration = librosa.get_duration(y=y, sr=sr)
        window_size = 2.0 
        hop_size = 1.0 
        
        # 1. Generate the Parameter Trajectory
        print("Calculating Neural Trajectory...")
        trajectory = []
        for start in np.arange(0, duration - window_size, hop_size):
            end = start + window_size
            start_samp = int(start * sr)
            end_samp = int(end * sr)
            chunk = y[:, start_samp:end_samp]
            
            dna = self.get_dna(chunk)
            params = self.get_params(dna)
            trajectory.append((start, params))

        # 2. Temporal Slew-Rate Smoothing
        times = np.array([t[0] for t in trajectory])
        gains = np.array([t[1][0] for t in trajectory])
        ratios = np.array([t[1][1] for t in trajectory])
        threshs = np.array([t[1][2] for t in trajectory])
        
        interp_gain = interp1d(times, gains, kind='cubic', fill_value="extrapolate")
        interp_ratio = interp1d(times, ratios, kind='cubic', fill_value="extrapolate")
        interp_thresh = interp1d(times, threshs, kind='cubic', fill_value="extrapolate")

        # 3. Physical Rendering
        print("Applying Neural Sculpting to Audio...")
        mastered = np.zeros_like(y)
        block_size = int(0.1 * sr) 
        for start_samp in range(0, y.shape[1] - block_size, block_size):
            end_samp = start_samp + block_size
            t = start_samp / sr
            
            self.gain.gain_db = float(interp_gain(t))
            self.comp.ratio = float(interp_ratio(t))
            self.comp.threshold_db = float(interp_thresh(t))
            
            chunk = y[:, start_samp:end_samp]
            processed = self.board(chunk, sample_rate=sr, reset=False)
            mastered[:, start_samp:end_samp] = processed

        sf.write(output_path, mastered.T, sr)
        print(f"✅ Sovereign-Flow-X Master Complete: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    engine = SovereignFlowX()
    engine.process(args.input, args.output)
