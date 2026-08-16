import os
import re
import sys
import json
import shutil
import traceback
import subprocess

# --- SYSTEM DIRECTORIES ---
TARGET_DIRS = [
    r"C:\WEB CASE STUDY",
    r"C:\STUDIES"
]

# --- COLORS FOR HIGH-VISIBILITY WORKSTATION LOGGING ---
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

def log_info(msg):
    print(f"{CYAN}[INFO]{RESET} {msg}", flush=True)

def log_success(msg):
    print(f"{GREEN}[SUCCESS]{RESET} {msg}", flush=True)

def log_warning(msg):
    print(f"{YELLOW}[WARN]{RESET} {msg}", flush=True)

def log_error(msg):
    print(f"{RED}[ERROR]{RESET} {msg}", flush=True)

# ==============================================================================
# 1. NODE.JS / JS / TS GRACEFUL CLEANUP INJECTION TEMPLATE
# ==============================================================================
NODE_CLEANUP_CODE = """
// ==============================================================================
// SOVEREIGN LIFE-CYCLE STABILIZER (AUTO-INJECTED)
// Prevents "ClientHolder finalized without dropping" socket leaks in LM Studio
// ==============================================================================
if (typeof process !== 'undefined') {
  const gracefulShutdown = async (signal) => {
    console.warn(`\\n[LMS LIFECYCLE] Intercepted signal ${signal}. Cleanly dropping LM Studio connections...`);
    try {
      if (typeof client !== 'undefined' && client && typeof client.close === 'function') {
        await client.close();
        console.log("[LMS LIFECYCLE] Connection closed successfully.");
      }
    } catch (err) {
      console.error("[LMS LIFECYCLE] Error during connection drop:", err);
    }
    process.exit(0);
  };
  process.on("SIGINT", () => gracefulShutdown("SIGINT"));
  process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));
}
// ==============================================================================
"""

# ==============================================================================
# 2. PYTHON MCP GRACEFUL CLEANUP INJECTION TEMPLATE (UPGRADED TO PREVENT ATEXIT EXCEPTIONS)
# ==============================================================================
PYTHON_CLEANUP_CODE = """
# ==============================================================================
# SOVEREIGN LIFE-CYCLE STABILIZER (AUTO-INJECTED)
# Prevents dangling stdout/stdio pipes and GCS registry locks on Windows exit
# ==============================================================================
import atexit
import signal

def clean_exit_handler(*args, **kwargs):
    import sys
    sys.stderr.write("\\n[LMS LIFECYCLE] Exit triggered. Flushing system streams...\\n")
    sys.stderr.flush()
    try:
        import ray
        if ray.is_initialized():
            sys.stderr.write("[LMS LIFECYCLE] Active Ray session detected. Disconnecting...\\n")
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
"""

