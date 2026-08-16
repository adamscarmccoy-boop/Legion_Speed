import time
import os
import sys

print("=== Gemma ONNX Isolation Test ===")
print(r"Checking path: C:\WEB CASE STUDY\gemma_onnx")

model_path = r"C:\WEB CASE STUDY\gemma_onnx"

if not os.path.exists(model_path):
    print(f"[ERROR] Model path NOT FOUND: {model_path}")
    sys.exit(1)

print("[*] Attempting to load model via onnxruntime_genai...")
t0 = time.perf_counter()

try:
    import onnxruntime_genai as og
    
    print("[*] Calling og.Model(model_path)...")
    model = og.Model(model_path)
    print("[+] Model object created successfully.")
    
    print("[*] Calling og.Tokenizer(model)...")
    tokenizer = og.Tokenizer(model)
    print("[+] Tokenizer initialized.")
    
    elapsed = time.perf_counter() - t0
    print(f"\n[SUCCESS] Model load completed in {elapsed:.2f} seconds.")
    
except Exception as e:
    print(f"\n[!!!] FAILED during isolation test!")
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    
    # Check if it's a memory issue
    if "out of memory" in str(e).lower() or "oom" in str(e).lower():
        print("\n[DIAGNOSIS] This is a GPU/System Memory error (OOM).")
    
    sys.exit(1)

print("\nTest finished. The model is loadable in isolation.")
