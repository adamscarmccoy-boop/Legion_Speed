import os
import sys
import json
import asyncio

# Ensure execution path is workspace
sys.path.insert(0, r"C:\WEB CASE STUDY")

from langchain_core.messages import HumanMessage

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

try:
    from antigravity_vscode_ext.backend.legion_langgraph_brain import LegionLangGraphAgent
except Exception:
    LegionLangGraphAgent = None

# TABLE 1: WORKSPACE MODEL WEIGHTS & ENGINES
TABLE_1_WEIGHTS = """
### TABLE 1: WORKSPACE MODEL WEIGHTS & ENGINES INVENTORY
| Model / Weight File | Type | IO Signature / Shape / Architecture |
|---|---|---|
| sovereign_vision_brain.pth | PyTorch Checkpoint (.pth) | 6 Layers (Sequential MLP 41 -> 128 -> 64 -> 12) |
| sovereign_master_unified_brain.pth | PyTorch Checkpoint (.pth) | 12 Layers (Fused Vision/Audio/Genome Branches -> 128) |
| Dolly_pitch_delta.pt | PyTorch Tensor (.pt) | Tensor Shape: torch.Size([1]) |
| snoop_dna.pt | PyTorch Tensor (.pt) | Tensor Shape: torch.Size([13]) |
| snoop_pitch_delta.pt | PyTorch Tensor (.pt) | Tensor Shape: torch.Size([13]) |
| dna_brain.onnx | ONNX Engine (.onnx) | Inputs: ['dna_features'] -> Outputs: ['genre_logits'] |
| fretflow_omni_v4.onnx | ONNX Engine (.onnx) | Inputs: ['omni_vector_v4'] -> Outputs: ['mastering_command_set', 'linear_2', 'linear_3'] |
| omni_master_brain_v1.onnx | ONNX Engine (.onnx) | Inputs: ['section_features'] -> Outputs: ['mastering_command_set'] |
| real_data_brain.onnx | ONNX Engine (.onnx) | Inputs: ['features'] -> Outputs: ['tempo_pred'] |
| sovereign_big_brain_exhaustive.onnx | ONNX Engine (.onnx) | Inputs: ['dna_vector'] -> Outputs: ['dsp_state'] |
| sovereign_bridge_v1.onnx | ONNX Engine (.onnx) | Inputs: ['dna_vector'] -> Outputs: ['dsp_state'] |
"""

# TABLE 2: NVIDIA TAO NVDINOv2 SKILL BLUEPRINT
TABLE_2_NVDINOV2_SKILL = """
### TABLE 2: NVIDIA TAO NVDINOv2 SKILL SPECIFICATION
| Field | Value / Blueprint Spec |
|---|---|
| Skill Name | tao-train-nvdinov2 |
| Learning Strategy | Self-Supervised Vision Transformer (Teacher-Student Self-Distillation) |
| Supported Backbones | ViT-Small (vit_s), ViT-Large (vit_l) |
| Output Latent Bottleneck | bottleneck_dim: 384 |
| Head Dimension | hidden_dim: 2048, num_layers: 3 |
| Crop Architecture | Global Crops: 224x224 (scale 0.32-1.0), Local Crops: 98x98 (scale 0.05-0.32) |
| Target Export | ONNX Engine / TensorRT Deployment |
"""

# Read actual code context from workspace
def get_full_workspace_code_context():
    v2_p = r"C:\WEB CASE STUDY\legion_vision_orchestrator_v2.py"
    bridge_p = r"C:\WEB CASE STUDY\sovereign_vision_bridge.py"
    v2_code = open(v2_p, "r", encoding="utf-8").read() if os.path.exists(v2_p) else ""
    bridge_code = open(bridge_p, "r", encoding="utf-8").read() if os.path.exists(bridge_p) else ""
    return v2_code, bridge_code

_V2_CODE, _BRIDGE_CODE = get_full_workspace_code_context()

PROMPT_QUESTION = f"""
### SYSTEM CONTRACT: YOU ARE AN NVIDIA SENIOR ARCHITECT. READ THIS ACTUAL CODE:

=== ACTUAL WORKSPACE SOURCE CODE 1: legion_vision_orchestrator_v2.py ===
```python
{_V2_CODE}
```

=== ACTUAL WORKSPACE SOURCE CODE 2: sovereign_vision_bridge.py ===
```python
{_BRIDGE_CODE}
```

{TABLE_1_WEIGHTS}

### INSTRUCTIONS:
Based on the EXACT Python code above from `legion_vision_orchestrator_v2.py` and `sovereign_vision_bridge.py`:
Analyze the exact 7 nodes, the 41-feature Librosa DNA extraction, `VisionBrainMLP` (41 -> 128 -> 64 -> 12), Cosine Similarity thresholding (0.65), and the CLIP/HUD pipeline.
Provide a complete, line-by-line architectural critique and optimization blueprint specifically for this exact codebase.
"""

async def query_nvidia_langgraph():
    print("=" * 70)
    print(" DISPATCHING TABLES 1 & 2 TO NVIDIA LANGGRAPH ENDPOINT ")
    print("=" * 70)
    
    # Initialize Ray & detached SwarmKnowledgeRegistry actor in namespace 'legion'
    try:
        import ray
        from ray_arrow_swarm import SwarmKnowledgeRegistry
        if not ray.is_initialized():
            ray.init(namespace="legion", ignore_reinit_error=True)
        try:
            reg = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
            print("[INFO] Connected to existing SwarmKnowledgeRegistry actor on Ray.")
        except Exception:
            reg = SwarmKnowledgeRegistry.options(
                name="SwarmKnowledgeRegistry",
                namespace="legion",
                lifetime="detached"
            ).remote()
            print("[INFO] Spawned detached SwarmKnowledgeRegistry actor on Ray.")
    except Exception as ray_err:
        print(f"[WARN] Ray swarm setup note: {ray_err}")

    if LegionLangGraphAgent is not None:
        agent = LegionLangGraphAgent(max_recursion_limit=3, provider="nvidia")
        initial_input = {"messages": [HumanMessage(content=PROMPT_QUESTION)]}
        print("[INFO] Invoking LangGraph Agent with Open-Ended Multi-Table Query...", flush=True)
        final_state = await agent.ainvoke(initial_input)
        
        output_lines = []
        for msg in final_state["messages"]:
            if msg.type == "ai":
                output_lines.append(f"\n[NVIDIA LangGraph Response]:\n{msg.content}")
        
        full_text = "\n".join(output_lines)
        print(full_text, flush=True)
        
        # Save output to scratch
        out_file = r"C:\WEB CASE STUDY\scratch\nvidia_langgraph_open_tables_response.txt"
        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(full_text)
        print(f"\nSaved raw response to: {out_file}")
    else:
        print("[WARN] LegionLangGraphAgent unavailable. Displaying raw tables & prompt sent:")
        print(PROMPT_QUESTION)

if __name__ == "__main__":
    asyncio.run(query_nvidia_langgraph())