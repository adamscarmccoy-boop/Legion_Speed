import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import time
import warnings
import numpy as np
import pyarrow as pa
import lancedb
import ray
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from sklearn.preprocessing import StandardScaler

# ==============================================================================
# SOVEREIGN LIFE-CYCLE STABILIZER (AUTO-INJECTED)
# Prevents dangling stdout/stdio pipes and GCS registry locks on Windows exit
# ==============================================================================
import atexit
import signal

def clean_exit_handler(*args, **kwargs):
    import sys
    sys.stderr.write("\n[LMS LIFECYCLE] Exit triggered. Flushing system streams...\n")
    sys.stderr.flush()
    try:
        import ray
        if ray.is_initialized():
            sys.stderr.write("[LMS LIFECYCLE] Active Ray session detected. Disconnecting...\n")
            ray.shutdown()
    except Exception:
        pass
    sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================


from pedalboard.io import AudioFile
from dsp_alignment_actor import DSPAlignmentActor
from legion_schema import SegmentPhysics, AlignmentQuery, AlignmentResult, VerificationReport

warnings.filterwarnings('ignore')

# ── Config ────────────────────────────────────────────────────────────────────
LANCEDB_PATH   = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
TABLE_NAME     = "omni_semantic_baselines"
BASELINE_TRACK = "Somebody (2024)"
SEGMENT_SEC    = 6.0
THRESHOLD      = 82.0
NUM_ACTORS     = 4
ASSETS_DIR     = r"C:\WEB CASE STUDY\Acoustic-DNA-Audio-Engine\assets"

import glob

GPU_OUT_DIR = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\AI_Logs\gpu_outputs"
TARGET_FILES = glob.glob(os.path.join(GPU_OUT_DIR, "*_MASTERED.wav"))

SHORT_NAMES = {}

# ── Feature extraction (same as fire_test.py) ──────────────────────────────────
def extract_features(wav_path, segment_sec=6.0):
    segments = []
    track_name = os.path.splitext(os.path.basename(wav_path))[0]
    with AudioFile(wav_path) as f:
        sr, frames, seg_idx = f.samplerate, int(segment_sec * f.samplerate), 0
        while True:
            audio = f.read(frames)
            if audio.shape[1] < frames // 2:
                break
            mono    = audio.mean(axis=0)
            rms_lin = float(np.sqrt(np.mean(mono ** 2)))
            rms_db  = float(20 * np.log10(rms_lin)) if rms_lin > 1e-9 else -100.0
            peak    = float(np.max(np.abs(mono)))
            crest   = float(peak / rms_lin) if rms_lin > 1e-9 else 0.0
            segments.append(SegmentPhysics(
                segment_name=f"{track_name}_seg{seg_idx:03d}",
                track_name=track_name,
                rms_db=rms_db,
                crest_factor=crest,
            ))
            seg_idx += 1
    return segments

def load_baseline_arrow(lancedb_path, table_name, track_filter):
    db  = lancedb.connect(lancedb_path)
    tbl = db.open_table(table_name)
    df  = tbl.to_pandas()
    df_base = df[df["track_name"].str.contains(track_filter, case=False, regex=False, na=False)].copy()
    if df_base.empty:
        raise RuntimeError(f"No baseline segments found for '{track_filter}'")
    return pa.RecordBatch.from_pandas(df_base)

# ── Visuals ───────────────────────────────────────────────────────────────────
FIRE_CMAP = LinearSegmentedColormap.from_list("fire", [
    (0.0,  "#1a0a00"),
    (0.5,  "#8b1a00"),
    (0.75, "#ff6600"),
    (0.88, "#ffcc00"),
    (1.0,  "#ffffff"),
])

def save_heatmap(track_results: dict, path: str):
    tracks  = list(track_results.keys())
    max_seg = max(len(v) for v in track_results.values())

    matrix = np.full((len(tracks), max_seg), np.nan)
    for i, (t, segs) in enumerate(track_results.items()):
        for j, r in enumerate(segs):
            matrix[i, j] = r.alignment_score

    fig, ax = plt.subplots(figsize=(max(12, max_seg * 0.25), max(4, len(tracks) * 1.0)),
                           dpi=180, facecolor="#0d0d0d")
    ax.set_facecolor("#0d0d0d")

    im = ax.imshow(matrix, aspect='auto', cmap=FIRE_CMAP, vmin=0, vmax=100,
                   interpolation='nearest')

    cbar = fig.colorbar(im, ax=ax, fraction=0.02, pad=0.01)
    cbar.ax.yaxis.set_tick_params(color='white')
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color='white', fontsize=9)
    cbar.set_label('Alignment %', color='white', fontsize=10)

    ax.set_yticks(range(len(tracks)))
    short = [SHORT_NAMES.get(t, t[:22]) for t in tracks]
    ax.set_yticklabels(short, color='white', fontsize=9, fontweight='bold')
    ax.set_xlabel('Segment Index (6s each)', color='#aaaaaa', fontsize=10)
    ax.set_title('🔥 DSP Alignment Heatmap — vs Chris Lake "Somebody (2024)"',
                 color='white', fontsize=13, fontweight='bold', pad=14)
    ax.tick_params(colors='#666666')
    for spine in ax.spines.values():
        spine.set_edgecolor('#333333')

    # Annotate scores inside the cells
    for i in range(len(tracks)):
        for j in range(max_seg):
            v = matrix[i, j]
            if not np.isnan(v):
                color = 'white' if v < 60 else ('black' if v > 90 else '#111111')
                ax.text(j, i, f'{v:.0f}', ha='center', va='center',
                        fontsize=6, color=color, fontweight='bold')

    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches='tight', facecolor='#0d0d0d')
    plt.close()
    print(f"  💾 Saved heatmap: {os.path.basename(path)}")


