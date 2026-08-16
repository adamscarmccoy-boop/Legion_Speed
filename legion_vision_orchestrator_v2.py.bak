import sys
import os
import subprocess
import glob
import time
import numpy as np
import ray
import torch
import torch.nn as nn
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

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


# ─── 1. ENVIRONMENT STABILIZATION ───
VENV_PATH = r"C:\WEB CASE STUDY\.venv\Lib\site-packages"
if VENV_PATH not in sys.path:
    sys.path.insert(0, VENV_PATH)

sys.stdout.reconfigure(encoding="utf-8")

# Import your existing Bridge Actor
from sonic_to_visual_bridge import SonicToVisualBridgeActor

# ─── 2. PATH CONFIGURATION ───
VENV_GPU  = r"C:\WEB CASE STUDY\.venv\Scripts\python.exe"
VENV_CPU  = r"C:\WEB CASE STUDY\.venv\Scripts\python.exe"
WORKSPACE = r"C:\WEB CASE STUDY"

SCRIPT_CLIP   = os.path.join(WORKSPACE, "clip_generative_art.py")
SCRIPT_VISION = os.path.join(WORKSPACE, "ray_vision_pipeline.py")
SCRIPT_VIDEO  = os.path.join(WORKSPACE, "feedback_visualizer.py")
PTH_PATH      = os.path.join(WORKSPACE, "sovereign_vision_brain.pth")
# THE NEW GOLD BASELINE
NEW_BASELINE = r"C:\Users\adams\Downloads\image-1783570687667.png"

# ─── 3. NEURAL ARCHITECTURE ───
class VisionBrainMLP(nn.Module):
    def __init__(self, input_dim: int, output_dim: int = 12):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, output_dim),
            nn.Softmax(dim=1)
        )
    def forward(self, x): return self.net(x)

# ─── 4. STATE DEFINITION ───
class AgentState(TypedDict):
    audio_path:          str
    json_intent:         Optional[dict]
    dna_vector:          Optional[list]
    visual_prompt:       Optional[str]
    vibe_vector:         Optional[list]
    alignment_score:     float
    retry_count:         int
    master_vibe_check:   bool
    generated_art_path:  Optional[str]
    hud_art_path:        Optional[str]
    final_video_path:    Optional[str]
    error:               Optional[str]
    status:              str

