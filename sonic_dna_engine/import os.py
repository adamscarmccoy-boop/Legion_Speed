import os, time, warnings
import numpy as np
import pandas as pd
import soundfile as sf
import librosa
import onnxruntime as ort
from pedalboard import Pedalboard, Compressor, HighpassFilter, Gain, Limiter

warnings.filterwarnings("ignore")

# ── ADJUSTED CONFIG ──────────────────────────────────────────────────────────
DOWNLOADS_DIR      = r"C:\Users\adams\Downloads"
ONNX_PATH          = r"C:\WEB CASE STUDY\sonic_dna_engine\audio_llm_v1.onnx"
OUTPUT_DIR         = os.path.join(DOWNLOADS_DIR, "SOVEREIGN_GENERATIONS")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TARGET_LUFS        = -9.0
BLOCK_SIZE         = 1024
GLIDE_MS           = 150.0
HIGHPASS_HZ        = 30.0
SUB_BASS_MONO_HZ   = 150.0
LIMITER_CEILING_DB = -0.3

# ── 1. ADJUSTED: SonicDNAMaster (Now using your ONNX Engine) ─────────────────
class SonicDNAMaster:
    def __init__(self, model_path):
        self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        self.input_name = self.session.get_inputs()[0].name
        print(f"[OK] ONNX Neural Engine Loaded: {model_path}")

    def predict(self, feat_dict: dict):
        # Mapping your feat_dict to the 11-dim vector your ONNX expects
        dna_vector = [
            feat_dict["rms_db"], feat_dict["crest_factor"], feat_dict["sub_bass_energy"],
            feat_dict["bass_energy"], feat_dict["mid_energy"], feat_dict["high_energy"],
            feat_dict["spectral_centroid"], feat_dict["spectral_bandwidth"],
            feat_dict["spectral_rolloff"], feat_dict["spectral_contrast"],
            feat_dict["zero_crossing_rate"]
        ]
        input_tensor = np.array(dna_vector, dtype=np.float32).reshape(1, 11)
        out = self.session.run(None, {self.input_name: input_tensor})[0][0]
        
        # Mapping ONNX output back to your v5 logic: gain, ratio, threshold
        gain_db      = float(np.clip(out[0], -12.0, 12.0))
        comp_ratio   = float(np.clip(out[1], 1.0, 4.5))
        threshold_db = float(np.clip(out[2], -80.0, 0.0))
        return gain_db, comp_ratio, threshold_db

# ── 2. UNTOUCHED: Your Exact DSP Templates ───────────────────────────────────
def extract_dsp_features(y_mono: np.ndarray, sr: int):
    rms_val = float(np.sqrt(np.mean(y_mono**2)))
    rms_db  = float(20 * np.log10(max(rms_val, 1e-9)))
    peak    = float(np.max(np.abs(y_mono)) + 1e-9)
    crest   = float(peak / max(rms_val, 1e-9))
    N   = len(y_mono)
    fft = np.abs(np.fft.rfft(y_mono)) ** 2
    freqs = np.fft.rfftfreq(N, 1.0/sr)
    def band(lo, hi): return float(np.sum(fft[(freqs >= lo) & (freqs < hi)]))
    try:
        sc  = float(np.mean(librosa.feature.spectral_centroid(y=y_mono, sr=sr)))
        sbw = float(np.mean(librosa.feature.spectral_bandwidth(y=y_mono, sr=sr)))
        sr_ = float(np.mean(librosa.feature.spectral_rolloff(y=y_mono, sr=sr)))
        sct = float(np.mean(librosa.feature.spectral_contrast(y=y_mono, sr=sr)))
        zcr = float(np.mean(librosa.feature.zero_crossing_rate(y_mono)))
    except Exception:
        sc = sbw = sr_ = sct = zcr = 0.0
    return {
        "rms_db": rms_db, "crest_factor": crest,
        "sub_bass_energy": band(20, 80), "bass_energy": band(80, 300),
        "mid_energy": band(300, 3000), "high_energy": band(3000, 16000),
        "spectral_centroid": sc, "spectral_bandwidth": sbw,
        "spectral_rolloff": sr_, "spectral_contrast": sct,
        "zero_crossing_rate": zcr,
    }

