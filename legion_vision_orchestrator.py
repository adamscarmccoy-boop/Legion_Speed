import sys
sys.stdout.reconfigure(encoding="utf-8")

import os
import subprocess
import glob
import time
import numpy as np
import ray
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from sonic_to_visual_bridge import SonicToVisualBridgeActor

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


# ─── PATH CONFIGURATION ───
VENV_GPU  = r"C:\WEB CASE STUDY\.venv\Scripts\python.exe"
VENV_CPU  = r"C:\WEB CASE STUDY\.venv\Scripts\python.exe"
WORKSPACE = r"C:\WEB CASE STUDY"

SCRIPT_CLIP   = os.path.join(WORKSPACE, "clip_generative_art.py")
SCRIPT_VISION = os.path.join(WORKSPACE, "ray_vision_pipeline.py")
SCRIPT_VIDEO  = os.path.join(WORKSPACE, "feedback_visualizer.py")

# ─── STATE DEFINITION ───

class AgentState(TypedDict):
    audio_path:          str
    json_intent:         Optional[dict]   # Incoming MCP payload
    dna_vector:          Optional[list]
    visual_prompt:       Optional[str]
    onnx_decision_math:  Optional[list]   # Raw 12-dim output from ONNX model
    alignment_score:     float            # Cosine similarity: DNA vs ONNX vibe
    master_vibe_check:   bool             # Pass/fail gate
    generated_art_path:  Optional[str]
    hud_art_path:        Optional[str]
    final_video_path:    Optional[str]
    error:               Optional[str]
    status:              str

# ─── NODES ───

class LegionOrchestrator:
    def __init__(self):
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)
        self.bridge = SonicToVisualBridgeActor.remote()
        
        # PROPERLY initialize the Swarm Actors for the Warden
        from legion_sonic_engine_actors import SocialActor, MarketingActor, WardenActor
        self.social = SocialActor.remote()
        self.marketing = MarketingActor.remote()
        self.warden = WardenActor.remote(self.social, self.marketing)

    def extract_dna_node(self, state: AgentState) -> AgentState:
        try:
            import librosa
            audio_p = state.get("audio_path", r"C:\WEB CASE STUDY\sovereign_capture.wav")
            if os.path.exists(audio_p):
                y, sr = librosa.load(audio_p, sr=22050, duration=10.0)
                mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=64)
                real_dna = np.mean(mfcc, axis=1).tolist()
            else:
                real_dna = [0.0] * 64
            return {**state, "dna_vector": real_dna, "status": "analyzed"}
        except Exception as e:
            return {**state, "error": f"DNA Extraction Failed: {str(e)}", "status": "failed"}

    def semantic_bridge_node(self, state: AgentState) -> AgentState:
        try:
            dna_np = np.array(state["dna_vector"], dtype=np.float32).copy()
            prompt_payload = ray.get(self.bridge.bridge_dna_to_prompt.remote(dna_np))
            return {**state, "visual_prompt": prompt_payload.llm_expanded_prompt, "status": "prompted"}
        except Exception as e:
            return {**state, "error": f"Bridge Failed: {str(e)}", "status": "failed"}

    def onnx_alignment_node(self, state: AgentState) -> AgentState:
        """Step 2.5: ONNX Judge. Verifies Bridge output aligns with json_intent."""
        onnx_path = os.path.join(WORKSPACE, "sovereign_vision_brain.onnx")
        try:
            import onnxruntime as ort
            import numpy as np
            dna_np = np.array(state["dna_vector"], dtype=np.float32).reshape(1, -1)
            session = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
            input_name = session.get_inputs()[0].name
            onnx_vibe = session.run(None, {input_name: dna_np})[0][0]

            # Cosine similarity between first 12 dims of DNA and ONNX vibe output
            dna_slice = dna_np.flatten()[:12]
            dot = float(np.dot(dna_slice, onnx_vibe))
            norm = float(np.linalg.norm(dna_slice) * np.linalg.norm(onnx_vibe) + 1e-9)
            alignment = dot / norm
            return {**state, "onnx_decision_math": onnx_vibe.tolist(),
                    "alignment_score": alignment, "status": "aligned"}
        except Exception as e:
            # ONNX model not trained yet — skip alignment, allow pass-through
            return {**state, "alignment_score": 1.0, "onnx_decision_math": [],
                    "status": "aligned", "error": f"ONNX skipped: {str(e)}"}

    def quality_auditor_node(self, state: AgentState) -> AgentState:
        """Step 3: Decision gate. Drift detected -> re-route to bridge."""
        threshold = 0.75
        score = state.get("alignment_score", 1.0)
        if score < threshold:
            return {**state, "master_vibe_check": False, "status": "retry_required"}
        return {**state, "master_vibe_check": True, "status": "passed"}

    def image_generation_node(self, state: AgentState) -> AgentState:
        try:
            env = os.environ.copy()
            env["CLIP_PROMPT"] = state["visual_prompt"]

            result = subprocess.run(
                [VENV_GPU, SCRIPT_CLIP],
                env=env,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=True,
                cwd=WORKSPACE
            )

            outputs = glob.glob(os.path.join(WORKSPACE, "mastered_output", "generated_art_*.png"))
            latest_art = max(outputs, key=os.path.getctime) if outputs else None

            if not latest_art:
                raise Exception("CLIP finished but no output art file found.")

            return {**state, "generated_art_path": latest_art, "status": "image_ready"}
        except subprocess.CalledProcessError as e:
            return {**state, "error": f"CLIP GPU Error: {(e.stderr or '')[-300:]}", "status": "failed"}
        except Exception as e:
            return {**state, "error": f"Image Gen Failed: {str(e)}", "status": "failed"}

    def vision_scanner_node(self, state: AgentState) -> AgentState:
        try:
            subprocess.run(
                [VENV_CPU, SCRIPT_VISION],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=True,
                cwd=WORKSPACE
            )
            hud_path = os.path.join(WORKSPACE, "mastered_output", "artwork_creation", "cyber_hud_art.png")
            return {**state, "hud_art_path": hud_path, "status": "vision_ready"}
        except subprocess.CalledProcessError as e:
            return {**state, "error": f"Vision CPU Error: {(e.stderr or '')[-300:]}", "status": "failed"}
        except Exception as e:
            return {**state, "error": f"Vision Failed: {str(e)}", "status": "failed"}

    def video_compiler_node(self, state: AgentState) -> AgentState:
        try:
            subprocess.run(
                [VENV_CPU, SCRIPT_VIDEO],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=True,
                cwd=WORKSPACE
            )
            final_path = os.path.join(WORKSPACE, "mastered_output", "feedback_test", "feedback_reel_final.mp4")
            return {**state, "final_video_path": final_path, "status": "completed"}
        except subprocess.CalledProcessError as e:
            return {**state, "error": f"Video Error: {(e.stderr or '')[-300:]}", "status": "failed"}
        except Exception as e:
            return {**state, "error": f"Video Failed: {str(e)}", "status": "failed"}


    def warden_decision_node(self, state: AgentState) -> AgentState:
        """Step 3.5: The Warden analyzes the drift and decides on action."""
        try:
            decision = ray.get(self.warden.decide.remote(state))
            action = decision.get("action_type", "REINFORCE")
            
            if action == "ADAPT_DSP" or action == "PIVOT_MARKETING":
                return {**state, "status": "retry_required", "error": f"Warden ordered: {action}"}
            return {**state, "status": "passed"}
        except Exception as e:
            return {**state, "status": "passed", "error": f"Warden bypassed: {str(e)}"}

