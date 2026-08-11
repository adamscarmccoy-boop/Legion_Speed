"""
SOVEREIGN SCHEMAS — Unified Pydantic Contract for Legion Pipeline
=================================================================
Every node, every LLM call, every data lane speaks this typed language.
Extracted from session_intel_pipeline.ipynb (H.O.R.N. Stack).
Wired into: legion_graph.py, autonomous_learning_engine.py, mcp_api_server.py

The Pydantic models ARE the decoder muzzle — LLMs are forced to output
these exact shapes via format=Model.model_json_schema(). No hallucination.
No freeform text. Structured intelligence only.
"""

from typing import Literal, List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, computed_field, TypeAdapter
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════════
# SOVEREIGN TARGETS (DNA Master Baseline)
# ═══════════════════════════════════════════════════════════════════════════════
SOVEREIGN_TARGET_RMS = -13.9        # LUFS
SOVEREIGN_TARGET_CREST = 5.69       # dB
SOVEREIGN_TARGET_MID_MULT = 289.34  # Mid-injection multiplier
LANCEDB_DIMENSION_LIMIT = 384       # Vector dimension ceiling


# ═══════════════════════════════════════════════════════════════════════════════
# CORE DIAGNOSTIC MODEL (THE DECODER MUZZLE)
# Used by: Ollama/Phi-3 local, Gemini API, any LLM in the pipeline
# The LLM is forced to output this exact schema — no freeform text allowed
# ═══════════════════════════════════════════════════════════════════════════════
class SovereignDAWDiagnostic(BaseModel):
    """The core output every LLM reasoning call must produce."""
    diagnosed_target: str = Field(
        ..., description="The channel track or frequency block evaluated (e.g., sub, drums, master)")
    status_flag: Literal["INFO", "WARNING", "CRITICAL"]
    anomalies_found: List[str] = Field(
        ..., description="List of concrete technical mix issues found in the data")
    assistant_remediation_monologue: str = Field(
        ..., description="Step-by-step instructions to correct the mix anomalies")


# ═══════════════════════════════════════════════════════════════════════════════
# TRUTH vs TIME — The Physics and Structure Models
# Used by: LangGraph Architect node, session analysis pipeline
# ═══════════════════════════════════════════════════════════════════════════════
class AudioTruth(BaseModel):
    """The Physical Baseline: Extracted from DuckDB/Parquet audio_features table."""
    filename: str
    rms_db: float
    crest_factor: float
    sub_bass_energy: float


class SessionTime(BaseModel):
    """The Structural Arrangement: Extracted from Ableton .als XML."""
    track_name: str
    active_plugins: List[str]
    time_sparsity_score: Optional[float] = Field(
        default=1.0, description="Arrangement density metric from TDM calculation")


# ═══════════════════════════════════════════════════════════════════════════════
# THE 3 DATA LANES — Typed routing for every data stream
# Used by: SystemMatrixConductor, MCP tools, LangGraph nodes
# ═══════════════════════════════════════════════════════════════════════════════
class Lane1DuckDBAnalytics(BaseModel):
    """Lane 1: Structured SQL query results from DuckDB/Parquet."""
    table_source: str = Field(..., description="Target Parquet table evaluated")
    processed_row_count: int
    anomalous_metric_detected: bool
    structural_monologue: str


class Lane2LanceDBVectors(BaseModel):
    """Lane 2: Vector similarity search results from LanceDB."""
    matched_vector_keys: List[int]
    maximum_semantic_distance: float
    nearest_file_nodes: List[str]


class Lane3SystemLogs(BaseModel):
    """Lane 3: System execution logs and audit trails."""
    process_id: int
    execution_severity: Literal["INFO", "WARNING", "CRITICAL"]
    root_cause_analysis: str


# ═══════════════════════════════════════════════════════════════════════════════
# LANGGRAPH STATE — Shared memory across all graph nodes
# Used by: sovereign_brain (LangGraph StateGraph), legion_graph.py
# ═══════════════════════════════════════════════════════════════════════════════
class UserIntent(BaseModel):
    """Parsed user command → typed action."""
    action_type: str
    target_session: str
    instruction: str


# Note: SovereignGraphState uses TypedDict (not BaseModel) for LangGraph compat
# Import this pattern in your graph files:
#   from sovereign_schemas import AudioTruth, SessionTime, UserIntent, SovereignDAWDiagnostic


