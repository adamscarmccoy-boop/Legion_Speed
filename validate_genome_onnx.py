import os
import sys
import time
import socket
import logging
import traceback
import sysconfig
from pathlib import Path

# ==============================================================================
# SOVEREIGN LIFE-CYCLE STABILIZER (AUTO-INJECTED)
# Prevents dangling stdout/stdio pipes and GCS registry locks on Windows exit
# ==============================================================================
import atexit
import signal

def clean_exit_handler(*args, **kwargs):
    import sys
    sys.stderr.write("\n[LMS LIFECYCLE] Exit triggered. Flushing system streams...\n")
    sys.stderr.flush()
    try:
        import ray
        if ray.is_initialized():
            sys.stderr.write("[LMS LIFECYCLE] Active Ray session detected. Disconnecting...\n")
            ray.shutdown()
    except Exception:
        pass
    # Avoid raising SystemExit inside an atexit callback (which causes RuntimeWarnings)
    if args and isinstance(args[0], int):
        sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================


# =============================================================================
# 1. CORE SYSTEM ENVIRONMENT STABILIZERS
# =============================================================================
os.environ["RAY_gcs_rpc_server_reconnect_timeout_s"] = "120"
os.environ["RAY_memory_monitor_refresh_ms"] = "250"
os.environ["RAY_DEDUP_LOGS"] = "0"
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

# Set up logging specifically for standard error to protect standard output protocols
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | [GENOME VALIDATOR] | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("GenomeValidator")

# Ensure proper library loading of Ray C++ bindings on Windows platforms
try:
    purelib_path = Path(sysconfig.get_paths()["purelib"])
    dll_dir = purelib_path / "ray" / "libs"
    if dll_dir.exists():
        os.add_dll_directory(dll_dir)
    elif (purelib_path / "ray.libs").exists():
        os.add_dll_directory(purelib_path / "ray.libs")
except Exception as e:
    log.warning(f"Native Windows DLL directory routing bypassed: {e}")

# =============================================================================
# 2. RESOLVING AND IMPORTING DISTRIBUTED INFRASTRUCTURE
# =============================================================================
try:
    import numpy as np
    import onnxruntime as ort
except ImportError as imp_err:
    log.error("[-] Missing local scientific runtimes. Run 'pip install numpy onnxruntime'.")
    sys.exit(1)

try:
    import ray
except ImportError:
    log.error("[-] Missing Ray Core SDK. Run 'pip install ray'.")
    sys.exit(1)

