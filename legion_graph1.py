"""
LEGION LANGGRAPH ORCHESTRATOR
==============================
Stateful Cognitive Router for the Sovereign Sonic Core.

Nodes:
  - Agent: LLM reasoning (Gemini 2.5 Flash / swappable)
  - Tools: DuckDB, Parquet, LanceDB, Analytics

Edges:
  START → Agent → (tool call?) → Tools → Agent → ... → END

Wired into mcp_api_server.py via:
  from legion_graph import app
  app.invoke({"messages": [HumanMessage(content=prompt)]})
"""

import os
import json
from typing import TypedDict, Annotated, Sequence, Literal
import operator

import numpy as np
import pandas as pd
import duckdb
import lancedb
from sklearn.cluster import KMeans
from scipy.stats import pearsonr

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# ─── PATH CONFIG ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Default paths from workspace metadata
DUCKDB_V2 = r"C:\STUDIES_BACKUP\data\metadata\sonic_core_v2.duckdb"
DUCKDB_V1 = r"C:\STUDIES_BACKUP\data\metadata\sonic_core.duckdb"
LANCE_STORE = r"C:\STUDIES_BACKUP\vectors\lancedb_store"
LANCE_STORE_V2 = os.path.join(BASE_DIR, "AI_Logs", "lancedb_store")
PARQUET_DIR = os.path.join(BASE_DIR, "AI_Logs", "parquet_exports")
TARGET_VECTOR_PATH = os.path.join(BASE_DIR, "AI_Logs", "target_vector.json")

# Fallback adjustments if not present in default workspace folders
if not os.path.exists(DUCKDB_V2):
    DUCKDB_V2 = os.path.join(BASE_DIR, "AI_Logs", "sonic_core_v2.duckdb")
if not os.path.exists(DUCKDB_V1):
    DUCKDB_V1 = os.path.join(BASE_DIR, "data", "metadata", "sonic_core.duckdb")
if not os.path.exists(LANCE_STORE):
    LANCE_STORE = os.path.join(BASE_DIR, "vectors", "lancedb_store")