# ─── 5. THE ORCHESTRATOR ───
class LegionOrchestrator:
    def __init__(self):
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)
        self.bridge = SonicToVisualBridgeActor.remote()
        
        self.input_dim = 41 
        self.brain = VisionBrainMLP(self.input_dim)
        if os.path.exists(PTH_PATH):
            self.brain.load_state_dict(torch.load(PTH_PATH))
            self.brain.eval()
            print("[System] Sovereign Brain Loaded into Memory.")

        # Load feature lake and fit the StandardScaler
        import json
        import pandas as pd
        from sklearn.preprocessing import StandardScaler
        feature_lake_path = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/exported_json/duckdb_audio_features.json"
        self.scaler = None
        if os.path.exists(feature_lake_path):
            try:
                with open(feature_lake_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                df = pd.DataFrame(data)
                skip = {"artist", "filepath", "timestamp"}
                feats = [c for c in df.columns if c not in skip and df[c].dtype in [float, int, "float64", "int64"]]
                df = df.dropna(subset=feats)
                self.scaler = StandardScaler()
                self.scaler.fit(df[feats].values)
                print("[System] StandardScaler fitted on duckdb_audio_features.json.")
            except Exception as e:
                print(f"[System] Warning: Failed to fit StandardScaler: {str(e)}")

    def extract_dna_node(self, state: AgentState) -> AgentState:
        print(f"[Node: DNA] Analyzing: {os.path.basename(state['audio_path'])}")
        try:
            import librosa
            # Real 41-feature extraction matching the training dataset schema
            y, sr = librosa.load(state['audio_path'], sr=None, mono=True)
            
            tempo = float(librosa.beat.beat_track(y=y, sr=sr)[0].flat[0])
            rms_val = float(np.sqrt(np.mean(y**2)))
            rms_db = float(20 * np.log10(max(rms_val, 1e-9)))
            crest_factor = float(np.max(np.abs(y)) / (rms_val + 1e-9))

            S = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
            freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)

            def band_energy(S, freqs, lo, hi):
                mask = (freqs >= lo) & (freqs < hi)
                return float(np.mean(S[mask, :] ** 2)) if mask.any() else 0.0

            sub_bass_energy = band_energy(S, freqs, 20, 60)
            bass_energy = band_energy(S, freqs, 60, 250)
            mid_energy = band_energy(S, freqs, 250, 4000)
            high_energy = band_energy(S, freqs, 4000, 20000)

            spectral_centroid = float(np.mean(librosa.feature.spectral_centroid(S=S, freq=freqs)))
            spectral_rolloff = float(np.mean(librosa.feature.spectral_rolloff(S=S, freq=freqs)))
            spectral_bandwidth = float(np.mean(librosa.feature.spectral_bandwidth(S=S, freq=freqs)))
            spectral_contrast = float(np.mean(librosa.feature.spectral_contrast(S=S, sr=sr)))
            zcr = float(np.mean(librosa.feature.zero_crossing_rate(y)))

            onset_strength = float(np.mean(librosa.onset.onset_strength(y=y, sr=sr)))
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            transient_density = float(len(librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr))) / (len(y)/sr)

            y_harmonic, y_percussive = librosa.effects.hpss(y)
            harmonic_ratio = float(np.mean(y_harmonic**2) / (rms_val**2 + 1e-9))
            percussive_ratio = float(np.mean(y_percussive**2) / (rms_val**2 + 1e-9))

            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            mfcc_means = [float(np.mean(m)) for m in mfccs]

            chromas = librosa.feature.chroma_stft(y=y, sr=sr)
            chroma_means = [float(np.mean(c)) for c in chromas]

            features_41 = [
                tempo, rms_db, crest_factor, sub_bass_energy, bass_energy, mid_energy, high_energy,
                spectral_centroid, spectral_rolloff, spectral_bandwidth, spectral_contrast, zcr,
                onset_strength, transient_density, harmonic_ratio, percussive_ratio
            ] + mfcc_means + chroma_means

            dna_64 = np.zeros(64, dtype=np.float32)
            dna_64[:41] = features_41
            real_dna = dna_64.tolist()
            return {**state, "dna_vector": real_dna, "retry_count": state.get("retry_count", 0), "status": "analyzed"}
        except Exception as e:
            return {**state, "error": f"DNA Extraction Failed: {str(e)}", "status": "failed"}

    def semantic_bridge_node(self, state: AgentState) -> AgentState:
        print("[Node: Bridge] Converting Math to CLIP Prompt...")
        dna_np = np.array(state["dna_vector"], dtype=np.float32).copy()
        prompt_payload = ray.get(self.bridge.bridge_dna_to_prompt.remote(dna_np))
        return {**state, "visual_prompt": prompt_payload.llm_expanded_prompt, "status": "prompted"}

    def neural_alignment_node(self, state: AgentState) -> AgentState:
        print(f"[Node: Neural Alignment] Running Vibe Check (Attempt {state.get('retry_count', 0) + 1})...")
        raw_dna = np.array(state["dna_vector"], dtype=np.float32).flatten()[:41]
        
        # Scale inputs for neural network
        if hasattr(self, 'scaler') and self.scaler is not None:
            scaled_dna = self.scaler.transform(raw_dna.reshape(1, -1)).flatten()
        else:
            scaled_dna = raw_dna
            
        dna_t = torch.FloatTensor(scaled_dna.reshape(1, -1))
        with torch.no_grad():
            vibe_vector = self.brain(dna_t).numpy().flatten()
            
        dna_slice = np.abs(raw_dna[:12]) 
        dot = float(np.dot(dna_slice, vibe_vector))
        norm = float(np.linalg.norm(dna_slice) * np.linalg.norm(vibe_vector) + 1e-9)
        alignment = dot / norm
        return {**state, "vibe_vector": vibe_vector.tolist(), "alignment_score": alignment, "status": "aligned"}

    def quality_auditor_node(self, state: AgentState) -> AgentState:
        threshold = 0.65 
        retries = state.get("retry_count", 0)
        max_retries = 3 
        if state["alignment_score"] < threshold and retries < max_retries:
            print(f"[Audit] REJECTED ({state['alignment_score']:.2f}). Generating new DNA mutation...")
            return {**state, "retry_count": retries + 1, "status": "retry_required"}
        print(f"[Audit] PASS ({state['alignment_score']:.2f}). Proceeding to GPU...")
        return {**state, "master_vibe_check": True, "status": "passed"}

    def image_generation_node(self, state: AgentState) -> AgentState:
        print(f"[Node: Image Gen] Firing CLIP on E:\\ Drive...")
        env = os.environ.copy()
        env["CLIP_PROMPT"] = state["visual_prompt"]
        # INJECTING NEW BASELINE
        env["INIT_IMAGE"] = NEW_BASELINE
        try:
            subprocess.run([VENV_GPU, SCRIPT_CLIP], env=env, check=True, cwd=WORKSPACE)
            outputs = glob.glob(os.path.join(WORKSPACE, "mastered_output", "generated_art_*.png"))
            if not outputs: return {**state, "error": "No files found", "status": "failed"}
            latest_art = max(outputs, key=os.path.getctime)
            import shutil
            shutil.copy(latest_art, os.path.join(WORKSPACE, "mastered_output", "generated_art.png"))
            return {**state, "generated_art_path": latest_art, "status": "image_ready"}
        except Exception as e:
            return {**state, "error": str(e), "status": "failed"}

    def vision_scanner_node(self, state: AgentState) -> AgentState:
        print("[Node: Scanner] Running HUD Overlay on C:\\ Drive...")
        subprocess.run([VENV_CPU, SCRIPT_VISION], check=True, cwd=WORKSPACE)
        hud_path = os.path.join(WORKSPACE, "mastered_output", "artwork_creation", "cyber_hud_art.png")
        return {**state, "hud_art_path": hud_path, "status": "vision_ready"}

    def video_compiler_node(self, state: AgentState) -> AgentState:
        print("[Node: Video] Muxing Final Sovereign Reel...")
        subprocess.run([VENV_CPU, SCRIPT_VIDEO], check=True, cwd=WORKSPACE)
        final_path = os.path.join(WORKSPACE, "mastered_output", "feedback_test", "feedback_reel_final.mp4")
        return {**state, "final_video_path": final_path, "status": "completed"}

