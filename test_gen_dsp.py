import sys
import onnxruntime as ort
import duckdb
import numpy as np
import json

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

print("=== 1. Loading Real Kick Data from DuckDB ===")
LLM_PATH = r"C:\WEB CASE STUDY\sonic_dna_engine\audio_llm_v1.onnx"
with open(LLM_PATH + ".meta.json", "r") as f:
    meta = json.load(f)
    DSP_COLS = [c if c != 'zero_crossing_rate' else 'zcr' for c in meta["dsp_cols"]]
    IN_DIM = meta["in_dim"]

conn = duckdb.connect(r"C:\WEB CASE STUDY\web_intel_sonicdb.duckdb", read_only=True)
df_kick = conn.execute("SELECT * FROM audio_features WHERE asset_type='SAMPLE' AND drum_type='KICK' ORDER BY random() LIMIT 1").fetchdf()
kick_path = df_kick["filepath"].iloc[0]
kick_vec = df_kick[DSP_COLS].values.astype(np.float32)
conn.close()

print(f"Loaded Kick: {kick_path}")
print(f"Kick Vector Shape: {kick_vec.shape} (Expected IN_DIM: {IN_DIM})")

print("\n=== 2. Hallucinating Bass Vector (Generative Engine) ===")
session_llm = ort.InferenceSession(LLM_PATH, providers=["CPUExecutionProvider"])
input_name_llm = session_llm.get_inputs()[0].name
hallucinated_bass = session_llm.run(None, {input_name_llm: kick_vec.reshape(1, -1)})[0][0]

print(f"Hallucinated Bass Shape: {hallucinated_bass.shape}")

print("\n=== 3. End DSP (Big Brain Exhaustive) ===")
BIG_BRAIN_PATH = r"C:\WEB CASE STUDY\sovereign_big_brain_exhaustive.onnx"
session_dsp = ort.InferenceSession(BIG_BRAIN_PATH, providers=["CPUExecutionProvider"])
input_name_dsp = session_dsp.get_inputs()[0].name
input_shape_dsp = session_dsp.get_inputs()[0].shape
print(f"Big Brain Expects Input Shape: {input_shape_dsp}")

# The bridge: Zero-pad the 11-dim latent vector to 64 dims!
padded_bass = np.pad(hallucinated_bass, (0, 64 - len(hallucinated_bass)), mode='constant')

try:
    dsp_out = session_dsp.run(None, {input_name_dsp: padded_bass.reshape(1, -1).astype(np.float32)})[0][0]
    print(f"\n✅ SUCCESS! Tensor Shapes are perfectly aligned.")
    print(f"Big Brain DSP Output Shape: {dsp_out.shape}")
    print(f"DSP Values (First 5): {dsp_out[:5]}")
except Exception as e:
    print(f"\n❌ SHAPE MISMATCH ERROR during DSP inference: {e}")
