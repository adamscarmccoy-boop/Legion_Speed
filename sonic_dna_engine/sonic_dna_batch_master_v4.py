"""
sonic_dna_batch_master_v4.py
============================
BULLETPROOF REBUILD using the exact DSP section logic from fire_test.py.

Section logic (from flog.txt / fire_test.py — proven working):
  - Pedalboard C++ AudioFile for 6-second segment extraction (channels-first)
  - Only rms_db + crest_factor for CL nearest-neighbor matching
  - Combined StandardScaler fitted on baseline + target together
  - LanceDB 'rms' is linear — converted to dB for matching
  - Fresh Pedalboard per section (no shared state)
  - LUFS normalization post-pass

The Sonic DNA model weights are NOT involved in mastering decisions.
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
TARGET_LUFS   = -9.0    # -9.0 = Beatport/club   |   -14.0 = Spotify
SEGMENT_SEC   = 6.0     # 6s segments — matches fire_test.py / LanceDB granularity
THRESHOLD     = 82.0    # alignment pass threshold (same as fire_test.py)
# =====================================================================

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import os, time, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import soundfile as sf
from pedalboard.io import AudioFile
from pedalboard import Pedalboard, Compressor, HighpassFilter, Gain, Limiter
import lancedb
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import cdist

try:
    from marketing_scorer import MarketingScorer
    forest_engine = MarketingScorer()
    print("[OK] Forest Engine loaded")
except ImportError:
    forest_engine = None

# ── Config ─────────────────────────────────────────────────────────────────────
LANCEDB_PATH   = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
TABLE_NAME     = "omni_semantic_baselines"
BASELINE_TRACK = "Somebody (2024)"

BLOCK_SIZE         = 1024    # Tiny chunk size for parameter automation updates (~23ms)
GLIDE_MS           = 150.0   # How long it takes parameters to glide between sections
HIGHPASS_HZ        = 30.0
SUB_BASS_MONO_HZ   = 150.0
LIMITER_CEILING_DB = -0.3


# ── Step 1: Feature extraction — Pedalboard C++ (channels-first) ───────────────
def extract_features_pedalboard(audio_path: str, segment_sec: float = SEGMENT_SEC) -> list:
    """
    Exact replica of fire_test.py extract_features_pedalboard().
    Returns list of dicts: {rms_lin, rms_db, crest_factor, start_sec, end_sec}
    AudioFile reads (channels, samples) — channels-first, matches LanceDB computation.
    """
    segments = []
    with AudioFile(audio_path) as f:
        sr     = f.samplerate
        frames = int(segment_sec * sr)
        seg_idx = 0
        pos_sec = 0.0

        while True:
            audio = f.read(frames)              # (channels, samples)
            if audio.shape[1] < frames // 2:   # skip tiny tail
                break
            mono = audio.mean(axis=0)           # (samples,)

            rms_lin = float(np.sqrt(np.mean(mono ** 2)))
            rms_db  = float(20 * np.log10(rms_lin)) if rms_lin > 1e-9 else -100.0
            peak    = float(np.max(np.abs(mono)))
            crest   = float(peak / rms_lin) if rms_lin > 1e-9 else 0.0

            segments.append({
                "seg_idx":    seg_idx,
                "rms_lin":    rms_lin,
                "rms_db":     rms_db,
                "crest_factor": crest,
                "start_sec":  pos_sec,
                "end_sec":    pos_sec + segment_sec,
            })
            seg_idx += 1
            pos_sec += segment_sec

    return segments


# ── Step 2: Load Chris Lake baseline from LanceDB ─────────────────────────────
def load_baseline(baseline_track: str = BASELINE_TRACK):
    """
    Pull Chris Lake segments, convert linear rms → rms_db.
    Returns (baseline_df, X_base_raw) in [rms_db, crest_factor] space.
    """
    print(f"[INIT] Loading reference space from LanceDB...")
    db  = lancedb.connect(LANCEDB_PATH)
    tbl = db.open_table(TABLE_NAME)
    df  = tbl.to_pandas()

    df_base = df[df["track_name"].str.contains(
        baseline_track, case=False, regex=False, na=False)].copy()

    if df_base.empty:
        print(f"  [WARN] '{baseline_track}' not found. Falling back to 'chris lake'.")
        df_base = df[df["track_name"].str.contains(
            "chris lake", case=False, na=False)].copy()

    if df_base.empty:
        raise RuntimeError(f"No reference found for '{baseline_track}'")

    # LanceDB stores linear rms → convert to dB (same as fire_test.py)
    df_base["rms_db"] = df_base["rms"].apply(
        lambda v: float(20 * np.log10(max(v, 1e-9))) if pd.notna(v) and v > 0 else -100.0)

    df_base = df_base.reset_index(drop=True)
    X_base_raw = df_base[["rms_db", "crest_factor"]].fillna(0.0).values.astype(np.float64)

    print(f"  [OK] {len(df_base)} reference segments | "
          f"RMS range: {X_base_raw[:,0].min():.1f} to {X_base_raw[:,0].max():.1f} dBrms")
    return df_base, X_base_raw


# ── Step 3: Build combined scaler (baseline + target) ────────────────────────
def build_combined_scaler(X_base_raw: np.ndarray, all_track_segments: dict) -> StandardScaler:
    """
    Fire_test.py pattern: fit scaler on combined baseline + ALL target segments.
    This ensures both sides live in the same unit space.
    """
    targ_rows = []
    for segs in all_track_segments.values():
        for seg in segs:
            targ_rows.append([seg["rms_db"], seg["crest_factor"]])

    X_targ = np.array(targ_rows, dtype=np.float64)
    combined = np.vstack([X_base_raw, X_targ])
    scaler = StandardScaler()
    scaler.fit(combined)
    print(f"  [OK] Combined scaler fitted on {len(combined)} samples "
          f"({len(X_base_raw)} baseline + {len(X_targ)} target)")
    return scaler


# ── Audio helpers ──────────────────────────────────────────────────────────────
def enforce_sub_bass_mono(audio_frame: np.ndarray, sr: int) -> np.ndarray:
    """Force sub-150Hz to mono. audio_frame is (N, channels) — sf.read format."""
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


def calculate_mastering_targets(target_rms: float, current_rms: float,
                                target_crest: float, current_crest: float):
    """
    Deterministic mastering targets from DSP math.
    Calculates the desired end-state for a given section.
    """
    if current_crest > target_crest * 1.05:
        ratio        = float(np.clip(2.0 + (current_crest - target_crest) * 0.75, 1.8, 4.5))
        threshold_db = current_rms - 3.0
    else:
        ratio        = 1.0
        threshold_db = 0.0

    gain_db = float(np.clip(target_rms - current_rms, -12.0, 12.0))
    return gain_db, ratio, threshold_db


# ── Core mastering ─────────────────────────────────────────────────────────────
def process_track(input_path: str, df_base: pd.DataFrame,
                  X_base_scaled: np.ndarray, scaler: StandardScaler):
    base     = os.path.splitext(os.path.basename(input_path))[0]
    out_path = os.path.join(os.path.dirname(input_path),
                            base + "_SONIC_DNA_V4_MASTERED.wav")

    if not os.path.exists(input_path):
        print(f"  [SKIP] Not found: {input_path}")
        return None

    print(f"\n[>>] {os.path.basename(input_path)}")

    # ── Phase A: Feature extraction (Pedalboard C++, channels-first) ──────────
    t0 = time.perf_counter()
    segments = extract_features_pedalboard(input_path, SEGMENT_SEC)
    print(f"     Feature extraction: {len(segments)} segments "
          f"({(time.perf_counter()-t0)*1000:.0f}ms)")

    if not segments:
        print("     [SKIP] No segments extracted")
        return None

    # ── Phase B: Scale target features (same scaler as baseline) ─────────────
    X_targ = np.array([[s["rms_db"], s["crest_factor"]] for s in segments])
    X_targ_scaled = scaler.transform(X_targ)

    # ── Phase C: Nearest CL match per segment ─────────────────────────────────
    dists    = cdist(X_targ_scaled, X_base_scaled, metric="euclidean")
    best_idx = np.argmin(dists, axis=1)   # (N_segments,)

    # Alignment score: convert euclidean dist to % similarity
    max_dist = dists.max() + 1e-9
    scores   = (1.0 - dists[np.arange(len(segments)), best_idx] / max_dist) * 100.0

    # Print alignment table
    print(f"     {'Segment':<8}  {'Matched Base':<28}  {'Score':>6}  {'Status'}")
    print(f"     " + "-" * 65)
    passed = 0
    for i, (seg, bidx, score) in enumerate(zip(segments, best_idx, scores)):
        match_name = df_base.loc[bidx, "segment_name"] if "segment_name" in df_base.columns else f"seg{bidx}"
        status = "passed" if score >= THRESHOLD else "fallback"
        icon   = "OK" if score >= THRESHOLD else "--"
        if score >= THRESHOLD:
            passed += 1
        print(f"     seg{i:03d}    {match_name:<28}  {score:>5.1f}%  [{icon}]")
    print(f"     Passed: {passed}/{len(segments)} ({passed/len(segments)*100:.0f}%)")

    # ── Phase D: Load audio for mastering buffer (sf.read, samples-first) ─────
    y_full, sr_full = sf.read(input_path, always_2d=True)  # (N, channels)
    mastered   = np.zeros_like(y_full)

    print(f"\n     Planning mastering automation curves...")
    
    # 1. Pre-calculate targets for all sections
    section_targets = []
    for i, seg in enumerate(segments):
        s = max(0, int(seg["start_sec"] * sr_full))
        e = min(y_full.shape[0], int(seg["end_sec"] * sr_full))
        chunk = y_full[s:e]
        if chunk.shape[0] == 0:
            section_targets.append((0.0, 1.0, 0.0))
            continue

        bidx = best_idx[i]
        target_rms = float(df_base.loc[bidx, "rms_db"])
        target_crest = float(df_base.loc[bidx, "crest_factor"])
        
        mono_chunk  = chunk.mean(axis=1) if chunk.ndim > 1 else chunk
        rms_lin     = float(np.sqrt(np.mean(mono_chunk ** 2)))
        current_rms = float(20 * np.log10(rms_lin)) if rms_lin > 1e-9 else -100.0
        peak        = float(np.max(np.abs(mono_chunk)))
        current_crest = float(peak / rms_lin) if rms_lin > 1e-9 else 0.0

        gain_db, ratio, thr = calculate_mastering_targets(target_rms, current_rms, target_crest, current_crest)
        section_targets.append((gain_db, ratio, thr))

        if i < 5 or i == len(segments) - 1:
            print(f"     seg{i:03d}  curr={current_rms:.1f}dBrms  tgt={target_rms:.1f}dBrms  gain={gain_db:+.1f}dB  ratio={ratio:.2f}:1")
            
    if len(segments) > 5:
        print(f"     ... ({len(segments)-6} more sections planned)")

    # 2. Build block-by-block parameter arrays
    num_blocks = int(np.ceil(y_full.shape[0] / BLOCK_SIZE))
    param_gain = np.zeros(num_blocks)
    param_ratio = np.ones(num_blocks)
    param_thresh = np.zeros(num_blocks)
    
    for i, seg in enumerate(segments):
        b_start = int((seg["start_sec"] * sr_full) // BLOCK_SIZE)
        b_end   = int((seg["end_sec"] * sr_full) // BLOCK_SIZE)
        b_end   = min(b_end, num_blocks)
        if b_end > b_start:
            param_gain[b_start:b_end] = section_targets[i][0]
            param_ratio[b_start:b_end] = section_targets[i][1]
            param_thresh[b_start:b_end] = section_targets[i][2]

    # 3. Apply smoothing filter to glide the boundaries
    blocks_per_glide = max(1, int((GLIDE_MS / 1000.0 * sr_full) / BLOCK_SIZE))
    window = np.ones(blocks_per_glide) / blocks_per_glide
    param_gain = np.convolve(param_gain, window, mode='same')
    param_ratio = np.clip(np.convolve(param_ratio, window, mode='same'), 1.0, 100.0)
    param_thresh = np.convolve(param_thresh, window, mode='same')

    # 4. Process entire track dynamically through a single global chain
    print(f"     Processing continuous stream ({num_blocks} micro-blocks)...")
    global_board = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=HIGHPASS_HZ),
        Gain(gain_db=0.0),
        Compressor(threshold_db=0.0, ratio=1.0, attack_ms=10.0, release_ms=100.0),
        Limiter(threshold_db=LIMITER_CEILING_DB, release_ms=100.0),
    ])
    
    for b in range(num_blocks):
        s = b * BLOCK_SIZE
        e = min(s + BLOCK_SIZE, y_full.shape[0])
        chunk = y_full[s:e]
        
        # Automate properties (mid-process)
        global_board[1].gain_db      = float(param_gain[b])
        global_board[2].ratio        = float(param_ratio[b])
        global_board[2].threshold_db = float(param_thresh[b])
        
        chunk = enforce_sub_bass_mono(chunk, sr_full)
        processed = global_board(chunk, sample_rate=sr_full, reset=False)
        mastered[s:e] = processed

    # ── Phase E: LUFS normalization ────────────────────────────────────────────
    try:
        import pyloudnorm as pyln
        meter = pyln.Meter(sr_full)
        lufs  = meter.integrated_loudness(mastered)
        if lufs > -70.0 and not np.isinf(lufs):
            delta  = float(np.clip(TARGET_LUFS - lufs, -6.0, 12.0))
            makeup = 10 ** (delta / 20.0)
            mastered = np.clip(mastered * makeup, -0.98, 0.98)
            print(f"     LUFS: {lufs:.1f} -> {TARGET_LUFS:.1f} LUFS  "
                  f"(makeup {delta:+.1f}dB)")
    except Exception as ex:
        print(f"     LUFS pass skipped: {ex}")

    # ── Phase F: Write output ──────────────────────────────────────────────────
    sf.write(out_path, mastered, sr_full)

    if forest_engine:
        try:
            mono_out = mastered.mean(axis=1) if mastered.ndim > 1 else mastered
            rms_fin  = float(np.sqrt(np.mean(mono_out**2)))
            rms_db_fin = float(20*np.log10(rms_fin)) if rms_fin > 1e-9 else -100.0
            peak_fin = float(np.max(np.abs(mono_out)))
            feats = {"rms_db": rms_db_fin, "crest_factor": peak_fin/max(rms_fin,1e-9)}
            score = forest_engine.score_track(feats)
            print(f"     Forest Engine: {score['top_match']} "
                  f"({score['marketing_score_confidence']*100:.1f}%)  "
                  f"Anomaly: {'Yes' if score['is_anomaly'] else 'No'}")
        except Exception:
            pass

    print(f"     [OK] -> {os.path.basename(out_path)}")
    return out_path


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 70)
    print("  SONIC DNA BATCH MASTER v4")
    print("  Bulletproof DSP. fire_test.py section logic. No model in chain.")
    print("=" * 70)

    # Load Chris Lake baseline
    df_base, X_base_raw = load_baseline(BASELINE_TRACK)

    tracks = MY_TRACK_LIST if RUN_AS_BATCH_LIST else [MY_TRACK_LIST[0]]

    # Pre-extract features from all tracks (Pedalboard C++, fast)
    print(f"\n[INIT] Pre-extracting features from {len(tracks)} tracks...")
    all_segments = {}
    for path in tracks:
        if os.path.exists(path):
            segs = extract_features_pedalboard(path, SEGMENT_SEC)
            all_segments[path] = segs
            print(f"  {os.path.basename(path)}: {len(segs)} segments")
        else:
            print(f"  [MISSING] {path}")

    # Build combined scaler (fire_test.py pattern)
    scaler = build_combined_scaler(X_base_raw, all_segments)
    X_base_scaled = scaler.transform(X_base_raw)

    print(f"\nProcessing {len(tracks)} tracks...\n")
    results = []
    t0 = time.time()
    for track_path in tracks:
        try:
            out = process_track(track_path, df_base, X_base_scaled, scaler)
            results.append((track_path, out))
        except Exception as ex:
            import traceback
            print(f"  [ERR] {os.path.basename(track_path)}: {ex}")
            traceback.print_exc()
            results.append((track_path, None))

    print("\n" + "=" * 70)
    print(f"  DONE in {time.time()-t0:.1f}s")
    print("=" * 70)
    for src, dst in results:
        status = "[OK]  " if dst else "[FAIL]"
        print(f"  {status}  {os.path.basename(src)}")
    print("=" * 70)
