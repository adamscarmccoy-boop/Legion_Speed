import os
import sys
import json
import time
import datetime
import onnxruntime as ort

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# --- MANUAL ENV LOADER (No dotenv dependency needed) ---
env_path = r"C:\WEB CASE STUDY\.env"
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                os.environ[k] = v

if not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ.get("GEMINI_API_KEY") or os.environ.get("AISTUDIO_API_KEY") or ""

from google import genai
from google.genai import types

onnx_path = r"C:\WEB CASE STUDY\sovereign_big_brain_exhaustive.onnx"
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# Resolve to the newly generated stateful master sidecar JSON
json_dir = r"C:\WEB CASE STUDY\sovereign_onnx_masters_v2"
json_files = sorted([f for f in os.listdir(json_dir) if f.endswith(".dna.json") and "223418" in f])
if json_files:
    json_path = os.path.join(json_dir, json_files[-1])
else:
    # General fallback
    json_path = r"C:\WEB CASE STUDY\sovereign_onnx_masters_v2\ONNX2_20260716_223418_SCAR-red strobe.wav.dna.json"

gemma_sandbox_out = os.path.join(r"C:\WEB CASE STUDY\logs", f"gemma_sandbox_audit_report_{timestamp}.md")

print(f"Loading metadata for model and dynamic master JSON from: {json_path}")
session = ort.InferenceSession(onnx_path)
onnx_info = {
    "inputs": [{"name": i.name, "shape": i.shape, "type": i.type} for i in session.get_inputs()],
    "outputs": [{"name": o.name, "shape": o.shape, "type": o.type} for o in session.get_outputs()]
}

raw_json_data = "{}"
if os.path.exists(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        raw_json_data = f.read()
else:
    print(f"Error: JSON telemetry file not found at {json_path}")
    sys.exit(1)

prompt = f"""
You are the Sovereign Council Reasoner. You have access to a Python Code Execution Sandbox.
We want to verify the dynamic range scaling equations and check shape compatibility for our ONNX model.

Here is the local metadata from our ONNX model:
{json.dumps(onnx_info, indent=2)}

Below is the complete raw telemetry JSON file containing the actual array of target values predicted by the model:
{raw_json_data}

Unmastered Reference:
- Unmastered RMS for SCAR-red strobe: 0.0740 (-22.61 dB)
- Gold Chris Lake Baseline Target Mean RMS: 0.3160 (-10.01 dB)

TASK:
1. Write a Python script to parse the provided raw JSON data in your sandbox. Extract the list of model-predicted RMS targets (or trajectory parameters from the sidecar metrics).
2. In the sandbox, use NumPy to calculate:
   - The mean, variance, and standard deviation of the predicted targets.
   - The makeup gain curve using the formula: gain_db = 20 * log10(target_rms) - 20 * log10(0.0740)
3. Check the calculated gain values:
   - Identify if any values exceed safe boundaries (e.g., gain > 18dB or gain < -12dB).
   - Propose an optimized clipping or blending formula (such as blending 70% target with 30% baseline) to prevent transient distortion.
4. Output the sandbox execution print logs and your final analysis.
"""

client = genai.Client()
print("Sending query to Gemini 2.5 Flash with Code Execution sandbox tool...")
try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(code_execution=types.ToolCodeExecution())]
        )
    )
    print("\n=== SANDBOX REPORT ===")
    print(response.text)
    
    with open(gemma_sandbox_out, "w", encoding="utf-8") as f:
        f.write(response.text)
    print(f"\nSaved sandbox report successfully to: {gemma_sandbox_out}")
except Exception as e:
    print(f"Error: {e}")
