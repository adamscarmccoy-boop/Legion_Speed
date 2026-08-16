"""
One-shot ingest: mine Python sources from C:\\WEB CASE STUDY into a
'mined_code_vectors' LanceDB table at lancedb_web_intel_rag/, using
snowflake-arctic-embed-l-v2.0 (already in HF cache).

After running, mcp_rag_server.py's `semantic_code_search` tool will
have real data to query.

Usage (from project root):
    .venv\\Scripts\\python.exe build_mined_code_vectors.py
"""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

import lancedb
import pyarrow as pa
from lancedb.embeddings import EmbeddingFunctionRegistry

PROJECT_ROOT = Path(r"C:\WEB CASE STUDY")
LANCEDB_PATH = PROJECT_ROOT / "lancedb_web_intel_rag"
TABLE_NAME = "mined_code_vectors"

# Snowflake Arctic Embed L v2.0 is already in the local HF cache.
EMBED_MODEL = "Snowflake/snowflake-arctic-embed-l-v2.0"


def mine_symbols(path: Path) -> list[dict]:
    """Extract top-level functions/classes from a Python file as discrete rows."""
    try:
        src = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []

    rows: list[dict] = []
    lines = src.splitlines()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            snippet = "\n".join(lines[node.lineno - 1: node.end_lineno])
            doc = ast.get_docstring(node) or ""
            rows.append({
                "source_file": str(path.relative_to(PROJECT_ROOT)),
                "symbol_name": node.name,
                "symbol_kind": kind,
                "lines_of_code": (node.end_lineno or 0) - (node.lineno - 1),
                "docstring": doc[:2000],
                "code": snippet[:8000],
                "vector": snippet,  # embedded by LanceDB embedding function
            })
    if not rows:
        # File with no top-level symbols: index the whole file as one row
        rows.append({
            "source_file": str(path.relative_to(PROJECT_ROOT)),
            "symbol_name": path.stem,
            "symbol_kind": "module",
            "lines_of_code": len(lines),
            "docstring": "",
            "code": src[:8000],
            "vector": src[:8000],
        })
    return rows


def main() -> int:
    print(f"[1/3] Scanning {PROJECT_ROOT} for .py files...")
    py_files = [p for p in PROJECT_ROOT.rglob("*.py")
                if ".venv" not in p.parts
                and "node_modules" not in p.parts
                and "__pycache__" not in p.parts]
    print(f"      Found {len(py_files)} Python files")

    print("[2/3] Mining symbols...")
    all_rows: list[dict] = []
    for p in py_files:
        all_rows.extend(mine_symbols(p))
    print(f"      Extracted {len(all_rows)} rows")

    if not all_rows:
        print("No rows to ingest. Aborting.")
        return 1

    print(f"[3/3] Connecting to LanceDB at {LANCEDB_PATH}...")
    db = lancedb.connect(str(LANCEDB_PATH))

    print(f"      Loading embedding model: {EMBED_MODEL}")
    registry = EmbeddingFunctionRegistry.get_instance()
    embed_fn = registry.get("huggingface").create(
        name=EMBED_MODEL,
        device="cpu",  # RTX cards get used by vLLM later; keep ingest cheap
    )

    print(f"      Writing table '{TABLE_NAME}' ({len(all_rows)} rows)...")
    # Drop and recreate to ensure clean state
    if TABLE_NAME in db.table_names():
        db.drop_table(TABLE_NAME)
    table = db.create_table(TABLE_NAME, data=all_rows, embedding_function=embed_fn)

    print(f"      Done. Table rows: {table.count_rows()}")
    print(f"      LanceDB tables now: {db.table_names()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