# =============================================================================
# 3. HIGH-PERFORMANCE DISTRIBUTED ONNX REASONING ACTOR
# =============================================================================
@ray.remote(
    max_restarts=-1,         # Infinite self-healing lifecycle restarts
    max_task_retries=-1,     # Auto-retry pending queued queries
    namespace="legion"       # Fixed namespace to prevent cluster isolation
)
class SovereignGenomeInferenceActor:
    """
    Stateful Ray Actor executing sub-millisecond local predictions using your 
    newly compiled Code Genome Random Forest model over onnxruntime.
    """
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.session = None
        self.input_name = None
        self.output_name = None
        self._initialize_onnx()

    def _initialize_onnx(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"ONNX Model not found at expected path: {self.model_path}")
        
        # Load the serialized computation graph into CPU Execution space
        self.session = ort.InferenceSession(self.model_path, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = [output.name for output in self.session.get_outputs()]
        log.info(f"🧬 ONNX Engine bound successfully. Input Node: '{self.input_name}' | Outputs: {self.output_name}")

    def evaluate_footprint(self, size_kb: float, rows: int, encoded_ext: float, encoded_source: float) -> dict:
        """
        Processes file metadata footprints through the ONNX classifier.
        Bypasses memory allocation boundaries by evaluating arrays in-place.
        """
        # Formulate a structured 1x4 float matrix matching the scaler footprint schema
        input_data = np.array([[size_kb, float(rows), encoded_ext, encoded_source]], dtype=np.float32)
        
        start_t = time.perf_counter()
        raw_outputs = self.session.run(self.output_name, {self.input_name: input_data})
        latency_ms = (time.perf_counter() - start_t) * 1000.0

        # Output formatting matching classification mappings
        predicted_label = int(raw_outputs[0][0])
        probabilities = raw_outputs[1][0] if len(raw_outputs) > 1 else {}

        return {
            "predicted_class": predicted_label,
            "probabilities": {int(k): float(v) for k, v in probabilities.items()} if isinstance(probabilities, dict) else str(probabilities),
            "inference_latency_ms": latency_ms
        }

# =============================================================================
# 4. BENCHMARK AND VALIDATION SUITE
# =============================================================================
def run_validation_sequence():
    log.info("=" * 80)
    log.info("🧬 COGNITIVE GENOME ONNX RUNTIME VERIFICATION SUITE")
    log.info("=" * 80)

    ONNX_MODEL_PATH = r"C:\WEB CASE STUDY\mastered_output\code_genome_brain.onnx"
    
    # Check if physical ONNX exists on disk
    if not os.path.exists(ONNX_MODEL_PATH):
        log.error(f"[-] Physical model brain is missing at: {ONNX_MODEL_PATH}")
        log.error("[!] Please run your Code Forest Engine compilation script first to export the genome model!")
        sys.exit(1)

    log.info(f"[1/4] Attaching to GCS Ray Cluster under 'legion' namespace...")
    try:
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        log.info("✅ Connected to live Ray GCS under 'legion' registry plane.")
    except Exception as cluster_err:
        log.warning(f"[-] Auto-attachment failed: {cluster_err}")
        log.info("[*] Spawning a clean single-node loopback cluster for local test validation...")
        ray.init(namespace="legion", ignore_reinit_error=True)
        log.info("✅ Local testing cluster initialized.")

    log.info(f"[2/4] Deploying persistent 'GenomeONNXAgent' into shared cluster memory...")
    try:
        # Check if an instance is already registered to prevent GCS leaks
        inference_actor = ray.get_actor("SovereignGenomeAgent", namespace="legion")
        log.info("💎 Persistent 'SovereignGenomeAgent' handle located. Running hot swap...")
    except ValueError:
        log.info("[-] Instantiating new detached inference actor on cluster...")
        inference_actor = SovereignGenomeInferenceActor.options(
            name="SovereignGenomeAgent",
            lifetime="detached"
        ).remote(model_path=ONNX_MODEL_PATH)
        log.info("✅ Detached 'SovereignGenomeAgent' deployed into Ray namespace successfully.")

    log.info("[3/4] Dispatching concurrent pre-flight payload footprints...")
    # Simulate a set of 3 different code footprint footprints
    # Features: [size_kb, rows, encoded_ext, encoded_source]
    test_payloads = {
        "mcp_swarm_gateway.py": [45.2, 380, 1.0, 0.0],  # Standard Script
        "legion_memory.parquet": [1024.0, 12000, 2.0, 1.0], # Parquet audit block
        "broken_config.json": [0.1, 4, 3.0, 2.0] # Lightweight JSON config
    }

    futures = {}
    for filename, features in test_payloads.items():
        futures[filename] = inference_actor.evaluate_footprint.remote(
            size_kb=features[0],
            rows=features[1],
            encoded_ext=features[2],
            encoded_source=features[3]
        )

    log.info("[4/4] Harvesting execution matrices and profiling jitter...")
    print("\n" + "=" * 80)
    print("⚡ BARE-METAL SUB-MILLISECOND ONNX INFERENCE BENCHMARK:")
    print("=" * 80)
    
    total_latency = 0.0
    successful_runs = 0
    
    for filename, future in futures.items():
        try:
            res = ray.get(future, timeout=5.0)
            lat = res["inference_latency_ms"]
            total_latency += lat
            successful_runs += 1
            print(f"📄 File: {filename:<25} | Class: {res['predicted_class']} | Latency: {lat:.4f} ms")
        except Exception as execution_crash:
            log.error(f"❌ Failed processing transaction for {filename}: {execution_crash}")

    if successful_runs > 0:
        avg_lat = total_latency / successful_runs
        print("-" * 80)
        print(f"📊 Mean Cluster Intercept Latency: {avg_lat:.4f} ms")
        print(f"🚀 Estimated Local Inference Throughput: {1000.0 / avg_lat:.1f} classifications/sec")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    run_validation_sequence()