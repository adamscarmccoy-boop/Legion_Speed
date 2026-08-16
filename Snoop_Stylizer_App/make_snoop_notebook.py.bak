"""
ADAMSCARMCCOY_QUERY_RAG.PY
==========================
Drop-in terminal RAG query tool for C:\\WEB CASE STUDY.

What it does:
1. Probes known LanceDB locations and chooses the populated one.
2. Searches code/documentation vector tables, using semantic search when an embedding model is available.
3. Falls back to keyword scanning if embedding/search is unavailable.
4. Connects to a live Ray cluster with address="auto" in namespace="legion" and tries localhost fallbacks.
5. Searches SwarmKnowledgeRegistry live-memory tables when present.

Usage:
    .venv\Scripts\python.exe ADAMSCARMCCOY_QUERY_RAG.PY "AcousticDNAEngine"

Optional env vars:
    RAG_DB_PATH=C:\path\to\lancedb
    RAG_LIMIT=12
    RAG_CHARS=4000
    RAG_EMBED_MODEL=text-embedding-snowflake-arctic-embed-l-v2.0
    RAY_ADDRESS=auto
    RAY_NAMESPACE=legion
    RAY_REGISTRY_ACTOR=SwarmKnowledgeRegistry
"""

from __future__ import annotations

# pyrefly: ignore [missing-import]
from Snoop_Stylizer_App.langgraph_ray_optimizer import langgraph_ray_optimizer
# pyrefly: ignore [missing-import]
from Snoop_Stylizer_App.swarm_knowledge_reg import swarm_knowledge_reg

import json
import os
import re
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_DB_PATHS = [
    r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag"
]

CODE_TABLE_CANDIDATES = ["mined_code_vectors", "code_vectors", "chris_lake_speed_test"]
DOC_TABLE_CANDIDATES = ["mined_documentation_vectors", "documentation_vectors", "chris_lake_web_intel"]

CONTENT_COLUMNS = ["content", "text", "chunk", "page_content", "snippet", "body", "document", "code"]
SOURCE_COLUMNS = ["source_file", "file_path", "path", "source", "url", "filename", "document_title"]
SYMBOL_COLUMNS = ["symbol_name", "symbol", "function_name", "name", "title"]
VECTOR_COLUMNS = ["vector", "embedding", "embeddings"]

LEGION_NAMESPACE = os.getenv("RAY_NAMESPACE", "legion")
REGISTRY_ACTOR = os.getenv("RAY_REGISTRY_ACTOR", "SwarmKnowledgeRegistry")
LIMIT = int(os.getenv("RAG_LIMIT", "12"))
CHARS = int(os.getenv("RAG_CHARS", "4000"))