# ═══════════════════════════════════════════════════════════════════════════════
# MARKET SCORING MODELS — Used by autonomous_learning_engine.py
# ═══════════════════════════════════════════════════════════════════════════════
class MarketScoreBreakdown(BaseModel):
    """6-factor weighted market score decomposition."""
    tempo_alignment: float = Field(..., ge=0.0, le=1.0)
    spectral_match: float = Field(..., ge=0.0, le=1.0)
    harmonic_progression: float = Field(..., ge=0.0, le=1.0)
    market_gap: float = Field(..., ge=0.0, le=1.0)
    uniqueness: float = Field(..., ge=0.0, le=1.0)
    production_quality: float = Field(..., ge=0.0, le=1.0)

    @property
    def weighted_score(self) -> float:
        return round(
            0.30 * self.tempo_alignment
            + 0.20 * self.spectral_match
            + 0.20 * self.harmonic_progression
            + 0.15 * self.market_gap
            + 0.10 * self.uniqueness
            + 0.05 * self.production_quality,
            3,
        )


class ScoredTrack(BaseModel):
    """A track with its full market score analysis."""
    filename: str
    filepath: Optional[str] = None
    tempo: Optional[float] = None
    key: Optional[str] = None
    drum_type: Optional[str] = None
    collision_score: Optional[float] = None
    market_score: float
    source: str = "unknown"
    score_breakdown: MarketScoreBreakdown
    expert_insight: Optional[str] = None


class CatalogDNAProfile(BaseModel):
    """Artist's signature sound profile extracted from catalog analysis."""
    artist_id: str
    track_count: int
    avg_tempo: float
    tempo_std_dev: float
    dominant_key: Optional[str] = None
    dominant_drum_type: Optional[str] = None
    avg_collision_score: Optional[float] = None
    dna_anchor_prompt: Optional[str] = None
    key_distribution: Optional[Dict[str, int]] = None
    vector_store_stats: Optional[Dict[str, Any]] = None


class OraclePrediction(BaseModel):
    """Top hit predictions from the learning engine."""
    cycle_number: int
    timestamp: str
    artist_id: str
    tracks_analyzed: int
    catalog_dna: CatalogDNAProfile
    top_hits: List[ScoredTrack]


class AlignedDSPTrackRecord(BaseModel):
    """Pre-inference validated track record — raw database output
    must pass through this before any LLM sees it."""
    filename: str
    tempo: Optional[float] = None
    key: Optional[str] = None
    rms_db: Optional[float] = None
    crest_factor: Optional[float] = None
    sub_bass_energy: Optional[float] = None
    spectral_centroid: Optional[float] = None
    collision_score: Optional[float] = None
    drum_type: Optional[str] = None
    source: str = "unknown"


# ═══════════════════════════════════════════════════════════════════════════════
# LIVE TRACK DELTA — Computed Fields (model IS the engine)
# The delta, severity, and FX recommendation calculate themselves.
# ═══════════════════════════════════════════════════════════════════════════════
class LiveTrackDelta(BaseModel):
    """Track with auto-computed deltas against Sovereign Targets.
    No separate delta engine needed — the model IS the engine."""
    filename: str
    rms_db: Optional[float] = None
    crest_factor: Optional[float] = None
    sub_bass_energy: Optional[float] = None
    spectral_centroid: Optional[float] = None
    tempo: Optional[float] = None
    key: Optional[str] = None
    drum_type: Optional[str] = None

    @computed_field
    @property
    def rms_delta(self) -> Optional[float]:
        if self.rms_db is None:
            return None
        return round(self.rms_db - SOVEREIGN_TARGET_RMS, 3)

    @computed_field
    @property
    def crest_delta(self) -> Optional[float]:
        if self.crest_factor is None:
            return None
        return round(self.crest_factor - SOVEREIGN_TARGET_CREST, 3)

    @computed_field
    @property
    def severity(self) -> str:
        rms_d = abs(self.rms_delta) if self.rms_delta is not None else 0
        crest_d = abs(self.crest_delta) if self.crest_delta is not None else 0
        if rms_d > 4 or crest_d > 4:
            return "CRITICAL"
        if rms_d > 2 or crest_d > 2:
            return "WARNING"
        return "INFO"

    @computed_field
    @property
    def fx_recommendation(self) -> str:
        parts = []
        if self.rms_delta is not None:
            if self.rms_delta < -3:
                parts.append(f"Boost gain by {abs(self.rms_delta):.1f} dB (limiter input)")
            elif self.rms_delta > 2:
                parts.append(f"Reduce gain by {self.rms_delta:.1f} dB")
        if self.crest_delta is not None:
            if self.crest_delta > 3:
                parts.append(f"Compress: ratio 2:1, threshold -20 dB (crest {self.crest_delta:+.1f})")
            elif self.crest_delta < -2:
                parts.append(f"Release compression (over-compressed by {abs(self.crest_delta):.1f} dB)")
        return " | ".join(parts) if parts else "On target — no FX changes needed"


