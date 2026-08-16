
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

# =====================================================================
# LEGION LANGGRAPH ORCHESTRATOR (PHI-3 SWAPPABLE LLM)
# =====================================================================
# Adapted from legion_graph.py (commit b5d1c3d) to use local phi-3 via
# Ollama instead of Gemini 2.5 Flash. The 6 tools are the "inside people"
# that fetch data for phi-3 to reason over.
#
# Architecture:
#   START -> [Agent/phi-3] -> (tool call?) -> [Tools/6 specialists] -> [Agent/phi-3] -> ... -> END
#
# The 6 specialist tools:
#   1. analyze_parquet_data  - DuckDB SQL over parquet exports
#   2. query_sonic_core      - direct DuckDB v1/v2 SQL
#   3. search_vibe_vectors   - LanceDB 384/768-dim semantic search
#   4. feature_correlation   - Pearson analysis (scipy)
#   5. cluster_subgenres     - K-Means discovery (sklearn)
#   6. list_available_data   - full inventory of all stores
# =====================================================================
import os
import sys
import ray
os.environ["LOGFIRE_CONFIG_FILE"] = ""
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import json
import operator
import urllib.request
from typing import TypedDict, Annotated, Sequence, Literal, List, Any, Dict, Optional

import numpy as np
import pandas as pd
import duckdb
import lancedb
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from scipy.stats import pearsonr

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# --- Pydantic validation suite (must be installed via Cell 8 diagnostic) ---
from pydantic import BaseModel, Field


# =====================================================================
# PATH CONFIG (matches legion_graph.py from your git)
# =====================================================================
PROJECT_ROOT = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline"
BASE_DIR = PROJECT_ROOT
PARQUET_DIR = os.path.join(BASE_DIR, "AI_Logs", "parquet_exports")
DUCKDB_V1 = r"C:\STUDIES_BACKUP\data\metadata\sonic_core.duckdb"
DUCKDB_V2 = r"C:\STUDIES_BACKUP\data\metadata\sonic_core_v2.duckdb"
LANCE_STORE = r"C:\STUDIES_BACKUP\vectors\lancedb_store"
LANCE_STORE_V2 = os.path.join(BASE_DIR, "AI_Logs", "lancedb_store")
TARGET_VECTOR_PATH = os.path.join(BASE_DIR, "AI_Logs", "target_vector.json")

# Fallback adjustments
if not os.path.exists(DUCKDB_V2):
    DUCKDB_V2 = os.path.join(BASE_DIR, "AI_Logs", "sonic_core_v2.duckdb")
if not os.path.exists(DUCKDB_V1):
    DUCKDB_V1 = os.path.join(BASE_DIR, "data", "metadata", "sonic_core.duckdb")

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
LLM_MODEL = os.environ.get("LEGION_LLM", "gemma-2-2b-it-onnx")


# =====================================================================
# AGENT STATE (LangGraph state container)
# =====================================================================
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    active_dna_context: dict


# =====================================================================
# THE 6 SPECIALIST TOOLS (the "inside people" that fetch data for phi-3)
# =====================================================================

@tool
def analyze_parquet_data(query: str, parquet_file: str = "collision_results_final.parquet", limit: int = 20) -> str:
    """Query exported Parquet data with DuckDB SQL. Available parquet files include:
    audio_manifest_vectors, audio_vibe_gpu, collision_results_final,
    duckdb_metadata_vectors, interaction_logs, legion_memory, skill_brain, t_core_memory.
    The query runs directly against the parquet via DuckDB.
    Use 'DESCRIBE' or 'SELECT *' to explore schemas.
    """
    parquet_path = os.path.join(PARQUET_DIR, parquet_file)
    if not parquet_path.endswith(".parquet"):
        parquet_path += ".parquet"
    if not os.path.exists(parquet_path):
        available = [f for f in os.listdir(PARQUET_DIR) if f.endswith(".parquet")] if os.path.exists(PARQUET_DIR) else []
        return json.dumps({"error": f"File not found: {parquet_file}", "available": available})

    con = duckdb.connect()
    try:
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
        return json.dumps({"error": str(e), "sql_attempted": sql if 'sql' in dir() else query})
    finally:
        con.close()


