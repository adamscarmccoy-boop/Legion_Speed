import os
import sys
import time
import ast
import ray
import json

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
    sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================


# Force output to UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Workspaces to search
WORKSPACES = [
    r"c:\WEB CASE STUDY",
    r"c:\STUDIES_BACKUP\Legion-Jacked-Pipeline"
]

print("=== Starting Ray-Arrow Python Script Analyzer ===")

# Connect to local Ray cluster
if not ray.is_initialized():
    ray.init(address="auto", ignore_reinit_error=True)
    print("Successfully connected to Ray.")

@ray.remote
def analyze_script(file_path):
    """Parses a Python file, counts lines, and extracts key modules/imports."""
    filename = os.path.basename(file_path)
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()
        
        lines = code.splitlines()
        line_count = len(lines)
        
        # Parse imports using Abstract Syntax Tree (AST) to be precise
        imports = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except Exception:
            # Fallback regex if AST parsing fails (syntax errors, etc.)
            import re
            imports = re.findall(r"^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)", code, re.MULTILINE)

        unique_imports = sorted(list(set(imports)))
        
        # Check for specific audio keywords
        keywords = {
            "pedalboard": "pedalboard" in code.lower(),
            "essentia": "essentia" in code.lower(),
            "librosa": "librosa" in code.lower(),
            "torchaudio": "torchaudio" in code.lower(),
            "ray": "import ray" in code.lower() or "@ray.remote" in code,
            "mastering": "master" in code.lower()
        }
        
        found_keywords = [k for k, v in keywords.items() if v]

        return {
            "status": "SUCCESS",
            "filename": filename,
            "path": file_path,
            "line_count": line_count,
            "imports": unique_imports,
            "keywords": found_keywords
        }
    except Exception as e:
        return {
            "status": "FAILED",
            "filename": filename,
            "path": file_path,
            "error": str(e)
        }

def main():
    t0 = time.time()
    
    # 1. Discover all Python files
    py_files = []
    for ws in WORKSPACES:
        if not os.path.exists(ws):
            continue
        for root, dirs, files in os.walk(ws):
            # Exclude virtual environments and caching directories
            dirs[:] = [d for d in dirs if d not in ['.venv', '.venv_fresh', '.git', '__pycache__', '.pytest_cache', 'node_modules']]
            for file in files:
                if file.endswith('.py'):
                    py_files.append(os.path.join(root, file))

    print(f"Discovered {len(py_files)} python files. Sending to Ray workers for parallel analysis...")
    
    # 2. Fire remote tasks
    futures = [analyze_script.remote(path) for path in py_files]
    
    # 3. Retrieve all results simultaneously
    results = ray.get(futures)
    
    successes = [r for r in results if r["status"] == "SUCCESS"]
    
    # Sort scripts by line count descending
    successes.sort(key=lambda x: x["line_count"], reverse=True)
    
    print("\n========================================================")
    print(f"✅ Analysis Complete: {len(successes)}/{len(py_files)} files analyzed in {time.time() - t0:.2f}s")
    print("========================================================")
    
    # Print the top 15 longest scripts and any with key audio keywords
    print("\nTop 15 Longest Scripts & Audio Master Modules:")
    for i, s in enumerate(successes[:15]):
        print(f"\n{i+1}. {s['filename']} ({s['line_count']} lines)")
        print(f"   Path: {s['path']}")
        print(f"   Imports: {', '.join(s['imports'][:8])}")
        if s['keywords']:
            print(f"   Acoustic Keys: {', '.join(s['keywords'])}")

    # 4. Export to JSON for Gemini
    export_path = os.path.join(r"c:\WEB CASE STUDY", "mastering_swarm_summary.json")
    with open(export_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_files": len(py_files),
            "analyzed_files": len(successes),
            "scripts": successes
        }, f, indent=2)
    
    print(f"\n[+] Saved analysis payload to: {export_path}")

if __name__ == "__main__":
    main()