# ═══════════════════════════════════════════════════════════════════════════════
# MARKET BENCHMARK — ListenBrainz context
# ═══════════════════════════════════════════════════════════════════════════════
class MarketBenchmark(BaseModel):
    """Aggregated market data from ListenBrainz."""
    artist_count: int
    track_count: int
    avg_listen_count: float
    avg_user_count: float
    top_artist: str


# ═══════════════════════════════════════════════════════════════════════════════
# DISCRIMINATED UNION — Auto-route any analysis result by type
# ═══════════════════════════════════════════════════════════════════════════════
class DiagnosticResult(BaseModel):
    result_type: Literal["daw_diagnostic"] = "daw_diagnostic"
    data: SovereignDAWDiagnostic

class MarketResult(BaseModel):
    result_type: Literal["market_score"] = "market_score"
    data: MarketScoreBreakdown

class DNAResult(BaseModel):
    result_type: Literal["catalog_dna"] = "catalog_dna"
    data: CatalogDNAProfile

class AnalysisRouter(BaseModel):
    """Accepts any analysis result — Pydantic auto-routes by discriminator."""
    result: Union[DiagnosticResult, MarketResult, DNAResult] = Field(discriminator="result_type")


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION DNA — The full intelligence tree in one object
# ═══════════════════════════════════════════════════════════════════════════════
class SessionDNA(BaseModel):
    """Complete intelligence state for one analysis run.
    Carries everything: tracks, deltas, DNA, market context, severity."""
    session_name: str
    timestamp: str
    tracks: List[LiveTrackDelta]
    catalog_dna: CatalogDNAProfile
    market_context: MarketBenchmark
    aggregate_severity: Dict[str, int]
    top_critical: List[LiveTrackDelta]

    @computed_field
    @property
    def health_score(self) -> float:
        """0-100. 100 = every track on target."""
        total = len(self.tracks)
        if total == 0:
            return 0.0
        info = sum(1 for t in self.tracks if t.severity == "INFO")
        warn = sum(1 for t in self.tracks if t.severity == "WARNING")
        return round((info * 1.0 + warn * 0.5) / total * 100, 1)

    @computed_field
    @property
    def mastering_verdict(self) -> str:
        """Plain-English verdict on catalog health."""
        score = self.health_score
        if score >= 80:
            return "Catalog is release-ready. Minor tweaks on outliers only."
        elif score >= 60:
            return "Catalog is in good shape. Address warnings for polish."
        elif score >= 40:
            return "Catalog needs work. Significant gain staging and compression issues."
        elif score >= 20:
            return "Catalog requires serious mastering attention across most tracks."
        else:
            return "Catalog is far from target. Full remaster recommended."


# ═══════════════════════════════════════════════════════════════════════════════
# TYPE ADAPTERS — Batch validation at wire speed
# ═══════════════════════════════════════════════════════════════════════════════
AlignedDSPTrackAdapter = TypeAdapter(List[AlignedDSPTrackRecord])
LiveTrackDeltaAdapter = TypeAdapter(List[LiveTrackDelta])


# ═══════════════════════════════════════════════════════════════════════════════
# DUAL-AGENT CONFIG (from notebook Cell 0)
# ═══════════════════════════════════════════════════════════════════════════════
ARCHITECT_CONFIG = {
    "model": "phi3",
    "temperature": 0.0,
    "top_k": 1,
    "role": "SYSTEM_ORCHESTRATOR",
}

PHI_ASSISTANT_CONFIG = {
    "model": "phi3",
    "temperature": 0.7,
    "top_k": 40,
    "role": "USER_INTERFACE_AGENT",
}


