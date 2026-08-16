"""
LEGION SONIC ENGINE — The Autonomous EDM Career & Marketing Organism
====================================================================
This module defines the high-level orchestration, social, and marketing 
layers of the Legion Sonic Engine. It is designed to act as the 
"Warden/Orchestrator" within a LangGraph-powered agentic workflow.

INTEGRATION:
- Connects to the Ray-Arrow Swarm for high-speed data ingestion.
- Interfaces with LanceDB for persistent "Audio DNA" and "Career History".
- Uses Pydantic (PHI Layer) for deterministic decision-making.
- Orchestrates the 'Band of Five' agent personas.
"""

import os
import sys
import json
import random
import time
from datetime import datetime
from typing import List, Dict, Literal, Optional, Any
from uuid import uuid4
from pydantic import BaseModel, Field

# --- 1. CORE STATE & SCHEMAS (The DNA) ---

# The shared state for the LangGraph Orchestrator
class AgentState(BaseModel):
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
    intelligence_gap: Optional[str] = None  # e.g., "Market trending towards Melodic Techno"
    decision_log: List[str] = []

# The decision object produced by the 'Warden' node
class WardenDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid4()))
    action_type: Literal["REINFORCE", "ADAPT_DSP", "PIVOT_MARKETING", "EXPAND_TOUR", "REBUILD"]
    reasoning: str
    parameters: Dict[str, Any]
    confidence_score: float = Field(ge=0.0, le=1.0)

# --- 2. THE SOCIAL ENGINE (The Relationship Layer) ---

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

class SocialEngine:
    def __init__(self):
        self.npcs: Dict[str, NPCProfile] = {}

    def add_npc(self, profile: NPCProfile):
        self.npcs[profile.id] = profile

    def resolve_interaction(self, actor_id: str, target_id: str, interaction: str) -> Dict:
        """
        Simulates a social encounter.
        Returns a summary of the affinity shift and narrative impact.
        """
        target = self.npcs.get(target_id)
        if not target: return {"error": "NPC not found"}
        
        # Simplified logic: In production, this is a weighted probabilistic model
        shift = random.uniform(-10, 10)
        if "gatekeeper" in target.traits and interaction == "hustle":
            shift = -20
        
        target.affinity = max(-100, min(100, target.affinity + shift))
        return {
            "target_name": target.name,
            "affinity_shift": shift,
            "new_affinity": target.affinity,
            "description": f"Interaction type '{interaction}' resulted in a {shift:.1f} affinity shift."
        }

# --- 3. THE MARKETING ENGINE (The Content Layer) ---

class ContentAsset(BaseModel):
    asset_id: str = Field(default_factory=lambda: str(uuid4()))
    type: Literal["clip", "story", "reel", "post", "epk", "visual"]
    platform: str
    angle: Literal["hype", "emotional", "behind-the-scenes", "educational", "gritty"]
    caption: str
    visual_prompt: str

class MarketingEngine:
    def __init__(self):
        self.asset_library: List[ContentAsset] = []

    def generate_from_event(self, event_desc: str, mood: str) -> ContentAsset:
        """
        The 'Generative' part of the marketing loop. 
        In production, this calls a high-fidelity LLM (The Composer/Sound Engineer).
        """
        return ContentAsset(
            type="reel" if "gig" in event_desc.lower() else "post",
            platform="instagram",
            angle="hype" if "success" in event_desc.lower() else "behind-the-scenes",
            caption=f"Moment captured: {event_desc}. #ADAMSCARMCCOY #MusicLife",
            visual_prompt=f"Cinematic footage of {event_desc} with {mood} color grading."
        )

# --- 4. THE WARDEN (The LangGraph Orchestrator) ---

class LegionWarden:
    """
    The Warden is the high-level supervisory actor.
    It operates as a LangGraph node that manages the state of the entire system
    using the MCP RAG engine for vector space & swarm intelligence context.
    """
    def __init__(self, social_engine: SocialEngine, marketing_engine: MarketingEngine):
        self.social = social_engine
        self.marketing = marketing_engine

    def run_decision_loop(self, state: AgentState) -> WardenDecision:
        """
        The core decision-making function. 
        Analyzes Intelligence Gap via MCP RAG -> Detects Anomaly -> Decides Action.
        """
        gap = state.intelligence_gap or ""
        
        # 1. MCP RAG Vector Context Integration
        rag_context = ""
        try:
            from mcp_rag_server import semantic_code_search
            if gap.strip():
                rag_context = semantic_code_search(gap, limit=2)
        except Exception as e:
            rag_context = f"RAG notice: {e}"

        has_rag_match = "Source File" in rag_context or "Symbol" in rag_context

        # 2. Deterministic & Vector RAG Decision Routing (PHI Layer)
        if gap and (has_rag_match or "trending" in gap.lower() or "techno" in gap.lower() or "adapt" in gap.lower()):
            confidence = 0.94 if has_rag_match else 0.85
            return WardenDecision(
                action_type="ADAPT_DSP",
                reasoning=f"MCP RAG Vector Engine matched intelligence gap '{gap}'. Adapting parameters.",
                parameters={
                    "intelligence_gap": gap,
                    "mcp_rag_matched": has_rag_match,
                    "target_genre": "Melodic Techno",
                    "target_bpm": 126.0,
                    "rag_context_snippet": rag_context[:200] + "..." if len(rag_context) > 200 else rag_context
                },
                confidence_score=confidence
            )
        
        elif state.career_stats.get("energy", 100.0) < 20:
            return WardenDecision(
                action_type="REBUILD",
                reasoning="Energy levels critical. Initiating burnout recovery protocol.",
                parameters={"focus": "rest_and_creative_reset"},
                confidence_score=0.95
            )

        # Default: Reinforce current path
        return WardenDecision(
            action_type="REINFORCE",
            reasoning="System operating within nominal parameters. Maintaining current trajectory.",
            parameters={"mcp_rag_active": True},
            confidence_score=0.99
        )

# --- 5. MAIN ENTRY POINT (The Simulator Runner) ---

def main():
    print("=== Legion Sonic Engine: Startup Sequence ===")
    
    # Initialize Components
    social = SocialEngine()
    marketing = MarketingEngine()
    warden = LegionWarden(social, marketing)
    
    # Create a New Session (The Sim Start)
    state = AgentState(
        session_id=str(uuid4()),
        current_phase="intro",
        current_city="Charlotte",
        intelligence_gap="Market is shifting toward deeper, darker techno textures."
    )
    
    print(f"Session Started: {state.session_id} in {state.current_city}")
    print(f"Initial Stats: {state.career_stats}")

    # Run a Turn
    print("\n--- Running Simulation Turn ---")
    decision = warden.run_decision_loop(state)
    
    print(f"Decision: {decision.action_type}")
    print(f"Reasoning: {decision.reasoning}")
    print(f"Confidence: {decision.confidence_score}")

    # Execute Action (If Marketing)
    if decision.action_type == "ADAPT_DSP":
        asset = marketing.generate_from_event("Adapting production to match new techno trends", "dark")
        state.marketing_assets.append(asset.asset_id)
        print(f"Action Executed: Generated new marketing asset: {asset.caption}")

    print("\n=== Turn Complete ===")
    print(f"Final State: {state.model_dump()}")

if __name__ == "__main__":
    main()
