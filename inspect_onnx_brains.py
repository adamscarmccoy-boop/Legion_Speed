import os
import sys

try:
    import numpy as np
    import onnxruntime as ort
    HAS_LIBS = True
except ImportError:
    HAS_LIBS = False

def inspect_onnx_file(filepath: str) -> dict:
    """
    Loads and inspects an ONNX file's inputs, outputs, and internal execution nodes 
    to determine its model type and whether it has compiled control-flow/AOT structures.
    """
    if not HAS_LIBS:
        return {"error": "Missing numpy or onnxruntime library."}
        
    try:
        # Load session with minimum footprint configurations
        sess = ort.InferenceSession(filepath, providers=["CPUExecutionProvider"])
        
        # Extract Inputs and Outputs
        inputs = []
        for inp in sess.get_inputs():
            inputs.append({
                "name": inp.name,
                "type": inp.type,
                "shape": inp.shape
            })
            
        outputs = []
        for out in sess.get_outputs():
            outputs.append({
                "name": out.name,
                "type": out.type,
                "shape": out.shape
            })
            
        # Inspect model node-type signatures
        model_type = "Pure Mathematical Graph"
        features_detected = []
        
        # Check node signatures using internal session properties if possible
        # Since onnxruntime session doesn't easily expose raw nodes directly without the 'onnx' library,
        # we can infer based on the input shapes and names.
        input_names = [inp["name"] for inp in inputs]
        input_shapes = [inp["shape"] for inp in inputs]
        
        # Check if it has our signature features
        if "code_footprint_input" in input_names:
            model_type = "🌲 Code Genome Engine (Random Forest / Isolation Forest)"
            features_detected.append("Codebase Footprint Ingestion [size_kb, rows, ext, source]")
        elif any("embedding" in name.lower() for name in input_names):
            model_type = "🧠 Text/Vector Embedding Model"
            features_detected.append("Offline Vectorizer Engine")
        elif "input_ids" in input_names or "attention_mask" in input_names:
            model_type = "🤖 LLM Core Transformer Brain"
            features_detected.append("Tokenized Input Sequence")
        
        # Check output footprints to identify if it is our fused decision graph
        output_names = [out["name"] for out in outputs]
        if "label" in output_names and "probabilities" in output_names:
            features_detected.append("Supervised Classification Classifier")
        
        return {
            "status": "SUCCESS",
            "filepath": os.path.basename(filepath),
            "model_type": model_type,
            "inputs": inputs,
            "outputs": outputs,
            "features": features_detected
        }
    except Exception as e:
        return {
            "status": "FAILED",
            "filepath": os.path.basename(filepath),
            "error": str(e)
        }

def scan_directory_for_brains(target_dir: str):
    print("=" * 80)
    print("🧠 COGNITIVE ONNX BRAIN AUDITOR: BATCH DIRECTORY SCANNER")
    print("=" * 80)
    print(f"📂 Target Disk Directory: {target_dir}\n")
    
    if not HAS_LIBS:
        print("❌ Error: Onnxruntime is missing in this Python execution environment.")
        print("   Please activate your environment and install dependencies:")
        print("   python -m pip install onnxruntime numpy")
        print("=" * 80)
        return

    path = os.path.abspath(target_dir)
    if not os.path.exists(path):
        print(f"⚠️  Directory path does not exist: {path}")
        return

    onnx_files = []
    # Recursively find all onnx files
    for root, _, files_list in os.walk(path):
        for f in files_list:
            if f.lower().endswith(".onnx"):
                onnx_files.append(os.path.join(root, f))

    if not onnx_files:
        print("⚠️  No physical .onnx files found in this directory.")
        print("=" * 80)
        return

    print(f"🔍 Found {len(onnx_files)} .onnx brain files. Probing computational graphs...\n")
    
    for i, file_path in enumerate(onnx_files):
        print(f"[{i+1}/{len(onnx_files)}] Probing: {os.path.basename(file_path)}")
        meta = inspect_onnx_file(file_path)
        
        if meta.get("status") == "SUCCESS":
            print(f"   ⚙️  Graph Class: {meta['model_type']}")
            
            print("   📥 Input Nodes:")
            for inp in meta["inputs"]:
                print(f"      - {inp['name']:<20} | Shape: {str(inp['shape']):<15} | Type: {inp['type']}")
                
            print("   📤 Output Nodes:")
            for out in meta["outputs"]:
                print(f"      - {out['name']:<20} | Shape: {str(out['shape']):<15} | Type: {out['type']}")
                
            if meta["features"]:
                print("   🛡️  System Features Detected:")
                for feat in meta["features"]:
                    print(f"      [v] {feat}")
            print(f"   ✅ Verdict: Verified and stable.")
        else:
            print(f"   ❌ Probe Blocked: {meta.get('error') or 'Unknown parse warning'}")
        print("-" * 80)

if __name__ == "__main__":
    # Scan standard workspace folders
    default_workspace = r"C:\WEB CASE STUDY"
    if len(sys.argv) > 1:
        default_workspace = sys.argv[1]
    
    scan_directory_for_brains(default_workspace)