@tool
def query_sonic_core(sql_query: str, db_version: str = "v1") -> str:
    """Execute raw SQL against the DuckDB Sonic Core database.
    db_version='v1' uses sonic_core.duckdb (3560 rows in t_core_memory).
    db_version='v2' uses sonic_core_v2.duckdb (audio_features 46 cols,
    t_core_memory 9 cols, t_producer_dna_node0, t_sovereign_grading,
    t_musicological_registry_v10).
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


@tool
def search_vibe_vectors(search_text: str, table_name: str = "audio_vibe_gpu", top_k: int = 10, store: str = "v1") -> str:
    """Semantic vector search across LanceDB stores.
    store='v1': vectors/lancedb_store (audio_vibe_gpu: 384-dim).
    store='v2': AI_Logs/lancedb_store (audio_manifest_vectors: 768-dim,
                audio_vibe_gpu: 384-dim, duckdb_metadata_vectors, skill_brain, legion_memory).
    Uses the target_vector.json anchor for similarity. Phi-3 does not natively embed;
    we use the target_vector as the query anchor, perturbed by the search text hash.
    """
    store_path = LANCE_STORE_V2 if store == "v2" else LANCE_STORE
    if not os.path.exists(store_path):
        return json.dumps({"error": f"LanceDB store not found: {store_path}"})
    try:
        db = lancedb.connect(store_path)
        tbl = db.open_table(table_name)
        if os.path.exists(TARGET_VECTOR_PATH):
            with open(TARGET_VECTOR_PATH) as f:
                tv = json.load(f)
            query_vec = np.array(tv["vector"], dtype=np.float32)
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
        drop_cols = [c for c in results.columns if "vector" in c.lower()]
        if drop_cols:
            results = results.drop(columns=drop_cols)
        return results.to_json(orient="records", date_format="iso")
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def feature_correlation(feature_a: str = "bpm", feature_b: str = "spectral_centroid") -> str:
    """Calculate Pearson correlation between two features in the core memory / collision results."""
    parquet_path = os.path.join(PARQUET_DIR, "collision_results_final.parquet")
    if os.path.exists(parquet_path):
        try:
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
                        "feature_a": feature_a, "feature_b": feature_b,
                        "correlation": round(corr, 4), "p_value": round(p_val, 6),
                        "interpretation": f"{strength} {direction} correlation",
                        "sample_size": len(common),
                        "source": "collision_results_final.parquet"
                    })
        except Exception:
            pass
    if os.path.exists(DUCKDB_V1):
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
                        "feature_a": feature_a, "feature_b": feature_b,
                        "correlation": round(corr, 4), "p_value": round(p_val, 6),
                        "interpretation": f"{strength} {direction} correlation",
                        "sample_size": len(common),
                        "source": "sonic_core.duckdb/t_core_memory"
                    })
            return json.dumps({"error": f"Features not numeric: {feature_a}, {feature_b}"})
        finally:
            con.close()
    return json.dumps({"error": "No data sources available"})


@tool
def cluster_subgenres(n_clusters: int = 4, source: str = "collision_results") -> str:
    """Run K-Means clustering on audio features to discover hidden sub-genres.
    source='collision_results' uses collision_results_final.parquet (tempo, collision_score).
    source='core_memory' uses t_core_memory.parquet (bpm).
    Returns cluster assignments with centroids and suggested genre labels.
    """
    if source == "collision_results":
        parquet_path = os.path.join(PARQUET_DIR, "collision_results_final.parquet")
        if not os.path.exists(parquet_path):
            return json.dumps({"error": "collision_results_final.parquet not found"})
        df = pd.read_parquet(parquet_path)
        numeric_cols = [c for c in ["tempo", "collision_score"] if c in df.columns]
        if not numeric_cols:
            return json.dumps({"error": "No numeric features found for clustering"})
        features = df[numeric_cols].dropna()
    else:
        parquet_path = os.path.join(PARQUET_DIR, "t_core_memory.parquet")
        if not os.path.exists(parquet_path):
            return json.dumps({"error": "t_core_memory.parquet not found"})
        df = pd.read_parquet(parquet_path)
        numeric_cols = [c for c in df.columns if df[c].dtype in ["int64", "float64"]]
        if not numeric_cols:
            return json.dumps({"error": "No numeric features found for clustering"})
        features = df[numeric_cols].dropna()
    if len(features) < n_clusters:
        return json.dumps({"error": f"Not enough data points ({len(features)}) for {n_clusters} clusters"})

    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(scaled)
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
        if "key" in cluster_data.columns and len(cluster_data["key"].mode()) > 0:
            cluster_info["dominant_key"] = cluster_data["key"].mode().iloc[0]
        clusters.append(cluster_info)
    return json.dumps({"n_clusters": n_clusters, "total_tracks": len(features),
                       "features_used": numeric_cols, "clusters": clusters})


@tool
def list_available_data() -> str:
    """List all available data sources: Parquet files, DuckDB tables, and LanceDB stores.
    Use this first to understand what data is available before querying.
    """
    inventory = {"parquet_files": [], "duckdb": {}, "lancedb": {}}
    if os.path.exists(PARQUET_DIR):
        for f in sorted(os.listdir(PARQUET_DIR)):
            if f.endswith(".parquet"):
                path = os.path.join(PARQUET_DIR, f)
                size = os.path.getsize(path)
                con = duckdb.connect()
                try:
                    count = con.execute(f"SELECT COUNT(*) FROM '{path}'").fetchone()[0]
                    cols = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM '{path}'").fetchall()]
                finally:
                    con.close()
                inventory["parquet_files"].append({
                    "name": f, "rows": count, "columns": cols, "size_bytes": size
                })
    for label, path in [("sonic_core_v1", DUCKDB_V1), ("sonic_core_v2", DUCKDB_V2)]:
        if os.path.exists(path):
            con = duckdb.connect(path, read_only=True)
            try:
                tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
                db_info = {}
                for t in tables:
                    count = con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
                    cols = [r[0] for r in con.execute(f'DESCRIBE "{t}"').fetchall()]
                    db_info[t] = {"rows": count, "columns": cols}
            finally:
                con.close()
            inventory["duckdb"][label] = db_info
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


@tool
def fetch_research_articles(query: str, limit: int = 3) -> str:
    """
    Search and fetch research articles using the OpenResearch CLI (orx lit).
    Use this tool to find academic papers or articles related to a topic.
    """
    try:
        import subprocess
        cmd = f"orx lit \"{query}\" --limit {limit} --json"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout if result.returncode == 0 else result.stderr or result.stdout
    except Exception as e:
        return f"Error fetching articles: {str(e)}"

# All 7 specialist tools (the "inside people" that fetch data for phi-3)
TOOLS_LIST = [
    analyze_parquet_data,
    query_sonic_core,
    search_vibe_vectors,
    feature_correlation,
    cluster_subgenres,
    list_available_data,
    fetch_research_articles,
]


# =====================================================================
# PHI-3 LLM CLIENT (local Ollama with tool-calling support)
# =====================================================================

SYSTEM_PROMPT = """You are the Legion Sovereign Intelligence - the cognitive router for a Tech House
audio production pipeline. You have access to 7 specialist tools that query DuckDB databases,
analyze Parquet data exports, search LanceDB vector stores containing 384-dim and 768-dim
audio embeddings, run advanced analytics (Pearson correlation, K-Means clustering), and fetch
research articles using the OpenResearch CLI.