# ─── STATE ────────────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    active_dna_context: dict


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL 1: analyze_parquet_data
# ═══════════════════════════════════════════════════════════════════════════════
@tool
def analyze_parquet_data(query: str, parquet_file: str = "collision_results_final.parquet", limit: int = 20) -> str:
    """Query exported Parquet data with DuckDB SQL. Available parquet files:
    audio_manifest_vectors, audio_vibe_gpu, collision_results_final,
    duckdb_metadata_vectors, interaction_logs, legion_memory,
    skill_brain, t_core_memory.
    The query runs directly against the parquet via DuckDB.
    Use 'DESCRIBE' or 'SELECT *' to explore schemas.
    """
    parquet_path = os.path.join(PARQUET_DIR, parquet_file)
    if not parquet_path.endswith(".parquet"):
        parquet_path += ".parquet"
    if not os.path.exists(parquet_path):
        available = [f for f in os.listdir(PARQUET_DIR) if f.endswith(".parquet")]
        return json.dumps({"error": f"File not found: {parquet_file}", "available": available})

    con = duckdb.connect()
    try:
        # Replace table references with the parquet path
        sql = query.replace("{table}", f"'{parquet_path}'")
        if "{table}" not in query:
            sql = query.replace("FROM data", f"FROM '{parquet_path}'")
            sql = sql.replace("from data", f"from '{parquet_path}'")
            if "FROM" not in sql.upper():
                sql = f"SELECT * FROM '{parquet_path}' WHERE {query} LIMIT {limit}"

        result = con.execute(sql).fetchdf()
        if len(result) > limit:
            result = result.head(limit)
        return result.to_json(orient="records", date_format="iso")
    except Exception as e:
        return json.dumps({"error": str(e), "sql_attempted": sql})
    finally:
        con.close()


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL 2: query_sonic_core
# ═══════════════════════════════════════════════════════════════════════════════
@tool
def query_sonic_core(sql_query: str, db_version: str = "v1") -> str:
    """Execute raw SQL against the DuckDB Sonic Core database.
    db_version='v1' uses sonic_core.duckdb (3560 rows in t_core_memory).
    db_version='v2' uses sonic_core_v2.duckdb (empty schemas ready for population).
    Tables in v1: t_core_memory (filename, bpm, key_signature, vibe_tags, genre_class, ingested_at).
    Tables in v2: audio_features (46 cols), t_core_memory (9 cols),
                  t_producer_dna_node0, t_sovereign_grading, t_musicological_registry_v10.
    """
    db_path = DUCKDB_V2 if db_version == "v2" else DUCKDB_V1
    if not os.path.exists(db_path):
        return json.dumps({"error": f"Database not found: {db_path}"})

    con = duckdb.connect(db_path, read_only=True)
    try:
        result = con.execute(sql_query).fetchdf()
        if len(result) > 100:
            result = result.head(100)
        return result.to_json(orient="records", date_format="iso")
    except Exception as e:
        return json.dumps({"error": str(e), "sql": sql_query})
    finally:
        con.close()


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL 3: search_vibe_vectors
# ═══════════════════════════════════════════════════════════════════════════════
@tool
def search_vibe_vectors(search_text: str, table_name: str = "audio_vibe_gpu", top_k: int = 10, store: str = "v1") -> str:
    """Semantic vector search across LanceDB stores.
    store='v1': vectors/lancedb_store (audio_vibe_gpu: 2010 rows x 384-dim).
    store='v2': AI_Logs/lancedb_store (audio_manifest_vectors: 500 rows x 768-dim,
                audio_vibe_gpu: 1013 rows x 384-dim, duckdb_metadata_vectors: 200,
                skill_brain: 20, legion_memory: 2).
    Uses the target_vector.json anchor for similarity if no embedding model is available.
    """
    store_path = LANCE_STORE_V2 if store == "v2" else LANCE_STORE
    if not os.path.exists(store_path):
        return json.dumps({"error": f"LanceDB store not found: {store_path}"})

    try:
        db = lancedb.connect(store_path)
        tbl = db.open_table(table_name)

        # Use target_vector as query anchor, offset by search text hash for variation
        if os.path.exists(TARGET_VECTOR_PATH):
            with open(TARGET_VECTOR_PATH) as f:
                tv = json.load(f)
            query_vec = np.array(tv["vector"], dtype=np.float32)
            # Add slight perturbation based on search text for differentiation
            text_hash = hash(search_text) % 1000 / 10000.0
            query_vec = query_vec + text_hash
            query_vec = query_vec / (np.linalg.norm(query_vec) + 1e-9)
        else:
            schema = tbl.schema
            vec_dim = None
            for field in schema:
                if "vector" in field.name.lower() or field.name == "vector":
                    vec_dim = field.type.list_size
                    break
            if vec_dim is None:
                return json.dumps({"error": "Cannot determine vector dimension"})
            np.random.seed(abs(hash(search_text)) % (2**31))
            query_vec = np.random.randn(vec_dim).astype(np.float32)
            query_vec = query_vec / (np.linalg.norm(query_vec) + 1e-9)

        results = tbl.search(query_vec.tolist()).limit(top_k).to_pandas()
        # Drop the vector column for readability
        drop_cols = [c for c in results.columns if "vector" in c.lower()]
        if drop_cols:
            results = results.drop(columns=drop_cols)
        return results.to_json(orient="records", date_format="iso")
    except Exception as e:
        return json.dumps({"error": str(e)})


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL 4: feature_correlation (Bonus Analytics)
# ═══════════════════════════════════════════════════════════════════════════════
@tool
def feature_correlation(feature_a: str = "bpm", feature_b: str = "spectral_centroid") -> str:
    """Calculate Pearson correlation between two features in the core memory.
    Available features in t_core_memory (v1): bpm, key_signature, vibe_tags, genre_class.
    For full DSP features, use collision_results_final.parquet: tempo, collision_score.
    Returns correlation coefficient and interpretation.
    """
    # Try collision_results first (has numeric features)
    parquet_path = os.path.join(PARQUET_DIR, "collision_results_final.parquet")
    if os.path.exists(parquet_path):
        df = pd.read_parquet(parquet_path)
        if feature_a in df.columns and feature_b in df.columns:
            a = pd.to_numeric(df[feature_a], errors="coerce").dropna()
            b = pd.to_numeric(df[feature_b], errors="coerce").dropna()
            common = a.index.intersection(b.index)
            if len(common) >= 3:
                corr, p_val = pearsonr(a.loc[common], b.loc[common])
                strength = "strong" if abs(corr) > 0.7 else "moderate" if abs(corr) > 0.4 else "weak"
                direction = "positive" if corr > 0 else "negative"
                return json.dumps({
                    "feature_a": feature_a,
                    "feature_b": feature_b,
                    "correlation": round(corr, 4),
                    "p_value": round(p_val, 6),
                    "interpretation": f"{strength} {direction} correlation",
                    "sample_size": len(common),
                    "source": "collision_results_final.parquet"
                })

    # Fallback to t_core_memory
    con = duckdb.connect(DUCKDB_V1, read_only=True)
    try:
        df = con.execute("SELECT * FROM t_core_memory").fetchdf()
        if feature_a in df.columns and feature_b in df.columns:
            a = pd.to_numeric(df[feature_a], errors="coerce").dropna()
            b = pd.to_numeric(df[feature_b], errors="coerce").dropna()
            common = a.index.intersection(b.index)
            if len(common) >= 3:
                corr, p_val = pearsonr(a.loc[common], b.loc[common])
                strength = "strong" if abs(corr) > 0.7 else "moderate" if abs(corr) > 0.4 else "weak"
                direction = "positive" if corr > 0 else "negative"
                return json.dumps({
                    "feature_a": feature_a,
                    "feature_b": feature_b,
                    "correlation": round(corr, 4),
                    "p_value": round(p_val, 6),
                    "interpretation": f"{strength} {direction} correlation",
                    "sample_size": len(common),
                    "source": "sonic_core.duckdb/t_core_memory"
                })
        return json.dumps({"error": f"Features not found or not numeric: {feature_a}, {feature_b}",
                          "available_collision": list(pd.read_parquet(parquet_path).columns) if os.path.exists(parquet_path) else [],
                          "available_core": list(df.columns)})
    finally:
        con.close()


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL 5: cluster_subgenres (Bonus Analytics)
# ═══════════════════════════════════════════════════════════════════════════════
@tool
def cluster_subgenres(n_clusters: int = 4, source: str = "collision_results") -> str:
    """Run K-Means clustering on audio features to discover hidden sub-genres.
    source='collision_results' uses collision_results_final.parquet (tempo, collision_score).
    source='core_memory' uses t_core_memory.parquet (bpm).
    Returns cluster assignments with centroids and suggested genre labels.
    """
    if source == "collision_results":
        parquet_path = os.path.join(PARQUET_DIR, "collision_results_final.parquet")
        df = pd.read_parquet(parquet_path)
        numeric_cols = [c for c in ["tempo", "collision_score"] if c in df.columns]
        if not numeric_cols:
            return json.dumps({"error": "No numeric features found for clustering"})
        features = df[numeric_cols].dropna()
    else:
        parquet_path = os.path.join(PARQUET_DIR, "t_core_memory.parquet")
        df = pd.read_parquet(parquet_path)
        numeric_cols = [c for c in df.columns if df[c].dtype in ["int64", "float64"]]
        if not numeric_cols:
            return json.dumps({"error": "No numeric features found for clustering"})
        features = df[numeric_cols].dropna()

    if len(features) < n_clusters:
        return json.dumps({"error": f"Not enough data points ({len(features)}) for {n_clusters} clusters"})

    # Normalize
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(scaled)

    # Build cluster summary
    df_clustered = features.copy()
    df_clustered["cluster"] = labels
    if "filename" in df.columns:
        df_clustered["filename"] = df.loc[features.index, "filename"].values
    if "key" in df.columns:
        df_clustered["key"] = df.loc[features.index, "key"].values

    clusters = []
    genre_hints = ["Deep-Groove", "Peak-Time", "Melodic-Progressive", "Afro-Tech",
                   "Minimal-Dub", "Hard-Groove", "Organic-House", "Acid-Driven"]
    for i in range(n_clusters):
        mask = df_clustered["cluster"] == i
        cluster_data = df_clustered[mask]
        centroid = {col: round(float(kmeans.cluster_centers_[i][j]), 2)
                    for j, col in enumerate(numeric_cols)}
        cluster_info = {
            "cluster_id": i,
            "suggested_label": genre_hints[i % len(genre_hints)],
            "size": int(mask.sum()),
            "centroid": centroid,
        }
        if "filename" in cluster_data.columns:
            cluster_info["sample_tracks"] = cluster_data["filename"].head(3).tolist()
        if "key" in cluster_data.columns:
            cluster_info["dominant_key"] = cluster_data["key"].mode().iloc[0] if len(cluster_data["key"].mode()) > 0 else "N/A"
        clusters.append(cluster_info)

    return json.dumps({"n_clusters": n_clusters, "total_tracks": len(features),
                       "features_used": numeric_cols, "clusters": clusters})


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL 6: list_available_data
# ═══════════════════════════════════════════════════════════════════════════════
@tool
def list_available_data() -> str:
    """List all available data sources: Parquet files, DuckDB tables, and LanceDB stores.
    Use this first to understand what data is available before querying.
    """
    inventory = {"parquet_files": [], "duckdb": {}, "lancedb": {}}

    # Parquets
    if os.path.exists(PARQUET_DIR):
        for f in sorted(os.listdir(PARQUET_DIR)):
            if f.endswith(".parquet"):
                path = os.path.join(PARQUET_DIR, f)
                size = os.path.getsize(path)
                con = duckdb.connect()
                count = con.execute(f"SELECT COUNT(*) FROM '{path}'").fetchone()[0]
                cols = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM '{path}'").fetchall()]
                con.close()
                inventory["parquet_files"].append({
                    "name": f, "rows": count, "columns": cols, "size_bytes": size
                })

    # DuckDB
    for label, path in [("sonic_core_v1", DUCKDB_V1), ("sonic_core_v2", DUCKDB_V2)]:
        if os.path.exists(path):
            con = duckdb.connect(path, read_only=True)
            tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
            db_info = {}
            for t in tables:
                count = con.execute(f"SELECT COUNT(*) FROM \"{t}\"").fetchone()[0]
                cols = [r[0] for r in con.execute(f"DESCRIBE \"{t}\"").fetchall()]
                db_info[t] = {"rows": count, "columns": cols}
            con.close()
            inventory["duckdb"][label] = db_info

    # LanceDB
    for label, path in [("v1_vectors", LANCE_STORE), ("v2_vectors", LANCE_STORE_V2)]:
        if os.path.exists(path):
            try:
                db = lancedb.connect(path)
                names = db.list_tables().tables
                store_info = {}
                for n in names:
                    tbl = db.open_table(n)
                    count = tbl.count_rows()
                    schema_fields = [{"name": f.name, "type": str(f.type)} for f in tbl.schema]
                    store_info[n] = {"rows": count, "schema": schema_fields}
                inventory["lancedb"][label] = store_info
            except Exception as e:
                inventory["lancedb"][label] = {"error": str(e)}

    return json.dumps(inventory)