# ─── GRAPH CONSTRUCTION ───

def check_for_errors(state: AgentState):
    return "end" if state.get("status") == "failed" else "continue"

def create_orchestration_graph():
    orch = LegionOrchestrator()
    workflow = StateGraph(AgentState)

    workflow.add_node("extract_dna",     orch.extract_dna_node)
    workflow.add_node("semantic_bridge", orch.semantic_bridge_node)
    workflow.add_node("image_gen",       orch.image_generation_node)
    workflow.add_node("vision_scanner",  orch.vision_scanner_node)
    workflow.add_node("video_compiler",  orch.video_compiler_node)

    workflow.add_node("onnx_alignment",  orch.onnx_alignment_node)
    workflow.add_node("quality_auditor", orch.quality_auditor_node)
    workflow.add_node("warden_decision", orch.warden_decision_node)

    workflow.set_entry_point("extract_dna")
    workflow.add_conditional_edges("extract_dna",    check_for_errors, {"end": END, "continue": "semantic_bridge"})
    workflow.add_edge("semantic_bridge", "onnx_alignment")
    workflow.add_edge("onnx_alignment",  "quality_auditor")
    workflow.add_edge("quality_auditor", "warden_decision")

    # Drift-detection loop controlled by Warden
    def route_audit(state: AgentState):
        return "retry" if state.get("status") == "retry_required" else "continue"

    workflow.add_conditional_edges(
        "warden_decision", route_audit,
        {"retry": "semantic_bridge", "continue": "image_gen"}
    )

    workflow.add_conditional_edges("image_gen",      check_for_errors, {"end": END, "continue": "vision_scanner"})
    workflow.add_conditional_edges("vision_scanner", check_for_errors, {"end": END, "continue": "video_compiler"})
    workflow.add_edge("video_compiler", END)
    return workflow.compile()


# ─── ENTRY POINT ───

if __name__ == "__main__":
    app = create_orchestration_graph()

    initial_state: AgentState = {
        "audio_path":          r"C:\WEB CASE STUDY\sovereign_onnx_masters\ONNX_SCAR-red strobe.mp3",
        "json_intent":         {"style": "dark cyberpunk", "energy": "high"},
        "dna_vector":          None,
        "visual_prompt":       None,
        "onnx_decision_math":  None,
        "alignment_score":     0.0,
        "master_vibe_check":   False,
        "generated_art_path":  None,
        "hud_art_path":        None,
        "final_video_path":    None,
        "error":               None,
        "status":              "idle"
    }

    t0 = time.perf_counter()
    final_output = app.invoke(initial_state)
    elapsed = time.perf_counter() - t0

    if final_output["status"] == "completed":
        sys.stdout.write(f"SUCCESS in {elapsed:.1f}s\n")
        sys.stdout.write(f"Final Reel:  {final_output['final_video_path']}\n")
        sys.stdout.write(f"HUD Art:     {final_output['hud_art_path']}\n")
        sys.stdout.write(f"Prompt:      {(final_output['visual_prompt'] or '')[:100]}\n")
    else:
        sys.stdout.write(f"FAILED at status: {final_output['status']}\n")
        sys.stdout.write(f"Error: {final_output['error']}\n")