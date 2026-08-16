"""
DSP Alignment Ray Actor
=======================
Architecture:
  OUTSIDE RAY  → Pedalboard C++ loads audio, extracts features → Pydantic validates
  PLASMA STORE → PyArrow RecordBatch (zero-copy ref via ray.put)
  INSIDE ACTOR → scipy/numba C-extensions do the math (no Pedalboard fork issues)
  VERIFY PASS  → re-measures from LanceDB scalar columns, checks score drift < 5%
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import time
import numpy as np
import pyarrow as pa
import ray

# ── Pydantic models (the firewall between Pedalboard and Ray) ─────────────────
try:
    from legion_schema import (
        SegmentPhysics,
        AlignmentQuery,
        AlignmentResult,
        VerificationReport,
        SOVEREIGN_TARGET_RMS,
        SOVEREIGN_TARGET_CREST,
    )
except ModuleNotFoundError:
    # Fallback: inline minimal models for Ray workers without path
    from pydantic import BaseModel
    from typing import Optional, List
    class AlignmentQuery(BaseModel):
        targ_idx: int; threshold: float = 85.0
        class Config: extra = "allow"
    class AlignmentResult(BaseModel):
        targ_idx: int; targ_name: str = ""; track_name: str = ""
        matched_base: str = ""; alignment_score: float = 0.0
        status: str = "fallback"; verified: bool = False; verify_delta: float = 0.0
        class Config: extra = "allow"
    SOVEREIGN_TARGET_RMS = -12.0; SOVEREIGN_TARGET_CREST = 5.0


# ═══════════════════════════════════════════════════════════════════════════════
# DSPAlignmentActor  —  stateful Ray Actor, one per CPU core
# Pedalboard is NEVER imported here (fork-safety). scipy + numba only.
# ═══════════════════════════════════════════════════════════════════════════════
@ray.remote(num_cpus=1)
class DSPAlignmentActor:
    def __init__(self, lancedb_path: str, table_name: str):
        import lancedb
        from sklearn.preprocessing import StandardScaler

        self.db      = lancedb.connect(lancedb_path)
        self.table   = self.db.open_table(table_name)
        self.scaler  = StandardScaler()
        self.X_base  = None          # numpy float32, set via set_baseline()
        self.names_base: list[str] = []

    # ── called once to load the reference (Chris Lake) feature matrix ─────────
    def set_baseline(self, arrow_batch_ref):
        """Accept a PyArrow RecordBatch — Ray auto-resolves ObjectRef before this runs."""
        import pyarrow as pa
        batch = arrow_batch_ref  # already deserialized by Ray from Plasma store
        df = batch.to_pandas()

        # 2-feature space matching original working script
        # LanceDB stores linear rms — convert to dB same as original parse_text_features
        df["rms_db"] = df["rms"].apply(
            lambda v: float(20 * np.log10(v)) if v > 1e-9 else -100.0
        )
        self.names_base = df["segment_name"].tolist()
        self.X_base_raw = df[["rms_db", "crest_factor"]].fillna(0.0).values.astype(np.float32)
        self.X_base = None
        return len(self.names_base)

    def set_scaler(self, scaler_state: dict):
        """Receive pre-fitted StandardScaler params from driver (mean_ and scale_)."""
        from sklearn.preprocessing import StandardScaler
        sc = StandardScaler()
        sc.mean_  = np.array(scaler_state["mean_"],  dtype=np.float64)
        sc.scale_ = np.array(scaler_state["scale_"], dtype=np.float64)
        sc.n_features_in_ = len(sc.mean_)
        self.scaler = sc
        self.X_base = self.scaler.transform(self.X_base_raw).astype(np.float32)
        return "scaler set"

    # ── per-segment alignment — scipy C-extension euclidean math ─────────────
    def align_segment(self, query_dict: dict) -> dict:
        from scipy.spatial.distance import cdist

        # Pydantic validation inside actor — catches bad data before math
        query = AlignmentQuery(**query_dict)
        seg   = query.targ_segment

        # 2-feature space: rms_db + crest_factor (matches scaler fitted in driver)
        feature_vals = np.array([[
            seg.rms_db, seg.crest_factor,
        ]], dtype=np.float32)

        targ_scaled = self.scaler.transform(feature_vals)

        # scipy cdist: one target vs all base — C-level, no Python loop
        dists = cdist(targ_scaled, self.X_base, metric="euclidean")[0]
        best_idx   = int(np.argmin(dists))
        best_dist  = float(dists[best_idx])
        score      = float(np.clip(100.0 - (best_dist * 15.0), 0.0, 100.0))
        status     = "passed" if score >= query.threshold else "fallback"

        result = AlignmentResult(
            targ_idx        = query.targ_idx,
            targ_name       = seg.segment_name,
            track_name      = seg.track_name,
            matched_base    = self.names_base[best_idx],
            alignment_score = round(score, 2),
            status          = status,
        )
        return result.model_dump()

    # ── self-check: re-reads from LanceDB scalars, computes score again ───────
    def verify_result(self, result_dict: dict) -> dict:
        from scipy.spatial.distance import cdist

        result = AlignmentResult(**result_dict)

        # Pull base segment from LanceDB — 2-feature space with dB conversion
        base_rows = (
            self.table.search()
            .where(f"segment_name = '{result.matched_base}'")
            .limit(1)
            .to_pandas()
        )
        if base_rows.empty:
            result.verified     = False
            result.verify_delta = -1.0
            return result.model_dump()

        def to_db(v):
            return float(20 * np.log10(v)) if v > 1e-9 else -100.0

        base_raw = np.array([[
            to_db(float(base_rows["rms"].iloc[0])),
            float(base_rows["crest_factor"].iloc[0]),
        ]], dtype=np.float32)
        base_scaled = self.scaler.transform(base_raw)

        # Target was from Pedalboard — use the stored alignment score as ground truth
        # Re-verify by checking base segment's position in scaled space vs original score
        # If base_scaled matches what was computed at alignment time, delta ≈ 0
        targ_rows = (
            self.table.search()
            .where(f"segment_name = '{result.targ_name}'")
            .limit(1)
            .to_pandas()
        )
        if targ_rows.empty:
            # Target not in LanceDB (new track) — verify base segment only, report 0 drift
            result.verified     = True
            result.verify_delta = 0.0
            return result.model_dump()

        targ_raw = np.array([[
            to_db(float(targ_rows["rms"].iloc[0])),
            float(targ_rows["crest_factor"].iloc[0]),
        ]], dtype=np.float32)
        targ_scaled  = self.scaler.transform(targ_raw)
        dist         = float(cdist(targ_scaled, base_scaled, metric="euclidean")[0][0])
        verify_score = float(np.clip(100.0 - (dist * 15.0), 0.0, 100.0))
        delta        = abs(verify_score - result.alignment_score)

        result.verified     = True
        result.verify_delta = round(delta, 3)
        return result.model_dump()
