import os
import sys
import time
import glob
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

# =============================================================================
# 1. FAULT-TOLERANT LOCAL RUNTIME DEPS
# =============================================================================
try:
    import onnxruntime as ort
    from openai import OpenAI
except ImportError:
    print("[-] Missing required local packages. Run: pip install onnxruntime openai pandas pyarrow scikit-learn")
    sys.exit(1)

# Target Windows workspaces matching your layout
WORKSPACE_C = r"C:\\WEB CASE STUDY"
WORKSPACE_STUDIES = r"C:\\STUDIES"

if not os.path.exists(WORKSPACE_C):
    WORKSPACE_C = os.getcwd()
if not os.path.exists(WORKSPACE_STUDIES):
    WORKSPACE_STUDIES = os.getcwd()

# =============================================================================
# 2. LOCAL STATIC FILE DISCOVERY AND INGESTION
# =============================================================================
def discover_system_files():
    parquet_files = []
    onnx_files = []
    search_paths = [WORKSPACE_C, WORKSPACE_STUDIES]
    
    for path in search_paths:
        if not os.path.exists(path):
            continue
        for f in glob.glob(os.path.join(path, "**", "*.parquet"), recursive=True):
            parquet_files.append(os.path.abspath(f))
        for f in glob.glob(os.path.join(path, "**", "*.onnx"), recursive=True):
            onnx_files.append(os.path.abspath(f))
            
    return list(set(parquet_files)), list(set(onnx_files))

def ingest_and_normalize_parquet(file_path: str) -> np.ndarray:
    try:
        df = pd.read_parquet(file_path)
        if df.empty:
            return np.empty((0, 4))
            
        if "size_kb" not in df.columns:
            if "size_bytes" in df.columns:
                df["size_kb"] = df["size_bytes"] / 1024.0
            else:
                df["size_kb"] = 1.0
                
        if "rows" not in df.columns:
            df["rows"] = float(len(df))
                
        if "encoded_ext" not in df.columns:
            if "ext" in df.columns:
                try:
                    le = LabelEncoder()
                    df["encoded_ext"] = le.fit_transform(df["ext"].astype(str)).astype(float)
                except Exception:
                    df["encoded_ext"] = 0.0
            else:
                df["encoded_ext"] = df.index.map(lambda x: float(hash(str(x)) % 10))
                
        if "encoded_source" not in df.columns:
            if "source" in df.columns:
                try:
                    le = LabelEncoder()
                    df["encoded_source"] = le.fit_transform(df["source"].astype(str)).astype(float)
                except Exception:
                    df["encoded_source"] = 0.0
            else:
                df["encoded_source"] = 1.0
                
        return df[["size_kb", "rows", "encoded_ext", "encoded_source"]].to_numpy()
        
    except Exception as e:
        print(f"⚠️  [INGESTION] Skipping {os.path.basename(file_path)}: {e}")
        return np.empty((0, 4))

