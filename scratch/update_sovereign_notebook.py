import nbformat

nb_path = r'C:\WEB CASE STUDY\Sovereign_Mastering_Audit_Notebook.ipynb'
nb = nbformat.read(nb_path, as_version=4)

markdown_cell = nbformat.v4.new_markdown_cell("""## ⚡ Cell 4: Native C++ High-Performance Rendering Engine (LLVM Clang / CMake)

This cell compiles and executes the **Sovereign Native C++ DSP Rendering Engine** (`sovereign_render.cpp`) built with **LLVM Clang** and **Ninja**. It renders audio trajectory curves at native C++ memory speed with sample-accurate slew-rate smoothing.""")

code_cell = nbformat.v4.new_code_cell("""import os
import subprocess

cpp_source = r"C:\\WEB CASE STUDY\\sovereign_render.cpp"
cmake_lists = r"C:\\WEB CASE STUDY\\CMakeLists.txt"
curves_file = r"C:\\WEB CASE STUDY\\test_curves.csv"
input_audio = r"C:\\WEB CASE STUDY\\sovereign_30s_capture.wav"

print("[1/3] Verifying C++ Source and CMake Toolchain...")
assert os.path.exists(cpp_source), f"Missing C++ source: {cpp_source}"
assert os.path.exists(cmake_lists), f"Missing CMakeLists.txt: {cmake_lists}"

print("[2/3] Building C++ Binary with CMake + Ninja (Clang)... ")
build_cmd = ["wsl", "bash", "-c", "cd '/mnt/c/WEB CASE STUDY' && CC=clang CXX=clang++ cmake -B build_wsl -G Ninja && cmake --build build_wsl"]
res = subprocess.run(build_cmd, capture_output=True, text=True)
print(res.stdout)
if res.returncode != 0:
    print("Build Error:", res.stderr)

print("[3/3] Executing Native C++ Audio Rendering Engine...")
run_cmd = ["wsl", "bash", "-c", f"cd '/mnt/c/WEB CASE STUDY' && ./build_wsl/SovereignAudioIngest input.wav {os.path.basename(curves_file)} output.wav"]
run_res = subprocess.run(run_cmd, capture_output=True, text=True)
print(run_res.stdout)
""")

nb.cells.extend([markdown_cell, code_cell])
nbformat.write(nb, nb_path)
print("Successfully appended Cell 4 to Sovereign Mastering Audit Notebook!")
