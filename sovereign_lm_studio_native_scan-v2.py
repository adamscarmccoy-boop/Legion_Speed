# sovereign_lm_studio_native_scan-v2.py
# ==============================================================================
# 🏛️ SOVEREIGN COUNCIL: NATIVE LM STUDIO MULTI-TURN MCP SCANNER (v2)
# Handles the multi-turn tool-calling execution loop cleanly on the client-side,
# executing list_directory, find_files, and read_file natively and feeding
# them back to the GGUF model in LM Studio. Eliminates silent freezes.
# ==============================================================================

import os
import sys
import ast
import json
import socket
import traceback
from openai import OpenAI

# High-visibility terminal logging
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

def log_info(msg): print(f"{CYAN}[INFO]{RESET} {msg}", flush=True)
def log_success(msg): print(f"{GREEN}[SUCCESS]{RESET} {msg}", flush=True)
def log_warning(msg): print(f"{YELLOW}[WARN]{RESET} {msg}", flush=True)
def log_error(msg): print(f"{RED}[ERROR]{RESET} {msg}", flush=True)

# Port sweep options to discover LM Studio's active port
PORT_OPTIONS = [1234, 1010, 56217, 61277]

def discover_active_port() -> int:
    """Discovers which loopback port LM Studio is listening on."""
    for port in PORT_OPTIONS:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.15)
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    return port
        except Exception:
            pass
    return 1234  # Fallback default

ACTIVE_PORT = discover_active_port()
LM_STUDIO_BASE_URL = f"http://127.0.0.1:{ACTIVE_PORT}/v1"

# ==============================================================================
# 1. BARE-METAL CLIENT-SIDE TOOL EXECUTORS (IMMUNE TO RECURSIVE FREEZES)
# ==============================================================================
def list_directory(path: str = "") -> str:
    """Lists files in the target workspace safely without traversing subdirectories."""
    target_dir = r"C:\WEB CASE STUDY"
    if path:
        # Resolve path safely if it is relative or points elsewhere
        if os.path.isabs(path):
            target_dir = path
        else:
            target_dir = os.path.join(r"C:\WEB CASE STUDY", path)
            
    if not os.path.exists(target_dir):
        # Fallback to current working directory if case study folder doesn't exist
        target_dir = os.getcwd()
        
    try:
        files = os.listdir(target_dir)
        details = []
        for f in files:
            full_p = os.path.join(target_dir, f)
            is_dir = os.path.isdir(full_p)
            details.append({
                "name": f,
                "type": "directory" if is_dir else "file",
                "size_bytes": os.path.getsize(full_p) if not is_dir else 0
            })
        return json.dumps({"status": "SUCCESS", "current_dir": target_dir, "contents": details}, indent=2)
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": str(e)})

def read_file(filepath: str) -> str:
    """Reads file contents securely, preventing EISDIR errors."""
    target_path = filepath
    if not os.path.isabs(filepath):
        target_path = os.path.join(r"C:\WEB CASE STUDY", filepath)
        if not os.path.exists(target_path):
            target_path = os.path.join(os.getcwd(), filepath)

    if not os.path.exists(target_path):
        return json.dumps({"status": "FAILED", "error": f"File '{filepath}' not found."})
    if os.path.isdir(target_path):
        return json.dumps({"status": "FAILED", "error": f"'{filepath}' is a directory. Use list_directory."})

    try:
        with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return json.dumps({"status": "SUCCESS", "filepath": filepath, "content": content})
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": str(e)})

