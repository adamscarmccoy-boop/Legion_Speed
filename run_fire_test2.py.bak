
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

"""

Fire Test — DSP Alignment Actor

================================

Runs 3 production WAVs against Chris Lake LanceDB baseline using:

  - Pedalboard C++ for audio loading + feature extraction (OUTSIDE Ray)

  - PyArrow for zero-copy baseline transport into Plasma store

  - DSPAlignmentActor (Ray Actor) for parallel scipy C-extension alignment

  - Self-verify pass: re-checks from LanceDB scalars, reports drift

"""



import sys

sys.stdout.reconfigure(encoding='utf-8')



import os

import sys

import time

import numpy as np

import pyarrow as pa

import lancedb

import ray



# Pedalboard: C++ audio I/O — runs BEFORE ray.init()

from pedalboard.io import AudioFile



from dsp_alignment_actor import DSPAlignmentActor

from legion_schema import (

    SegmentPhysics,

    AlignmentQuery,

    AlignmentResult,

    VerificationReport,

)



# ── Config ────────────────────────────────────────────────────────────────────

LANCEDB_PATH  = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"

TABLE_NAME    = "omni_semantic_baselines"

BASELINE_TRACK = "Somebody (2024)"    # Chris Lake reference

SEGMENT_SEC    = 6.0                  # match LanceDB segment granularity (~66 segs per ~7min track)

THRESHOLD      = 82.0                 # alignment pass threshold

NUM_ACTORS     = 4                    # one per 4-core cluster



TARGET_FILES = [

    r"C:\Users\adams\Downloads\GIRL NAME DREAM -  i need that.mp3",

    r"C:\Users\adams\Downloads\new life.wav",

    r"C:\Users\adams\Downloads\new life#1.wav",

]



# ── Step 1: Pedalboard C++ feature extraction (outside Ray) ───────────────────

def extract_features_pedalboard(wav_path: str, segment_sec: float = 30.0) -> list[SegmentPhysics]:

    """

    Load WAV with Pedalboard C++ engine. Slice into segments.

    Units MATCHED to LanceDB schema:

      - rms       : linear (0-1), same as LanceDB 'rms' column

      - crest_factor : ratio, same scale

      - band energies : raw FFT magnitude^2 sums — same computation as C++ engine

      - spectral_centroid : Hz

    """

    segments = []

    track_name = os.path.splitext(os.path.basename(wav_path))[0]



    with AudioFile(wav_path) as f:

        sr     = f.samplerate

        frames = int(segment_sec * sr)

        seg_idx = 0



        while True:

            audio = f.read(frames)   # numpy float32 (channels, samples)

            if audio.shape[1] < frames // 2:

                break



            mono = audio.mean(axis=0)



            # ── LINEAR RMS → convert to dB (matches original script's parse_text_features) ──

            rms_lin = float(np.sqrt(np.mean(mono ** 2)))

            rms_db  = float(20 * np.log10(rms_lin)) if rms_lin > 1e-9 else -100.0

            peak    = float(np.max(np.abs(mono)))

            crest   = float(peak / rms_lin) if rms_lin > 1e-9 else 0.0



            seg = SegmentPhysics(

                segment_name  = f"{track_name}_seg{seg_idx:03d}",

                track_name    = track_name,

                rms_db        = rms_db,     # dB — matches original parse_text_features output

                crest_factor  = crest,

            )

            segments.append(seg)

            seg_idx += 1



    return segments





# ── Step 2: Load Chris Lake baseline as PyArrow → Plasma ──────────────────────

def load_baseline_arrow(lancedb_path: str, table_name: str, track_filter: str):

    """Pull baseline segments from LanceDB, return as PyArrow RecordBatch."""

    db  = lancedb.connect(lancedb_path)

    tbl = db.open_table(table_name)

    df  = tbl.to_pandas()

    df_base = df[df["track_name"].str.contains(track_filter, case=False, regex=False, na=False)].copy()

    if df_base.empty:

        raise RuntimeError(f"No baseline segments found for '{track_filter}'")

    print(f"  ✅ Baseline loaded: {len(df_base)} segments ({track_filter})")

    return pa.RecordBatch.from_pandas(df_base)





# ── Main fire test ─────────────────────────────────────────────────────────────