def save_bar_chart(track_results: dict, threshold: float, path: str):
    tracks = list(track_results.keys())
    short  = [SHORT_NAMES.get(t, t[:22]) for t in tracks]
    avgs   = [np.mean([r.alignment_score for r in segs]) for segs in track_results.values()]
    bests  = [max(r.alignment_score for r in segs) for segs in track_results.values()]
    worsts = [min(r.alignment_score for r in segs) for segs in track_results.values()]
    
    x = np.arange(len(tracks))
    fig, ax = plt.subplots(figsize=(12, 6), dpi=180, facecolor='#0d0d12')

    ax.set_facecolor('#13131d')
    for spine in ax.spines.values():
        spine.set_edgecolor('#333333')

    w = 0.25
    ax.bar(x - w, avgs,  w, label='Avg',  color='#ff6600', alpha=0.9)
    ax.bar(x,     bests, w, label='Best', color='#ffcc00', alpha=0.9)
    ax.bar(x + w, worsts,w, label='Worst',color='#8b1a00', alpha=0.9)
    ax.axhline(threshold, color='#00ffff', linestyle='--', linewidth=1.2,
                label=f'Threshold {threshold}%', alpha=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels(short, color='white', fontsize=9, fontweight='bold')
    ax.set_ylabel('Alignment Score %', color='#aaaaaa')
    ax.set_ylim(0, 105)
    ax.set_title('🎯 Dynamic segment alignment scoring comparison', color='white', fontsize=12, fontweight='bold')
    ax.legend(facecolor='#222222', edgecolor='#444444', labelcolor='white', fontsize=9)
    ax.tick_params(colors='#666666')
    ax.yaxis.label.set_color('#aaaaaa')

    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches='tight', facecolor='#0d0d12')
    plt.close()
    print(f"  💾 Saved bar chart: {os.path.basename(path)}")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("  🔥 RUNNING REAL RAY ALIGNMENT & GENERATING VISUALS")
    print("=" * 70)
    
    # 1. Extract target features
    all_track_segments = {}
    for wav_path in TARGET_FILES:
        if not os.path.exists(wav_path):
            print(f"  ⚠️ Skipping missing target file: {wav_path}")
            continue
        name = os.path.splitext(os.path.basename(wav_path))[0]
        all_track_segments[name] = extract_features(wav_path, SEGMENT_SEC)
        print(f"  Loaded: {name} -> {len(all_track_segments[name])} segments")

    if not all_track_segments:
        print("❌ No valid files found.")
        sys.exit(1)

    # 2. Boot Ray & load baseline to Plasma
    print("\n🚀 Initializing Ray cluster...")
    ray.init(ignore_reinit_error=True, log_to_driver=False)
    
    baseline_batch = load_baseline_arrow(LANCEDB_PATH, TABLE_NAME, BASELINE_TRACK)
    baseline_ref = ray.put(baseline_batch)
    
    # Spin up actor pool
    actors = [DSPAlignmentActor.remote(LANCEDB_PATH, TABLE_NAME) for _ in range(NUM_ACTORS)]
    
    # Initialize baseline in actors
    init_refs = [a.set_baseline.remote(baseline_ref) for a in actors]
    ray.get(init_refs)

    # 3. Fit StandardScaler in driver
    print("Fitting Scaler on combined features...")
    baseline_df = baseline_batch.to_pandas()
    baseline_df["rms_db"] = baseline_df["rms"].apply(
        lambda v: float(20 * np.log10(v)) if v > 1e-9 else -100.0
    )
    X_base_raw = baseline_df[["rms_db", "crest_factor"]].fillna(0.0).values

    targ_rows = []
    for segs in all_track_segments.values():
        for seg in segs:
            targ_rows.append([seg.rms_db, seg.crest_factor])
    X_targ_raw = np.array(targ_rows, dtype=np.float64)

    combined = np.vstack([X_base_raw, X_targ_raw])
    scaler = StandardScaler()
    scaler.fit(combined)

    scaler_state = {
        "mean_":  scaler.mean_.tolist(),
        "scale_": scaler.scale_.tolist(),
    }
    
    # Push scaler state to actors
    scale_refs = [a.set_scaler.remote(scaler_state) for a in actors]
    ray.get(scale_refs)

    # 4. Perform parallel alignment
    print("Running parallel alignment...")
    track_results_dict = {}
    
    for name, segments in all_track_segments.items():
        tasks = []
        for i, seg in enumerate(segments):
            actor = actors[i % NUM_ACTORS]
            query = AlignmentQuery(
                targ_idx=i,
                targ_segment=seg,
                threshold=THRESHOLD,
            )
            tasks.append(actor.align_segment.remote(query.model_dump()))
            
        raw_results = ray.get(tasks)
        track_results_dict[name] = [AlignmentResult(**r) for r in raw_results]
        
    ray.shutdown()

    # 5. Save visual assets
    print("\nGenerating charts...")
    os.makedirs(ASSETS_DIR, exist_ok=True)
    
    save_heatmap(track_results_dict, os.path.join(ASSETS_DIR, "alignment_heatmap.png"))
    save_bar_chart(track_results_dict, THRESHOLD, os.path.join(ASSETS_DIR, "alignment_bar_chart.png"))
    
    print("\n✅ Verification visuals generated successfully.")

if __name__ == "__main__":
    main()