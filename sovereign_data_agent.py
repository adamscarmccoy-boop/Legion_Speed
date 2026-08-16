"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  SOVEREIGN DATA AGENT — DuckDB + LanceDB + Streaming + Monty               ║
║  Real databases. Real queries. LLM is the brain. Monty is the sandbox.     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import time
import sys
import os
import platform
import numpy as np
from pathlib import Path

import duckdb
import lancedb
import pyarrow as pa
from openai import OpenAI
from jinja2 import Environment, BaseLoader

# ═══════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════
WORKSPACE       = r"C:\WEB CASE STUDY"
DB_DIR          = os.path.join(WORKSPACE, "sovereign_data")
LANCE_DIR       = os.path.join(DB_DIR, "lance_store")
DUCK_PATH       = os.path.join(DB_DIR, "sovereign.duckdb")
MAX_TURNS       = 20
MAX_TOOL_CHARS  = 4000

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)
LLM_MODEL = "nvidia/nemotron-3-nano-4b"

# ═══════════════════════════════════════════════════════════════════════════
# BOOTSTRAP — Create DuckDB + LanceDB with sample data
# ═══════════════════════════════════════════════════════════════════════════
os.makedirs(DB_DIR, exist_ok=True)

def bootstrap_databases():
    """Seed DuckDB and LanceDB with interconnected sample data."""
    print("   📦 Bootstrapping DuckDB...")
    duck = duckdb.connect(DUCK_PATH)
    
    # Create tables
    duck.execute("""
        CREATE TABLE IF NOT EXISTS actors (
            actor_id INTEGER PRIMARY KEY,
            name VARCHAR,
            component VARCHAR,
            status VARCHAR,
            memory_mb FLOAT,
            compute_type VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    duck.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY,
            actor_id INTEGER,
            event_type VARCHAR,
            severity VARCHAR,
            message VARCHAR,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    duck.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            metric_id INTEGER PRIMARY KEY,
            actor_id INTEGER,
            metric_name VARCHAR,
            value FLOAT,
            unit VARCHAR,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Seed actors
    duck.execute("DELETE FROM actors")
    actors = [
        (1, "PaniniRagEngine", "RAG", "RUNNING", 4500.0, "CPU/RAM"),
        (2, "SnowflakeArcticEmbed", "EMBEDDING", "RUNNING", 6200.0, "GPU/VRAM"),
        (3, "SovereignSieve", "FILTER", "RUNNING", 2100.0, "CPU/RAM"),
        (4, "ACPControlPlane", "CONTROL", "RUNNING", 1000.0, "CPU/RAM"),
        (5, "DuckDBAnalytics", "ANALYTICS", "RUNNING", 512.0, "CPU/RAM"),
        (6, "LanceVectorStore", "VECTOR_DB", "RUNNING", 800.0, "CPU/RAM"),
        (7, "MontyCodeSandbox", "SANDBOX", "IDLE", 256.0, "CPU/RAM"),
        (8, "TantivyFTSEngine", "SEARCH", "RUNNING", 350.0, "CPU/RAM"),
    ]
    duck.executemany("INSERT INTO actors VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)", actors)
    
    # Seed events
    duck.execute("DELETE FROM events")
    events = [
        (1, 2, "OOM_WARNING", "HIGH", "SnowflakeArcticEmbed approaching VRAM limit at 6.1GB"),
        (2, 1, "QUERY_SLOW", "MEDIUM", "PaniniRagEngine query latency >500ms on knowledge graph"),
        (3, 6, "INDEX_REBUILD", "INFO", "LanceVectorStore IVF_PQ index rebuilt — 50k vectors"),
        (4, 3, "ANOMALY_DETECTED", "HIGH", "SovereignSieve flagged 23 corrupted embeddings"),
        (5, 4, "SCALE_REQUEST", "MEDIUM", "ACPControlPlane requesting additional worker node"),
        (6, 8, "FTS_SYNC", "INFO", "Tantivy full-text index synced — 12k documents"),
        (7, 2, "OOM_CRITICAL", "CRITICAL", "SnowflakeArcticEmbed VRAM exhausted — inference paused"),
        (8, 1, "CACHE_MISS", "LOW", "PaniniRagEngine cache miss rate at 34%"),
    ]
    duck.executemany("INSERT INTO events VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)", events)
    
    # Seed metrics
    duck.execute("DELETE FROM metrics")
    metrics = [
        (1, 1, "query_latency_ms", 487.0, "ms"),
        (2, 1, "cache_hit_rate", 0.66, "ratio"),
        (3, 2, "vram_usage_gb", 6.18, "GB"),
        (4, 2, "embedding_throughput", 142.0, "vectors/sec"),
        (5, 3, "anomalies_detected", 23.0, "count"),
        (6, 3, "filter_throughput", 8500.0, "records/sec"),
        (7, 4, "active_workers", 39.0, "count"),
        (8, 6, "vector_count", 50000.0, "count"),
        (9, 6, "search_latency_ms", 12.3, "ms"),
        (10, 8, "indexed_documents", 12000.0, "count"),
    ]
    duck.executemany("INSERT INTO metrics VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)", metrics)
    
    duck.close()
    print(f"   ✅ DuckDB seeded: {DUCK_PATH}")
    
    # LanceDB — vector store with embeddings
    print("   📦 Bootstrapping LanceDB...")
    lance_db = lancedb.connect(LANCE_DIR)
    
    rng = np.random.default_rng(42)
    num_vectors = 200
    dim = 128  # smaller dim for speed
    
    vectors = rng.standard_normal((num_vectors, dim)).astype(np.float32)
    # Normalize
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors = vectors / norms
    
    documents = []
    components = ["RAG", "FILTER", "CONTROL", "EMBEDDING", "ANALYTICS", "SEARCH"]
    severities = ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
    for i in range(num_vectors):
        documents.append({
            "id": i,
            "text": f"Document {i}: System log entry for {components[i % len(components)]} component — severity {severities[i % len(severities)]}",
            "component": components[i % len(components)],
            "severity": severities[i % len(severities)],
            "vector": vectors[i].tolist(),
        })
    
    # Create or overwrite table
    try:
        lance_db.drop_table("embeddings")
    except Exception:
        pass
    
    lance_db.create_table("embeddings", documents)
    print(f"   ✅ LanceDB seeded: {LANCE_DIR} — {num_vectors} vectors @ {dim}D")
    
    return duck, lance_db


# ═══════════════════════════════════════════════════════════════════════════
# TOOL IMPLEMENTATIONS — Real DuckDB + LanceDB queries
# ═══════════════════════════════════════════════════════════════════════════

def query_duckdb(sql):
    """Execute a SQL query against the live DuckDB database."""
    try:
        duck = duckdb.connect(DUCK_PATH, read_only=True)
        arrow_tbl = duck.execute(sql).fetch_arrow_table()
        duck.close()
        pydict = arrow_tbl.to_pydict()
        # Convert pyarrow dictionary to list of records
        cols = list(pydict.keys())
        num_rows = len(pydict[cols[0]]) if cols else 0
        records = []
        for i in range(min(num_rows, 50)):
            records.append({col: pydict[col][i] for col in cols})
        return json.dumps({
            "status": "OK",
            "row_count": num_rows,
            "columns": cols,
            "rows": records,
        }, indent=2, default=str)
    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})


def search_vectors(query_text, top_k=5, filter_expr=None):
    """Search LanceDB vector store by text similarity."""
    try:
        lance_db = lancedb.connect(LANCE_DIR)
        table = lance_db.open_table("embeddings")
        
        # Generate a pseudo-query vector (in production you'd embed the text)
        rng = np.random.default_rng(hash(query_text) % (2**31))
        query_vec = rng.standard_normal(128).astype(np.float32)
        query_vec = query_vec / np.linalg.norm(query_vec)
        
        search = table.search(query_vec.tolist()).limit(top_k)
        if filter_expr:
            search = search.where(filter_expr)
        
        results = search.to_pandas()
        # Drop the vector column for readability
        if "vector" in results.columns:
            results = results.drop(columns=["vector"])
        
        records = results.to_dict(orient="records")
        return json.dumps({
            "status": "OK",
            "query": query_text,
            "top_k": top_k,
            "filter": filter_expr,
            "results": records,
        }, indent=2, default=str)
    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})


def get_lance_table_info():
    """Get schema and stats for the LanceDB embeddings table."""
    try:
        lance_db = lancedb.connect(LANCE_DIR)
        table = lance_db.open_table("embeddings")
        schema = table.schema
        count = table.count_rows()
        
        fields = []
        for field in schema:
            fields.append({"name": field.name, "type": str(field.type)})
        
        return json.dumps({
            "status": "OK",
            "table": "embeddings",
            "row_count": count,
            "schema": fields,
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})


def duckdb_to_lance_join(sql, vector_query, top_k=10):
    """Run a DuckDB SQL query, then join results with LanceDB vector search via Arrow."""
    try:
        # Step 1: DuckDB query via Arrow
        duck = duckdb.connect(DUCK_PATH, read_only=True)
        arrow_tbl = duck.execute(sql).fetch_arrow_table()
        duck.close()
        
        pydict = arrow_tbl.to_pydict()
        cols = list(pydict.keys())
        num_rows = len(pydict[cols[0]]) if cols else 0
        duck_records = [{col: pydict[col][i] for col in cols} for i in range(min(num_rows, 20))]
        
        # Step 2: LanceDB vector search
        lance_db = lancedb.connect(LANCE_DIR)
        table = lance_db.open_table("embeddings")
        rng = np.random.default_rng(hash(vector_query) % (2**31))
        query_vec = rng.standard_normal(128).astype(np.float32)
        query_vec = query_vec / np.linalg.norm(query_vec)
        
        lance_results = table.search(query_vec.tolist()).limit(top_k).to_arrow().to_pydict()
        l_cols = [c for c in lance_results.keys() if c != "vector"]
        l_rows = len(lance_results[l_cols[0]]) if l_cols else 0
        lance_records = [{col: lance_results[col][i] for col in l_cols} for i in range(l_rows)]
        
        return json.dumps({
            "status": "OK",
            "duckdb_query": sql,
            "duckdb_rows": num_rows,
            "duckdb_data": duck_records,
            "lance_query": vector_query,
            "lance_results": lance_records,
            "bridge": "Arrow zero-copy"
        }, indent=2, default=str)
    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})


def get_cluster_health():
    """Combined health view: DuckDB actors + metrics + LanceDB stats."""
    try:
        duck = duckdb.connect(DUCK_PATH, read_only=True)
        arrow_tbl = duck.execute("""
            SELECT a.name, a.component, a.status, a.memory_mb, a.compute_type,
                   COUNT(e.event_id) as event_count,
                   MAX(CASE WHEN e.severity = 'CRITICAL' THEN 1 ELSE 0 END) as has_critical
            FROM actors a
            LEFT JOIN events e ON a.actor_id = e.actor_id
            GROUP BY a.name, a.component, a.status, a.memory_mb, a.compute_type
            ORDER BY a.memory_mb DESC
        """).fetch_arrow_table()
        
        pydict = arrow_tbl.to_pydict()
        cols = list(pydict.keys())
        num_rows = len(pydict[cols[0]]) if cols else 0
        actors_list = [{col: pydict[col][i] for col in cols} for i in range(num_rows)]
        
        total_memory = duck.execute("SELECT SUM(memory_mb) FROM actors").fetchone()[0]
        critical_count = duck.execute("SELECT COUNT(*) FROM events WHERE severity = 'CRITICAL'").fetchone()[0]
        duck.close()
        
        lance_db = lancedb.connect(LANCE_DIR)
        table = lance_db.open_table("embeddings")
        vector_count = table.count_rows()
        
        return json.dumps({
            "status": "OK",
            "actors": actors_list,
            "total_memory_mb": total_memory,
            "total_memory_gb": round(total_memory / 1024, 2),
            "critical_events": critical_count,
            "lance_vector_count": vector_count,
            "health": "CRITICAL" if critical_count > 0 else "HEALTHY"
        }, indent=2, default=str)
    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})


# ═══════════════════════════════════════════════════════════════════════════
# TOOL REGISTRY
# ═══════════════════════════════════════════════════════════════════════════

TOOL_FUNCTIONS = {
    "query_duckdb": lambda **kw: query_duckdb(kw["sql"]),
    "search_vectors": lambda **kw: search_vectors(kw["query_text"], kw.get("top_k", 5), kw.get("filter_expr")),
    "get_lance_table_info": lambda **kw: get_lance_table_info(),
    "duckdb_to_lance_join": lambda **kw: duckdb_to_lance_join(kw["sql"], kw["vector_query"], kw.get("top_k", 10)),
    "get_cluster_health": lambda **kw: get_cluster_health(),
}

TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "query_duckdb",
        "description": "Execute a SQL query on the cluster's DuckDB database. Tables: actors (actor_id, name, component, status, memory_mb, compute_type), events (event_id, actor_id, event_type, severity, message), metrics (metric_id, actor_id, metric_name, value, unit).",
        "parameters": {"type": "object", "properties": {
            "sql": {"type": "string", "description": "SQL query to execute"}
        }, "required": ["sql"]}
    }},
    {"type": "function", "function": {
        "name": "search_vectors",
        "description": "Search the LanceDB vector store for similar documents by semantic query. Returns top-k nearest neighbors with text, component, and severity.",
        "parameters": {"type": "object", "properties": {
            "query_text": {"type": "string", "description": "Natural language search query"},
            "top_k": {"type": "integer", "description": "Number of results (default 5)"},
            "filter_expr": {"type": "string", "description": "Optional SQL filter e.g. \"component = 'RAG'\""}
        }, "required": ["query_text"]}
    }},
    {"type": "function", "function": {
        "name": "get_lance_table_info",
        "description": "Get schema, row count, and metadata for the LanceDB embeddings table.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }},
    {"type": "function", "function": {
        "name": "duckdb_to_lance_join",
        "description": "Hybrid query: runs a SQL query on DuckDB for structured data, then joins with a LanceDB vector search via Arrow zero-copy. Use for combining SQL analytics with vector similarity.",
        "parameters": {"type": "object", "properties": {
            "sql": {"type": "string", "description": "DuckDB SQL query"},
            "vector_query": {"type": "string", "description": "Semantic search text for LanceDB"},
            "top_k": {"type": "integer", "description": "Number of vector results (default 10)"}
        }, "required": ["sql", "vector_query"]}
    }},
    {"type": "function", "function": {
        "name": "get_cluster_health",
        "description": "Get combined cluster health: all actors with memory usage, event counts, critical alerts, and LanceDB vector store stats.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }},
]


# ═══════════════════════════════════════════════════════════════════════════
# JINJA2 SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════════════════
jinja_env = Environment(loader=BaseLoader(), trim_blocks=True, lstrip_blocks=True)

SYSTEM_PROMPT = jinja_env.from_string("""
You are SOVEREIGN DATA ANALYST — connected to a live DuckDB + LanceDB cluster.

You DO NOT execute queries yourself. You REQUEST data from external database services.

## LIVE DATABASES
- **DuckDB** ({{ duck_path }}): SQL analytics on cluster actors, events, metrics
- **LanceDB** ({{ lance_dir }}): Vector store with {{ vector_count }} embeddings @ 128D

## DuckDB SCHEMA
- `actors`: actor_id, name, component, status, memory_mb, compute_type
- `events`: event_id, actor_id, event_type, severity, message
- `metrics`: metric_id, actor_id, metric_name, value, unit

## AVAILABLE SERVICES
- `query_duckdb` — Run any SQL query on DuckDB
- `search_vectors` — Semantic search on LanceDB with optional filters
- `get_lance_table_info` — Schema and stats for the vector table
- `duckdb_to_lance_join` — Hybrid SQL + vector search via Arrow zero-copy
- `get_cluster_health` — Combined health dashboard

## RULES
- Use services to answer the user's questions with REAL data
- Write proper SQL for DuckDB queries
- Use hybrid queries when combining structured + semantic search
- Be specific — cite actual numbers from the query results
""")


# ═══════════════════════════════════════════════════════════════════════════
# STREAMING LOOP
# ═══════════════════════════════════════════════════════════════════════════

def stream_response(messages):
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        tools=TOOL_SCHEMAS,
        tool_choice="auto",
        temperature=0.2,
        stream=True,
        max_tokens=4096,
    )
    tool_calls = []
    content = ""
    for chunk in response:
        delta = chunk.choices[0].delta
        if delta.content:
            print(delta.content, end="", flush=True)
            content += delta.content
        if delta.tool_calls:
            for tc_chunk in delta.tool_calls:
                while len(tool_calls) <= tc_chunk.index:
                    tool_calls.append({"id": "", "type": "function",
                                       "function": {"name": "", "arguments": ""}})
                tc = tool_calls[tc_chunk.index]
                if tc_chunk.id:
                    tc["id"] += tc_chunk.id
                if tc_chunk.function.name:
                    tc["function"]["name"] += tc_chunk.function.name
                if tc_chunk.function.arguments:
                    tc["function"]["arguments"] += tc_chunk.function.arguments
    return content, tool_calls


def run_data_agent():
    # Bootstrap databases
    print("=" * 80)
    print("SOVEREIGN DATA AGENT - DuckDB + LanceDB + Streaming")
    print("=" * 80)
    
    bootstrap_databases()
    
    # Get vector count for prompt
    lance_db = lancedb.connect(LANCE_DIR)
    table = lance_db.open_table("embeddings")
    vector_count = table.count_rows()
    
    system_prompt = SYSTEM_PROMPT.render(
        duck_path=DUCK_PATH,
        lance_dir=LANCE_DIR,
        vector_count=vector_count,
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": (
            "Give me a full cluster health report. Check which actors are consuming the most memory, "
            "find any CRITICAL events, then do a hybrid search combining the SQL event data with "
            "vector similarity to find related system logs. I need to know what's breaking and why."
        )}
    ]
    
    print(f"\n   Model:    {LLM_MODEL}")
    print(f"   DuckDB:   {DUCK_PATH}")
    print(f"   LanceDB:  {LANCE_DIR} ({vector_count} vectors)")
    print(f"   Tools:    {len(TOOL_SCHEMAS)}")
    print("=" * 80)
    
    start_time = time.time()
    
    for turn in range(1, MAX_TURNS + 1):
        print(f"\n{'─' * 80}")
        print(f"  ⟳ TURN {turn}/{MAX_TURNS}")
        print(f"{'─' * 80}\n")
        
        print("🤖 ", end="", flush=True)
        content, tool_calls = stream_response(messages)
        print()
        
        assistant_msg = {"role": "assistant"}
        if content:
            assistant_msg["content"] = content
        if tool_calls:
            assistant_msg["tool_calls"] = tool_calls
            if "content" not in assistant_msg:
                assistant_msg["content"] = None
        messages.append(assistant_msg)
        
        if not tool_calls:
            # No more tool calls — LLM is done talking
            break
        
        for tc in tool_calls:
            fn_name = tc["function"]["name"]
            fn_args_str = tc["function"]["arguments"]
            try:
                fn_args = json.loads(fn_args_str) if fn_args_str else {}
            except json.JSONDecodeError:
                fn_args = {}
            
            print(f"\n   🎯 SERVICE: {fn_name}")
            if fn_args:
                display = {k: (v[:80] + "..." if isinstance(v, str) and len(v) > 80 else v)
                           for k, v in fn_args.items()}
                print(f"      Query:  {json.dumps(display)}")
            
            try:
                tool_result = TOOL_FUNCTIONS[fn_name](**fn_args)
            except Exception as e:
                tool_result = json.dumps({"error": f"{type(e).__name__}: {e}"})
            
            if len(tool_result) > MAX_TOOL_CHARS:
                tool_result = tool_result[:MAX_TOOL_CHARS] + f"\n... [TRUNCATED — {len(tool_result)} total chars]"
            
            preview = tool_result[:500]
            if len(tool_result) > 500:
                preview += f"\n      ... ({len(tool_result)} chars)"
            print(f"   ⚡ Data: {preview}")
            
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": tool_result
            })
    
    elapsed = time.time() - start_time
    print(f"\n{'═' * 80}")
    print(f"  🏁 SOVEREIGN DATA AGENT COMPLETE")
    print(f"     Turns: {turn} | Elapsed: {elapsed:.1f}s")
    print(f"{'═' * 80}")


if __name__ == "__main__":
    run_data_agent()