# ═══════════════════════════════════════════════════════════════════════════════
# FILE MANIFEST — The 15+ JSON tracking files (from notebook Cell 2)
# Maps logical names to filenames in exported_json/
# ═══════════════════════════════════════════════════════════════════════════════
HORN_FILE_MANIFEST = {
    "library_analysis": "verified_library_analysis.json",
    "enriched_audio": "enriched_audio_dataset.json",
    "enriched_samples": "enriched_samples_only.json",
    "enriched_tracks": "enriched_tracks_only.json",
    "collision_results": "collision_results_final.json",
    "core_memory": "t_core_memory.json",
    "manifest_vectors": "audio_manifest_vectors.json",
    "vibe_gpu": "audio_vibe_gpu.json",
    "metadata_vectors": "duckdb_metadata_vectors.json",
    "interaction_logs": "interaction_logs.json",
    "legion_memory": "legion_memory.json",
    "fused_metadata": "rchgen_metadata_fused.json",
    "skill_brain": "skill_brain.json",
    "db_audio_features": "duckdb_audio_features.json",
    "db_core_memory": "duckdb_t_core_memory.json",
    "db_tool_index": "duckdb_tool_index.json",
    "db_analysis_logs": "duckdb_agent_analysis_logs.json",
    "lance_vibe_gpu": "lancedb_audio_vibe_gpu.json",
    "lance_legion_memory": "lancedb_legion_memory.json",
}


# ═══════════════════════════════════════════════════════════════════════════════
# PATH REGISTRY — Every data source in the pipeline
# ═══════════════════════════════════════════════════════════════════════════════
import os

_BASE = os.path.dirname(os.path.abspath(__file__))

PATH_REGISTRY = {
    # Parquet exports (8 files + ListenBrainz market data)
    "parquet_dir": os.path.join(_BASE, "AI_Logs", "parquet_exports"),
    "collision_results_parquet": os.path.join(_BASE, "AI_Logs", "parquet_exports", "collision_results_final.parquet"),
    "t_core_memory_parquet": os.path.join(_BASE, "AI_Logs", "parquet_exports", "t_core_memory.parquet"),
    "audio_manifest_vectors_parquet": os.path.join(_BASE, "AI_Logs", "parquet_exports", "audio_manifest_vectors.parquet"),
    "audio_vibe_gpu_parquet": os.path.join(_BASE, "AI_Logs", "parquet_exports", "audio_vibe_gpu.parquet"),
    "duckdb_metadata_vectors_parquet": os.path.join(_BASE, "AI_Logs", "parquet_exports", "duckdb_metadata_vectors.parquet"),
    "skill_brain_parquet": os.path.join(_BASE, "AI_Logs", "parquet_exports", "skill_brain.parquet"),
    "legion_memory_parquet": os.path.join(_BASE, "AI_Logs", "parquet_exports", "legion_memory.parquet"),
    "interaction_logs_parquet": os.path.join(_BASE, "AI_Logs", "parquet_exports", "interaction_logs.parquet"),
    "listenbrainz_market_parquet": os.path.join(_BASE, "AI_Logs", "parquet_exports", "listenbrainz_market_data.parquet"),

    # DuckDB databases
    "sonic_core_v1": os.path.join(_BASE, "data", "metadata", "sonic_core.duckdb"),
    "sonic_core_v2": os.path.join(_BASE, "AI_Logs", "sonic_core_v2.duckdb"),

    # LanceDB vector stores
    "lancedb_v1": os.path.join(_BASE, "vectors", "lancedb_store"),
    "lancedb_v2": os.path.join(_BASE, "AI_Logs", "lancedb_store"),

    # JSON sources
    "target_vector": os.path.join(_BASE, "AI_Logs", "target_vector.json"),
    "collision_results_json": os.path.join(_BASE, "AI_Logs", "collision_results_final.json"),
    "sovereign_audit_v1": os.path.join(_BASE, "AI_Logs", "sovereign_audit_v1.json"),
    "sovereign_audit_v2": os.path.join(_BASE, "AI_Logs", "sovereign_audit_v2.json"),
    "listenbrainz_market_json": os.path.join(_BASE, "AI_Logs", "listenbrainz_market_data.json"),

    # Engine outputs
    "audit_log": os.path.join(_BASE, "AI_Logs", "engine_audit_log.json"),
    "oracle_reports_dir": os.path.join(_BASE, "oracle_reports"),

    # Ableton session intelligence
    "ableton_intel_dir": os.path.join(_BASE, "ableton-session-intelligence"),
    "exported_json_dir": os.path.join(_BASE, "ableton-session-intelligence", "exported_json"),
    "raw_sessions_dir": os.path.join(_BASE, "ableton-session-intelligence", "raw_sessions"),
}
