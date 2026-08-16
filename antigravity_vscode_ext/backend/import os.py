import os
import sys
import platform
import subprocess
import importlib.util
from typing import List, Tuple

# ANSI escape codes for terminal formatting
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Initialize report registry
passes: List[str] = []
warnings: List[str] = []
failures: List[str] = []

def log_pass(msg: str):
    print(f"{Colors.GREEN}[✅ PASS]{Colors.ENDC} {msg}")
    passes.append(msg)

def log_warn(msg: str, action: str):
    print(f"{Colors.WARNING}[⚠️ WARN]{Colors.ENDC} {msg}\n   {Colors.BLUE}➔ Action:{Colors.ENDC} {action}")
    warnings.append(f"{msg} (Action: {action})")

def log_fail(msg: str, fix: str):
    print(f"{Colors.FAIL}[❌ FAIL]{Colors.ENDC} {msg}\n   {Colors.BOLD}➔ Fix:{Colors.ENDC} {fix}")
    failures.append(f"{msg} (Fix: {fix})")

def resolve_path(win_path: str) -> str:
    """Safely resolve C:\ paths to /mnt/c/ if running inside WSL."""
    if "microsoft-standard" in platform.uname().release.lower() and win_path.startswith("C:\\"):
        return win_path.replace("C:\\", "/mnt/c/").replace("\\", "/")
    return win_path

def check_system_and_wsl():
    print(f"\n{Colors.HEADER}=== 1. HARDWARE & OS DIAGNOSTICS ==={Colors.ENDC}")
    
    # OS / WSL Check
    uname_release = platform.uname().release.lower()
    is_wsl = "microsoft-standard" in uname_release
    if is_wsl:
        log_pass("WSL Environment Detected.")
    elif platform.system() == "Windows":
        log_pass("Native Windows Environment Detected.")
    else:
        log_warn("Running on non-Windows/non-WSL Linux.", "Ensure this is the correct target machine.")

    # CPU Check (Targeting exactly 12 CPUs as per architecture)
    cpu_count = os.cpu_count()
    if cpu_count is not None and cpu_count >= 12:
        log_pass(f"CPU Core Count: {cpu_count} (Meets >=12 requirement for Ray Plasma Store)")
    else:
        log_fail(f"CPU Core Count: {cpu_count}", "Allocate at least 12 physical/logical cores to this environment.")

def check_python_env():
    print(f"\n{Colors.HEADER}=== 2. PYTHON VIRTUAL ENVIRONMENT ==={Colors.ENDC}")
    
    # Python Version (Targeting 3.12.10 based on system logs)
    py_version = platform.python_version_tuple()
    if py_version == '3' and py_version[1] == '12':
        log_pass(f"Python Version: {platform.python_version()}")
    else:
        log_fail(f"Python Version: {platform.python_version()}", "Downgrade/Upgrade to Python 3.12.x to match Legion Architect constraints.")

    # Venv Check
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if in_venv:
        log_pass(f"Virtual Environment Active: {sys.prefix}")
        if ".venv" in sys.prefix:
            log_pass("Verified standard '.venv' nomenclature.")
        else:
            log_warn(f"Venv name is not '.venv'", "Check if this matches 'C:\\WEB CASE STUDY\\.venv'")
    else:
        log_fail("No Virtual Environment Active.", "Activate C:\\WEB CASE STUDY\\.venv\\Scripts\\activate before running tasks.")

def check_hard_paths():
    print(f"\n{Colors.HEADER}=== 3. LEGION ARCHITECTURE PATHS ==={Colors.ENDC}")
    
    critical_paths = {
        "Architect's Domain": r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline",
        "Producer's Domain": r"C:\WEB CASE STUDY",
        "Target Virtual Env": r"C:\WEB CASE STUDY\.venv",
        "Training Latents": r"C:\WEB CASE STUDY\training_latents",
        "Modelship Deploy (vLLM Qwen)": r"C:\WEB CASE STUDY\modelship\modelship-main"
    }

    for name, raw_path in critical_paths.items():
        eval_path = resolve_path(raw_path)
        if os.path.exists(eval_path):
            log_pass(f"Found {name}: {eval_path}")
        else:
            log_fail(f"Missing {name} at {eval_path}", f"Verify directory exists. If cloned recently, rebuild path.")