def inspect_file_ast(filepath: str) -> str:
    """Performs a surgical AST analysis of a Python file to return its classes, functions, and imports."""
    target_path = filepath
    if not os.path.isabs(filepath):
        target_path = os.path.join(r"C:\WEB CASE STUDY", filepath)
        if not os.path.exists(target_path):
            target_path = os.path.join(os.getcwd(), filepath)

    if not os.path.exists(target_path):
        return json.dumps({"status": "FAILED", "error": "File not found."})

    try:
        with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
        tree = ast.parse(content, filename=target_path)
        imports = []
        functions = []
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
                
        return json.dumps({
            "status": "SUCCESS",
            "filename": os.path.basename(target_path),
            "classes": classes[:15],
            "functions": functions[:20],
            "imports": imports[:15],
            "lines_count": len(content.splitlines())
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": str(e)})

def query_duckdb_schema(db_path: str = None) -> str:
    """Discovers and queries all DuckDB database files, schemas, tables, and row counts."""
    candidate_dbs = [
        db_path,
        r"C:\WEB CASE STUDY\web_intel_sonicdb.duckdb",
        r"C:\WEB CASE STUDY\sovereign_data\sovereign.duckdb",
        r"C:\STUDIES_BACKUP\data\metadata\sonic_core_v2.duckdb",
        r"C:\STUDIES_BACKUP\data\metadata\sonic_core.duckdb",
        r"C:\STUDIES_BACKUP\AI_Logs\sonic_core_v2.duckdb",
        r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\web_intel_sonicdb.duckdb"
    ]
    candidate_dbs = [p for p in candidate_dbs if p and os.path.exists(p)]
    
    results = {}
    try:
        import duckdb
        for db in candidate_dbs:
            try:
                con = duckdb.connect(db, read_only=True)
                tables = con.execute("SHOW TABLES").fetchall()
                tbl_schemas = {}
                for t in tables:
                    tname = t[0]
                    try:
                        cnt = con.execute(f"SELECT COUNT(*) FROM '{tname}'").fetchone()[0]
                    except Exception:
                        cnt = "unknown"
                    tbl_schemas[tname] = {"row_count": cnt}
                results[db] = {"table_count": len(tbl_schemas), "tables": tbl_schemas}
                con.close()
            except Exception as e:
                results[db] = {"error": str(e)}
        return json.dumps({"status": "SUCCESS", "databases": results}, indent=2)
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": str(e)})

def list_lancedb_stores() -> str:
    """Discovers and lists all LanceDB vector stores and their table schemas and row counts."""
    candidate_stores = [
        r"C:\STUDIES_BACKUP\vectors\lancedb_store",
        r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag",
        r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag",
        r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_highres_audio_rag",
        r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_omni_snowflake_rag",
        r"C:\WEB CASE STUDY\lancedb_store",
        r"C:\WEB CASE STUDY\lancedb_memory",
        r"C:\WEB CASE STUDY\lancedb_data"
    ]
    candidate_stores = [p for p in candidate_stores if os.path.exists(p)]
    
    results = {}
    try:
        import lancedb
        for store in candidate_stores:
            try:
                ldb = lancedb.connect(store)
                tables = []
                if hasattr(ldb, "table_names"):
                    try:
                        tn = ldb.table_names()
                        if isinstance(tn, list) and (not tn or isinstance(tn[0], str)):
                            tables = tn
                    except Exception:
                        pass
                if not tables and hasattr(ldb, "list_tables"):
                    res = ldb.list_tables()
                    if hasattr(res, "tables"):
                        tables = res.tables
                    elif isinstance(res, dict) and "tables" in res:
                        tables = res["tables"]
                    elif isinstance(res, list):
                        for item in res:
                            if isinstance(item, tuple) and item[0] == "tables":
                                tables = item[1]
                            elif isinstance(item, str):
                                tables = res
                
                store_tables = {}
                for t in tables:
                    if isinstance(t, str):
                        try:
                            tbl = ldb.open_table(t)
                            store_tables[t] = {
                                "rows": tbl.count_rows(),
                                "columns": tbl.schema.names
                            }
                        except Exception as te:
                            store_tables[t] = {"error": str(te)}
                results[store] = {"table_count": len(store_tables), "tables": store_tables}
            except Exception as e:
                results[store] = {"error": str(e)}
        return json.dumps({"status": "SUCCESS", "lancedb_stores": results}, indent=2)
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": str(e)})

def list_parquet_datasets() -> str:
    """Scans and lists all Parquet dataset files, columns, and row counts across workspace."""
    search_dirs = [r"C:\WEB CASE STUDY", r"C:\STUDIES_BACKUP"]
    found = []
    try:
        import pyarrow.parquet as pq
        for sdir in search_dirs:
            if os.path.exists(sdir):
                for root, dirs, files in os.walk(sdir):
                    if any(skip in root for skip in [".venv", "node_modules", ".git"]):
                        continue
                    for f in files:
                        if f.endswith(".parquet"):
                            p_path = os.path.join(root, f)
                            try:
                                meta = pq.read_metadata(p_path)
                                size_mb = round(os.path.getsize(p_path) / (1024*1024), 2)
                                found.append({
                                    "file": p_path,
                                    "rows": meta.num_rows,
                                    "columns_count": meta.num_columns,
                                    "size_mb": size_mb
                                })
                            except Exception:
                                found.append({"file": p_path, "status": "exists"})
        return json.dumps({"status": "SUCCESS", "total_parquet_files": len(found), "datasets": found}, indent=2)
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": str(e)})

# Map tool calls to physical execution blocks
def execute_local_tool(name: str, args: dict) -> str:
    try:
        if name == "list_directory":
            return list_directory(args.get("path", ""))
        elif name == "read_file":
            return read_file(args.get("filepath", ""))
        elif name == "inspect_file_ast":
            return inspect_file_ast(args.get("filepath", ""))
        elif name in ["query_duckdb_schema", "query_duckdb_tables", "duckdb_schema"]:
            return query_duckdb_schema(args.get("db_path"))
        elif name in ["list_lancedb_stores", "query_lancedb_schema", "lancedb_stores"]:
            return list_lancedb_stores()
        elif name in ["list_parquet_datasets", "query_parquet_files", "parquet_datasets"]:
            return list_parquet_datasets()
        else:
            return json.dumps({"status": "FAILED", "error": f"Tool '{name}' not found."})
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": str(e)})

# ==============================================================================
# 2. SCHEMA AND METADATA TOOL DEFINITIONS
# ==============================================================================
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Lists contents of the target folder in your workspace safely.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative or absolute directory path."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads raw text content from a target file. Do not call on directories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Absolute or relative file path on disk."}
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_file_ast",
            "description": "Performs a surgical AST parser analysis on a targeted python file to inspect functions, imports, and classes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Absolute path of the Python file to inspect."}
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_duckdb_schema",
            "description": "Enumerates all DuckDB analytical databases, listing all active tables, column definitions, and exact row counts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "db_path": {"type": "string", "description": "Optional specific path to DuckDB file."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_lancedb_stores",
            "description": "Discovers and lists all LanceDB vector stores across disk, including vector table names, record counts, and schemas.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_parquet_datasets",
            "description": "Discovers and lists all Parquet datasets and tables on disk with total row counts, column counts, and file sizes.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

