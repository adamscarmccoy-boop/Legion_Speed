import os
import subprocess
import sys

def build():
    sdk_base = r"C:\Program Files\Microsoft Visual Studio\18\Community\SDK\ScopeCppSDK\vc15"
    cl_exe = os.path.join(sdk_base, r"VC\bin\cl.exe")
    source_cpp = r"C:\Users\adams\Downloads\main.cpp"
    out_exe = r"C:\WEB CASE STUDY\legion_graph.exe"

    if not os.path.exists(cl_exe):
        print(f"[FAIL] cl.exe not found at: {cl_exe}")
        return False

    includes = [
        os.path.join(sdk_base, r"VC\include"),
        os.path.join(sdk_base, r"SDK\include\um"),
        os.path.join(sdk_base, r"SDK\include\shared"),
        os.path.join(sdk_base, r"SDK\include\ucrt"),
    ]

    libs = [
        os.path.join(sdk_base, r"VC\lib"),
        os.path.join(sdk_base, r"SDK\lib"),
        os.path.join(sdk_base, r"SDK\lib\ucrt"),
    ]

    inc_flags = " ".join([f'/I "{i}"' for i in includes if os.path.exists(i)])
    lib_flags = " ".join([f'/LIBPATH:"{l}"' for l in libs if os.path.exists(l)])

    # Setup environment PATH for mspdb/compiler DLLs
    env = os.environ.copy()
    bin_dir = os.path.join(sdk_base, r"VC\bin")
    env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")

    cmd = f'"{cl_exe}" /nologo /EHsc /std:c++17 /O2 "{source_cpp}" {inc_flags} /Fe:"{out_exe}" /link {lib_flags} ws2_32.lib'
    print("[BUILD] Compiling C++ bare-metal LangGraph State Machine...")
    print(f"[CMD] {cmd}\n")

    res = subprocess.run(cmd, env=env, capture_output=True, text=True, shell=True)
    print(res.stdout)
    if res.stderr:
        print("[STDERR]\n", res.stderr)

    if res.returncode == 0 and os.path.exists(out_exe):
        print(f"✨ [SUCCESS] Bare-metal executable compiled: {out_exe}")
        return True
    else:
        print(f"❌ [FAIL] Compilation failed with code {res.returncode}")
        return False

if __name__ == "__main__":
    success = build()
    sys.exit(0 if success else 1)
