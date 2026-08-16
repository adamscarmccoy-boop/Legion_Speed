from pydantic import BaseModel, Field
from typing import List, Dict, Literal, Optional
from uuid import uuid4
import random

# --- Core Models ---

RoleType = Literal["promoter", "rival_dj", "fan", "agent", "club_owner", "media"]
TraitType = Literal["shady", "loyal", "clout_chaser", "visionary", "gatekeeper", "hype_man", "indie", "mainstream"]

class NPCProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    role: RoleType
    traits: List[TraitType]
    influence: int = Field(ge=1, le=100, default=50) # How much they can affect the scene
    affinity: int = Field(ge=-100, le=100, default=0)  # Relationship with ADAMSCARMCCOY
    current_mood: str = "neutral"

class SocialInteraction(BaseModel):
    actor_id: str
    target_id: str
    interaction_type: Literal["networking", "conflict", "collaboration", "fan_service", "hustle"]
    outcome_score: float # -1.0 to 1.0
    description: str

# --- The Engine ---

class SocialEngine:
    """
    The SocialEngine manages the complex web of relationships and social dynamics 
    within the EDM simulation world.
    """
    def __init__(self):
        self.npcs: Dict[str, NPCProfile] = {}
        self.interaction_history: List[SocialInteraction] = []

    def add_npc(self, profile: NPCProfile):
        self.npcs[profile.id] = profile

    def get_npc(self, npc_id: str) -> Optional[NPCProfile]:
        return self.npcs.get(npc_id)

    def interact(self, actor_id: str, target_id: str, interaction_type: str) -> SocialInteraction:
        """
        Executes a social interaction between two entities.
        In a full implementation, this would be called by the 'Warden' or 'Orchestrator'.
        """
        actor = self.get_npc(actor_id)
        target = self.get_npc(target_id)

        if not actor or not target:
            raise ValueError("Both actor and target must exist in the social engine.")

        # Base logic: Affinity changes based on interaction type and NPC traits
        affinity_change = 0.0
        description = ""

        if interaction_type == "networking":
            # High influence promoters are harder to impress but more rewarding
            difficulty = target.influence / 100.0
            success = random.random() > (0.3 * difficulty)
            if success:
                affinity_change = random.uniform(2, 10)
                description = f"Successful networking with {target.name}. They seem interested in your sound."
            else:
                affinity_change = random.uniform(-5, 2)
                description = f"Tried to connect with {target.name}, but it felt awkward."

        elif interaction_type == "conflict":
            # Conflict with a 'gatekeeper' is risky
            if "gatekeeper" in target.traits:
                affinity_change = random.uniform(-15, -5)
                description = f"A heated exchange with {target.name}. The tension is palpable."
            else:
                affinity_change = random.uniform(-5, 5)
                description = f"A minor clash with {target.name} regarding a set time."

        elif interaction_type == "collaboration":
            # Collaborations depend heavily on current affinity
            if target.affinity > 20:
                affinity_change = random.uniform(5, 15)
                description = f"A brilliant collab session with {target.name}! The energy was electric."
            else:
                affinity_change = random.uniform(-10, 5)
                description = f"Attempted a collab with {target.name}, but the vibes were off."

        elif interaction_type == "fan_service":
            # Fans respond well to attention
            if target.role == "fan":
                affinity_change = random.uniform(5, 12)
                description = f"You took time to chat with {target.name}. They are now a loyal follower."
            else:
                affinity_change = random.uniform(-2, 2)
                description = f"You interacted with {target.name}, but they weren't looking for a fan moment."

        elif interaction_type == "hustle":
            # Hustling (trying to get gigs/money) can alienate 'visionary' types
            if "visionary" in target.traits:
                affinity_change = random.uniform(-10, -2)
                description = f"Your hustle felt a bit too aggressive for {target.name}'s taste."
            else:
                affinity_change = random.uniform(2, 8)
                description = f"You made a smart move with {target.name}. They respect the grind."

        # Apply the change
        target.affinity = max(-100, min(100, target.affinity + affinity_change))
        
        interaction = SocialInteraction(
            actor_id=actor_id,
            target_id=target_id,
            interaction_type=interaction_type,
            outcome_score=affinity_change,
            description=description
        )
        self.interaction_history.append(interaction)
        return interaction

    def get_social_status(self) -> Dict:
        """Returns a summary of the current social climate."""
        return {
            "total_npcs": len(self.npcs),
            "average_affinity": sum(n.affinity for n in self.npcs.values()) / len(self.npcs) if self.npcs else 0,
            "top_allies": [n.name for n in self.npcs.values() if n.affinity > 50],
            "key_rivals": [n.name for n in self.npcs.values() if n.affinity < -30]
        }