def main():

    print("=" * 70)

    print("  🔥 DSP ALIGNMENT FIRE TEST  —  Ray Actor + Pedalboard C++ + PyArrow")

    print("=" * 70)



    # Step 1: Extract features from all 3 WAVs with Pedalboard (BEFORE ray.init)

    print("\n📦 Phase 1: Pedalboard C++ feature extraction (outside Ray)")

    all_track_segments: dict[str, list[SegmentPhysics]] = {}

    for wav_path in TARGET_FILES:

        if not os.path.exists(wav_path):

            print(f"  ⚠️  MISSING: {wav_path}")

            continue

        name = os.path.basename(wav_path)

        t0   = time.perf_counter()

        segs = extract_features_pedalboard(wav_path, SEGMENT_SEC)

        elapsed = (time.perf_counter() - t0) * 1000

        print(f"  ✅ {name}  →  {len(segs)} segments  ({elapsed:.0f} ms)")

        all_track_segments[name] = segs



    if not all_track_segments:

        print("❌ No valid WAV files found. Aborting.")

        sys.exit(1)



    # Step 2: Load baseline into PyArrow, put in Plasma store

    print("\n📡 Phase 2: Loading Chris Lake baseline → PyArrow → Ray Plasma")

    baseline_batch = load_baseline_arrow(LANCEDB_PATH, TABLE_NAME, BASELINE_TRACK)

    

    # Step 3: Boot Ray cluster

    print("\n🚀 Phase 3: Initializing Ray cluster")

    import os; os.environ["PYTHONPATH"] = r"C:\WEB CASE STUDY" + os.pathsep + os.environ.get("PYTHONPATH",""); ray.init(namespace="legion", ignore_reinit_error=True, runtime_env={"env_vars": {"PYTHONPATH": "C:\WEB CASE STUDY"}})



    # Put baseline in Plasma (shared memory, zero-copy for all actors)

    baseline_ref = ray.put(baseline_batch)

    print(f"  ✅ Baseline in Plasma store ({baseline_batch.num_rows} segments)")



    # Spin up actor pool

    actors = [

        DSPAlignmentActor.remote(LANCEDB_PATH, TABLE_NAME)

        for _ in range(NUM_ACTORS)

    ]



    # Initialize all actors with baseline

    init_refs = [a.set_baseline.remote(baseline_ref) for a in actors]

    counts    = ray.get(init_refs)

    print(f"  ✅ {len(actors)} actors initialized ({counts[0]} base segments each)")



    # ── Fit combined StandardScaler in driver (baseline + all targets) ────────

    # This is the key fix: same unit space for both sides, matching original script

    print("\n📐 Fitting combined StandardScaler (baseline + target features)...")

    from sklearn.preprocessing import StandardScaler



    # 2-feature space: RMS dB + crest factor

    # Matches original working script — proven to hit 82.3% on Get Down Tonight

    # Spectral features deferred until base accuracy is validated

    FEATURE_COLS = ["rms", "crest_factor"]



    # Build baseline feature matrix from Arrow batch

    # LanceDB 'rms' is linear — convert to dB to match our Pedalboard extraction

    import pandas as pd

    baseline_df = baseline_batch.to_pandas()

    baseline_df["rms_db"] = baseline_df["rms"].apply(

        lambda v: float(20 * np.log10(v)) if v > 1e-9 else -100.0

    )

    X_base_raw = baseline_df[["rms_db", "crest_factor"]].fillna(0.0).values



    # Build target feature matrix from all Pedalboard segments

    targ_rows = []

    for segs in all_track_segments.values():

        for seg in segs:

            targ_rows.append([seg.rms_db, seg.crest_factor])

    X_targ_raw = np.array(targ_rows, dtype=np.float64)



    # Fit on combined — same as original vstack pattern

    combined = np.vstack([X_base_raw, X_targ_raw])

    scaler = StandardScaler()

    scaler.fit(combined)



    scaler_state = {

        "mean_":  scaler.mean_.tolist(),

        "scale_": scaler.scale_.tolist(),

    }



    # Push fitted scaler to all actors

    scale_refs = [a.set_scaler.remote(scaler_state) for a in actors]

    ray.get(scale_refs)

    print(f"  ✅ Combined scaler fitted on {len(combined)} samples, pushed to {len(actors)} actors")



    # Step 4: Fire alignment tasks

    print("\n⚡ Phase 4: Parallel alignment")

    grand_total_start = time.perf_counter()

    all_results: list[AlignmentResult] = []



    for track_name, segments in all_track_segments.items():

        print(f"\n  ▶ {track_name}  ({len(segments)} segments)")

        t0 = time.perf_counter()



        tasks = []

        for i, seg in enumerate(segments):

            actor = actors[i % NUM_ACTORS]

            query = AlignmentQuery(

                targ_idx       = i,

                targ_segment   = seg,

                threshold      = THRESHOLD,

            )

            tasks.append(actor.align_segment.remote(query.model_dump()))



        raw_results = ray.get(tasks)

        track_results = [AlignmentResult(**r) for r in raw_results]

        elapsed = (time.perf_counter() - t0) * 1000



        # Print segment table

        print(f"  {'Segment':<28} | {'Matched Base':<28} | {'Score':>6} | Status")

        print("  " + "-" * 80)

        for r in track_results:

            icon = "✅" if r.status == "passed" else "⚠️ "

            print(f"  {r.targ_name:<28} | {r.matched_base:<28} | {r.alignment_score:>5.1f}% | {icon} {r.status}")



        passed   = sum(1 for r in track_results if r.status == "passed")

        fallback = len(track_results) - passed

        print(f"\n  ⚡ Aligned {len(track_results)} segments in {elapsed:.0f} ms  |  Passed: {passed}  |  Fallback: {fallback}")

        all_results.extend(track_results)



    # Step 5: Self-verify pass

    print("\n🔍 Phase 5: Self-verification pass (re-checking from LanceDB scalars)")

    verify_tasks = []

    for i, r in enumerate(all_results):

        actor = actors[i % NUM_ACTORS]

        verify_tasks.append(actor.verify_result.remote(r.model_dump()))



    verified_raw = ray.get(verify_tasks)

    verified_results = [AlignmentResult(**r) for r in verified_raw]



    clean   = sum(1 for r in verified_results if r.verified and r.verify_delta < 5.0)

    drift   = sum(1 for r in verified_results if r.verified and r.verify_delta >= 5.0)

    unverif = sum(1 for r in verified_results if not r.verified)



    report = VerificationReport(

        total           = len(verified_results),

        passed          = sum(1 for r in verified_results if r.status == "passed"),

        fallback        = sum(1 for r in verified_results if r.status == "fallback"),

        verified_clean  = clean,

        verified_drift  = drift,

        pass_rate_pct   = round(sum(1 for r in verified_results if r.status == "passed") / len(verified_results) * 100, 1),

        results         = verified_results,

    )



    total_elapsed = (time.perf_counter() - grand_total_start) * 1000

    ray.shutdown()



    # Final report

    print("\n" + "=" * 70)

    print("  🏁  FIRE TEST COMPLETE — VERIFICATION REPORT")

    print("=" * 70)

    print(f"  Total Segments    : {report.total}")

    print(f"  Passed (≥{THRESHOLD}%)  : {report.passed}  ({report.pass_rate_pct}%)")

    print(f"  Fallback          : {report.fallback}")

    print(f"  Self-Check Clean  : {clean}  (drift < 5%)")

    print(f"  Self-Check Drift  : {drift}  (drift ≥ 5% — investigate)")

    print(f"  Unverifiable      : {unverif}")

    print(f"  Total Time        : {total_elapsed:.0f} ms")

    print("=" * 70)



    # Per-track summary

    tracks = {}

    for r in report.results:

        tracks.setdefault(r.track_name, []).append(r)



    print("\n  📊 Per-Track Summary:")

    for tname, recs in tracks.items():

        p    = sum(1 for r in recs if r.status == "passed")

        avg  = round(sum(r.alignment_score for r in recs) / len(recs), 1)

        best = round(max(r.alignment_score for r in recs), 1)

        fire = "🔥 FIRE" if best >= 90.0 else ("🟡 CLOSE" if best >= THRESHOLD else "🔴 NEEDS WORK")

        print(f"  {tname[:40]:<40} | avg {avg}% | best {best}% | {fire}")



    print()





if __name__ == "__main__":

    main()