Your producer's DNA signature: dominant tempo 128 BPM, dominant key G major,
target RMS -13.9 LUFS, crest factor 5.69, mid-injection multiplier x289.34.
Lineage: MPC/SP1200.

When answering questions:
1. Use list_available_data first if you need to understand what's available.
2. Use query_sonic_core for structured metadata queries (BPM, key, genre).
3. Use analyze_parquet_data for analytics on exported data.
4. Use search_vibe_vectors for semantic audio similarity search.
5. Use feature_correlation and cluster_subgenres for advanced analytics.
6. Use fetch_research_articles to retrieve academic literature and papers from alphaXiv.

You may call multiple tools in sequence to gather context before answering.
Always be precise with numbers. Reference the Sovereign Targets when relevant.
You may emit tool_calls to fetch data; the orchestrator will route them to the
appropriate specialist tool and feed the results back to you."""


def _ollama_chat_with_tools(messages: list, tools_schema: list) -> Dict[str, Any]:
    """
    Call Ollama /api/chat with tool-calling support.
    Returns dict with 'content' (str) and optional 'tool_calls' (list).
    """
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 1024},
    }
    if tools_schema:
        payload["tools"] = tools_schema
    try:
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
        return data
    except Exception as e:
        return {"message": {"content": f"[PHI3_ERROR] {e}", "tool_calls": []}, "error": str(e)}


def _build_ollama_tools_schema() -> List[Dict[str, Any]]:
    """Convert LangChain tool @tool objects into Ollama's tool schema format."""
    schema = []
    for t in TOOLS_LIST:
        # LangChain tools expose .name, .description, .args (dict of arg -> json-schema)
        try:
            args_schema = {}
            if hasattr(t, 'args') and isinstance(t.args, dict):
                args_schema = t.args
            elif hasattr(t, 'args_schema'):
                # Pydantic schema on the tool
                try:
                    args_schema = t.args_schema.model_json_schema()
                except Exception:
                    args_schema = {}
            schema.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or "",
                    "parameters": args_schema if args_schema else {"type": "object", "properties": {}},
                }
            })
        except Exception as e:
            print(f"[WARN] Could not build schema for tool {t.name}: {e}")
    return schema