def check_cuda_components():
    print(f"\n{Colors.HEADER}=== 4. CUDA 13.3 UPDATE 1 METRICS ==={Colors.ENDC}")
    
    # Check nvidia-smi
    try:
        subprocess.run(["nvidia-smi"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        log_pass("NVIDIA Driver & nvidia-smi accessible.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        log_fail("nvidia-smi not found or failed.", "Ensure NVIDIA drivers are installed and passed through to WSL.")

    # Check NVCC Compiler Version (Target: 13.3.73)
    try:
        nvcc_output = subprocess.check_output(["nvcc", "--version"], universal_newlines=True)
        if "release 13.3" in nvcc_output:
            log_pass("CUDA NVCC Compiler is active and matches 13.3.x family.")
        else:
            log_warn("NVCC Compiler found, but version mismatch from 13.3.73.", "Verify nvcc version if C++ DSP compiles fail.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        log_fail("NVCC Compiler not found in PATH.", "Install CUDA Toolkit 13.3 Update 1 and add to PATH.")

def check_ray_and_vllm():
    print(f"\n{Colors.HEADER}=== 5. RAY CLUSTER & vLLM COMPATIBILITY ==={Colors.ENDC}")
    
    # Ray Check
    ray_version = None
    try:
        ray = importlib.import_module("ray")
        ray_version = ray.__version__
        log_pass(f"Ray installed: version {ray_version}")
    except ImportError:
        log_fail("Ray module not found.", "Run 'pip install ray==2.56.0' (or 2.55.0)")

    # vLLM Check
    vllm_version = None
    try:
        vllm = importlib.import_module("vllm")
        vllm_version = vllm.__version__
        log_pass(f"vLLM installed: version {vllm_version}")
    except ImportError:
        log_fail("vLLM module not found.", "Run 'pip install vllm==0.22.0' (or 0.18.0)")

    # Version Alignment Check based on Ray Specs
    if ray_version and vllm_version:
        if "2.56" in ray_version and "0.22" in vllm_version:
            log_pass("Ray 2.56.0 and vLLM 0.22.0 are strictly aligned.")
        elif "2.55" in ray_version and "0.18" in vllm_version:
            log_pass("Ray 2.55.0 and vLLM 0.18.0 are strictly aligned.")
        else:
            log_fail(f"Version mismatch! Ray: {ray_version}, vLLM: {vllm_version}.", 
                     "Strictly pin Ray 2.56.0 with vLLM 0.22.0 OR Ray 2.55.0 with vLLM 0.18.0 to avoid deployment crashes.")

def generate_clear_path_forward():
    print(f"\n{Colors.HEADER}{Colors.BOLD}======================================================================{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}                      CLEAR PATH FORWARD                              {Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}======================================================================{Colors.ENDC}")
    
    if len(failures) == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}ALL SYSTEMS GREEN.{Colors.ENDC}")
        print("Your environment is perfectly aligned with the Legion System Manifest.")
        print("Next Steps:")
        print("1. From C:\\WEB CASE STUDY\\modelship\\modelship-main, run 'python mship_deploy.py' to launch Qwen.")
        print("2. Ensure ALL other IDEs/terminals locking the .venv are closed to avoid the lib64 'Access Denied' error.")
        print("3. Launch 'python build_diffusion_dataset.py' to route samples through the C++ DSP Zero-Copy Bridge.")
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}BLOCKERS DETECTED ({len(failures)}). YOU MUST FIX THESE BEFORE DEPLOYING:{Colors.ENDC}")
        for i, fail in enumerate(failures, 1):
            print(f" {i}. {fail}")
        
    if warnings:
        print(f"\n{Colors.WARNING}Non-Critical Warnings to Monitor:{Colors.ENDC}")
        for i, warn in enumerate(warnings, 1):
            print(f" - {warn}")

if __name__ == "__main__":
    check_system_and_wsl()
    check_python_env()
    check_hard_paths()
    check_cuda_components()
    check_ray_and_vllm()
    generate_clear_path_forward()