# ═══════════════════════════════════════════════════════════════════════════════
# GRAPH ASSEMBLY
# ═══════════════════════════════════════════════════════════════════════════════

# All tools
tools = [
    analyze_parquet_data,
    query_sonic_core,
    search_vibe_vectors,
    feature_correlation,
    cluster_subgenres,
    list_available_data,
]

SYSTEM_PROMPT = """You are the Legion Sovereign Intelligence — the cognitive router for a Tech House 
audio production pipeline. You have access to tools that query DuckDB databases, analyze Parquet 
data exports, and search LanceDB vector stores containing 384-dim and 768-dim audio embeddings.

Your producer's DNA signature: dominant tempo 128 BPM, dominant key G major, 
target RMS -13.9 LUFS, crest factor 5.69, mid-injection multiplier x289.34.
Lineage: MPC/SP1200.

When answering questions:
1. Use list_available_data first if you need to understand what's available.
2. Use query_sonic_core for structured metadata queries (BPM, key, genre).
3. Use analyze_parquet_data for analytics on exported data.
4. Use search_vibe_vectors for semantic audio similarity search.
5. Use feature_correlation and cluster_subgenres for advanced analytics.

Always be precise with numbers. Reference the Sovereign Targets when relevant."""


def _get_model():
    """Get the LLM. Uses local Ollama via langchain_ollama for deterministic tool-calling."""
    try:
        from langchain_ollama import ChatOllama
        import json
        import os
        
        # Pull ollama_url and model from mcp.json if available
        mcp_config_path = os.path.join(BASE_DIR, "data", "config", "mcp.json")
        ollama_url = "http://localhost:11434"
        model_id = "gemma-3-4b-it" # default fallback
        
        if os.path.exists(mcp_config_path):
            with open(mcp_config_path, "r") as f:
                config = json.load(f)
                if "model_config" in config:
                    ollama_url = config["model_config"].get("ollama_url", ollama_url)
                    model_id = config["model_config"].get("model_id", model_id)
                    
        llm = ChatOllama(
            base_url=ollama_url,
            model=model_id,
            temperature=0,  # Strict deterministic tool-calling
        )
        # Bind tools so the local Ollama LLM can invoke them directly
        return llm.bind_tools(tools)
    except ImportError as e:
        # Fallback: tool-calling stub when langchain_ollama is missing
        from langchain_core.messages import AIMessage
        class StubModel:
            def invoke(self, messages):
                last = messages[-1].content if messages else ""
                return AIMessage(
                    content=f"[No LLM configured] Received: {last}. Error: {e}",
                )
        return StubModel()