class Phi3Agent:
    """
    Phi-3 chat model that exposes .invoke(messages) -> AIMessage.
    Emits tool_calls in the OpenAI/Ollama format; LangGraph's ToolNode
    expects a standard 'tool_calls' list on the message.
    """

    def __init__(self):
        self.tools_schema = _build_ollama_tools_schema()

    def invoke(self, messages: Sequence[BaseMessage]) -> AIMessage:
        # Convert LangChain messages to Ollama format
        ollama_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for m in messages:
            role = "user"
            if isinstance(m, SystemMessage):
                role = "system"
            elif isinstance(m, AIMessage):
                role = "assistant"
                if m.tool_calls:
                    # Re-include previous tool calls so phi-3 has context
                    ollama_messages.append({
                        "role": "assistant",
                        "content": m.content or "",
                        "tool_calls": [
                            {"function": {"name": tc["name"], "arguments": tc["args"]}}
                            for tc in m.tool_calls
                        ],
                    })
                    continue
            elif isinstance(m, ToolMessage):
                ollama_messages.append({"role": "tool", "content": m.content})
                continue
            ollama_messages.append({"role": role, "content": m.content})

        result = _ollama_chat_with_tools(ollama_messages, self.tools_schema)
        msg = result.get("message", {}) if isinstance(result, dict) else {}
        content = msg.get("content", "")
        tool_calls = msg.get("tool_calls") or []

        # Normalize tool_calls into LangChain's expected structure
        lc_tool_calls = []
        for tc in tool_calls:
            fn = tc.get("function", {}) if isinstance(tc, dict) else {}
            name = fn.get("name", "")
            args = fn.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}
            lc_tool_calls.append({
                "name": name,
                "args": args,
                "id": f"call_{len(lc_tool_calls)}",
            })

        return AIMessage(content=content, tool_calls=lc_tool_calls)