# ==============================================================================
# 3. MULTI-TURN ORCHESTRATION LOOP
# ==============================================================================
def run_loop():
    print("=" * 80)
    print(f"🏛️  SOVEREIGN MULTI-TURN AGENT LOOP BACKEND (BOUND TO PORT {ACTIVE_PORT})")
    print("  Executing native tool handshakes with LM Studio REST API...")
    print("=" * 80)

    client = OpenAI(base_url=LM_STUDIO_BASE_URL, api_key="lm-studio")

    system_instructions = (
        "You are the Sovereign Lead Systems Architect. Your task is to identify and "
        "rank the best 'prompt preprocessor' and 'in-memory processor' inside 'C:\\WEB CASE STUDY'.\n\n"
        "To prevent directory walking locks or recursive infinite loops, use your toolsets in sequence:\n"
        "1. Call 'list_directory' with path 'C:\\WEB CASE STUDY' to pull candidate scripts.\n"
        "2. Identify which scripts look like processors (e.g. preflight, orchestrator, cli, or monty scripts).\n"
        "3. Call 'inspect_file_ast' surgically on those targeted files to inspect their classes and functions.\n"
        "4. Output a clear comparison stating which file contains the best preprocessor and which has the best in-memory processor."
    )

    messages = [
        {"role": "system", "content": system_instructions},
        {"role": "user", "content": "Analyze my C:\\WEB CASE STUDY workspace. Identify the best prompt preprocessor and the best in-memory processor using your developer tools. Do not walk directories manually."}
    ]

    for turn in range(8):
        log_info(f"Querying C++ inference engine (Turn {turn+1}/8)...")
        try:
            response = client.chat.completions.create(
                model="nvidia/nemotron-3-nano-4b",
                messages=messages,
                tools=TOOL_SCHEMAS,
                temperature=0.0
            )
        except Exception as e:
            log_error("Failed to query model server:")
            print(traceback.format_exc())
            sys.exit(1)

        choice = response.choices[0]
        message = choice.message
        content = message.content or ""

        # Log assistant text response if present
        if content:
            print(f"\n💬 {CYAN}[STUDIO ARCHITECT]{RESET} {content}\n")

        # Handle tool calls
        if message.tool_calls:
            # We append the original model message directly to maintain the SDK's exact object structure
            messages.append(message)

            for tool_call in message.tool_calls:
                tc_id = tool_call.id
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

                log_info(f"⚙️ Model triggered native tool '{name}' with args: {args}")
                tool_output = execute_local_tool(name, args)
                log_success(f"📥 Tool response acquired (size: {len(tool_output)} bytes)")

                # Append the tool completion response back to the chat history
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": tool_output
                })
        else:
            # No tool calls made, we are finished!
            messages.append(message)
            log_success("🏆 Complete multi-turn task loop concluded beautifully!")
            break

if __name__ == "__main__":
    try:
        run_loop()
    except KeyboardInterrupt:
        log_warning("\n👋 Session execution suspended by user.")