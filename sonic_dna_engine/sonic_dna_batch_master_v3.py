"""
sonic_dna_batch_master_v3.py
============================
upgraded_dynamic_batch_master_v2.py -- now powered by sonic_dna_master_v2.pt

Changes from v2:
  - LanceDB lookup REMOVED (no runtime DB dependency)
  - Chris Lake nearest-neighbor search REMOVED
  - Mastering params now come from the Sonic DNA model forward pass
  - Path bug fixed (MY_TRACK_LIST supports full paths)
"""

# =====================================================================
# USER INPUT CONFIGURATION
# =====================================================================
RUN_AS_BATCH_LIST = True
MY_TRACK_LIST = [
    r"C:\Users\adams\Downloads\feed this desire.wav",
    r"C:\Users\adams\Downloads\jumpy jumpy.wav",
    r"C:\Users\adams\Downloads\admit it.mp3",
    r"C:\Users\adams\Downloads\VIZON & Ren Carter - Had To Go [Extended Mix] (1).mp3"
]
# =====================================================================

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import os, time, logging, warnings
warnings.filterwarnings("ignore")
import numpy as np
import soundfile as sf
import librosa
import torch
import torch.nn as nn
from pedalboard import Pedalboard, Compressor, HighpassFilter, Gain, Limiter

# ── Sonic DNA Master Model ─────────────────────────────────────────────────────
MODEL_PATH = r"C:\WEB CASE STUDY\sonic_dna_output\sonic_dna_master_v2.pt"

DSP_COLS_MODEL = [
    "rms_db","crest_factor","sub_bass_energy","bass_energy",
    "mid_energy","high_energy","spectral_centroid",
    "spectral_bandwidth","spectral_rolloff","spectral_contrast",
    "zero_crossing_rate"
]

class _MasteringNet(nn.Module):
    def __init__(self, in_dim, out_dim):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(in_dim, 128), nn.LayerNorm(128), nn.GELU(),
            nn.Linear(128, 64),    nn.LayerNorm(64),  nn.GELU(),
        )
        self.sonic_dna   = nn.Linear(64, 64)
        self.master_head = nn.Sequential(nn.Linear(64, 32), nn.GELU(), nn.Linear(32, out_dim))
    def forward(self, x):
        h = self.encoder(x)
        return self.master_head(h)


class SonicDNAMaster:
    """Drop-in replacement for LanceDB lookup + build_section_board."""

    def __init__(self, model_path):
        ckpt = torch.load(model_path, weights_only=False)
        self.in_dim  = ckpt["in_dim"]
        self.out_dim = ckpt["out_dim"]
        self.dsp_cols = ckpt["dsp_cols"]
        self.X_mean  = torch.tensor(ckpt["X_mean"])
        self.X_std   = torch.tensor(ckpt["X_std"])
        self.Y_mean  = torch.tensor(ckpt["Y_mean"])
        self.Y_std   = torch.tensor(ckpt["Y_std"])
        self.model   = _MasteringNet(self.in_dim, self.out_dim)
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.model.eval()
        print(f"[OK] SonicDNAMaster loaded: {self.in_dim}D DSP -> [gain_db, ratio, threshold]")

    def predict(self, feat_dict: dict):
        """feat_dict: any dict containing DSP feature keys. Returns (gain_db, ratio, threshold_db)."""
        vec = torch.tensor(
            [float(feat_dict.get(c, 0.0)) for c in self.dsp_cols],
            dtype=torch.float32
        )
        vec_norm = (vec - self.X_mean) / self.X_std
        with torch.no_grad():
            raw = self.model(vec_norm.unsqueeze(0)).squeeze()
        out = raw * self.Y_std + self.Y_mean
        gain_db      = float(np.clip(out[0].item(), -12.0, 12.0))
        comp_ratio   = float(np.clip(out[1].item(), 1.0, 4.5))
        threshold_db = float(np.clip(out[2].item(), -80.0, 0.0))
        return gain_db, comp_ratio, threshold_db

    def build_board(self, feat_dict: dict, limiter_ceiling: float = -0.3) -> Pedalboard:
        """Predict mastering params and return a ready Pedalboard."""
        gain_db, ratio, threshold_db = self.predict(feat_dict)
        return Pedalboard([
            HighpassFilter(cutoff_frequency_hz=30.0),
            Gain(gain_db=gain_db),
            Compressor(threshold_db=threshold_db, ratio=ratio, attack_ms=10.0, release_ms=100.0),
            Limiter(threshold_db=limiter_ceiling, release_ms=100.0),
        ]), gain_db, ratio, threshold_db


