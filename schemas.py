"""
LEGION SONIC ENGINE — Centralized Schemas
=========================================
This module serves as the single source of truth for all data structures
used across the Legion Sonic Engine, including the Ray Actors, 
the Intelligence Bridge, and the Marketing Engine.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Literal, Optional, Any
from uuid import uuid4
from datetime import datetime

# --- 1. CORE SIMULATION SCHEMAS (The Agent's Reality) ---

class AgentState(BaseModel):
    """The shared state for the LangGraph Orchestrator."""
    session_id: str
    current_phase: Literal["intro", "build", "drop", "outro"]
    current_city: str
    career_stats: Dict[str, float] = Field(default_factory=lambda: {
        "reputation": 50.0,
        "fame": 10.0,
        "craft": 20.0,
        "energy": 100.0,
        "integrity": 100.0,
        "money": 500.0
    })
    active_events: List[Dict] = []
    marketing_assets: List[str] = []
    intelligence_gap: Optional[str] = None
    decision_log: List[str] = []

class WardenDecision(BaseModel):
    """The decision object produced by the 'Warden' node."""
    decision_id: str = Field(default_factory=lambda: str(uuid4()))
    # FIX: Add 'ADAPT_DSP_FAILED' to the list of allowed action types
    action_type: Literal["REINFORCE", "ADAPT_DSP", "PIVOT_MARKETING", "EXPAND_TOUR", "REBUILD", "ADAPT_DSP_FAILED"]
    reasoning: str
    parameters: Dict[str, Any]
    confidence_score: float = Field(ge=0.0, le=1.0)

# --- 2. SOCIAL & NPC SCHEMAS (The Relationship Layer) ---

RoleType = Literal["promoter", "rival_dj", "fan", "agent", "club_owner", "media"]
TraitType = Literal["shady", "loyal", "clout_chaser", "visionary", "gatekeeper", "hype_man", "indie", "mainstream"]

class NPCProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    role: RoleType
    traits: List[TraitType]
    influence: int = Field(ge=1, le=100, default=50)
    affinity: int = Field(ge=-100, le=100, default=0)
    current_mood: str = "neutral"

class SocialInteraction(BaseModel):
    actor_id: str
    target_id: str
    interaction_type: Literal["networking", "conflict", "collaboration", "fan_service", "hustle"]
    outcome_score: float
    description: str

# --- 3. MARKETING & CONTENT SCHEMAS (The Brand Layer) ---

class ContentAsset(BaseModel):
    asset_id: str = Field(default_factory=lambda: str(uuid4()))
    type: Literal["clip", "story", "reel", "post", "epk", "visual"]
    platform: str
    angle: Literal["hype", "emotional", "behind-the-scenes", "educational", "gritty"]
    caption: str
    visual_prompt: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MarketingCampaign(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    goal: Literal["awareness", "engagement", "conversion", "loyalty"]
    target_audience: str
    status: Literal["planned", "active", "completed", "failed"]
    assets: List[str] = []

# --- 4. INTELLIGENCE & COLLISION SCHEMAS (The Data Layer) ---

class MarketTrend(BaseModel):
    metric: str
    value: float
    direction: Literal["up", "down", "stable"]
    description: str

class IntelligenceReport(BaseModel):
    trends: List[MarketTrend]
    audio_baseline: Dict[str, float]
    intelligence_gap: Optional[str] = None

class TrackPhysics(BaseModel):
    filename: str
    dsp_tempo: Optional[float] = None
    dsp_key: Optional[str] = None
    rms_db: Optional[float] = None
    crest_factor: Optional[float] = None
    sub_bass_energy: Optional[float] = None
    bass_energy: Optional[float] = None
    mid_energy: Optional[float] = None
    high_energy: Optional[float] = None
    spectral_centroid: Optional[float] = None

class SovereignDelta(BaseModel):
    filename: str
    rms_delta: float
    crest_delta: float
    sovereign_score: float
    grade: str

class CollisionRecord(BaseModel):
    filename: str
    physics: TrackPhysics
    delta: SovereignDelta
    vector_score: float
    source_level: int = 3

class CollisionResult(BaseModel):
    query_concept: str
    query_bpm: Optional[float] = None
    query_key: Optional[str] = None
    level: int
    records: List[CollisionRecord]
    total_found: int
    duck_ms: float
    lance_ms: float
    merge_ms: float

class Level3Query(BaseModel):
    concept: str
    bpm: Optional[float] = None
    key: Optional[str] = None
    drum_type: Optional[str] = None
    top_k: int = 3
    bpm_tolerance: float = 3.0