# =============================================================================
# 3. DIRECT LOCAL INFERENCE SESSION RUNNER (CONTEXT SWITCHER FOR DATA COEXISTENCE)
# =============================================================================
class LocalSweepSession:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model_name = os.path.basename(model_path)
        self.session = None
        self.inputs = []
        self.expected_features = 4
        self.initialized = False
        
        # Switch context to the model folder to let ONNX natively load .data files
        orig_cwd = os.getcwd()
        model_dir = os.path.dirname(os.path.abspath(model_path))
        try:
            if model_dir:
                os.chdir(model_dir)
            self.session = ort.InferenceSession(self.model_name, providers=["CPUExecutionProvider"])
            self.inputs = self.session.get_inputs()
            self.output_names = [out.name for out in self.session.get_outputs()]
            
            # Determine overall expected features across all input nodes
            total_feats = 0
            for inp in self.inputs:
                shape = inp.shape
                if len(shape) > 1 and isinstance(shape[1], int):
                    total_feats += shape[1]
                else:
                    total_feats += 1
            
            self.expected_features = total_feats if total_feats > 0 else 4
            self.initialized = True
        except Exception as e:
            print(f"❌ [ONNX FAIL] {self.model_name}: {e}")
        finally:
            os.chdir(orig_cwd)

    def run_sweep(self, base_features: np.ndarray, duration_sec: float) -> dict:
        if not self.initialized:
            return {"runs": 0, "status": "FAILED"}
            
        run_count = 0
        best_score = -9999.0
        best_params = None
        
        start_time = time.perf_counter()
        end_time = start_time + duration_sec
        
        # Ensure base_features is a 2D numpy array
        features_matrix = np.array(base_features, dtype=np.float32)
        if len(features_matrix.shape) == 1:
            features_matrix = np.expand_dims(features_matrix, axis=0)
            
        while time.perf_counter() < end_time:
            # High-speed AOT Mutator
            perturbations = np.random.uniform(0.9, 1.1, size=features_matrix.shape).astype(np.float32)
            mutated_batch = features_matrix * perturbations
            
            # Map columns of mutated_batch to individual ONNX input nodes dynamically
            input_feed = {}
            col_offset = 0
            for inp in self.inputs:
                shape = inp.shape
                if len(shape) > 1 and isinstance(shape[1], int):
                    num_feats = shape[1]
                else:
                    num_feats = 1
                
                # Slice columns safely matching this input node's features
                end_offset = min(col_offset + num_feats, mutated_batch.shape[1])
                slice_data = mutated_batch[:, col_offset:end_offset]
                
                # If the slice size is too narrow for this input node, pad with zeros
                if slice_data.shape[1] < num_feats:
                    padding = np.zeros((slice_data.shape[0], num_feats - slice_data.shape[1]), dtype=np.float32)
                    slice_data = np.hstack((slice_data, padding)).astype(np.float32)
                
                # Ensure correct format
                slice_data = np.ascontiguousarray(slice_data, dtype=np.float32)
                input_feed[inp.name] = slice_data
                col_offset += num_feats
                
            # Execute sub-millisecond forward pass
            try:
                raw_outputs = self.session.run(self.output_names, input_feed)
                predictions = raw_outputs[0]
                run_count += len(mutated_batch)
                
                # Track best performance mapping
                max_idx = np.argmax(predictions)
                max_val = float(predictions.flat[max_idx])
                if max_val > best_score:
                    best_score = max_val
                    best_params = mutated_batch[max_idx // predictions.shape[-1] if len(predictions.shape) > 1 else max_idx]
            except Exception as e:
                return {
                    "runs": run_count,
                    "status": "CRASHED",
                    "error": str(e)
                }
                
        return {
            "runs": run_count,
            "status": "SUCCESS",
            "best_score": best_score,
            "best_params": list(best_params) if best_params is not None else []
        }

# =============================================================================
# 4. MASTER ENGINE
# =============================================================================
def main():
    print("=" * 80)
    print("⚡ ZERO-RAY LOCAL AOT SWEEP & LM STUDIO DIRECT PIPELINE - V2")
    print("   Fixed Dynamic Feature & Input Node Mapping (No More ValueError)")
    print("=" * 80)

    # Step 1: Discover files
    print("\n🔍 [1/3] Scanning local directories for Parquets and ONNX models...")
    parquet_paths, onnx_paths = discover_system_files()
    print(f"   -> Located {len(parquet_paths)} Parquet files.")
    print(f"   -> Located {len(onnx_paths)} ONNX neural models.")

    # Step 2: Execute In-Memory Swaps Sequential (Microseconds execution)
    print("\n🧬 [2/3] Performing local AOT optimization sweeps (No middleware overhead)...")
    sweep_duration_seconds = 2.0 # Keep it tight for instant response
    results_matrix = []
    
    for opath in onnx_paths:
        mname = os.path.basename(opath)
        session = LocalSweepSession(opath)
        if not session.initialized:
            continue
            
        for ppath in parquet_paths:
            pname = os.path.basename(ppath)
            feats = ingest_and_normalize_parquet(ppath)
            if len(feats) == 0:
                continue
                
            sweep_res = session.run_sweep(feats, sweep_duration_seconds)
            if sweep_res["status"] == "SUCCESS":
                results_matrix.append({
                    "model": mname,
                    "table": pname,
                    "runs": sweep_res["runs"],
                    "best_score": sweep_res["best_score"],
                    "best_params": sweep_res["best_params"]
                })
                print(f"   ✅ Swept {mname:<25} x {pname:<25} | Runs: {sweep_res['runs']:,} | Best: {sweep_res['best_score']:.4f}")
            elif sweep_res["status"] == "CRASHED":
                print(f"   ⚠️  Skipped combination {mname} x {pname}: {sweep_res.get('error')}")

    if not results_matrix:
        print("❌ [FAIL] No successful model-table combinations executed.")
        return

    # Sort to find the absolute winning configuration
    winner = max(results_matrix, key=lambda x: x["best_score"])
    print("\n🏆 OPTIMIZATION SWEEP COMPLETE!")
    print(f"   Winner Model: {winner['model']}")
    print(f"   Winner Table: {winner['table']}")
    print(f"   Total Runs  : {sum(r['runs'] for r in results_matrix):,} trials executed.")

    # Step 3: Direct API handshake to LM Studio via lightweight OpenAI client
    print("\n📡 [3/3] Dispatched digested telemetry to LM Studio (Port 1234)...")
    try:
        client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")
        
        # Build prompt COMPLETELY BEFORE LLM - Zero raw JSON string mappings
        system_prompt = (
            "You are the Legion Sovereign Intelligence. You translate complex optimization telemetry "
            "into human-readable producer directives. Always be precise, authoritative, and direct."
        )
        
        user_prompt = (
            f"We have executed an AOT optimization sweep over {len(parquet_paths)} parquet tables and {len(onnx_paths)} models.\\n\\n"
            f"The champion configuration emerged from model '{winner['model']}' using source table '{winner['table']}'.\\n"
            f"Optimal Fitness Score: {winner['best_score']:.4f}\\n"
            f"Calibrated Feature Vectors: {winner['best_params']}\\n\\n"
            f"Translate these raw performance numbers into a clean, professional, expert Tech House production directive "
            f"concerning BPM and mastering profiles."
        )
        
        # Call LLM Exactly Once (No recursive round-tripping)
        start_t = time.time()
        response = client.chat.completions.create(
            model="nvidia/nemotron-3-nano-4b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        latency = (time.time() - start_t) * 1000
        
        print(f"\n📥 FINAL ANALYSIS RECEIVED FROM LM STUDIO ({latency:.2f} ms)")
        print("=" * 80)
        print(response.choices[0].message.content)
        print("=" * 80)
        
    except Exception as api_err:
        print(f"❌ [API CONNECT FAILED] Could not connect to LM Studio on Port 1234: {api_err}")
        print("   Make sure LM Studio's Local Server is turned ON and running nemotron-3-nano.")

if __name__ == "__main__":
    main()