@ray.remote
class GemmaONNXAgent:
    """
    Gemma-2 ONNX chat model that exposes .invoke(messages) -> AIMessage.
    Executes locally on CPU inside the Ray cluster.
    """

    def __init__(self):
        self.tools_schema = _build_ollama_tools_schema()
        import onnxruntime_genai as og
        model_path = r"C:\WEB CASE STUDY\gemma_onnx"
        self.model = og.Model(model_path)
        self.tokenizer = og.Tokenizer(self.model)

    def invoke(self, messages: Sequence[BaseMessage]) -> AIMessage:
        if not self.model or not self.tokenizer:
            return AIMessage(content="Gemma ONNX model offline.", tool_calls=[])

        # Formulate system prompt + tools instruction
        system_content = SYSTEM_PROMPT + "\n\nAvailable tools:\n" + json.dumps(self.tools_schema, indent=2) + (
            "\n\nTo call a tool, you MUST output a JSON block wrapped in triple backticks containing a list of tool calls in this format:\n"
            "```json\n"
            "[\n"
            "  {\n"
            "    \"name\": \"tool_name\",\n"
            "    \"arguments\": {\"arg_name\": \"value\"}\n"
            "  }\n"
            "]\n"
            "```\n"
            "Do not output anything else if you are calling a tool. If you have the final answer, do not output any tool call JSON block."
        )

        prompt_parts = []
        for i, m in enumerate(messages):
            if isinstance(m, SystemMessage):
                continue
            elif isinstance(m, HumanMessage):
                content = m.content
                if i == 0 or (i == 1 and isinstance(messages[0], SystemMessage)):
                    content = system_content + "\n\nUser Question: " + content
                prompt_parts.append(f"<start_of_turn>user\n{content}<end_of_turn>\n")
            elif isinstance(m, AIMessage):
                if m.tool_calls:
                    tc_list = []
                    for tc in m.tool_calls:
                        tc_list.append({"name": tc["name"], "arguments": tc["args"]})
                    tc_str = json.dumps(tc_list, indent=2)
                    prompt_parts.append(f"<start_of_turn>model\n```json\n{tc_str}\n```<end_of_turn>\n")
                else:
                    prompt_parts.append(f"<start_of_turn>model\n{m.content}<end_of_turn>\n")
            elif isinstance(m, ToolMessage):
                prompt_parts.append(f"<start_of_turn>user\nTool response ({m.name}):\n{m.content}<end_of_turn>\n")

        prompt_parts.append("<start_of_turn>model\n")
        full_prompt = "".join(prompt_parts)

        # Generate tokens
        input_tokens = self.tokenizer.encode(full_prompt)
        import onnxruntime_genai as og
        params = og.GeneratorParams(self.model)
        params.set_search_options(max_length=8192, temperature=0.1)
        generator = og.Generator(self.model, params)
        generator.append_tokens(input_tokens)
        while not generator.is_done():
            generator.generate_next_token()
        output_tokens = generator.get_sequence(0)
        response_text = self.tokenizer.decode(output_tokens[len(input_tokens):])

        # Extract tool calls
        lc_tool_calls = []
        content = response_text.strip()
        json_str = None
        if "```json" in content:
            try:
                start = content.index("```json") + 7
                end = content.index("```", start)
                json_str = content[start:end].strip()
            except ValueError:
                pass
        elif "```" in content:
            try:
                start = content.index("```") + 3
                end = content.index("```", start)
                json_str = content[start:end].strip()
            except ValueError:
                pass

        if not json_str:
            try:
                start = content.find("[")
                end = content.rfind("]") + 1
                if start != -1 and end > start:
                    json_str = content[start:end]
            except Exception:
                pass

        if json_str:
            try:
                parsed = json.loads(json_str)
                if isinstance(parsed, list):
                    for tc in parsed:
                        if isinstance(tc, dict) and "name" in tc:
                            lc_tool_calls.append({
                                "name": tc["name"],
                                "args": tc.get("arguments", tc.get("args", {})),
                                "id": f"call_{len(lc_tool_calls)}"
                            })
                elif isinstance(parsed, dict) and "name" in parsed:
                    lc_tool_calls.append({
                        "name": parsed["name"],
                        "args": parsed.get("arguments", parsed.get("args", {})),
                        "id": f"call_{len(lc_tool_calls)}"
                    })
            except Exception as e:
                print(f"[WARN] Failed to parse extracted JSON content: {e}")

        # If a tool call was detected, strip the JSON from the final content
        # so it doesn't pollute subsequent messages
        clean_content = content
        if lc_tool_calls and json_str:
            clean_content = content.replace(f"```json\n{json_str}\n```", "").replace(f"```json{json_str}```", "").strip()

        return AIMessage(content=clean_content, tool_calls=lc_tool_calls)


