"""
LEGION SONIC ENGINE — Master Orchestrator (V2 - Stem-Aware)
===========================================================
This is the entry point for the autonomous EDM career simulation.
This version has been updated to use the stem_mastering_orchestrator.py
workflow when the Warden decides to adapt the DSP.
"""

import os
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
import asyncio

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

import ray
import json
import subprocess
from typing import Dict, Any
from datetime import datetime

# --- INTERNAL IMPORTS ---
from schemas import AgentState, WardenDecision
from legion_mcp_client import SyncLegionMCPClient
from intelligence_bridge import IntelligenceBridge

# --- CONFIGURATION ---
MARKET_DATA_PATH = r"C:\WEB CASE STUDY\data\chris_lake_fused_raw.json"
LOG_FILE = r"C:\WEB CASE STUDY\simulation_log_v2.json"
# Use the audio file we found as the test input for the mastering workflow
TEST_AUDIO_FILE = "SCAR-red strobe.mp3"


class LegionOrchestratorV2:
    """
    The Master Orchestrator, now updated to call the stem mastering workflow.
    """
    def __init__(self):
        self.state = AgentState(
            session_id=f"session_{int(datetime.utcnow().timestamp())}",
            current_phase="intro",
            current_city="Charlotte"
        )
        self.actors = {}
        self.mcp = None

    def boot_swarm(self):
        """Initializes all Ray Actors and the MCP connection."""
        print("[OrchestratorV2] Booting the Legion Swarm...")
        
        if not ray.is_initialized():
            ray.init(namespace="legion", ignore_reinit_error=True)

        self.bridge = IntelligenceBridge.remote(MARKET_DATA_PATH)
        from legion_sonic_engine_actors import SocialActor, MarketingActor, WardenActor
        
        self.actors['social'] = SocialActor.remote()
        self.actors['marketing'] = MarketingActor.remote()
        self.actors['warden'] = WardenActor.remote(self.actors['social'], self.actors['marketing'])
        
        print("[OrchestratorV2] ✅ Swarm Booted. All actors online.")

    def run_turn(self):
        """Executes a single simulation turn."""
        print(f"\n--- Running Simulation Turn: {self.state.session_id} ---")
        
        current_metrics = {"dsp_sub": 12.0, "dsp_rms": -10.5}
        gap = ray.get(self.bridge.get_intelligence_gap.remote(current_metrics))
        self.state.intelligence_gap = gap
        print(f"[SENSE] Intelligence Gap: {self.state.intelligence_gap}")

        decision = ray.get(self.actors['warden'].decide.remote(self.state.model_dump()))
        self.state.decision_log.append(decision['reasoning'])
        
        # --- FORCING DECISION FOR TESTING ---
        decision['action_type'] = "ADAPT_DSP"
        decision['reasoning'] = "Forced bypass of Warden to test stem mastering."
        
        print(f"[DECIDE] Action: {decision['action_type']} | Reason: {decision['reasoning']}")

        # --- MODIFIED LOGIC: Call Stem Mastering Workflow ---
        if decision['action_type'] == "ADAPT_DSP":
            print("\n[ACTION] ADAPT_DSP decision received. Initiating stem mastering workflow...")
            try:
                # Call the new orchestrator script as a subprocess
                subprocess.run([
                    sys.executable, # Use the same python executable
                    "stem_mastering_orchestrator.py",
                    TEST_AUDIO_FILE,
                    self.state.intelligence_gap
                ], check=True)
                print("[ACTION] Stem mastering workflow completed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"[ACTION] Stem mastering workflow failed: {e}")
            except FileNotFoundError:
                print("[ACTION] Error: Could not find 'stem_mastering_orchestrator.py'. Make sure it's in the same directory.")

        self._save_state()

    def _save_state(self):
        """Persists the current session state to disk."""
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(self.state.model_dump_json(indent=2))

    def trigger_antigravity_audit(self):
        """Pipes the final simulation result to the Antigravity Architect."""
        print("\n[Audit] Triggering Antigravity Architectural Audit...")
        try:
            subprocess.run([sys.executable, "ask_antigravity.py"], check=True)
            print("[Audit] Antigravity audit completed.")
        except Exception as e:
            print(f"[Audit] Audit failed: {e}")

    def shutdown(self):
        """Graceful shutdown of the swarm."""
        ray.shutdown()

if __name__ == "__main__":
    # Set the working directory to the script's location
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    orchestrator = LegionOrchestratorV2()
    orchestrator.boot_swarm()
    
    # Run only one turn to demonstrate the new workflow
    orchestrator.run_turn()
    
    orchestrator.trigger_antigravity_audit()
    orchestrator.shutdown()
    
    print("\n V2 Simulation Complete.")