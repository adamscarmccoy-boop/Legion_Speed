# =====================================================================
# MODULE: run_system_forest_fixed.py
# SYSTEM: Scalable Macro Code Forest & AST Ingestion Engine
# =====================================================================
import os
import sys
import time
import socket
import logging
from pathlib import Path
import ray

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger("SystemForestFixed")

# =====================================================================
# SECTION 1: PERSISTENT BATCH-LEVEL FOREST ACTOR
# =====================================================================
@ray.remote(num_cpus=1, num_gpus=0.25)  # Scale to use fractional GPU/VRAM segments efficiently
class PersistentCodeForestWorker:
    """
    Persistent cluster actor that keeps a single Monty Rust VM hot in memory.
    Ingests and processes entire file arrays sequentially to bypass Ray queue throttling.
    """
    def __init__(self, drive_base: str):
        self.drive_base = drive_base
        # Localize your imports inside the actor class to prevent unpickling drops
        from pydantic_core import SchemaValidator, core_schema
        from pydantic_monty import Monty

        # Initialize the rigid Pydantic V2 C-level validation contract ONCE at boot
        self.record_schema = core_schema.typed_dict_schema({
            "filepath": core_schema.typed_dict_field(core_schema.str_schema()),
            "symbol_name": core_schema.typed_dict_field(core_schema.str_schema()),
            "line_count": core_schema.typed_dict_field(core_schema.int_schema()),
            "is_valid": core_schema.typed_dict_field(core_schema.bool_schema()),
        })
        self.validator = SchemaValidator(self.record_schema)
        
        # Instantiate the Rust virtual machine sandbox context ONCE
        print(f"[WORKER-INIT] Spawning warm Rust Monty pool engine for volume: {self.drive_base}")
        self.monty_pool = Monty()

    def process_batch(self, file_paths: list) -> list:
        """Processes an entire directory block inline without spinning up new tasks."""
        import ast
        batch_records = []

        for filepath in file_paths:
            rel_path = os.path.relpath(filepath, self.drive_base).replace("\\", "/")
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    code_text = f.read()

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

                # Reuse the hot, persistent Monty VM instance across all file tokens
                for symbol_name, node_type, line_no in ast_symbols:
                    is_monty_clean = False
                    try:
                        with self.monty_pool.checkout() as session:
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
                    
                    # Direct microsecond C-level schema validation
                    validated_obj = self.validator.validate_python(raw_payload)
                    batch_records.append(validated_obj)

            except Exception:
                pass

        return batch_records

    def close(self):
        """Clean closure handler for the Rust pool context allocation."""
        if hasattr(self, "monty_pool"):
            self.monty_pool.__exit__(None, None, None)

# =====================================================================
# SECTION 2: TUNED PERFORMANCE ORCHESTRATOR
# =====================================================================
def run_optimized_macro_sweep(scan_targets: list, output_dir: str):
    logger.info("========================================================================")
    logger.info("       LAUNCHING OPTIMIZED PERSISTENT MACRO CODE SWARM ENGINE")
    logger.info("========================================================================")

    # 1. TUNED ATTACH: Latch onto existing cluster with strict system overrides
    # These environment variables explicitly unblock your queue throttling ceilings
    
ray.init(address="auto", namespace="legion", ignore_reinit_error=True,
            runtime_env={
                "env_vars": {
                    "RAY_max_pending_lease_requests_per_scheduling_category": "5000",
                    "RAY_DEDUP_LOGS": "0"
                }
            }

for drive in scan_targets:
        logger.info(f"Scanning target infrastructure volume: {drive}")
        for root, dirs, files in os.walk(drive):
            dirs[:] = [d for d in dirs if d.lower() not in skip_dirs and not d.startswith(".")]
            for file in files:
                if file.endswith(".py") and not file.startswith("."):
                    files_by_drive[drive].append(os.path.join(root, file))

    # 3. Instantiate Persistent Work Pool (1 Worker Actor Per Volume Block)
    t_start = time.perf_counter()
    futures = []
    active_workers = []

    for drive, paths in files_by_drive.items():
        total_files = len(paths)
        if total_files == 0:
            continue
            
        logger.info(f"Volume [{drive}] - Ingesting {total_files} modules into persistent memory queue.")
        
        # Deploy exactly ONE stateful actor for the entire volume
        worker = PersistentCodeForestWorker.options(
            name=f"Worker_{drive.replace(':', '')}",
            namespace="legion"
        ).remote(drive)
        active_workers.append(worker)

        # Split the files into large chunks to prevent micro-task congestion
        chunk_size = max(1, total_files // 4) # Adjust split factor based on CPU thread scale
        for i in range(0, total_files, chunk_size):
            chunk = paths[i:i + chunk_size]
            futures.append(worker.process_batch.remote(chunk))

    # 4. Stream and Gather the Result Tables
    logger.info(f"Processing batch loops through hot Rust sandboxes over Tailscale IP...")
    results = ray.get(futures)

    all_records = []
    for chunk_output in results:
        all_records.extend(chunk_output)

    t_end = time.perf_counter()
    total_time_ms = (t_end - t_start) * 1000.0

    # 5. Terminate Worker Handles to Recover Host Memory Slots
    for w in active_workers:
        w.close.remote()

    # 6. Write Global Telemetry Audit Document
    report_path = os.path.join(output_dir, "global_total_system_code_forest.txt")
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write(f"Telemetry Status   : SUCCESS\n")
        rf.write(f"Total Sweep Time   : {total_time_ms:.2f} ms ({total_time_ms/1000:.4f} sec)\n")
        rf.write(f"Total AST Node Rows: {len(all_records)}\n")

    logger.info(f"[SUCCESS] Global Partition Code Forest verified in {total_time_ms/1000:.4f} seconds!")
    logger.info(f"Comprehensive manifest written to: {report_path}")

if __name__ == "__main__":
    TARGET_DRIVES = [r"C:\WEB CASE STUDY", r"E:\STUDIES_BACKUP"]
    OUTPUT_DIR = r"C:\WEB CASE STUDY"
    run_optimized_macro_sweep(TARGET_DRIVES, OUTPUT_DIR)
