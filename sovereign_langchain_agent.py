import os
import sys
import json
import urllib.request
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Disable remote tracing retries if key is not configured
if not os.getenv("LANGSMITH_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
else:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
try:
    from langchain.agents import create_react_agent  # LangGraph V1.0+
except ImportError:
    from langgraph.prebuilt import create_react_agent  # fallback

TARGET_DIR = r"C:\WEB CASE STUDY"

# ==============================================================================
# 1. LANGCHAIN @tool DEFINITIONS (ZERO RAY, ZERO PORTS, PURE IN-PROCESS)
# ==============================================================================

@tool
def list_lancedb_stores() -> str:
    """Discovers and lists all LanceDB vector stores, tables, and dimensions across storage roots."""
    candidate_stores = [
        r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag",
        r"C:\STUDIES_BACKUP\vectors\lancedb_store",
        r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag",
        os.path.join(TARGET_DIR, "lancedb_memory")
    ]
    candidate_stores = [p for p in candidate_stores if os.path.exists(p)]
    results = {}
    try:
        import lancedb
        for store in candidate_stores:
            try:
                ldb = lancedb.connect(store)
                tables = list(ldb.list_tables()) if hasattr(ldb, "list_tables") else ldb.table_names()
                store_tables = {}
                for t in tables:
                    if isinstance(t, str):
                        try:
                            tbl = ldb.open_table(t)
                            store_tables[t] = {"rows": tbl.count_rows(), "columns": tbl.schema.names}
                        except Exception as te:
                            store_tables[t] = {"error": str(te)}
                results[store] = {"table_count": len(store_tables), "tables": store_tables}
            except Exception as e:
                results[store] = {"error": str(e)}
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error listing LanceDB stores: {e}"

@tool
def query_duckdb_schema() -> str:
    """Queries all DuckDB database catalogs and returns table counts and schemas across disk."""
    candidate_dbs = [
        os.path.join(TARGET_DIR, "web_intel_sonicdb.duckdb"),
        os.path.join(TARGET_DIR, "sovereign_data", "sovereign.duckdb"),
        r"C:\STUDIES_BACKUP\data\metadata\sonic_core_v2.duckdb",
        r"C:\STUDIES_BACKUP\data\metadata\sonic_core.duckdb",
        r"C:\STUDIES_BACKUP\AI_Logs\sonic_core_v2.duckdb"
    ]
    candidate_dbs = [p for p in candidate_dbs if os.path.exists(p)]
    results = {}
    try:
        import duckdb
        for db in candidate_dbs:
            try:
                con = duckdb.connect(db, read_only=True)
                tables_df = con.execute("SHOW TABLES").df()
                tables = list(tables_df.iloc[:, 0]) if not tables_df.empty else []
                table_schemas = {}
                for table in tables:
                    try:
                        count_df = con.execute(f"SELECT COUNT(*) FROM '{table}'").df()
                        row_count = int(count_df.iloc[0, 0])
                    except Exception:
                        row_count = "unknown"
                    table_schemas[table] = {"row_count": row_count}
                results[db] = {"table_count": len(table_schemas), "tables": table_schemas}
                con.close()
            except Exception as e:
                results[db] = {"error": str(e)}
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error querying DuckDB schema: {e}"

@tool
def query_sonic_core_sql(sql_query: str) -> str:
    """Executes a direct read-only analytical SQL query against the primary DuckDB database."""
    db_path = os.path.join(TARGET_DIR, "web_intel_sonicdb.duckdb")
    if not os.path.exists(db_path):
        db_path = r"C:\STUDIES_BACKUP\data\metadata\sonic_core_v2.duckdb"
    try:
        import duckdb
        con = duckdb.connect(db_path, read_only=True)
        res_df = con.execute(sql_query).df()
        con.close()
        return json.dumps({
            "db": os.path.basename(db_path),
            "rows": len(res_df),
            "data": res_df.head(20).to_dict(orient="records")
        }, default=str, indent=2)
    except Exception as e:
        return f"Error running SQL: {e}"

@tool
def inspect_onnx_models() -> str:
    """Inspects all compiled ONNX neural models and their input/output tensor shapes across disk."""
    search_dirs = [
        TARGET_DIR,
        os.path.join(TARGET_DIR, "models"),
        os.path.join(TARGET_DIR, "sonic_dna_engine"),
        r"C:\STUDIES_BACKUP\models"
    ]
    onnx_files = []
    try:
        import onnxruntime as ort
        for sdir in search_dirs:
            if os.path.exists(sdir):
                for item in os.listdir(sdir):
                    if item.endswith(".onnx"):
                        onnx_files.append(os.path.join(sdir, item))
        
        models_info = []
        for path in sorted(set(onnx_files)):
            try:
                session = ort.InferenceSession(path, providers=['CPUExecutionProvider'])
                inputs = [{"name": i.name, "shape": i.shape, "type": i.type} for i in session.get_inputs()]
                outputs = [{"name": o.name, "shape": o.shape, "type": o.type} for o in session.get_outputs()]
                models_info.append({
                    "model": os.path.basename(path),
                    "size_mb": round(os.path.getsize(path) / (1024*1024), 3),
                    "inputs": inputs,
                    "outputs": outputs
                })
            except Exception as me:
                models_info.append({"model": os.path.basename(path), "error": str(me)})
        return json.dumps(models_info, indent=2)
    except Exception as e:
        return f"Error inspecting ONNX models: {e}"

@tool
def semantic_code_search(query: str) -> str:
    """Searches LanceDB mined_code_vectors lakehouse using local 1024-D Snowflake Arctic embeddings."""
    try:
        embed_payload = {"model": "text-embedding-snowflake-arctic-embed-l-v2.0", "input": query}
        req = urllib.request.Request(
            "http://127.0.0.1:1234/v1/embeddings",
            data=json.dumps(embed_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            emb_data = json.loads(resp.read().decode("utf-8"))
            query_vec = emb_data["data"][0]["embedding"]
            
        import lancedb
        lakehouse_path = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag"
        if not os.path.exists(lakehouse_path):
            lakehouse_path = os.path.join(TARGET_DIR, "lancedb_memory")
            
        db = lancedb.connect(lakehouse_path)
        tbl = db.open_table("mined_code_vectors")
        df = tbl.search(query_vec).limit(3).to_pandas()
        drop_cols = [c for c in df.columns if "vector" in c.lower()]
        if drop_cols:
            df = df.drop(columns=drop_cols)
        return json.dumps(df.head(3).to_dict(orient="records"), default=str, indent=2)
    except Exception as e:
        return f"Error performing semantic code search: {e}"

@tool
def run_onnx_inference(model_name: str = "fretflow_omni_v4.onnx", input_values: list = None) -> str:
    """Executes real-time in-process C++ ONNX neural inference for audio DNA, DSP, or genre classification."""
    import onnxruntime as ort
    search_dirs = [TARGET_DIR, os.path.join(TARGET_DIR, "sonic_dna_engine"), r"C:\STUDIES_BACKUP\models"]
    model_path = None
    for sdir in search_dirs:
        candidate = os.path.join(sdir, model_name)
        if os.path.exists(candidate):
            model_path = candidate
            break
    if not model_path:
        return f"Error: ONNX model '{model_name}' not found."
    try:
        session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        input_meta = session.get_inputs()[0]
        dim = input_meta.shape[-1] if isinstance(input_meta.shape[-1], int) else 64
        if input_values and len(input_values) == dim:
            inp_arr = np.array([input_values], dtype=np.float32)
        else:
            inp_arr = np.random.randn(1, dim).astype(np.float32)
        outputs = session.run(None, {input_meta.name: inp_arr})
        output_dict = {session.get_outputs()[i].name: outputs[i].tolist() for i in range(len(outputs))}
        return json.dumps({
            "model": os.path.basename(model_path),
            "input_shape": list(inp_arr.shape),
            "outputs": output_dict
        }, indent=2)
    except Exception as e:
        return f"Error running ONNX inference: {e}"

# ==============================================================================
# 2. LANGCHAIN CHAT MODEL & LANGGRAPH AGENT SETUP
# ==============================================================================

TOOLS = [
    list_lancedb_stores,
    query_duckdb_schema,
    query_sonic_core_sql,
    inspect_onnx_models,
    semantic_code_search,
    run_onnx_inference
]

def get_sovereign_agent():
    """Initializes a LangGraph ReAct agent connected to local LM Studio via ChatOpenAI."""
    llm = ChatOpenAI(
        base_url="http://127.0.0.1:1234/v1",
        api_key="not-needed",
        model="nvidia/nemotron-3-nano-4b",
        temperature=0.0
    )
    return create_react_agent(llm, TOOLS)

def run_agent_query(user_query: str):
    """Executes a LangGraph query through the ReAct agent with native in-process tool binding."""
    agent = get_sovereign_agent()
    print(f"\n🤖 [LANGCHAIN / LANGGRAPH AGENT] Invoking with query: '{user_query}'...")
    response = agent.invoke({"messages": [HumanMessage(content=user_query)]})
    return response["messages"][-1].content

if __name__ == "__main__":
    test_q = "List all my active ONNX models and all DuckDB database table counts using your tools."
    ans = run_agent_query(test_q)
    print("\n==================================================================")
    print("🤖 [LANGGRAPH AGENT FINAL ANSWER]:")
    print("==================================================================")
    print(ans)
    print("==================================================================")
