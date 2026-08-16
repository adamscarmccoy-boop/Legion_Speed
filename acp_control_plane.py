"""
ACP Router & Event Bus Core Daemon for Legion / Ray / Model Swarm.
"""

import sys
import time
import uuid
import logging
from typing import Dict, List, Optional
from pydantic import BaseModel

try:
    from legion_schema import ACPEvent, AgentRegistration, StatePointer, ACPEnvelope
except ImportError:
    # Inline fallback if imported directly from an isolated environment
    from pydantic import BaseModel
    class ACPEvent(BaseModel):
        event_id: str
        source_agent: str
        event_type: str
        timestamp: float
        payload: dict = {}

    class AgentRegistration(BaseModel):
        agent_id: str
        agent_name: str
        capabilities: List[str]
        endpoint_uri: str
        status: str = "ONLINE"
        last_heartbeat: float

    class StatePointer(BaseModel):
        pointer_id: str
        store_type: str
        uri_or_ref: str
        schema_version: str = "v1"

    class ACPEnvelope(BaseModel):
        trace_id: str
        sender_id: str
        receiver_id: Optional[str] = None
        action: str
        state_pointer: Optional[StatePointer] = None
        parameters: dict = {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [ACP] %(levelname)s: %(message)s")
logger = logging.getLogger("ACPControlPlane")


class ACPControlPlane:
    def __init__(self):
        self.registered_agents: Dict[str, AgentRegistration] = {}
        self.event_log: List[ACPEvent] = []

    def register_agent(self, registration: AgentRegistration) -> bool:
        """Register or update an agent's capability card."""
        self.registered_agents[registration.agent_id] = registration
        logger.info(f"Registered Agent '{registration.agent_name}' ({registration.agent_id}) with capabilities: {registration.capabilities}")
        return True

    def find_agent_by_capability(self, capability: str) -> Optional[AgentRegistration]:
        """Find an online agent supporting the given capability."""
        for agent in self.registered_agents.values():
            if capability in agent.capabilities and agent.status == "ONLINE":
                return agent
        return None

    def publish_event(self, event_type: str, source_agent: str, payload: dict) -> ACPEvent:
        """Publish an event to the ACP event stream."""
        event = ACPEvent(
            event_id=str(uuid.uuid4()),
            source_agent=source_agent,
            event_type=event_type,
            timestamp=time.time(),
            payload=payload
        )
        self.event_log.append(event)
        logger.info(f"Event Broadcast [{event_type}] from {source_agent}: {payload}")
        return event

    def route_envelope(self, envelope: ACPEnvelope) -> dict:
        """Route an ACP message envelope to target agent or capability."""
        logger.info(f"Routing envelope [{envelope.trace_id}] Action: {envelope.action} from {envelope.sender_id}")
        
        target_agent = None
        if envelope.receiver_id and envelope.receiver_id in self.registered_agents:
            target_agent = self.registered_agents[envelope.receiver_id]
        else:
            target_agent = self.find_agent_by_capability(envelope.action)

        if not target_agent:
            msg = f"No available agent found for target: receiver={envelope.receiver_id}, action={envelope.action}"
            logger.warning(msg)
            return {"status": "FAILED", "error": msg}

        return {
            "status": "ROUTED",
            "target_agent": target_agent.agent_name,
            "endpoint_uri": target_agent.endpoint_uri,
            "trace_id": envelope.trace_id
        }


if __name__ == "__main__":
    logger.info("Initializing ACP Control Plane Standalone Verification...")
    acp = ACPControlPlane()

    # Self-test registration
    acp.register_agent(AgentRegistration(
        agent_id="ray_dsp_worker_1",
        agent_name="Ray DSP Worker Swarm",
        capabilities=["dsp_alignment", "segment_physics"],
        endpoint_uri="ray://127.0.0.1:6379",
        last_heartbeat=time.time()
    ))

    acp.register_agent(AgentRegistration(
        agent_id="lm_studio_agent",
        agent_name="LM Studio Local LLM",
        capabilities=["llm_inference", "chat_v4"],
        endpoint_uri="http://127.0.0.1:1234/v1",
        last_heartbeat=time.time()
    ))

    # Test routing
    test_envelope = ACPEnvelope(
        trace_id=str(uuid.uuid4()),
        sender_id="mcp_gateway",
        action="dsp_alignment",
        parameters={"threshold": 85.0}
    )

    route_res = acp.route_envelope(test_envelope)
    print("Routing result:", route_res)
    assert route_res["status"] == "ROUTED"
    logger.info("ACP Control Plane core verified successfully.")
