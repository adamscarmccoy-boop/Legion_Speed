import os
import sys
import site
from setuptools import setup, Extension

engine_dir = os.path.dirname(os.path.abspath(__file__))
cpp_src = os.path.join(engine_dir, "sovereign_agent_runner.cpp")

# Auto-locate ONNX Runtime include and lib in site-packages
site_pkgs = site.getsitepackages()
ort_dir = None
for sp in site_pkgs:
    candidate = os.path.join(sp, "onnxruntime", "capi")
    if os.path.exists(candidate):
        ort_dir = candidate
        break

if not ort_dir:
    print("[ERROR] ONNX Runtime not found in Python site-packages. Run: pip install onnxruntime")
    sys.exit(1)

ort_inc = os.path.abspath(os.path.join(ort_dir, ".."))

module = Extension(
    "sovereign_agent_runner",
    sources=[cpp_src],
    include_dirs=[ort_inc],
    library_dirs=[ort_dir],
    libraries=["onnxruntime"],
    language="c++",
    extra_compile_args=["/std:c++17", "/EHsc"] if sys.platform == "win32" else ["-std=c++17"]
)

if __name__ == "__main__":
    sys.argv = ["compiledll.py", "build_ext", "--inplace"]
    print("[1/1] Compiling C++ ONNX Runner via setuptools...")
    setup(
        name="sovereign_agent_runner",
        version="1.0",
        description="Sovereign ONNX Compiled Agent Runner",
        ext_modules=[module]
    )
    print("\n[SUCCESS] Compiled native extension built successfully!")