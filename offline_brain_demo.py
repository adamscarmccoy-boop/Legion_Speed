import pyarrow.parquet as pq
import onnxruntime as rt
import numpy as np
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("\n========================================================")
print("  🧠 CODE GENOME BRAIN: REAL DATA CLASSIFICATION RESULTS ")
print("========================================================\n")

try:
    table = pq.read_table(r"C:\WEB CASE STUDY\code_notebook_knowledge_audit.parquet")
    df = table.to_pandas()
    
    sess = rt.InferenceSession(r"C:\WEB CASE STUDY\mastered_output\code_genome_brain.onnx", providers=['CPUExecutionProvider'])
    input_name = sess.get_inputs()[0].name
    label_name = sess.get_outputs()[0].name
    
    mean = np.array([2000.0, 50.0])
    std = np.array([5000.0, 200.0])
    categories = ["aif", "aiff", "flac", "json", "m4a", "mp3", "wav"]
    
    count = 0
    for _, row in df.iterrows():
        if count >= 15:
            break
            
        filename = str(row.get('filename', 'Unknown'))
        size_kb = float(row.get('size_kb', 0.0))
        rows = int(row.get('rows', 0))
        
        # Scale input and CAST TO FLOAT32
        raw_input = np.array([[size_kb, rows]], dtype=np.float32)
        scaled_input = ((raw_input - mean) / std).astype(np.float32)
        
        pred = sess.run([label_name], {input_name: scaled_input})
        pred_idx = int(pred[0][0])
        predicted_category = categories[pred_idx] if pred_idx < len(categories) else "unknown"
        
        print(f"📄 {filename[:40].ljust(40)} | Size: {size_kb:8.2f} KB | Rows: {rows:5d} => 🧬 PREDICTION: [{predicted_category.upper()}]")
        count += 1

    print("\n========================================================")
except Exception as e:
    print(f"Failed to read parquet or run inference: {e}")