def enforce_sub_bass_mono(audio_frame: np.ndarray, sr: int) -> np.ndarray:
    if audio_frame.ndim == 1 or audio_frame.shape[1] < 2:
        return audio_frame
    left, right = audio_frame[:, 0], audio_frame[:, 1]
    mid  = (left + right) / 2.0
    side = (left - right) / 2.0
    side = HighpassFilter(cutoff_frequency_hz=SUB_BASS_MONO_HZ)(side, sample_rate=sr)
    out = np.zeros_like(audio_frame)
    out[:, 0] = mid + side
    out[:, 1] = mid - side
    return out

# ── 3. ADJUSTED: Process Group (Mix stems then process via your v5 logic) ────
def process_stem_group(group_name: str, stem_paths: list, model: SonicDNAMaster):
    print(f"\n[>>] FORGING GROUP: {group_name}")
    sr = 44100
    y_full = None
    
    for s_path in stem_paths:
        y_stem, _ = sf.read(s_path, always_2d=True)
        if y_full is None: y_full = y_stem
        else:
            mlen = min(len(y_full), len(y_stem))
            y_full = y_full[:mlen] + y_stem[:mlen]

    mastered = np.zeros_like(y_full)
    segment_sec = 6.0
    frames = int(segment_sec * sr)
    num_segments = int(np.ceil(y_full.shape[0] / frames))
    
    section_targets = []
    for i in range(num_segments):
        s, e = i * frames, min((i + 1) * frames, y_full.shape[0])
        mono_chunk = y_full[s:e].mean(axis=1)
        feats = extract_dsp_features(mono_chunk, sr)
        section_targets.append(model.predict(feats))

    num_blocks = int(np.ceil(y_full.shape[0] / BLOCK_SIZE))
    param_gain, param_ratio, param_thresh = np.zeros(num_blocks), np.ones(num_blocks), np.zeros(num_blocks)
    
    for i in range(num_segments):
        b_s, b_e = int((i*frames)//BLOCK_SIZE), int(((i+1)*frames)//BLOCK_SIZE)
        if b_e > b_s:
            param_gain[b_s:b_e], param_ratio[b_s:b_e], param_thresh[b_s:b_e] = section_targets[i]

    # Smooth & Process (Direct v5 Automation Logic)
    global_board = Pedalboard([HighpassFilter(cutoff_frequency_hz=HIGHPASS_HZ), Gain(0), Compressor(0,1), Limiter(LIMITER_CEILING_DB)])
    for b in range(num_blocks):
        s, e = b*BLOCK_SIZE, min((b+1)*BLOCK_SIZE, y_full.shape[0])
        global_board[1].gain_db, global_board[2].ratio, global_board[2].threshold_db = param_gain[b], param_ratio[b], param_thresh[b]
        chunk = enforce_sub_bass_mono(y_full[s:e], sr)
        mastered[s:e] = global_board(chunk, sample_rate=sr, reset=False)

    out_path = os.path.join(OUTPUT_DIR, f"SOVEREIGN_{group_name}.wav")
    sf.write(out_path, mastered, sr)
    print(f"     [OK] -> {os.path.basename(out_path)}")

# ── 4. Main (Recursive Search) ───────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 70)
    print("  SOVEREIGN STEM FORGE (ADJUSTED v5 NEURAL)")
    print("=" * 70)
    model = SonicDNAMaster(ONNX_PATH)
    for root, dirs, files in os.walk(DOWNLOADS_DIR):
        if "stems" in root.lower():
            wavs = [os.path.join(root, f) for f in files if f.endswith(".wav")]
            if wavs: process_stem_group(os.path.basename(os.path.dirname(root)), wavs, model)
