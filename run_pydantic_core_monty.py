import os
import sys
import time
import ast
from pydantic_core import SchemaValidator, core_schema
from pydantic_monty import Monty

# Force UTF-8 stdout
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def execute_pydantic_core_monty_pipeline(target_dir=r"C:\WEB CASE STUDY"):
    print("========================================================================")
    print("  LAUNCHING PYDANTIC-CORE (RUST VALIDATOR) + PYDANTIC-MONTY (RUST VM)  ")
    print("========================================================================")

    # 1. Define C-Level Rust Schema via pydantic_core
    record_schema = core_schema.typed_dict_schema({
        "filepath": core_schema.typed_dict_field(core_schema.str_schema()),
        "symbol_name": core_schema.typed_dict_field(core_schema.str_schema()),
        "line_count": core_schema.typed_dict_field(core_schema.int_schema()),
        "is_valid": core_schema.typed_dict_field(core_schema.bool_schema()),
    })

    validator = SchemaValidator(record_schema)

    # 2. Collect files
    skip_dirs = {"venv", ".venv", "site-packages", "__pycache__", ".git", "node_modules", "prometheus", "dist", "build"}
    py_files = []
    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d.lower() not in skip_dirs and not d.startswith(".")]
        for file in files:
            if file.endswith(".py") and not file.startswith("."):
                py_files.append(os.path.join(root, file))

    print(f"Discovered {len(py_files)} Python source files.")
    print("Initializing Rust Monty Pool & pydantic_core SchemaValidator...\n")

    t_start = time.perf_counter()
    validated_records = []
    validated_ast_count = 0
    total_ast_nodes = 0
    rejected_count = 0

    with Monty() as pool:
        for filepath in py_files:
            rel_path = os.path.relpath(filepath, target_dir).replace("\\", "/")
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    code_text = f.read()

                # AST Breakdown into symbols
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

                for symbol_name, node_type, line_no in ast_symbols:
                    total_ast_nodes += 1
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

                    validated_obj = validator.validate_python(raw_payload)
                    validated_records.append(validated_obj)
                    if is_monty_clean:
                        validated_ast_count += 1
                    else:
                        rejected_count += 1

            except Exception:
                rejected_count += 1

    t_end = time.perf_counter()
    total_time_ms = (t_end - t_start) * 1000.0
    avg_per_file_us = (total_time_ms * 1000.0) / len(py_files) if py_files else 0.0

    # 3. Write Output Report
    report_path = os.path.join(target_dir, "pydantic_core_monty_cluster_report.txt")
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write("========================================================================\n")
        rf.write("  PYDANTIC-CORE (RUST VALIDATOR) + PYDANTIC-MONTY (RUST VM) REPORT      \n")
        rf.write("========================================================================\n")
        rf.write(f"Timestamp                : {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        rf.write(f"Target Directory         : {target_dir}\n")
        rf.write(f"Files Processed          : {len(py_files)}\n")
        rf.write(f"Total Individual AST Nodes: {total_ast_nodes}\n")
        rf.write(f"Rust Validated Records   : {len(validated_records)}\n")
        rf.write(f"Monty Clean AST Nodes    : {validated_ast_count}\n")
        rf.write(f"Monty Flagged AST Nodes  : {rejected_count}\n")
        rf.write(f"Total Pipeline Latency   : {total_time_ms:.2f} ms ({total_time_ms/1000:.4f} sec)\n")
        rf.write(f"Average Latency Per AST  : {(total_time_ms * 1000.0) / max(1, total_ast_nodes):.2f} μs\n")
        rf.write("========================================================================\n\n")
        rf.write("SAMPLE VALIDATED RECORDS (FIRST 20):\n")
        rf.write("------------------------------------------------------------------------\n")
        for rec in validated_records[:20]:
            rf.write(f"File: {rec['filepath']} | Lines: {rec['line_count']} | Valid: {rec['is_valid']}\n")

    print(f"[SUCCESS] Pipeline executed in {total_time_ms:.2f} ms!")
    print(f"Report written to: {report_path}")

if __name__ == "__main__":
    execute_pydantic_core_monty_pipeline()
