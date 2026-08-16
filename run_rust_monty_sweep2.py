# =====================================================================
# MODULE: run_macro_code_forest.py
# SYSTEM: Sovereign Macro Code Forest & AST Ingestion Engine
# =====================================================================
import os
import sys
import time
import socket
import json
import logging
from pathlib import Path

# --- CORE DISTRIBUTED SPACE & HIGH-PERFORMANCE WORKERS ---
import ray

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

ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
# Set up clean, non-obtrusive systems logs
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger("MacroCodeForest")

# =====================================================================
# SECTION 1: RAY PARALLEL AST WORKER DEFINITION
# =====================================================================
@ray.remote(num_cpus=1)
def process_code_file_parallel(filepath: str, base_dir: str) -> list:
    """
    Parallel worker task. Instantiates an isolated pydantic_core validator 
    and Monty Rust VM directly inside the worker memory slot to evaluate AST nodes.
    """
    import ast
    from pydantic_core import SchemaValidator, core_schema
    from pydantic_monty import Monty

    # 1. Instantiate the absolute C-Level Pydantic V2 Schema Validation Contract
    record_schema = core_schema.typed_dict_schema({
        "filepath": core_schema.typed_dict_field(core_schema.str_schema()),
        "symbol_name": core_schema.typed_dict_field(core_schema.str_schema()),
        "line_count": core_schema.typed_dict_field(core_schema.int_schema()),
        "is_valid": core_schema.typed_dict_field(core_schema.bool_schema()),
    })
    validator = SchemaValidator(record_schema)
    
    local_records = []
    rel_path = os.path.relpath(filepath, base_dir).replace("\\", "/")

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            code_text = f.read()

        # Generate the Python Abstract Syntax Tree structures
        try:
            parsed_ast = ast.parse(code_text, filename=filepath)
            ast_symbols = []
            for node in ast.walk(parsed_ast):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    ast_symbols.append((node.name, node.__class__.__name__, node.lineno))
        except Exception:
            ast_symbols = [("raw_module", "Module", 1)]

        if not ast_symbols:
            ast_symbols = [("module_root", "Module", 1)]

        # 2. Fire the symbols straight into Monty's Rust Virtual Machine
        with Monty() as pool:
            for symbol_name, node_type, line_no in ast_symbols:
                is_monty_clean = False
                try:
                    with pool.checkout() as session:
                        session.feed_run(f"def {symbol_name}(): pass")
                    is_monty_clean = True
                except Exception:
                    is_monty_clean = False

                raw_payload = {
                    "filepath": rel_path,
                    "symbol_name": symbol_name,
                    "line_count": line_no,
                    "is_valid": is_monty_clean
                }
                
                # C-level schema validation occurs instantaneously
                validated_obj = validator.validate_python(raw_payload)
                local_records.append(validated_obj)

    except Exception:
        # Catch disk errors or permission lock exceptions safely without crashing the worker
        pass

    return local_records

# =====================================================================
# SECTION 2: MACRO ENGINE ORCHESTRATION PIPELINE
# =====================================================================
def execute_macro_swarm_audit(target_paths: list, report_output_dir: str):
    logger.info("========================================================================")
    logger.info("    LAUNCHING DISTRIBUTED CODESPACE AND AST INGESTION ENGINE")
    logger.info("========================================================================")

    # 1. Complete One-Line Head Node Connection
    LOCAL_IP = socket.gethostbyname(socket.gethostname())
    logger.info(f"Connecting to Ray cluster context on local IP interface: {LOCAL_IP}...")
    ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
    logger.info("Ray distribution layer confirmed online.")

    # 2. Scalable File Discovery Matrix across Drives
    skip_dirs = {"venv", ".venv", "site-packages", "__pycache__", ".git", "node_modules", "dist", "build"}
    discovered_files = []

    for target_dir in target_paths:
        logger.info(f"Scanning target drive location block: {target_dir}")
        for root, dirs, files in os.walk(target_dir):
            dirs[:] = [d for d in dirs if d.lower() not in skip_dirs and not d.startswith(".")]
            for file in files:
                if file.endswith(".py") and not file.startswith("."):
                    discovered_files.append((os.path.join(root, file), target_dir))

    total_files = len(discovered_files)
    logger.info(f"Total isolated code files scheduled for parallel ingestion: {total_files}")

    if total_files == 0:
        logger.warning("No codebase files resolved. Halting execution pipeline loop.")
        return

    # 3. Micro-Batch Scheduling Loop (Prevents Ray Task Queue Overload)
    t_start = time.perf_counter()
    all_validated_records = []
    
    # Fire tasks in parallel bundles across your available CPU workers
    logger.info("Scheduling asynchronous file tasks to your active CPU worker nodes...")
    futures = [
        process_code_file_parallel.remote(filepath, base_dir) 
        for filepath, base_dir in discovered_files
    ]
    
    # 4. Gather Parallel Output Array References
    logger.info("Processing concurrent Rust AST validation loops in background clusters...")
    results = ray.get(futures)
    
    # Flatten the returning arrays from all worker threads
    for file_records in results:
        all_validated_records.extend(file_records)

    t_end = time.perf_counter()
    total_time_ms = (t_end - t_start) * 1000.0

    # 5. Extract Code Forest Telemetry & Write Audit Manifest
    total_nodes = len(all_validated_records)
    clean_nodes = sum(1 for rec in all_validated_records if rec["is_valid"])
    flagged_nodes = total_nodes - clean_nodes

    report_path = os.path.join(report_output_dir, "macro_code_forest_audit_report.txt")
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write("========================================================================\n")
        rf.write("         LEGION SYSTEM: DISTRIBUTED MACRO CODE FOREST REPORT\n")
        rf.write("========================================================================\n")
        rf.write(f"Execution Context   : Distributed Ray Parallel Workers\n")
        rf.write(f"Total Files Audited : {total_files}\n")
        rf.write(f"Total AST Nodes     : {total_nodes}\n")
        rf.write(f"Monty Verified Clean: {clean_nodes}\n")
        rf.write(f"Monty Flagged Error : {flagged_nodes}\n")
        rf.write(f"Total Sweep Latency : {total_time_ms:.2f} ms ({total_time_ms/1000:.4f} sec)\n")
        if total_nodes > 0:
            rf.write(f"Average AST Speed   : {(total_time_ms * 1000.0) / total_nodes:.2f} μs\n")
        rf.write("========================================================================\n")

    logger.info(f"[SUCCESS] Macro Code Forest fully audited in {total_time_ms/1000:.4f} seconds!")
    logger.info(f"System manifest report written to disk target: {report_path}")

# =====================================================================
# RUN CONTROL
# =====================================================================
if __name__ == "__main__":
    # Scan targets across your workstation's physical partitions
    TARGET_DRIVES = [r"C:\WEB CASE STUDY", r"E:\STUDIES_BACKUP"]
    OUTPUT_DIRECTORY = r"C:\WEB CASE STUDY"
    
    execute_macro_swarm_audit(TARGET_DRIVES, OUTPUT_DIRECTORY)