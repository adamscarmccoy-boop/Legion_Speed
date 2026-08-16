import json
notebook_path = r'C:\.genkit\Sovereign_Audio_Intelligence_Generative_WhitePaper.ipynb'
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

new_cell = {
    'cell_type': 'code',
    'execution_count': None,
    'id': 'end_to_end_test',
    'metadata': {},
    'outputs': [],
    'source': [
        '# Full ONNX C++ Execution Pipeline (Generation -> DSP) on Real Audio\n',
        'import librosa\n',
        'import numpy as np\n',
        'import onnxruntime as ort\n',
        'import time\n',
        '\n',
        'print("1. Extracting Acoustic Manifold from Downloads...")\n',
        'wav_path = r"C:\\Users\\adams\\Downloads\\129bpm-ADMIT IT.wav"\n',
        'y, sr = librosa.load(wav_path, sr=44100, mono=True)\n',
        '\n',
        'rms_val = float(np.sqrt(np.mean(y ** 2)))\n',
        'peak = float(np.max(np.abs(y))) + 1e-9\n',
        'crest_factor = rms_val / peak\n',
        'zcr = float(np.mean(librosa.feature.zero_crossing_rate(y)))\n',
        'spectral_centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))\n',
        'spectral_rolloff = float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr)))\n',
        'spectral_bandwidth = float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr)))\n',
        'S = np.abs(librosa.stft(y))\n',
        'spectral_contrast = float(np.mean(librosa.feature.spectral_contrast(S=S, sr=sr)))\n',
        'onset_env = librosa.onset.onset_strength(y=y, sr=sr)\n',
        'onset_strength = float(np.mean(onset_env))\n',
        'transient_density = float(len(librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr))) / (len(y)/sr)\n',
        '\n',
        '# Extract exactly 11 dims to match audio_llm_v1.onnx\n',
        'features = np.array([rms_val, crest_factor, spectral_centroid, spectral_rolloff, spectral_bandwidth, spectral_contrast, zcr, onset_strength, transient_density, 0.5, 0.5], dtype=np.float32)\n',
        '\n',
        'print("2. Piping through pure ONNX C++ Engines...")\n',
        't0 = time.time()\n',
        '# Generative Engine\n',
        'session_llm = ort.InferenceSession(r"C:\\WEB CASE STUDY\\sonic_dna_engine\\audio_llm_v1.onnx", providers=["CPUExecutionProvider"])\n',
        'hallucinated = session_llm.run(None, {session_llm.get_inputs()[0].name: features.reshape(1, -1)})[0][0]\n',
        '\n',
        '# Zero-Pad to 64 dims\n',
        'padded = np.pad(hallucinated, (0, 64 - len(hallucinated)), mode="constant")\n',
        '\n',
        '# End DSP Engine\n',
        'session_dsp = ort.InferenceSession(r"C:\\WEB CASE STUDY\\sovereign_big_brain_exhaustive.onnx", providers=["CPUExecutionProvider"])\n',
        'dsp_params = session_dsp.run(None, {session_dsp.get_inputs()[0].name: padded.reshape(1, -1).astype(np.float32)})[0][0]\n',
        't1 = time.time()\n',
        '\n',
        'print(f"\\n🔥 Heavy lifting complete in {(t1-t0)*1000:.2f} ms (Pure C++ Execution)!")\n',
        'print(f"Final 12 DSP Parameters: {np.round(dsp_params, 4)}")\n'
    ]
}

nb['cells'].append(new_cell)

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)
print('Cell successfully appended to notebook!')
