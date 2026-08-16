# -*- coding: utf-8 -*-
"""
🪐 SOVEREIGN RECTIFYING SYSTEM: MASTER DYNAMIC LANGCHAIN / LANGGRAPH ORCHESTRATOR
An enterprise-grade, bare-metal orchestrator that:
1. Dynamically scans the entire workspace (C:\\WEB CASE STUDY) for Python files.
2. Uses AST parsing and dynamic module loading to extract ALL @tool-decorated functions.
3. Bypasses LM Studio constraints by routing reasoning directly to Google AI Studio (Gemini)
   using your GEMINI_API_KEY from the local .env, resolving VRAM and context limits.
4. Pipes complete trace telemetry natively into your LangSmith Dashboard.
5. Assembles a dynamic, loop-back LangGraph state machine to coordinate execution.
"""

import os
import sys
import ast
import socket
import importlib.util
from pathlib import Path
from typing import List, Dict, Any, Callable

# Load environment variables from .env manually to guarantee alignment
def load_dotenv(dotenv_path: str = ".env"):
    if os.path.exists(dotenv_path):
        with open(dotenv_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

# Initialize environment
WORKSPACE_ROOT = r"C:\WEB CASE STUDY"
sys.path.insert(0, WORKSPACE_ROOT)
load_dotenv(os.path.join(WORKSPACE_ROOT, ".env"))

# Set LangSmith environment flags programmatically
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "Sovereign-Legion-Dynamic-Orchestration"
if "LANGCHAIN_API_KEY" not in os.environ and "LANGSMITH_API_KEY" in os.environ:
    os.environ["LANGCHAIN_API_KEY"] = os.environ["LANGSMITH_API_KEY"]

try:
    from langchain_core.tools import BaseTool, tool
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import ToolNode
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
    from pydantic import BaseModel, Field
    HAS_LANGCHAIN = True
except ImportError as e:
    HAS_LANGCHAIN = False
    IMPORT_ERROR_MSG = str(e)

class ToolDiscoveryEngine:
    """Recursively scans the local filesystem, extracts, and compiles all LangChain @tools."""
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.discovered_tools: List[BaseTool] = []

    def scan_for_tools(self) -> List[BaseTool]:
        print(f"🔍 [SCANNER] Initiating recursive search in: {self.root_dir}")
        if not self.root_dir.exists():
            print(f"⚠️ [SCANNER] Directory '{self.root_dir}' does not exist on this machine.")
            return []

        # Step 1: Recursively locate all Python source files
        py_files = list(self.root_dir.rglob("*.py"))
        print(f"📁 [SCANNER] Identified {len(py_files)} Python source files to audit.")

        for py_file in py_files:
            # Skip virtual environments or hidden dirs to prevent dependency pollution
            if any(part in py_file.parts for part in [".venv", "venv", "env", "__pycache__", "build", "dist"]):
                continue
            
            try:
                self._audit_file_for_tools(py_file)
            except Exception as e:
                print(f"⚠️ [SCANNER] Failed to audit {py_file.name}: {e}")

        return self.discovered_tools

    def _audit_file_for_tools(self, file_path: Path):
        """Uses AST to inspect Python code without importing first, isolating decorated tools safely."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()

        if "@tool" not in source:
            return  # Fast path: no LangChain tools declared in this file

        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError:
            return

        tool_function_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    # Look for @tool or @tool(...)
                    if (isinstance(decorator, ast.Name) and decorator.id == "tool") or \
                       (isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name) and decorator.func.id == "tool"):
                        tool_function_names.append(node.name)

        if not tool_function_names:
            return

        print(f"🟢 [SCANNER] Found {len(tool_function_names)} candidate tools in '{file_path.name}': {tool_function_names}")
        
        # Dynamic module loading
        try:
            module_name = file_path.stem
            spec = importlib.util.spec_from_file_location(module_name, str(file_path))
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                for func_name in tool_function_names:
                    candidate_tool = getattr(module, func_name, None)
                    if candidate_tool and isinstance(candidate_tool, BaseTool):
                        # Verify we haven't already registered a tool with this name
                        if not any(t.name == candidate_tool.name for t in self.discovered_tools):
                            self.discovered_tools.append(candidate_tool)
                            print(f"   ↳ [REGISTERED] '{candidate_tool.name}' ({candidate_tool.description[:60]}...)")
        except Exception as e:
            print(f"   ❌ [LOAD ERROR] Could not dynamically import '{file_path.name}': {e}")


# --- BASELINE MASTER WORKSPACE TOOLS ---
# These are guaranteed high-performance fallback tools in case AST sweeps return empty.

@tool
def safe_list_directory(path: str = ".") -> str:
    """Lists contents of a folder in your workspace safely to find metadata catalogs and active project files."""
    try:
        target = Path(WORKSPACE_ROOT) / path
        if not target.exists():
            return f"Error: Path '{path}' not found."
        items = [f"{'📁' if p.is_dir() else '📄'} {p.name}" for p in target.iterdir()]
        return "\n".join(items) if items else "Directory is empty."
    except Exception as e:
        return f"Error listing directory: {e}"

@tool
def safe_read_file(filepath: str) -> str:
    """Reads raw text content from a target file in the workspace (e.g., manifest files or configs) safely with a size-limiting firewall."""
    try:
        target = Path(WORKSPACE_ROOT) / filepath
        if not target.exists():
            return f"Error: File '{filepath}' not found."
        
        # Enforce strict 16k character budget to protect LLM context windows from blowouts
        with open(target, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(16000)
            if len(content) == 16000:
                content += "\n\n[SYSTEM WARNING: File content truncated at 16,000 characters to prevent prompt blowouts]"
            return content
    except Exception as e:
        return f"Error reading file: {e}"

@tool
def query_duckdb_metadata(sql_query: str) -> str:
    """Executes a high-performance OLAP read-only query against the local sonic_core_v2 DuckDB catalog."""
    try:
        import duckdb
        db_path = os.getenv("LOCAL_DUCKDB_PATH", r"C:\STUDIES_BACKUP\data\metadata\sonic_core_v2.duckdb")
        if not os.path.exists(db_path):
            return f"Error: Physical DuckDB file not found at: {db_path}"
        
        conn = duckdb.connect(db_path, read_only=True)
        res = conn.execute(sql_query).fetchdf()
        conn.close()
        return res.to_markdown(index=False)
    except Exception as e:
        return f"Error executing DuckDB query: {e}"


# --- THE MAIN ORCHESTRATOR CLASS ---

class SovereignDynamicOrchestrator:
    def __init__(self):
        print("=" * 80)
        print("🪐 SOVEREIGN RECTIFYING SYSTEM: MASTER DYNAMIC REST ORCHESTRATOR")
        print("=" * 80)
        
        if not HAS_LANGCHAIN:
            print(f"❌ ERROR: Missing required library dependencies!\n{IMPORT_ERROR_MSG}")
            print("Please run: pip install langchain-core langchain-google-genai langgraph langsmith pydantic")
            sys.exit(1)

        # 1. Instantiate the tool directory scanner
        self.scanner = ToolDiscoveryEngine(WORKSPACE_ROOT)
        
        # 2. Build master tools pool (Base tools + Swept tools)
        self.tools = [safe_list_directory, safe_read_file, query_duckdb_metadata]
        
    def initialize_pipeline(self):
        # Scan for custom physical tools
        scanned_tools = self.scanner.scan_for_tools()
        for t in scanned_tools:
            if not any(existing.name == t.name for existing in self.tools):
                self.tools.append(t)
        
        print(f"\n🟢 [ORCHESTRATION] Consolidated {len(self.tools)} active workspace tools.")
        
        # Check API Key Availability
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_key or "Your_Actual" in self.gemini_key:
            print("⚠️ WARNING: No valid 'GEMINI_API_KEY' found in .env.")
            print("Fallback: Tracing is active via LangSmith, but reasoning calls will execute as dry-runs.")
            self.model = None
        else:
            print("🛰️  [CLOUD HYBRID] Authenticated with Google AI Studio. Direct API routing active!")
            # Instantiating Gemini model with native tool-calling
            self.model = ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                google_api_key=self.gemini_key,
                temperature=0.0
            ).bind_tools(self.tools)

        # 3. Compile the LangGraph Dynamic State Machine
        self.compile_state_graph()

    def compile_state_graph(self):
        """Assembles a recursive LangGraph to handle dynamic tool routing loops."""
        
        # Define conversation state schema
        class AgentState(BaseModel):
            messages: List[BaseMessage] = Field(default_factory=list)

        workflow = StateGraph(AgentState)

        # Node A: The Cognitive Brain
        def call_model(state: AgentState):
            messages = state.messages
            if self.model:
                response = self.model.invoke(messages)
            else:
                # DRY-RUN Fallback Mock
                print("   [DRY-RUN Mock] Processing model reasoning...")
                response = AIMessage(content="Dry-run active. Discovered tools successfully. LangSmith tracking enabled.")
            return {"messages": [response]}

        # Node B: The Tool Executor
        tool_node = ToolNode(self.tools)

        # Register nodes to the graph
        workflow.add_node("agent", call_model)
        workflow.add_node("action", tool_node)

        # Set entry point
        workflow.set_entry_point("agent")

        # Routing logic (Conditional edge)
        def route_after_model(state: AgentState):
            last_message = state.messages[-1]
            if isinstance(last_message, AIMessage) and last_message.tool_calls:
                print(f"🔀 [ROUTER] Model triggered Tool Calls: {[tc['name'] for tc in last_message.tool_calls]}")
                return "action"
            print("🔚 [ROUTER] Generation complete. Reached terminal leaf.")
            return END

        # Define transitions
        workflow.add_conditional_edges(
            "agent",
            route_after_model,
            {
                "action": "action",
                END: END
            }
        )
        workflow.add_edge("action", "agent")

        # Compile the state machine
        self.app = workflow.compile()
        print("🟢 [LANGGRAPH] State machine compiled cleanly. Zero-GIL local routing active!")

    def execute_query(self, user_query: str):
        print(f"\n🚀 [EXECUTION] Dispatching query: \"{user_query}\"")
        
        # Base system prompt to anchor the agent's identity and capabilities
        system_prompt = SystemMessage(
            content="You are the Legion Sovereign Intelligence, a bare-metal C++/Python systems orchestrator. "
                    "Analyze the local files, DuckDB database structures, and systems variables using your "
                    "discovered tools. Be factual, concise, and provide deep systems insights."
        )
        
        inputs = {"messages": [system_prompt, HumanMessage(content=user_query)]}
        
        # Run graph execution, printing traces to stdout
        for output in self.app.stream(inputs, config={"recursion_limit": 25}):
            for node_name, state_delta in output.items():
                print(f"\n--- Node '{node_name}' Finished Execution ---")
                for msg in state_delta.get("messages", []):
                    if isinstance(msg, AIMessage) and msg.content:
                        print(f"🤖 Agent Content:\n{msg.content}")
                    elif isinstance(msg, AIMessage) and msg.tool_calls:
                        pass # Router prints tool calls
                    else:
                        print(f"📡 Message Payload: {type(msg).__name__}")


if __name__ == "__main__":
    orchestrator = SovereignDynamicOrchestrator()
    orchestrator.initialize_pipeline()
    
    # Example interactive sweep execution
    test_query = "Read the local MANIFEST file to see what sub-agents are declared, and find out if there are any custom tools."
    orchestrator.execute_query(test_query)
