import onnxruntime as ort

# Load the ONNX model
model_path = "fretflow_omni_v4.onnx"
session = ort.InferenceSession(model_path)

# Dummy input: batch=1, 10 features (float32)
input_data = [[[0.5] * 10]]

# Run inference
outputs = session.run(None, {"omni_vector_v4": input_data})

# Outputs are in order: mastering_command_set, linear_2, linear_3
mastering_cmd, linear2, linear3 = outputs

print("Mastering command set:", mastering_cmd)
print("Linear 2:", linear2)
print("Linear 3:", linear3)