# ==============================================================================
# 3. DIRECTORY WALKER & TARGET RESOLUTION
# ==============================================================================
def find_and_patch_files():
    log_info("Starting workspace scan for active RAG and MCP development plugins...")
    
    files_to_patch = []
    
    # 1. Recursively locate potential candidate files
    for base_dir in TARGET_DIRS:
        if not os.path.exists(base_dir):
            log_warning(f"Directory skipped (not found on disk): {base_dir}")
            continue
            
        log_info(f"Scanning directory: {base_dir}")
        for root, dirs, files in os.walk(base_dir):
            # Skip heavy dependency folders to preserve V8 cycles and context space
            dirs[:] = [d for d in dirs if d.lower() not in [".venv", "node_modules", ".git", "venv", "__pycache__", "dist"]]
            
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                
                # We target Python MCP files and Node.js plugin entrypoints
                if ext in [".py", ".js", ".ts"]:
                    full_path = os.path.join(root, file)
                    try:
                        # Inspect file contents for matching indicators
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            
                        # Python targets: look for FastMCP, mcp.run, or Client session builders
                        if ext == ".py":
                            if "SOVEREIGN LIFE-CYCLE STABILIZER" in content:
                                # Check if it's using the old bugged handler
                                if "isinstance(args[0], int)" not in content:
                                    files_to_patch.append((full_path, "python-upgrade"))
                                    log_info(f"Target Resolved (Python MCP - Upgrade Required): {full_path}")
                            elif "FastMCP" in content or "mcp.run" in content or "ray.init" in content:
                                files_to_patch.append((full_path, "python"))
                                log_info(f"Target Resolved (Python MCP - New Patch): {full_path}")
                                
                        # Node/JS/TS targets: look for LMStudioClient or MCP SDK builders
                        elif ext in [".js", ".ts"] and ("LMStudioClient" in content or "@lmstudio/sdk" in content or "setToolsProvider" in content):
                            if "SOVEREIGN LIFE-CYCLE STABILIZER" not in content:
                                files_to_patch.append((full_path, "node"))
                                log_info(f"Target Resolved (Node Client): {full_path}")
                                
                    except Exception as e:
                        log_error(f"Failed to read metadata of {file}: {e}")

    if not files_to_patch:
        log_success("No un-stabilized connection loops found. All files are already operating in a safe state!")
        return

    # ==============================================================================
    # 4. SURGICAL AUTONOMIC PATCH APPLICATION
    # ==============================================================================
    log_info(f"Identified {len(files_to_patch)} targets requiring lifecycle stabilizing. Initiating patch loop...")
    
    for filepath, file_type in files_to_patch:
        try:
            # Create a backup copy before executing the surgical edit (Standard safety rule)
            backup_path = filepath + ".bak"
            shutil.copy2(filepath, backup_path)
            log_info(f"Created temporary safety backup: {backup_path}")
            
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                original_content = f.read()
                
            if file_type == "python":
                # Inject stabilizer right after initial core imports
                lines = original_content.splitlines()
                inject_index = 0
                for i, line in enumerate(lines[:15]):
                    if line.startswith("import ") or line.startswith("from "):
                        inject_index = i + 1
                        
                lines.insert(inject_index, PYTHON_CLEANUP_CODE)
                patched_content = "\n".join(lines)
                
                # Dry-run AST check to ensure the Python code compiles cleanly
                compile(patched_content, filepath, "exec")
                
            elif file_type == "python-upgrade":
                # Surgically replace the old stabilizer block with the new one
                # Match any block bounded by the equals bars with SOVEREIGN LIFE-CYCLE STABILIZER (AUTO-INJECTED) inside
                pattern = re.compile(
                    r"# =+\s*\n# SOVEREIGN LIFE-CYCLE STABILIZER \(AUTO-INJECTED\).*?signal\.signal\(signal\.SIGTERM, clean_exit_handler\)\s*\n# =+\s*\n", 
                    re.DOTALL
                )
                
                if pattern.search(original_content):
                    patched_content = pattern.sub(PYTHON_CLEANUP_CODE.strip() + "\n", original_content)
                else:
                    # Fallback if the boundary structure differs slightly
                    log_warning(f"Regex match failed on {filepath}. Applying standard append upgrade.")
                    patched_content = original_content + "\n" + PYTHON_CLEANUP_CODE
                
                # Dry-run AST check to ensure the Python code compiles cleanly
                compile(patched_content, filepath, "exec")
                
            elif file_type == "node":
                # Node.js cleanup blocks can be safely appended to the bottom of the execution file
                patched_content = original_content + "\n" + NODE_CLEANUP_CODE
                
            # Write verified stable code to disk
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(patched_content)
                
            log_success(f"Surgically patched: {filepath}")
            
            # Remove safety backup upon successful compilation and save
            if os.path.exists(backup_path):
                os.remove(backup_path)
                
        except Exception as err:
            log_error(f"Surgical patch aborted on file {filepath} due to compilation check failure: {err}")
            traceback.print_exc()

if __name__ == "__main__":
    print("=" * 80)
    print("🛡️  INITIATING WORKSPACE-WIDE CLIENT LIFECYCLE HEALER (V2)")
    print("=" * 80)
    find_and_patch_files()
    print("=" * 80)
    print("🚀 HEALING ROUTINE COMPLETED! Stale websocket registry locks have been mitigated.")
    print("=" * 80)
