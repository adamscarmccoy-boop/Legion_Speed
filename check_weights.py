import torch
import os

WEIGHTS_PATH = r"C:\WEB CASE STUDY\sonic_dna_output\fretflow_omni_v3.pt"

def check_weights():
    if not os.path.exists(WEIGHTS_PATH):
        print(f"File not found: {WEIGHTS_PATH}")
        return

    print(f"Checking weights: {WEIGHTS_PATH}")
    try:
        checkpoint = torch.load(WEIGHTS_PATH, map_location="cpu")
        if isinstance(checkpoint, dict):
            print("Checkpoint is a dictionary. Keys:")
            for k, v in checkpoint.items():
                if hasattr(v, 'shape'):
                    print(f"  {k}: {v.shape}")
                elif isinstance(v, (int, float)):
                    print(f"  {k}: {v}")
                else:
                    print(f"  {k}: {type(v)}")
        else:
            print(f"Checkpoint is not a dictionary. Type: {type(checkpoint)}")
    except Exception as e:
        print(f"Error loading weights: {e}")

if __name__ == "__main__":
    check_weights()
