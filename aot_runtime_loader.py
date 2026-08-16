"""
SOVEREIGN AOT RUNTIME LOADER
============================
Instantly loads pre-compiled AOT binaries (.dll on Windows, .so on Linux).
Zero runtime JIT compilation, zero GIL lockups, sub-microsecond execution.
"""

import ctypes
import os
import sys
import platform
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IS_WINDOWS = platform.system() == "Windows"
EXT = ".dll" if IS_WINDOWS else ".so"

KERNEL_BIN = os.path.join(BASE_DIR, f"sovereign_aot_kernel{EXT}")
BENCH_BIN = os.path.join(BASE_DIR, f"sovereign_real_benchmark{EXT}")

print(f"⚡ [AOT LOADER] Target Platform: {platform.system()} ({platform.machine()})")

# Load AOT Kernel
if os.path.exists(KERNEL_BIN):
    t0 = time.perf_counter_ns()
    kernel_lib = ctypes.CDLL(KERNEL_BIN)
    t1 = time.perf_counter_ns()
    print(f"✅ Loaded AOT Binary: {KERNEL_BIN} in {(t1-t0)/1000.0:.2f} µs")
else:
    print(f"⚠️ AOT Binary missing at {KERNEL_BIN}. Run AOT_BUILD_ALL_WINDOWS.bat to compile.")

# Load AOT Benchmark Library
if os.path.exists(BENCH_BIN):
    t0 = time.perf_counter_ns()
    bench_lib = ctypes.CDLL(BENCH_BIN)
    t1 = time.perf_counter_ns()
    print(f"✅ Loaded AOT Binary: {BENCH_BIN} in {(t1-t0)/1000.0:.2f} µs")
else:
    print(f"⚠️ AOT Binary missing at {BENCH_BIN}. Run AOT_BUILD_ALL_WINDOWS.bat to compile.")