# ── Audio helpers ──────────────────────────────────────────────────────────────
CROSSFADE_SAMPLES     = 512
SUB_BASS_MONO_HZ      = 150.0
LIMITER_CEILING_DB    = -0.3
TARGET_LUFS           = -9.0   # Club/Beatport standard. Change to -14.0 for Spotify.

def enforce_sub_bass_mono(audio_frame, sr):
    if audio_frame.ndim == 1 or audio_frame.shape[1] < 2:
        return audio_frame
    left, right = audio_frame[:, 0], audio_frame[:, 1]
    mid = (left + right) / 2.0
    side = (left - right) / 2.0
    side = HighpassFilter(cutoff_frequency_hz=SUB_BASS_MONO_HZ)(side, sample_rate=sr)
    out = np.zeros_like(audio_frame)
    out[:, 0] = mid + side
    out[:, 1] = mid - side
    return out

def blend_chunk(target, chunk, start, xfade=CROSSFADE_SAMPLES):
    clen = chunk.shape[0]
    if clen == 0: return
    target[start:start+clen] = chunk
    if start >= xfade and clen > xfade:
        ramp = np.linspace(0, 1, xfade).reshape(-1, 1) if target.ndim > 1 else np.linspace(0, 1, xfade)
        target[start:start+xfade] = chunk[:xfade] * ramp + target[start-xfade:start] * (1 - ramp)

def extract_dsp_features(y, sr):
    """Fast DSP feature extraction matching the model's expected inputs."""
    if y.ndim > 1:
        y_mono = y.mean(axis=1)
    else:
        y_mono = y

    rms_val = float(np.sqrt(np.mean(y_mono**2)))
    rms_db  = float(20 * np.log10(max(rms_val, 1e-9)))
    peak    = float(np.max(np.abs(y_mono)) + 1e-9)
    crest   = float(peak / max(rms_val, 1e-9))

    # Frequency band energies via FFT
    N   = len(y_mono)
    fft = np.abs(np.fft.rfft(y_mono)) ** 2
    freqs = np.fft.rfftfreq(N, 1.0/sr)
    def band(lo, hi): return float(np.sum(fft[(freqs >= lo) & (freqs < hi)]))

    sub_bass = band(20, 80)
    bass     = band(80, 300)
    mid      = band(300, 3000)
    high     = band(3000, 16000)

    # Spectral features via librosa
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
        "sub_bass_energy": sub_bass, "bass_energy": bass,
        "mid_energy": mid, "high_energy": high,
        "spectral_centroid": sc, "spectral_bandwidth": sbw,
        "spectral_rolloff": sr_, "spectral_contrast": sct,
        "zero_crossing_rate": zcr,
    }


# ── Structural segmenter (fallback if Essentia not available) ──────────────────
try:
    from essentia_wsl_bridge import get_structural_audio_analysis
    print("[OK] Essentia structural analysis available")
except ImportError:
    def get_structural_audio_analysis(path):
        dur = librosa.get_duration(path=path)
        seg_len = 30.0
        sections = []
        t = 0.0
        while t < dur:
            sections.append({"start_time_sec": t, "end_time_sec": min(t + seg_len, dur)})
            t += seg_len
        return {"sections": sections}
    print("[WARN] Essentia not found. Using 30s chunk fallback segmentation.")

# ── Forest Engine scorer (optional) ───────────────────────────────────────────
try:
    from marketing_scorer import MarketingScorer
    forest_engine = MarketingScorer()
except ImportError:
    forest_engine = None


