import sys
import torch
import torch.nn as nn
import json
import os

sys.stdout.reconfigure(encoding="utf-8")

print("Loading Audio LLM...")
LLM_PATH = r"C:\WEB CASE STUDY\sonic_dna_engine\audio_llm_v1.pt"
ONNX_PATH = r"C:\WEB CASE STUDY\sonic_dna_engine\audio_llm_v1.onnx"
SIDECAR_PATH = r"C:\WEB CASE STUDY\sonic_dna_engine\audio_llm_v1.onnx.data"

ckpt = torch.load(LLM_PATH, map_location="cpu", weights_only=False)
DSP_COLS = ckpt["dsp_cols"]
IN_DIM = ckpt["in_dim"]

class AudioLLM(nn.Module):
    def __init__(self, in_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 64), nn.LayerNorm(64), nn.GELU(),
            nn.Linear(64, 64),    nn.LayerNorm(64),  nn.GELU(),
            nn.Linear(64, in_dim)
        )
    def forward(self, x):
        return self.net(x)

model = AudioLLM(IN_DIM)
model.load_state_dict(ckpt["model_state_dict"])
model.eval()

print("Exporting to ONNX...")
dummy_input = torch.randn(1, IN_DIM, dtype=torch.float32)

# Use legacy exporter (JIT-based) to avoid Dynamo external data bugs for small models
if hasattr(torch.onnx, 'dynamo_export'):
    # PyTorch 2.x explicitly request legacy if possible, or just standard kwargs
    pass

try:
    torch.onnx.export(
        model, 
        dummy_input, 
        ONNX_PATH,
        export_params=True,
        opset_version=17,
        do_constant_folding=True,
        input_names=['input_vector'],
        output_names=['hallucinated_vector'],
        dynamic_axes={'input_vector': {0: 'batch_size'}, 'hallucinated_vector': {0: 'batch_size'}}
    )
except TypeError:
    # If dynamic_axes causes issues with newer APIs, drop it
    torch.onnx.export(
        model, 
        dummy_input, 
        ONNX_PATH,
        export_params=True,
        opset_version=17,
        do_constant_folding=True,
        input_names=['input_vector'],
        output_names=['hallucinated_vector']
    )

print(f"✅ Successfully exported to {ONNX_PATH}")

print("Writing DSP Columns")
# Save metadata so the serving side knows how to pack the inputs
meta = {
    "dsp_cols": DSP_COLS,
    "in_dim": IN_DIM
}
with open(ONNX_PATH + ".meta.json", "w") as f:
    json.dump(meta, f)
print(f"Exported metadata to {ONNX_PATH}.meta.json")

# Verify ONNX
try:
    import onnx
    import onnxruntime as ort
    onnx_model = onnx.load(ONNX_PATH)
    onnx.checker.check_model(onnx_model)
    ort_session = ort.InferenceSession(ONNX_PATH, providers=['CPUExecutionProvider'])
    
    # Run a quick test
    test_out = ort_session.run(None, {'input_vector': dummy_input.numpy()})
    print(f"✅ Test run successful! Output shape: {test_out[0].shape}")
except Exception as e:
    print(f"⚠️ ONNX check failed: {e}")