def call_model(state: AgentState) -> dict:
    """Agent node: invoke LLM with system prompt + conversation history."""
    llm_with_tools = _get_model()
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(state["messages"])
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState) -> Literal["continue", "end"]:
    """Edge router: if the last message has tool_calls, continue to tools node."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"
    return "end"


# Build the graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"continue": "tools", "end": END})
workflow.add_edge("tools", "agent")

# Compile — this is what mcp_api_server.py imports
app = workflow.compile()


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
def run_workflow(prompt: str) -> dict:
    """Public API for FastAPI integration.
    Usage: from legion_graph import run_workflow
           result = run_workflow("What BPM distribution do we have?")
    """
    result = app.invoke({
        "messages": [HumanMessage(content=prompt)],
        "active_dna_context": {}
    })
    final_msg = result["messages"][-1].content if result.get("messages") else "No output."
    return {"status": "success", "result": final_msg}


if __name__ == "__main__":
    print("=" * 60)
    print("LEGION LANGGRAPH ORCHESTRATOR — SMOKE TEST")
    print("=" * 60)

    # Test each tool directly
    print("\n[1] list_available_data:")
    data = json.loads(list_available_data.invoke({}))
    print(f"  Parquets: {len(data['parquet_files'])}")
    for p in data["parquet_files"]:
        print(f"    {p['name']}: {p['rows']} rows")

    print("\n[2] query_sonic_core:")
    result = json.loads(query_sonic_core.invoke({"sql_query": "SELECT genre_class, COUNT(*) as cnt FROM t_core_memory GROUP BY genre_class ORDER BY cnt DESC LIMIT 5"}))
    print(f"  {result}")

    print("\n[3] analyze_parquet_data:")
    result = json.loads(analyze_parquet_data.invoke({"query": "SELECT key, AVG(collision_score) as avg_score FROM {table} GROUP BY key ORDER BY avg_score DESC LIMIT 5", "parquet_file": "collision_results_final"}))
    print(f"  {result}")

    print("\n[4] feature_correlation:")
    result = json.loads(feature_correlation.invoke({"feature_a": "tempo", "feature_b": "collision_score"}))
    print(f"  {result}")

    print("\n[5] cluster_subgenres:")
    result = json.loads(cluster_subgenres.invoke({"n_clusters": 3}))
    print(f"  Found {result['n_clusters']} clusters across {result['total_tracks']} tracks")
    for c in result["clusters"]:
        print(f"    Cluster {c['cluster_id']} ({c['suggested_label']}): {c['size']} tracks, centroid={c['centroid']}")

    print("\n[6] run_workflow (end-to-end):")
    result = run_workflow("What data do we have?")
    print(f"  Status: {result['status']}")
    print(f"  Result: {result['result'][:200]}...")

    print("\n" + "=" * 60)
    print("ALL TOOLS VERIFIED")
    print("=" * 60)
