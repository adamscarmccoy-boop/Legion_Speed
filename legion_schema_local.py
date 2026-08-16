from pydantic import BaseModel, field_validator
from typing import Optional, List

SOVEREIGN_TARGET_RMS = -12.0
SOVEREIGN_TARGET_CREST = 5.0

class Level3Query(BaseModel):
    bpm: int
    key: str
    top_k: int
    bpm_tolerance: int
    concept: str

class TrackPhysics(BaseModel):
    filename: str
    dsp_tempo: Optional[float] = None
    dsp_key: Optional[str] = None
    rms_db: Optional[float] = None
    crest_factor: Optional[float] = None
    sub_bass_energy: Optional[float] = None

class SovereignDelta(BaseModel):
    filename: str
    rms_delta: float
    crest_delta: float
    sovereign_score: float = 0.0
    grade: Optional[str] = None

    @staticmethod
    def compute_grade(score: float) -> str:
        if score >= 90.0:
            return "A"
        elif score >= 80.0:
            return "B"
        elif score >= 70.0:
            return "C"
        else:
            return "D"

class CollisionRecord(BaseModel):
    filename: str
    physics: TrackPhysics
    delta: SovereignDelta
    vector_score: Optional[float] = None
    source_level: int = 3

class CollisionResult(BaseModel):
    query_concept: str
    query_bpm: int
    query_key: str
    level: int = 3
    records: List[CollisionRecord]
    total_found: int
    duck_ms: float
    lance_ms: float
    merge_ms: float


# ── DSP Alignment Actor Schema ────────────────────────────────────────────────

class SegmentPhysics(BaseModel):
    """Pre-computed DSP features for a single audio segment (computed OUTSIDE Ray)."""
    segment_name: str
    track_name: str
    rms_db: float
    crest_factor: float
    sub_bass_energy: float = 0.0
    bass_energy: float = 0.0
    mid_energy: float = 0.0
    high_energy: float = 0.0
    spectral_centroid: float = 0.0
    spectral_bandwidth: float = 0.0
    spectral_rolloff: float = 0.0
    spectral_flatness: float = 0.0
    zero_crossing_rate: float = 0.0

    @field_validator('rms_db', 'crest_factor', mode='before')
    @classmethod
    def coerce_float(cls, v):
        return float(v) if v is not None else 0.0


class AlignmentQuery(BaseModel):
    """Input contract for DSPAlignmentActor.align_segment() — validated before crossing Ray boundary."""
    targ_idx: int
    targ_segment: SegmentPhysics
    threshold: float = 85.0


class AlignmentResult(BaseModel):
    """Output from DSPAlignmentActor.align_segment()."""
    targ_idx: int
    targ_name: str
    track_name: str
    matched_base: str
    alignment_score: float
    status: str  # 'passed' | 'fallback'
    verified: bool = False
    verify_delta: float = 0.0  # score drift in self-check


class VerificationReport(BaseModel):
    """Self-check report emitted after alignment verify pass."""
    total: int
    passed: int
    fallback: int
    verified_clean: int   # verified with delta < 5%
    verified_drift: int   # verified but delta >= 5%
    pass_rate_pct: float
    results: list[AlignmentResult]