from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration

class RayONNXChatModel(BaseChatModel):
    """
    Custom LangChain BaseChatModel wrapper for local ONNX agents running in a Ray cluster.
    """
    actor_name: str = "GemmaONNXAgent"

    @property
    def _llm_type(self) -> str:
        return "ray_onnx_chat_model"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        import ray
        if not ray.is_initialized():
            try:
                ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
            except Exception:
                ray.init(namespace="legion", object_store_memory=1500 * 1024 * 1024)
                
        try:
            model = ray.get_actor(self.actor_name, namespace="legion")
        except ValueError:
            sys.path.append(r"C:\WEB CASE STUDY")
            try:
                from gemma_onnx_server import GemmaONNXAgent as ServerAgent
                model = ServerAgent.options(name=self.actor_name, namespace="legion", lifetime="detached").remote()
            except ImportError:
                print("[!] gemma_onnx_server not found. Falling back to local GemmaONNXAgent definition.")
                model = GemmaONNXAgent.options(name=self.actor_name, namespace="legion", lifetime="detached").remote()

        # Format messages to clean, serialization-safe dictionaries
        messages_list = []
        for m in messages:
            if isinstance(m, SystemMessage):
                messages_list.append({"role": "system", "content": m.content})
            elif isinstance(m, HumanMessage):
                messages_list.append({"role": "user", "content": m.content})
            elif isinstance(m, AIMessage):
                if m.tool_calls:
                    tc_list = [{"name": tc["name"], "arguments": tc["args"]} for tc in m.tool_calls]
                    tc_str = json.dumps(tc_list, indent=2)
                    messages_list.append({"role": "assistant", "content": f"```json\n{tc_str}\n```"})
                else:
                    messages_list.append({"role": "assistant", "content": m.content})
            elif isinstance(m, ToolMessage):
                messages_list.append({"role": "user", "content": f"Tool response ({m.name}):\n{m.content}"})

        # Format System Prompt with current tools list
        tools_schema = _build_ollama_tools_schema()
        system_prompt = SYSTEM_PROMPT + "\n\nAvailable tools:\n" + json.dumps(tools_schema, indent=2) + (
            "\n\nTo call a tool, you MUST output a JSON block wrapped in triple backticks containing a list of tool calls in this format:\n"
            "```json\n"
            "[\n"
            "  {\n"
            "    \"name\": \"tool_name\",\n"
            "    \"arguments\": {\"arg_name\": \"value\"}\n"
            "  }\n"
            "]\n"
            "```\n"
            "Do not output anything else if you are calling a tool. If you have the final answer, do not output any tool call JSON block."
        )

        # Invoke Remote Ray Actor
        response_text = ray.get(model.generate.remote(messages_list, system_prompt))
        
        # Extract Tool Calls from response_text
        lc_tool_calls = []
        content = response_text.strip()
        json_str = None
        if "```json" in content:
            try:
                start = content.index("```json") + 7
                end = content.index("```", start)
                json_str = content[start:end].strip()
                parsed_calls = json.loads(json_str)
                if not isinstance(parsed_calls, list):
                    parsed_calls = [parsed_calls]
                for parsed in parsed_calls:
                    lc_tool_calls.append({
                        "name": parsed["name"],
                        "args": parsed.get("arguments", parsed.get("args", {})),
                        "id": f"call_{len(lc_tool_calls)}"
                    })
            except Exception as e:
                print(f"[WARN] Failed to parse extracted JSON content: {e}")

        clean_content = content
        if lc_tool_calls and json_str:
            clean_content = content.replace(f"```json\n{json_str}\n```", "").replace(f"```json{json_str}```", "").strip()

        ai_message = AIMessage(content=clean_content, tool_calls=lc_tool_calls)
        return ChatResult(generations=[ChatGeneration(message=ai_message)])