@dataclass
class SearchHit:
    table: str
    score: Optional[float]
    row: dict[str, Any]
    mode: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def banner(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def compact(value: Any, max_chars: int = CHARS) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        try:
            value = json.dumps(value, ensure_ascii=False, default=str, indent=2)
        except Exception:
            value = str(value)
    value = value.replace("\r\n", "\n")
    return value[:max_chars] + ("\n... [truncated]" if len(value) > max_chars else "")


def pick_col(row: dict[str, Any], candidates: list[str]) -> Optional[str]:
    lower_map = {str(k).lower(): k for k in row.keys()}
    for c in candidates:
        if c.lower() in lower_map:
            return lower_map[c.lower()]
    # soft contains match
    for k in row.keys():
        lk = str(k).lower()
        if any(c.lower() in lk for c in candidates):
            return k
    return None


def row_text(row: dict[str, Any]) -> str:
    content_col = pick_col(row, CONTENT_COLUMNS)
    if content_col:
        return compact(row.get(content_col), CHARS)
    # fallback: concatenate useful scalar fields but skip vector-ish columns
    parts = []
    for k, v in row.items():
        if any(x in str(k).lower() for x in ["vector", "embedding"]):
            continue
        if isinstance(v, (str, int, float, bool)) or v is None:
            parts.append(f"{k}: {v}")
    return compact("\n".join(parts), CHARS)


def source_label(row: dict[str, Any]) -> str:
    src_col = pick_col(row, SOURCE_COLUMNS)
    sym_col = pick_col(row, SYMBOL_COLUMNS)
    src = str(row.get(src_col, "unknown source")) if src_col else "unknown source"
    sym = str(row.get(sym_col, "")) if sym_col else ""
    return f"{src}" + (f" | {sym}" if sym else "")


def safe_to_pylist(obj: Any, limit: int = 1000) -> list[dict[str, Any]]:
    """Convert PyArrow/Pandas/list/dict-ish objects to list[dict]."""
    if obj is None:
        return []
    try:
        import pandas as pd  # type: ignore
        if isinstance(obj, pd.DataFrame):
            return obj.head(limit).to_dict("records")
    except Exception:
        pass
    try:
        import pyarrow as pa  # type: ignore
        if isinstance(obj, (pa.Table, pa.RecordBatch)):
            return obj.slice(0, limit).to_pylist()
    except Exception:
        pass
    if isinstance(obj, list):
        out = []
        for item in obj[:limit]:
            out.append(item if isinstance(item, dict) else {"value": item})
        return out
    if isinstance(obj, dict):
        return [obj]
    try:
        return obj.to_pylist()[:limit]
    except Exception:
        return [{"value": str(obj)}]


def keyword_score(query: str, row: dict[str, Any]) -> int:
    hay = (source_label(row) + "\n" + row_text(row)).lower()
    terms = [t for t in re.split(r"\W+", query.lower()) if len(t) > 1]
    return sum(hay.count(t) for t in terms)


# Reconfigure stdout to prevent CP1252 character map crashes on unicode symbols
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

def get_snowflake_vector(text):
    """Query local LM Studio on port 1234 for 1024-dim Snowflake embeddings."""
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
        # STRICT TIMEOUT to prevent hanging
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data["data"][0]["embedding"]
    except Exception as e:
        print(f"[WARN] Local LM Studio not responding or model offline: {e}")
        return None

def find_correct_ray_cluster(expected_actor="SwarmKnowledgeRegistry"):
    """Probes multiple Ray instances to find the one hosting the Knowledge Registry."""
    potential_addresses = ["127.0.0.1:53678", "127.0.0.1:57712", "auto"]
    
    for addr in potential_addresses:
        try:
            print(f"Probing Ray cluster at {addr}...")
            ray.init(address=addr, namespace="legion", ignore_reinit_error=True)
            try:
                # Attempt to get the actor with a short timeout
                registry = ray.get_actor(expected_actor)
                ray.get(registry.get_registered_tables_summary.remote(), timeout=2)
                print(f"Successfully locked onto Ray cluster at {addr}")
                return addr
            except Exception:
                print(f"Actor {expected_actor} not found or unresponsive on {addr}.")
                ray.shutdown()
        except Exception as e:
            print(f"Could not connect to {addr}: {e}")
            ray.shutdown()
            
    return None

def main():
    print("=== Legion RAG Database Query Tool (Cluster-Aware) ===")
    
    # DEFAULT QUERY for Cloud Forge search
    query = "Cloud Forge Search"
    if len(sys.argv) > 1:
        query = sys.argv[1]
        
    if query == "INSERT QUESTION OR QUERY HERE":
        print("Please specify a query.")
        sys.exit(0)
    
    # 1. FIND THE CORRECT RAY CLUSTER
    correct_addr = find_correct_ray_cluster()
    if not correct_addr:
        print("FATAL: Could not find a Ray cluster hosting the SwarmKnowledgeRegistry.")
        sys.exit(1)
    
    # 2. CONNECT TO LANCEDB
    db_path = r"c:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag"
    if not os.path.exists(db_path):
        db_path = r"C:\WEB CASE STUDY\lancedb_web_intel_rag"
        
    print(f"Connecting to LanceDB at: {db_path}...")
    try:
        db = lancedb.connect(db_path)
    except Exception as e:
        print(f"Error connecting to LanceDB: {e}")
        sys.exit(1)
        
    query_vector = get_snowflake_vector(query)
    
    # --------------------------------------------------------------------------
    # SOURCE 1: Code Vector Search
    # --------------------------------------------------------------------------
    tables = db.table_names()
    if "mined_code_vectors" in tables:
        print(f"\\nSearching Code base for: '{query}'...")
        code_tbl = db.open_table("mined_code_vectors")
        try:
            if query_vector:
                code_results = code_tbl.search(query_vector).limit(3).to_pandas()
            else:
                df = code_tbl.to_pandas()
                mask = df["code_content"].astype(str).str.contains(query, case=False, na=False)
                code_results = df[mask].head(3)
                
            if not code_results.empty:
                print("\\n--- Semantic Code Results ---")
                for idx, row in code_results.iterrows():
                    print(f"\\n[Result #{idx + 1}] File: {row.get('source_file', 'Unknown')}")
                    if 'symbol_name' in row: print(f"  Symbol:  {row.get('symbol_name')}")
                    if 'code_content' in row: print(f"  Content:\\n{str(row.get('code_content'))[:250].strip()}\\n...")
                    print("-" * 50)
            else:
                print("No code matches found.")
        except Exception as e:
            print(f"Code search error: {e}")
            
    # --------------------------------------------------------------------------
    # SOURCE 2: Documentation Vector Search
    # --------------------------------------------------------------------------
    if "mined_documentation_vectors" in tables:
        print(f"\\nSearching Documentation for: '{query}'...")
        doc_tbl = db.open_table("mined_documentation_vectors")
        try:
            if query_vector:
                doc_results = doc_tbl.search(query_vector).limit(3).to_pandas()
            else:
                df = doc_tbl.to_pandas()
                mask = df["text"].astype(str).str.contains(query, case=False, na=False)
                doc_results = df[mask].head(3)
                
            if not doc_results.empty:
                print("\\n--- Semantic Documentation Results ---")
                for idx, row in doc_results.iterrows():
                    distance = f"(Distance: {row.get('_distance', 0.0):.4f})" if '_distance' in row else ""
                    print(f"\\n[Match #{idx + 1}] {distance}")
                    print(f"  {row.get('text')}")
                    print("-" * 50)
            else:
                print("No documentation matches found.")
        except Exception as e:
            print(f"Documentation search error: {e}")
    # --------------------------------------------------------------------------
    # SOURCE 3: Ray Swarm In-Memory Registry
    try:
        registry = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
        table_names = ray.get(registry.list_tables.remote())
        print("\n--- Ray Swarm In-Memory Registry ---")
        for table_name in table_names:
            print(f"Table: {table_name}")
    except Exception as e:
        print(f"Ray Registry error: {e}")       

if __name__ == "__main__":
    main() 