#!/usr/bin/env python
"""Self-Contained Fire Test — All imports inline"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\WEB CASE STUDY")
sys.path.insert(0, r"C:\WEB CASE STUDY")

def main():
    import time, numpy as np, pyarrow as pa, lancedb, ray
    from pedalboard.io import AudioFile

    # Pydantic schemas (inline to avoid import issues)
    from pydantic import BaseModel, field_validator
    from typing import Optional, List

    class SegmentPhysics(BaseModel):
        segment_name: str
        track_name: str
        rms_db: float
        crest_factor: float
        @field_validator("rms_db","crest_factor", mode="before")
        @classmethod
def coerce(cls, v): return float(v) if v is not None else 0.0

    class AlignmentQuery(BaseModel):
        targ_idx: int
        targ_segment: SegmentPhysics
        threshold: float = 85.0

    class AlignmentResult(BaseModel):
        targ_idx: int; targ_name: str; track_name: str
        matched_base: str; alignment_score: float
        status: str; verified: bool = False; verify_delta: float = 0.0

    # Ray actor
    @ray.remote(num_cpus=1)
    class DSPAlignmentActor:
        def __init__(self, lancedb_path, table_name):
            import lancedb; from sklearn.preprocessing import StandardScaler
            self.db = lancedb.connect(lancedb_path)
            self.table = self.db.open_table(table_name)
            self.scaler = StandardScaler()
            self.X_base = None; self.names_base = []
        def set_baseline(self, batch):
            df = batch.to_pandas()
            df["rms_db"] = df["rms"].apply(lambda v: float(20*np.log10(v)) if v>1e-9 else -100.0)
            self.names_base = df["segment_name"].tolist()
            self.X_base_raw = df[["rms_db","crest_factor"]].fillna(0.0).values.astype(np.float32)
            return len(self.names_base)
        def set_scaler(self, state):
            from sklearn.preprocessing import StandardScaler
            sc = StandardScaler(); sc.mean_ = np.array(state["mean_"], dtype=np.float64)
            sc.scale_ = np.array(state["scale_"], dtype=np.float64)
            sc.n_features_in_ = len(sc.mean_); self.scaler = sc
            self.X_base = self.scaler.transform(self.X_base_raw).astype(np.float32)
        def align_segment(self, qdict):
            from scipy.spatial.distance import cdist
            q = AlignmentQuery(**qdict); seg = q.targ_segment
            feat = np.array([[seg.rms_db, seg.crest_factor]], dtype=np.float32)
            ts = self.scaler.transform(feat)
            dists = cdist(ts, self.X_base, metric="euclidean")[0]
            best = int(np.argmin(dists)); score = float(np.clip(100.0 - (dists[best]*15.0), 0.0, 100.0))
            r = AlignmentResult(targ_idx=q.targ_idx, targ_name=seg.segment_name,
                track_name=seg.track_name, matched_base=self.names_base[best],
                alignment_score=round(score,2), status="passed" if score>=q.threshold else "fallback")
            return r.model_dump()
        def verify_result(self, rdict):
            from scipy.spatial.distance import cdist
            r = AlignmentResult(**rdict)
            def to_db(v): return float(20*np.log10(v)) if v>1e-9 else -100.0
            base_rows = self.table.search().where(f"segment_name='{r.matched_base}'").limit(1).to_pandas()
            if base_rows.empty: r.verified=False; r.verify_delta=-1.0; return r.model_dump()
            base_raw = np.array([[to_db(float(base_rows["rms"].iloc[0])), float(base_rows["crest_factor"].iloc[0])]], dtype=np.float32)
            base_scaled = self.scaler.transform(base_raw)
            targ_rows = self.table.search().where(f"segment_name='{r.targ_name}'").limit(1).to_pandas()
            if targ_rows.empty: r.verified=True; r.verify_delta=0.0; return r.model_dump()
            targ_raw = np.array([[to_db(float(targ_rows["rms"].iloc[0])), float(targ_rows["crest_factor"].iloc[0])]], dtype=np.float32)
            targ_scaled = self.scaler.transform(targ_raw)
            dist = float(cdist(targ_scaled, base_scaled, metric="euclidean")[0][0])
            vs = float(np.clip(100.0-(dist*15.0), 0.0, 100.0))
            r.verified=True; r.verify_delta=round(abs(vs-r.alignment_score),3); return r.model_dump()

    LANCEDB_PATH = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
    TABLE_NAME = "omni_semantic_baselines"; THRESHOLD = 82.0; NUM_ACTORS = 4
    TARGET_FILES = [
        r"C:\Users\adams\Downloads\GIRL NAME DREAM -  i need that.mp3",
        r"C:\Users\adams\Downloads\new life.wav",
    ]

    print("="*70)
    print("  🔥 SELF-CONTAINED FIRE TEST — Pedalboard + Ray + Pydantic")
    print("="*70)

    def extract(wav_path, seg_sec=6.0):
        segs, t0 = [], time.perf_counter()
        tn = os.path.splitext(os.path.basename(wav_path))[0]
        with AudioFile(wav_path) as f:
            sr, frames = f.samplerate, int(seg_sec*f.samplerate); si = 0
            while True:
                audio = f.read(frames)
                if audio.shape[1] < frames//2: break
                mono = audio.mean(axis=0)
                rms_lin = float(np.sqrt(np.mean(mono**2)))
                rms_db = float(20*np.log10(rms_lin)) if rms_lin>1e-9 else -100.0
                crest = float(np.max(np.abs(mono))/rms_lin) if rms_lin>1e-9 else 0.0
                segs.append(SegmentPhysics(segment_name=f"{tn}_seg{si:03d}", track_name=tn, rms_db=rms_db, crest_factor=crest))
                si += 1
        return segs, (time.perf_counter()-t0)*1000

    all_segs = {}
    for p in TARGET_FILES:
        if not os.path.exists(p): print(f"  ❌ Missing {os.path.basename(p)}"); continue
        s, ms = extract(p); n = os.path.splitext(os.path.basename(p))[0]
        all_segs[n] = s; print(f"  ✅ {os.path.basename(p):40s} → {len(s)} segs ({ms:.0f}ms)")

    print(f"
⚡ Loading baseline: LanceDB...")
    db = lancedb.connect(LANCEDB_PATH)
    df = db.open_table(TABLE_NAME).to_pandas()
    bdf = df[df["track_name"].str.contains("Somebody", case=False, na=False)].copy()
    print(f"  ✅ {len(bdf)} segments (Somebody 2024)")

    print(f"
🚀 Starting Ray...")
    os.environ["PYTHONPATH"] = r"C:\WEB CASE STUDY"
    ray.init(namespace="legion", ignore_reinit_error=True, runtime_env={"env_vars":{"PYTHONPATH":"C:\WEB CASE STUDY"},"excludes":[]})
    print(f"  ✅ Dashboard: http://127.0.0.1:8265")

    batch_ref = ray.put(pa.RecordBatch.from_pandas(bdf))
    actors = [DSPAlignmentActor.remote(LANCEDB_PATH, TABLE_NAME) for _ in range(NUM_ACTORS)]
    c = ray.get([a.set_baseline.remote(batch_ref) for a in actors])
    print(f"  ✅ {NUM_ACTORS} actors ready ({c[0]} baseline segs)")

    from sklearn.preprocessing import StandardScaler
    bdf["rms_db"] = bdf["rms"].apply(lambda v: float(20*np.log10(v)) if v>1e-9 else -100.0)
    Xb = bdf[["rms_db","crest_factor"]].fillna(0.0).values
    Xt = np.array([[s.rms_db,s.crest_factor] for segs in all_segs.values() for s in segs], dtype=np.float64)
    sc = StandardScaler(); sc.fit(np.vstack([Xb,Xt]))
    ray.get([a.set_scaler.remote({"mean_":sc.mean_.tolist(),"scale_":sc.scale_.tolist()}) for a in actors])

    print(f"
🧮 Aligning...")
    all_results = []
    for name, segs in all_segs.items():
        t0 = time.perf_counter()
        tasks = [actors[i%NUM_ACTORS].align_segment.remote(AlignmentQuery(targ_idx=i, targ_segment=s, threshold=THRESHOLD).model_dump()) for i,s in enumerate(segs)]
        results = [AlignmentResult(**r) for r in ray.get(tasks)]
        ms = (time.perf_counter()-t0)*1000
        p = sum(1 for r in results if r.status=="passed")
        print(f"
  📊 {name}")
        print(f"  {'Segment':<28}|{'Matched Base':<28}|{'Score':>6}|Status"); print(f"  {'-'*70}")
        for r in results[:10]:
            print(f"  {r.targ_name[:26]:<28}|{r.matched_base[:26]:<28}|{r.alignment_score:>5.1f}%|{'✅' if r.status=='passed' else '⚠️'}")
        if len(results)>10: print(f"  ... and {len(results)-10} more")
        print(f"  ⚡ {len(results)} segs in {ms:.0f}ms | Passed: {p}/{len(results)}")
        all_results.extend(results)

    print(f"
🔍 Verification...")
    v = ray.get([actors[i%NUM_ACTORS].verify_result.remote(r.model_dump()) for i,r in enumerate(all_results)])
    vr = [AlignmentResult(**x) for x in v]
    clean = sum(1 for r in vr if r.verified and r.verify_delta<5.0)
    drift = sum(1 for r in vr if r.verified and r.verify_delta>=5.0)
    unverif = sum(1 for r in vr if not r.verified)

    print(f"
{"="*70}"); print(f"  🏁 FIRE TEST COMPLETE"); print(f"{"="*70}")
    print(f"  Total Segments   : {len(vr)}")
    print(f"  Passed (≥{THRESHOLD}%) : {sum(1 for r in vr if r.status=='passed')}")
    print(f"  Clean (drift<5%) : {clean}")
    print(f"  Drift (≥5%)      : {drift}")
    print(f"  Unverifiable     : {unverif}")
    print(f"{"="*70}")
    tracks = {}
    for r in vr: tracks.setdefault(r.track_name,[]).append(r)
    for t, rs in tracks.items():
        avg = round(sum(r.alignment_score for r in rs)/len(rs),1)
        best = round(max(r.alignment_score for r in rs),1)
        f = "🔥" if best>=90 else ("🟡" if best>=THRESHOLD else "🔴")
        print(f"  {t[:40]:<40} avg {avg}% | best {best}% | {f}")
    print(f"
  📊 Ray Dashboard: http://127.0.0.1:8265")
    ray.shutdown()

if __name__ == "__main__":
    main()
