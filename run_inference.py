import sys
import numpy as np
import onnxruntime as ort

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# The 7 classes the model learned, in alphabetical order (how LabelEncoder sorts them):
CLASSES = ['.aif', '.aiff', '.flac', '.json', '.m4a', '.mp3', '.wav']

# Note: In a production app, we would load the exact StandardScaler object saved during 
# training. Since we didn't save it in the engine script, we'll apply a manual 
# rough scaling here just to demonstrate how the ONNX model is used for inference.
APPROX_MEAN = np.array([1000.0, 10.0]) 
APPROX_STD = np.array([5000.0, 100.0])

def run_inference(size_kb, rows):
    # 1. Load the ONNX model
    onnx_path = r"C:\WEB CASE STUDY\mastered_output\code_genome_brain.onnx"
    sess = ort.InferenceSession(onnx_path)
    
    # 2. Prepare the input data
    raw_input = np.array([[size_kb, rows]], dtype=np.float32)
    
    # 3. Scale it (approximate)
    scaled_input = (raw_input - APPROX_MEAN) / APPROX_STD
    
    # 4. Run through the ONNX model
    input_name = sess.get_inputs()[0].name
    label_name = sess.get_outputs()[0].name
    
    predictions = sess.run([label_name], {input_name: scaled_input})
    
    # 5. Decode the prediction index back to the string extension
    predicted_class_index = int(predictions[0][0])
    predicted_ext = CLASSES[predicted_class_index]
    
    return predicted_ext

if __name__ == "__main__":
    print("🔍 ONNX INFERENCE TEST - CODE GENOME 🔍")
    print("-" * 60)
    
    # Let's test it on some hypothetical files to see what it predicts
    test_cases = [
        {"name": "App.py equivalent", "size": 15.0, "rows": 450},     # Small file, lots of rows
        {"name": "Massive Song", "size": 65000.0, "rows": 0},         # Huge file, 0 rows 
        {"name": "Small Sound Effect", "size": 250.0, "rows": 0},     # Small file, 0 rows
        {"name": "Data Export", "size": 8000.0, "rows": 120000}       # Medium file, tons of rows
    ]
    
    for case in test_cases:
        ext = run_inference(case["size"], case["rows"])
        print(f"[{case['name']:<20}] Size: {case['size']:8.1f} KB | Rows: {case['rows']:6} => Predicted Type: {ext}")
