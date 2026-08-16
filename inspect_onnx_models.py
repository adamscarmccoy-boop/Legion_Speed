import onnx
import os

model_paths = [
    r"C:\WEB CASE STUDY\sovereign_big_brain_exhaustive.onnx",
    r"C:\WEB CASE STUDY\sovereign_bridge_v1.onnx",
    r"C:\WEB CASE STUDY\omni_master_brain_v1.onnx",
    r"C:\WEB CASE STUDY\fretflow_omni_v4.onnx",
    r"C:\WEB CASE STUDY\real_data_brain.onnx",
    r"C:\WEB CASE STUDY\dna_brain.onnx"
]

print("=" * 60)
print(" ONNX MODEL INSPECTION")
print("=" * 60)

for path in model_paths:
    if not os.path.exists(path):
        continue
    
    try:
        model = onnx.load(path)
        print(f"\n--- MODEL: {os.path.basename(path)} ---")
        
        # Inputs
        for input_tensor in model.graph.input:
            name = input_tensor.name
            try:
                dims = [d.dim_value if d.HasField('dim_value') else d.dim_param for d in input_tensor.type.tensor_type.shape.dim]
                print(f"  Input: {name} | Shape: {dims}")
            except Exception:
                print(f"  Input: {name} | Shape: Unknown")
                
        # Outputs
        for output_tensor in model.graph.output:
            name = output_tensor.name
            try:
                dims = [d.dim_value if d.HasField('dim_value') else d.dim_param for d in output_tensor.type.tensor_type.shape.dim]
                print(f"  Output: {name} | Shape: {dims}")
            except Exception:
                print(f"  Output: {name} | Shape: Unknown")
                
    except Exception as e:
        print(f"Error loading {path}: {e}")
