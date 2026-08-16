import os
import torch
from huggingface_hub import snapshot_download
from optimum.exporters.onnx import main_export
from pathlib import Path

# ─── HARD PATH CONFIGURATION ───
# This is where the raw weights will live (The "Source of Truth")
RAW_WEIGHTS_DIR = r"C:\WEB CASE STUDY\models\gemma_raw"

# This is where the compiled ONNX engine will live (The "Production Brain")
ONNX_EXPORT_DIR = r"C:\WEB CASE STUDY\models\gemma_onnx"

# The model ID on Hugging Face
# 'google/gemma-2b' is the small version. 
# Note: You may need to run 'huggingface-cli login' if the model is gated.
MODEL_ID = "google/gemma-2b"

def forge_onnx_model():
    """
    Downloads raw weights and compiles them into an optimized ONNX graph.
    """
    print(f"[FORGE] Starting Gemma ONNX Pipeline...")
    print(f"Target Raw Path: {RAW_WEIGHTS_DIR}")
    print(f"Target ONNX Path: {ONNX_EXPORT_DIR}")

    # 1. Ensure directories exist
    os.makedirs(RAW_WEIGHTS_DIR, exist_ok=True)
    os.makedirs(ONNX_EXPORT_DIR, exist_ok=True)

    # 2. DOWNLOAD PHASE
    if not os.path.exists(os.path.join(RAW_WEIGHTS_DIR, "config.json")):
        print(f"[DOWNLOAD] Downloading {MODEL_ID} to hard path...")
        try:
            snapshot_download(
                repo_id=MODEL_ID,
                local_dir=RAW_WEIGHTS_DIR,
                local_dir_use_symlinks=False,
                ignore_patterns=["*.msgpack", "*.h5"] # Skip unnecessary formats
            )
            print(f"[DOWNLOAD] Weights secured at {RAW_WEIGHTS_DIR}")
        except Exception as e:
            print(f"[DOWNLOAD] FAILED. Ensure you have access to the gated repo (huggingface-cli login): {e}")
            return
    else:
        print(f"[SKIP] Raw weights already exist at {RAW_WEIGHTS_DIR}")

    # 3. COMPILER PHASE (Optimizing for Inference)
    print(f"[COMPILE] Compiling to ONNX (this may take several minutes)...")
    print(f"Task: text-generation-with-past (Optimized for KV-Caching)")
    
    try:
        # main_export handles the heavy lifting: 
        # - Converts weights to ONNX
        # - Optimizes the computation graph
        # - Generates the required configuration files
        main_export(
            model_name_or_path=RAW_WEIGHTS_DIR,
            output=ONNX_EXPORT_DIR,
            task="text-generation-with-past", # Crucial for speed (enables KV cache)
            device="cpu",                     # Compile on CPU to avoid VRAM spikes during export
        )
        print(f"[COMPILE] SUCCESS! ONNX engine built at {ONNX_EXPORT_DIR}")
        
    except Exception as e:
        print(f"[COMPILE] FAILED: {str(e)}")
        return

    # 4. VERIFICATION
    print("\n" + "="*30)
    print("FINAL DIRECTORY INSPECTION")
    print("="*30)
    for file in os.listdir(ONNX_EXPORT_DIR):
        print(f"  {file}")
    print("="*30)
    print(f"Ready for Sovereign Orchestration.")

if __name__ == "__main__":
    # Check for HF Token if model is gated
    # If you haven't logged in, this might fail for Gemma.
    # Run 'huggingface-cli login' in your terminal first.
    forge_onnx_model()
