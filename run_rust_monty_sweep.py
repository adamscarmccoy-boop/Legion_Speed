import os
import sys
import time
import ast
import pyarrow as pa
import pyarrow.parquet as pq
from pydantic_monty import Monty

# Force UTF-8 stdout
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def run_rust_monty_pipeline(target_dir=r"C:\WEB CASE STUDY"):
    t_start = time.perf_counter()
    
    skip_dirs = {"venv", ".venv", "site-packages", "__pycache__", ".git", "node_modules", "prometheus", "dist", "build"}
    
    records = []
    total_bytes = 0
    total_files = 0
    clean_count = 0
    failed_count = 0

    print("=== LAUNCHING PYDANTIC-MONTY (RUST VM) + PYARROW ZERO-COPY PIPELINE ===")
    
    # 1. Walk Filesystem & Extract AST Symbols
    with Monty() as pool:
        for root, dirs, files in os.walk(target_dir):
            dirs[:] = [d for d in dirs if d.lower() not in skip_dirs and not d.startswith(".")]
            for file in files:
                if file.endswith(".py") and not file.startswith("."):
                    total_files += 1
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, target_dir)
                    
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            code_content = f.read()
                        
                        file_bytes = len(code_content.encode("utf-8"))
                        total_bytes += file_bytes

                        # AST Parsing
                        parsed_ast = ast.parse(code_content, filename=filepath)
                        
                        # Extract Top-Level Symbols
                        symbols = []
                        for node in ast.iter_child_nodes(parsed_ast):
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                                symbol_name = node.name
                                role_type = "class" if isinstance(node, ast.ClassDef) else "function"
                                line_start = node.lineno
                                line_end = getattr(node, "end_lineno", node.lineno)
                                snippet = ast.get_source_segment(code_content, node) or ""
                                symbols.append((symbol_name, role_type, line_start, line_end, snippet))

                        if not symbols:
                            symbols.append(("module", "module", 1, len(code_content.splitlines()) or 1, code_content[:1000]))

                        # Pass each snippet through Pydantic-Monty Rust VM Sandbox
                        for symbol_name, role_type, line_start, line_end, snippet in symbols:
                            is_verified = False
                            error_msg = ""
                            try:
                                with pool.checkout() as session:
                                    session.feed_run(snippet)
                                is_verified = True
                                clean_count += 1
                            except Exception as ex:
                                failed_count += 1
                                error_msg = str(ex)[:100]

                            records.append({
                                "id": f"{rel_path}:{symbol_name}:{line_start}",
                                "filepath": rel_path.replace("\\", "/"),
                                "symbol_name": symbol_name,
                                "role_type": role_type,
                                "line_start": line_start,
                                "line_end": line_end,
                                "code_content": snippet,
                                "monty_verified": is_verified,
                                "error": error_msg
                            })

                    except Exception as e:
                        failed_count += 1

    t_pipeline = time.perf_counter() - t_start

    # 2. Build PyArrow Table (Zero-Copy C++ Memory)
    arrow_table = pa.Table.from_pydict({
        "id": [r["id"] for r in records],
        "filepath": [r["filepath"] for r in records],
        "symbol_name": [r["symbol_name"] for r in records],
        "role_type": [r["role_type"] for r in records],
        "line_start": [r["line_start"] for r in records],
        "line_end": [r["line_end"] for r in records],
        "code_content": [r["code_content"] for r in records],
        "monty_verified": [r["monty_verified"] for r in records],
        "error": [r["error"] for r in records]
    })

    # 3. Write Parquet Catalog File
    parquet_path = os.path.join(target_dir, "code_knowledge_audit.parquet")
    pq.write_table(arrow_table, parquet_path)

    # 4. Generate Summary Text File
    report_path = os.path.join(target_dir, "codebase_monty_audit_report.txt")
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write("========================================================================\n")
        rf.write("     SOVEREIGN ENGINE: PYDANTIC-MONTY (RUST) + PYARROW AUDIT REPORT     \n")
        rf.write("========================================================================\n")
        rf.write(f"Execution Date / Time     : {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        rf.write(f"Target Root Directory     : {target_dir}\n")
        rf.write(f"Total Python Files Scanned: {total_files}\n")
        rf.write(f"Total Codebase Size       : {total_bytes / (1024*1024):.2f} MB ({total_bytes} bytes)\n")
        rf.write(f"Total AST Symbols Parsed  : {len(records)}\n")
        rf.write(f"Monty Clean / Verified ASTs: {clean_count}\n")
        rf.write(f"Monty Flagged / Failed ASTs: {failed_count}\n")
        rf.write(f"Pipeline Total Latency    : {t_pipeline * 1000:.2f} ms ({t_pipeline:.4f} sec)\n")
        rf.write(f"Average Speed Per Symbol  : {(t_pipeline * 1_000_000) / max(1, len(records)):.2f} μs\n")
        rf.write("------------------------------------------------------------------------\n")
        rf.write(f"Parquet Lakehouse Written : {parquet_path} ({os.path.getsize(parquet_path)} bytes)\n")
        rf.write("========================================================================\n\n")
        rf.write("TOP AST SYMBOLS AUDITED (FIRST 25 SAMPLES):\n")
        rf.write("------------------------------------------------------------------------\n")
        for r in records[:25]:
            status = "VERIFIED" if r["monty_verified"] else "FLAGGED"
            rf.write(f"[{status}] {r['filepath']} :: {r['role_type']} {r['symbol_name']} (L{r['line_start']}-L{r['line_end']})\n")
            if r["error"]:
                rf.write(f"         Error: {r['error']}\n")

    print(f"\n[SUCCESS] Pipeline complete in {t_pipeline * 1000:.2f} ms!")
    print(f"Report written to: {report_path}")
    print(f"Parquet Lakehouse written to: {parquet_path}")

if __name__ == "__main__":
    run_rust_monty_pipeline()
