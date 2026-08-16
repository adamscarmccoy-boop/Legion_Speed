import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import ast
import lancedb
import pandas as pd
import numpy as np
import urllib.request
import json
from concurrent.futures import ThreadPoolExecutor

# Connect to LanceDB
db_path = r"c:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag"
if not os.path.exists(db_path):
    db_path = r"C:\WEB CASE STUDY\lancedb_web_intel_rag"

print(f"Connecting to LanceDB at: {db_path}...")
try:
    db = lancedb.connect(db_path)
except Exception as e:
    print(f"Error connecting to LanceDB: {e}")
    sys.exit(1)

# Helper function to generate Snowflake embeddings via LM Studio local server
def get_snowflake_embedding(text):
    payload = {
        "input": [text],
        "model": "text-embedding-snowflake-arctic-embed-l-v2.0"
    }
    req = urllib.request.Request(
        "http://localhost:1234/v1/embeddings",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data["data"][0]["embedding"]
    except Exception as e:
        return None

def parse_python_file(filepath):
    """Parse AST to extract classes and functions with docstrings and code content."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
            
        tree = ast.parse(source, filename=filepath)
        items = []
        
        # Extract module-level docstring/code
        module_doc = ast.get_docstring(tree) or ""
        items.append({
            "source_file": filepath,
            "symbol_name": "module",
            "type": "module",
            "docstring": module_doc,
            "code_content": source[:1000]
        })
        
        # Traverse AST for classes and functions
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_source = ast.get_source_segment(source, node) or ""
                docstring = ast.get_docstring(node) or ""
                items.append({
                    "source_file": filepath,
                    "symbol_name": node.name,
                    "type": "function",
                    "docstring": docstring,
                    "code_content": func_source[:1500]
                })
            elif isinstance(node, ast.ClassDef):
                class_source = ast.get_source_segment(source, node) or ""
                docstring = ast.get_docstring(node) or ""
                items.append({
                    "source_file": filepath,
                    "symbol_name": node.name,
                    "type": "class",
                    "docstring": docstring,
                    "code_content": class_source[:1500]
                })
                
        return items
    except Exception as e:
        err_msg = str(e).encode('ascii', errors='ignore').decode('ascii')
        print(f"  -> Error parsing {os.path.basename(filepath)}: {err_msg}")
        return []

def main():
    print("=== Scanning Local Workspace for Code Files ===")
    
    # Active workspace gets top priority, backups get processed next
    primary_dir = r"C:\WEB CASE STUDY"
    backup_dir = r"c:\STUDIES_BACKUP\Legion-Jacked-Pipeline"
    
    py_files_primary = []
    py_files_backup = []
    
    exclude_keywords = ["cell_", "dump_", "Untitled", "venv", "node_modules", "chromadb"]
    
    # Scan Primary
    if os.path.exists(primary_dir):
        for root, dirs, files in os.walk(primary_dir):
            if any(kw in root.lower() for kw in exclude_keywords):
                continue
            for file in files:
                if file.endswith(".py"):
                    if not any(kw in file for kw in exclude_keywords):
                        py_files_primary.append(os.path.join(root, file))
                        
    # Scan Backup
    if os.path.exists(backup_dir):
        for root, dirs, files in os.walk(backup_dir):
            if any(kw in root.lower() for kw in exclude_keywords):
                continue
            for file in files:
                if file.endswith(".py"):
                    if not any(kw in file for kw in exclude_keywords):
                        py_files_backup.append(os.path.join(root, file))
                        
    # Prioritize primary workspace files
    py_files = py_files_primary + py_files_backup
    print(f"Found {len(py_files_primary)} files in primary workspace, and {len(py_files_backup)} files in backups.")
    print(f"Total: {len(py_files)} Python files to parse.")
    
    # Parse files to extract code symbols
    raw_symbols = []
    for filepath in py_files:
        symbols = parse_python_file(filepath)
        raw_symbols.extend(symbols)
        
    print(f"Extracted {len(raw_symbols)} classes, functions, and module blocks.")
    
    # Vectorize symbols concurrently using LM Studio
    print("\nVectorizing code symbols using LM Studio local Snowflake model...")
    records = []
    
    def embed_symbol(idx_item_tuple):
        idx, item = idx_item_tuple
        semantic_text = f"File: {item['source_file']}\nSymbol: {item['symbol_name']} ({item['type']})\nDocstring: {item['docstring']}\nCode:\n{item['code_content']}"
        vector = get_snowflake_embedding(semantic_text[:1200])
        
        if vector:
            return {
                "id": str(idx),
                "source_file": item["source_file"].replace("\\", "/"),
                "symbol_name": item["symbol_name"],
                "type": item["type"],
                "docstring": item["docstring"],
                "code_content": item["code_content"],
                "vector": vector
            }
        return None
        
    # Process up to 750 symbols, prioritizing primary files (since they are at the front)
    target_symbols = raw_symbols[:750]
    print(f"Vectorizing first {len(target_symbols)} symbols concurrently (prioritizing primary workspace)...")
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(embed_symbol, enumerate(target_symbols))
        for r in results:
            if r:
                records.append(r)
                
    if not records:
        print("Error: No code symbols were successfully vectorized.")
        return
        
    # Write to LanceDB
    table_name = "mined_code_vectors"
    df = pd.DataFrame(records)
    
    tbl = db.create_table(table_name, data=df, mode="overwrite")
    print(f"\nIngestion Complete! Vectorized and stored {len(df)} code symbols in table '{table_name}'.")

if __name__ == "__main__":
    main()
