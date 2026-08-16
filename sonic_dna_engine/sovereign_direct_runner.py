import os
import site
import ctypes
import numpy as np
import onnxruntime as ort

model_path = r"C:\WEB CASE STUDY\sovereign_big_brain_exhaustive.onnx"

# 1. Initialize session cleanly
try:
    session = ort.InferenceSession(model_path)
    print("[SOVEREIGN_LINK_OK] ONNX InferenceSession loaded successfully!")
except Exception as e:
    print(f"[CRITICAL_ERROR] Failed to load model at {model_path}: {e}")
    session = None

if session:
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name

    def run_sovereign_block(state_tensor_64: np.ndarray) -> np.ndarray:
        return session.run([output_name], {input_name: state_tensor_64})[0]

    # 2. Test Execution
    test_state = np.zeros((1, 64), dtype=np.float32)
    test_state[0, 0] = 1.0   # Opcode
    test_state[0, 8] = -14.0 # RMS dB

    dsp_params = run_sovereign_block(test_state)
    print(f"[SUCCESS] Bare-metal DSP Output shape: {dsp_params.shape}")