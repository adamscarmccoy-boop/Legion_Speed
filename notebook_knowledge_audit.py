import os
import json
import re
import pyarrow as pa
import pyarrow.parquet as pq
import sys

# Force output to UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Define workspaces
workspaces = [
    r"c:\WEB CASE STUDY",
    r"c:\STUDIES_BACKUP\Legion-Jacked-Pipeline"
]

print("=== Crawling Workspaces for Notebooks and Data Sources ===")
notebooks_found = []
data_sources = set()

# Safe regex pattern to look for file paths/data sources inside code cells
path_pattern = re.compile(r"['\"](E:[\\/][^'\"]+|[a-zA-Z]:[\\/][^'\"]+\.(?:csv|json|parquet|db|duckdb|wav|mp3))['\"]", re.IGNORECASE)

for ws in workspaces:
    if not os.path.exists(ws):
        continue
    for root, dirs, files in os.walk(ws):
        # Skip virtual envs and caches
        dirs[:] = [d for d in dirs if d not in ['.venv', '.venv_fresh', '.git', '__pycache__', '.pytest_cache', 'node_modules']]
        for file in files:
            if file.endswith('.ipynb'):
                full_path = os.path.join(root, file).replace('\\', '/')
                notebooks_found.append(full_path)

print(f"Found {len(notebooks_found)} notebooks.")

# Analyze each notebook to extract cells and potential data sources
notebook_mappings = []

for nb in notebooks_found:
    try:
        with open(nb, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
        
        cells = data.get("cells", [])
        code_cells_count = sum(1 for c in cells if c.get("cell_type") == "code")
        markdown_cells_count = sum(1 for c in cells if c.get("cell_type") == "markdown")
        
        nb_sources = []
        for cell in cells:
            if cell.get("cell_type") == "code":
                source = "".join(cell.get("source", []))
                # Find all path references
                matches = path_pattern.findall(source)
                for match in matches:
                    normalized = match.replace('\\', '/')
                    nb_sources.append(normalized)
                    data_sources.add(normalized)
        
        notebook_mappings.append({
            "notebook_path": nb,
            "code_cells": code_cells_count,
            "markdown_cells": markdown_cells_count,
            "potential_sources": list(set(nb_sources))
        })
    except Exception as e:
        pass  # Skip empty or corrupted notebook files quietly

# Save the PyArrow schema representation of this metadata catalog
arrow_data = []
for mapping in notebook_mappings:
    arrow_data.append({
        "notebook_path": mapping["notebook_path"],
        "code_cells_count": mapping["code_cells"],
        "markdown_cells_count": mapping["markdown_cells"],
        "potential_sources": ", ".join(mapping["potential_sources"])
    })

# Convert to PyArrow Table
schema = pa.schema([
    pa.field("notebook_path", pa.string()),
    pa.field("code_cells_count", pa.int64()),
    pa.field("markdown_cells_count", pa.int64()),
    pa.field("potential_sources", pa.string())
])

table = pa.Table.from_pylist(arrow_data, schema=schema)
parquet_output = r"c:\WEB CASE STUDY\notebook_knowledge_audit.parquet"
pq.write_table(table, parquet_output)

print(f"\nSaved notebook knowledge audit Parquet table with {len(table)} rows to: {parquet_output}")
print("\n--- Detailed Mappings ---")
for mapping in notebook_mappings:
    print(f"\n* Notebook: {os.path.basename(mapping['notebook_path'])}")
    print(f"   Path: [link](file:///{mapping['notebook_path']})")
    print(f"   Structure: {mapping['code_cells']} code cells, {mapping['markdown_cells']} markdown cells")
    if mapping['potential_sources']:
        print(f"   Data references:")
        for src in mapping['potential_sources']:
            print(f"     - {src}")
    else:
        print("   Data references: None detected.")
