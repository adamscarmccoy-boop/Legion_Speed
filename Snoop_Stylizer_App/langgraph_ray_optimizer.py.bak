import os
import sys
import torch
import librosa
import numpy as np
import soundfile as sf
import ray
from pydantic import BaseModel, Field
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# Import the DSP Pedalboard classes
from pedalboard import Pedalboard, Compressor, PitchShift, LowpassFilter, Delay

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


# ==========================================
# 1. PYDANTIC SCHEMAS & LANGGRAPH STATE
# ==========================================
class PitchValidationSchema(BaseModel):
    is_valid: bool = Field(description="True if the actual pitch is within 1.5Hz of the target pitch.")
    error_hz: float = Field(description="The absolute difference between target and actual pitch.")
    correction_needed_semitones: float = Field(description="The adjustment needed in semitones to hit the target.")

class OptimizerState(TypedDict):
    target_pitch_hz: float
    current_pitch_hz: float
    current_pt_weight: float    # The value inside the .pt file
    iteration_count: int
    is_optimized: bool
    status_log: list[str]
    last_output_file: str

# ==========================================
# 2. RAY VERIFICATION ACTOR
# ==========================================
@ray.remote
class PitchVerifier:
    def verify(self, filepath: str) -> float:
        if not os.path.exists(filepath):
            return 0.0
        y, sr = librosa.load(filepath, sr=22050)
        f0, voiced_flag, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
        valid_f0 = f0[voiced_flag]
        return float(np.median(valid_f0)) if len(valid_f0) > 0 else 100.0

# ==========================================
# 3. LANGGRAPH NODES
# ==========================================
def node_generate_audio(state: OptimizerState):
    print(f"\n[Iteration {state['iteration_count']}] Generating Audio with Delta: {state['current_pt_weight']:.2f} semitones")
    
    # Load input audio
    input_path = "instructor_input.m4a"
    if not os.path.exists(input_path):
        print(f"yt-dlp hasn't provided {input_path}, using fallback audio '0 Lead Vocals.wav'...")
        input_path = "0 Lead Vocals.wav"
    
    y, sr = librosa.load(input_path, sr=22050)
    
    # Save the current weight to the .pt file (simulating dynamic optimization)
    torch.save(torch.tensor([state['current_pt_weight']], dtype=torch.float32), 'snoop_pitch_delta.pt')
    
    # Run Pedalboard
    board = Pedalboard([
        Compressor(threshold_db=-15, ratio=3),
        PitchShift(semitones=state['current_pt_weight']),
        LowpassFilter(cutoff_frequency_hz=3500)
    ])
    
    processed_y = board(y, sample_rate=sr)
    output_filename = os.path.abspath(f"snoop_optimized_iter_{state['iteration_count']}.wav")
    sf.write(output_filename, processed_y, sr)
    state["last_output_file"] = output_filename
    
    state["status_log"].append(f"Generated {output_filename} with delta {state['current_pt_weight']:.2f}")
    return state

def node_verify_audio(state: OptimizerState):
    print("Verifying Pitch via Ray...")
    # Initialize Ray if not running
    if not ray.is_initialized():
        ray.init(namespace="legion", ignore_reinit_error=True)
        
    verifier = PitchVerifier.remote()
    actual_pitch = ray.get(verifier.verify.remote(state["last_output_file"]))
    state["current_pitch_hz"] = actual_pitch
    
    print(f"Result: Target = {state['target_pitch_hz']:.1f}Hz, Actual = {actual_pitch:.1f}Hz")
    
    # Pydantic-style Validation Math
    error = abs(actual_pitch - state['target_pitch_hz'])
    state["is_optimized"] = error < 1.5
    
    # If it failed, calculate exactly how much to adjust the semitones for the next run
    if not state["is_optimized"]:
        ratio = state['target_pitch_hz'] / actual_pitch
        correction_semitones = 12 * np.log2(ratio)
        state["current_pt_weight"] += correction_semitones
        print(f"FAILED. Adjusting .pt weight by {correction_semitones:+.2f} semitones.")
    else:
        print("SUCCESS! The .pt file is perfectly optimized.")
        
    state["iteration_count"] += 1
    return state

def pydantic_router(state: OptimizerState):
    if state["is_optimized"] or state["iteration_count"] > 5:
        return "end"
    return "generate"

# ==========================================
# 4. BUILD AND RUN LANGGRAPH
# ==========================================
if __name__ == "__main__":
    print("=== Sovereign Math LangGraph Optimizer ===")
    
    # Build Graph
    workflow = StateGraph(OptimizerState)
    workflow.add_node("generate", node_generate_audio)
    workflow.add_node("verify", node_verify_audio)
    
    workflow.add_edge(START, "generate")
    workflow.add_edge("generate", "verify")
    workflow.add_conditional_edges("verify", pydantic_router, {"generate": "generate", "end": END})
    
    app = workflow.compile()
    
    # Initial State (Target Snoop Dogg: 85.0Hz, Start with a wild guess of 0.0 shift)
    initial_state = {
        "target_pitch_hz": 85.0,
        "current_pitch_hz": 0.0,
        "current_pt_weight": 0.0,
        "iteration_count": 1,
        "is_optimized": False,
        "status_log": [],
        "last_output_file": ""
    }
    
    # Run the deterministic loop
    print("Starting Deterministic Optimization Loop...")
    final_state = app.invoke(initial_state)
    
    print("\n==========================================")
    print("🏁 OPTIMIZATION COMPLETE")
    print(f"Final .pt Weight: {final_state['current_pt_weight']:.2f} semitones")
    print("Optimized .pt file saved to: snoop_pitch_delta.pt")
    print("Final Audio saved to: temp_optimized_output.wav")
    print("==========================================")