# ── Core processing ────────────────────────────────────────────────────────────
def process_track(input_path: str, sonic_dna: SonicDNAMaster):
    base  = os.path.splitext(os.path.basename(input_path))[0]
    out_path = os.path.join(os.path.dirname(input_path),
                            base + "_SONIC_DNA_MASTERED.wav")

    if not os.path.exists(input_path):
        print(f"  [SKIP] File not found: {input_path}")
        return None

    print(f"\n[>>] {os.path.basename(input_path)}")

    # Structural analysis
    analysis = get_structural_audio_analysis(input_path)
    sections = analysis.get("sections", [])
    if not sections:
        dur = librosa.get_duration(path=input_path)
        sections = [{"start_time_sec": 0.0, "end_time_sec": dur}]

    # Load audio once
    y_full, sr = sf.read(input_path, always_2d=True)
    mastered   = np.zeros_like(y_full)

    print(f"     Sections: {len(sections)}  |  Duration: {y_full.shape[0]/sr:.1f}s  |  SR: {sr}Hz")

    for i, sect in enumerate(sections):
        s = max(0, int(sect["start_time_sec"] * sr))
        e = min(y_full.shape[0], int(sect["end_time_sec"] * sr))
        chunk = y_full[s:e]
        if chunk.shape[0] == 0:
            continue

        # Extract DSP features for this chunk
        feats = extract_dsp_features(chunk, sr)

        # Get mastering params from Sonic DNA model (no LanceDB, no lookup)
        board, gain_db, ratio, threshold_db = sonic_dna.build_board(feats, LIMITER_CEILING_DB)

        # Apply sub-bass mono enforcement + mastering chain
        chunk = enforce_sub_bass_mono(chunk, sr)
        processed = board(chunk, sample_rate=sr, reset=False)
        blend_chunk(mastered, processed, s)

        seg_name = sect.get("label", f"Section {i+1}")
        print(f"     [{i+1:2d}] {seg_name:<30} gain={gain_db:+.1f}dB  "
              f"ratio={ratio:.2f}:1  thr={threshold_db:.1f}dB")

    # ── LUFS targeting post-pass ──────────────────────────────
    try:
        import pyloudnorm as pyln
        meter = pyln.Meter(sr)
        if mastered.ndim > 1:
            lufs = meter.integrated_loudness(mastered)
        else:
            lufs = meter.integrated_loudness(mastered.reshape(-1, 1))
        if lufs > -70.0 and not np.isinf(lufs):  # valid LUFS reading
            delta_db = TARGET_LUFS - lufs
            # Safety clip: don't boost more than 12dB or cut more than 6dB
            delta_db = float(np.clip(delta_db, -6.0, 12.0))
            makeup = 10 ** (delta_db / 20.0)
            mastered = np.clip(mastered * makeup, -0.98, 0.98)
            print(f"     LUFS: {lufs:.1f} -> {TARGET_LUFS:.1f} (makeup {delta_db:+.1f}dB)")
        else:
            print(f"     LUFS: measurement invalid ({lufs:.1f}), skipping normalization")
    except Exception as ex:
        print(f"     LUFS pass skipped: {ex}")

    # Write output
    sf.write(out_path, mastered, sr)

    # Optional Forest Engine score
    if forest_engine:
        try:
            final_feats = extract_dsp_features(mastered, sr)
            score = forest_engine.score_track(final_feats)
            print(f"     Forest Engine: {score['top_match']} "
                  f"({score['marketing_score_confidence']*100:.1f}%) "
                  f"| Anomaly: {'Yes' if score['is_anomaly'] else 'No'}")
        except Exception as ex:
            print(f"     Forest Engine: {ex}")

    print(f"     [OK] -> {os.path.basename(out_path)}")
    return out_path


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 65)
    print("  SONIC DNA BATCH MASTER v3")
    print("  Powered by sonic_dna_master_v2.pt  (no LanceDB at runtime)")
    print("=" * 65)

    # Load model once
    sonic_dna = SonicDNAMaster(MODEL_PATH)

    tracks = MY_TRACK_LIST if RUN_AS_BATCH_LIST else [MY_TRACK_LIST[0]]
    print(f"\nProcessing {len(tracks)} tracks...\n")

    results = []
    t0 = time.time()
    for track_path in tracks:
        try:
            out = process_track(track_path, sonic_dna)
            results.append((track_path, out))
        except Exception as ex:
            print(f"  [ERR] {track_path}: {ex}")
            results.append((track_path, None))

    print("\n" + "=" * 65)
    print(f"  DONE in {time.time()-t0:.1f}s")
    print("=" * 65)
    for src, dst in results:
        status = "[OK]" if dst else "[FAIL]"
        print(f"  {status}  {os.path.basename(src)}")
    print("=" * 65)
