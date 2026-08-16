"""
Demucs stem separator that bypasses torchcodec/torchaudio file loading.
Uses soundfile to load WAV directly, then calls Demucs Python API.
"""
import sys, os, json
import numpy as np
import soundfile as sf
import torch

# Args: input_wav output_dir
input_wav = sys.argv[1]
output_dir = sys.argv[2]

print(f"Loading: {input_wav}", flush=True)
audio, sr = sf.read(input_wav, dtype='float32', always_2d=True)
# Demucs expects (channels, samples) as a torch tensor
audio_tensor = torch.from_numpy(audio.T)  # (C, T)

print(f"Audio shape: {audio_tensor.shape}, sr={sr}", flush=True)

from demucs.pretrained import get_model
from demucs.apply import apply_model

model = get_model('htdemucs')
model.eval()

# Resample to model sample rate if needed
model_sr = model.samplerate
if sr != model_sr:
    import torchaudio.functional as F
    audio_tensor = F.resample(audio_tensor, sr, model_sr)
    sr = model_sr
    print(f"Resampled to {model_sr}Hz", flush=True)

# Add batch dimension: (1, C, T)
audio_batch = audio_tensor.unsqueeze(0)

print("Running Demucs separation...", flush=True)
with torch.no_grad():
    sources = apply_model(model, audio_batch, device='cpu', progress=True)
# sources shape: (1, num_sources, C, T)
sources = sources[0]  # (num_sources, C, T)

track_name = os.path.splitext(os.path.basename(input_wav))[0]
stems_dir = os.path.join(output_dir, track_name)
os.makedirs(stems_dir, exist_ok=True)

for i, source_name in enumerate(model.sources):
    stem_data = sources[i].numpy().T  # (T, C)
    stem_path = os.path.join(stems_dir, f"{source_name}.wav")
    sf.write(stem_path, stem_data, model_sr)
    print(f"Saved stem: {stem_path}", flush=True)

print(json.dumps({"status": "SUCCESS", "stems_dir": stems_dir, "stems": model.sources}))
