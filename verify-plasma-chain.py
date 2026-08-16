import os
import sys
import time
import numpy as np
import pyarrow as pa
import ray
from pydantic import BaseModel
from typing import Any, Dict

# Standard Windows DLL and path routing fix to bypass Python 3.14 hijacks
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


try:
    purelib_path = Path(sysconfig.get_paths()["purelib"])
    dll_dir = purelib_path / "ray" / "libs"
    if dll_dir.exists():
        os.add_dll_directory(dll_dir)
    else:
        os.add_dll_directory(purelib_path / "ray.libs")
except Exception as e:
    print(f"DLL patch warning (can be ignored if Ray imports successfully): {e}")

# Explicitly insert site-packages
sys.path.insert(0, r"C:\WEB CASE STUDY\.venv\Lib\site-packages")

# ==============================================================================
# 🧬 PYDANTIC SYSTEM STATE & SERIALIZATION SAFEGUARDS
# ==============================================================================

class LangGraphSafeState(BaseModel):
    """
    Pydantic Model demonstrating how to safely route Ray ObjectRefs through 
    LangGraph State without breaking serialization or throwing schema validation errors.
    """
    node_id: str
    target_crest: float = 5.69
    target_lufs: float = -13.9
    
    # CRUCIAL: Do not store raw ray.ObjectRef directly. It is a C++ memory wrapper
    # and will crash standard serialization / Pydantic models.
    # Instead, we serialize the 20-byte Plasma Reference as a HEX string.
    plasma_ref_hex: str
    
    class Config:
        arbitrary_types_allowed = True

    def get_object_ref(self) -> ray.ObjectRef:
        """ Reconstructs the zero-copy C++ pointer from the hex identifier """
        return ray.ObjectRef(bytes.fromhex(self.plasma_ref_hex))


# ==============================================================================
# 🛰️ THE BENCHMARK & DIAGNOSTIC CORE
# ==============================================================================

def run_diagnostic():
    print("=" * 80)
    print("🛰️  SYSTEM-WIDE PLASMA & LANGGRAPH CHAIN DIAGNOSTIC SUITE")
    print("=" * 80)
    
    # 1. Check Python Interpreter and site-packages alignment
    print(f"\n[STEP 1] Environment Verification:")
    print(f" - Active Python Interpreter: {sys.executable}")
    print(f" - Python Version: {sys.version}")
    print(" - Package Site-Packages Paths:")
    for path in sys.path[:3]:
        print(f"   └── {path}")
        
    # 2. Ray Cluster Handshake
    print(f"\n[STEP 2] Ray Head Node Connection:")
    try:
        # Connect seamlessly using auto-discovery
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        print(" 🟢 SUCCESS: Connected to running Ray Head Node cluster!")
        print(f"   └── Cluster Nodes: {ray.nodes()}")
        print(f"   └── Cluster Resources: {ray.cluster_resources()}")
    except Exception as e:
        print(" ❌ FAULT: Could not reach the running head node.")
        print(f"   └── Error details: {e}")
        print("\n   [DIAGNOSIS] This occurs if your environment has partitioned ports.")
        print("   Ensure you ran: ray start --head --port=6379 before launching.")
        return

    # 3. Plasma Memory-Mapping Benchmarks (Zero-Copy)
    print(f"\n[STEP 3] Zero-Copy Memory Mapping Latency Test:")
    try:
        # Generate a mock 1024D Snowflake Vector Array (Batch Size 100)
        print(" - Generating 100x1024 float32 continuous array (Snowflake Mock)")
        mock_data = np.random.randn(100, 1024).astype(np.float32)
        
        # Ingest into Apache Arrow format
        t_arrow_0 = time.perf_counter()
        arrow_table = pa.Table.from_arrays([pa.array(mock_data.flatten())], names=["vector"])
        t_arrow_1 = time.perf_counter()
        arrow_latency = (t_arrow_1 - t_arrow_0) * 1000
        print(f"   └── Apache Arrow structuring latency: {arrow_latency:.4f} ms")

        # Push to Plasma Store
        t_plasma_0 = time.perf_counter()
        object_ref = ray.put(arrow_table)
        t_plasma_1 = time.perf_counter()
        plasma_write_latency = (t_plasma_1 - t_plasma_0) * 1000
        print(f"   └── Plasma Memory Ingestion (ray.put): {plasma_write_latency:.4f} ms")

        # Retrieve hex-encoded pointer
        hex_ref = object_ref.hex()
        print(f"   └── Plasma Object ID (Hex): {hex_ref}")
        
        # Pydantic State Mapping Test
        t_pydantic_0 = time.perf_counter()
        state = LangGraphSafeState(
            node_id="DSP_ALIGNED_INGEST_NODE",
            plasma_ref_hex=hex_ref
        )
        serialized_state = state.model_dump_json()
        t_pydantic_1 = time.perf_counter()
        pydantic_latency = (t_pydantic_1 - t_pydantic_0) * 1000
        print(f"   └── Pydantic State Serialization/Validation: {pydantic_latency:.4f} ms")
        
        # Simulate downstream node retrieving raw memory directly using pointer reconstruction
        t_read_0 = time.perf_counter()
        reconstructed_ref = state.get_object_ref()
        resolved_table = ray.get(reconstructed_ref)
        t_read_1 = time.perf_counter()
        read_latency = (t_read_1 - t_read_0) * 1000
        print(f"   └── Downstream Zero-Copy RAM Retrieval (ray.get): {read_latency:.4f} ms")
        
        print("\n" + "-"*80)
        total_zero_copy_overhead = plasma_write_latency + read_latency
        print(f" 🏁 VERDICT: Total shared-memory pointer overhead: {total_zero_copy_overhead:.4f} ms")
        print("   (Standard Python IPC serialization typically takes 100ms - 500ms for large tables)")
        print("-"*80)

    except Exception as e:
        print(f" ❌ FAULT during memory-mapping benchmarks: {e}")
        
    print("\nDiagnostic cycle complete.")

if __name__ == "__main__":
    run_diagnostic()