# ─── 6. THE GRAPH (FIXED INDENTATION) ───
def create_graph():
    orch = LegionOrchestrator()
    workflow = StateGraph(AgentState)

    workflow.add_node("extract_dna",     orch.extract_dna_node)
    workflow.add_node("semantic_bridge", orch.semantic_bridge_node)
    workflow.add_node("neural_alignment",orch.neural_alignment_node)
    workflow.add_node("quality_auditor", orch.quality_auditor_node)
    workflow.add_node("image_gen",       orch.image_generation_node)
    workflow.add_node("vision_scanner",  orch.vision_scanner_node)
    workflow.add_node("video_compiler",  orch.video_compiler_node)

    workflow.set_entry_point("extract_dna")
    workflow.add_edge("extract_dna", "semantic_bridge")
    workflow.add_edge("semantic_bridge", "neural_alignment")
    workflow.add_edge("neural_alignment", "quality_auditor")

    workflow.add_conditional_edges(
        "quality_auditor", 
        lambda x: "retry" if x["status"] == "retry_required" else "continue",
        {"retry": "semantic_bridge", "continue": "image_gen"}
    )

    workflow.add_edge("image_gen", "vision_scanner")
    workflow.add_edge("vision_scanner", "video_compiler")
    workflow.add_edge("video_compiler", END)
    
    return workflow.compile()

if __name__ == "__main__":
    app = create_graph()
    initial_state = {
        "audio_path": r"E:\DJSUSAN\LEGION\what a waste-2 (Edit).wav",
        "json_intent": {"vibe": "dark cyberpunk", "precision": "military"},
        "dna_vector": None, "visual_prompt": None, "vibe_vector": None,
        "alignment_score": 0.0, "retry_count": 0, "master_vibe_check": False,
        "generated_art_path": None, "hud_art_path": None, "final_video_path": None,
        "error": None, "status": "idle"
    }
    
    result = app.invoke(initial_state)
    print(f"\n🏁 FINAL STATUS: {result['status']}")