def call_model(state: AgentState) -> dict:
    """The Agent node. Invokes Gemma ONNX via Ray remote call using the LangChain wrapper."""
    llm = RayONNXChatModel(actor_name="GemmaONNXAgent")
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


def should_continue(state: AgentState) -> Literal["continue", "end"]:
    """Edge router: if the last message has tool_calls, continue to the tools node."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"
    return "end"


# =====================================================================
# GRAPH ASSEMBLY (Agent <-> Tools loop)
# =====================================================================

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(TOOLS_LIST))
workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent", should_continue, {"continue": "tools", "end": END}
)
workflow.add_edge("tools", "agent")

# Compiled graph - the LangGraph 'app'
app = workflow.compile()


# =====================================================================
# PYDANTIC OUTPUT SCHEMA (post-graph validation of phi-3's final answer)
# =====================================================================

class SovereignLegionResponse(BaseModel):
    """Pydantic validation of the final phi-3 response after all tool calls complete."""
    question: str = Field(..., description="The original user question.")
    answer: str = Field(..., description="Phi-3's synthesized final answer.")
    tools_called: List[str] = Field(default_factory=list)
    tool_results_summary: List[Dict[str, Any]] = Field(default_factory=list)
    raw_messages: int = Field(0, description="Total messages in the conversation trace.")
    model: str = LLM_MODEL


# =====================================================================
# PUBLIC ENTRY POINTS
# =====================================================================

def run_workflow(prompt: str) -> Dict[str, Any]:
    """
    Public API. Mirrors legion_graph.run_workflow() from your git.
    Usage:
        from legion_langgraph_brain import run_workflow
        result = run_workflow("What BPM distribution do we have?")
    """
    result = app.invoke({
        "messages": [HumanMessage(content=prompt)],
        "active_dna_context": {},
    })
    msgs = result.get("messages", [])
    final_msg = msgs[-1].content if msgs else "No output."

    # Collect tool call summary
    tools_called: List[str] = []
    for m in msgs:
        if hasattr(m, "tool_calls") and m.tool_calls:
            for tc in m.tool_calls:
                tools_called.append(tc.get("name", ""))

    return {
        "status": "success",
        "result": final_msg,
        "tools_called": tools_called,
        "message_count": len(msgs),
    }


def run_workflow_validated(prompt: str) -> SovereignLegionResponse:
    """
    Pydantic-validated entry point. Returns a SovereignLegionResponse.
    """
    result = app.invoke({
        "messages": [HumanMessage(content=prompt)],
        "active_dna_context": {},
    })
    msgs = result.get("messages", [])
    final_msg = msgs[-1].content if msgs else "No output."

    tools_called: List[str] = []
    tool_results: List[Dict[str, Any]] = []
    for m in msgs:
        if hasattr(m, "tool_calls") and m.tool_calls:
            for tc in m.tool_calls:
                tools_called.append(tc.get("name", ""))
        if isinstance(m, ToolMessage):
            try:
                parsed = json.loads(m.content) if isinstance(m.content, str) else {}
            except Exception:
                parsed = {"raw": m.content[:500]}
            tool_results.append({"name": m.name, "data": parsed})

    return SovereignLegionResponse(
        question=prompt,
        answer=final_msg,
        tools_called=tools_called,
        tool_results_summary=tool_results,
        raw_messages=len(msgs),
        model=LLM_MODEL,
    )


# =====================================================================
# SMOKE TEST
# =====================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("LEGION LANGGRAPH BRAIN (PHI-3) - SMOKE TEST")
    print("=" * 70)

    # Test 1: Each tool directly
    print("\n[1] list_available_data:")
    try:
        inv = json.loads(list_available_data.invoke({}))
        print(f"  Parquets: {len(inv['parquet_files'])}")
        for p in inv["parquet_files"][:3]:
            print(f"    {p['name']}: {p['rows']} rows, {len(p['columns'])} cols")
        print(f"  DuckDB v1: {len(inv['duckdb'].get('sonic_core_v1', {}))} tables")
        print(f"  LanceDB v2: {len(inv['lancedb'].get('v2_vectors', {}))} tables")
    except Exception as e:
        print(f"  [FAIL] {e}")

    print("\n[2] query_sonic_core:")
    try:
        r = json.loads(query_sonic_core.invoke({
            "sql_query": "SELECT genre_class, COUNT(*) as cnt FROM t_core_memory GROUP BY genre_class ORDER BY cnt DESC LIMIT 5"
        }))
        print(f"  {r[:3] if isinstance(r, list) else r}")
    except Exception as e:
        print(f"  [FAIL] {e}")

    print("\n[3] analyze_parquet_data:")
    try:
        r = json.loads(analyze_parquet_data.invoke({
            "query": "SELECT key, COUNT(*) as cnt FROM {table} GROUP BY key ORDER BY cnt DESC LIMIT 3",
            "parquet_file": "collision_results_final"
        }))
        print(f"  {r[:3] if isinstance(r, list) else r}")
    except Exception as e:
        print(f"  [FAIL] {e}")

    print("\n[4] feature_correlation:")
    try:
        r = json.loads(feature_correlation.invoke({"feature_a": "tempo", "feature_b": "collision_score"}))
        print(f"  {r}")
    except Exception as e:
        print(f"  [FAIL] {e}")

    print("\n[5] cluster_subgenres:")
    try:
        r = json.loads(cluster_subgenres.invoke({"n_clusters": 3}))
        if "clusters" in r:
            for c in r["clusters"]:
                print(f"    Cluster {c['cluster_id']} ({c['suggested_label']}): {c['size']} tracks, centroid={c['centroid']}")
        else:
            print(f"  {r}")
    except Exception as e:
        print(f"  [FAIL] {e}")

    print("\n[6] run_workflow (end-to-end with phi-3):")
    try:
        result = run_workflow("What audio data do we have? Summarize top genres and BPM.")
        print(f"  Status: {result['status']}")
        print(f"  Tools called: {result['tools_called']}")
        print(f"  Messages in trace: {result['message_count']}")
        print(f"  Result preview: {str(result['result'])[:300]}...")
    except Exception as e:
        print(f"  [FAIL] {e}")

    print("\n" + "=" * 70)
    print("BRAIN COMPILED AND READY")
    print("=" * 70)
    print(f"Graph nodes: {list(workflow.nodes.keys())}")
    print(f"Tools: {[t.name for t in TOOLS_LIST]}")
    print(f"Model: {LLM_MODEL}")
    print(f"Ollama: {OLLAMA_URL}")
    print(f"DuckDB v1: {os.path.exists(DUCKDB_V1)} at {DUCKDB_V1}")
    print(f"DuckDB v2: {os.path.exists(DUCKDB_V2)} at {DUCKDB_V2}")
    print(f"LanceDB v1: {os.path.exists(LANCE_STORE)}")
    print(f"LanceDB v2: {os.path.exists(LANCE_STORE_V2)}")