import os
import json
from typing import TypedDict, Annotated, Sequence, Literal
import operator

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
WORKSPACE_ROOT = r"C:\WEB CASE STUDY"
LM_STUDIO_URL = "http://127.0.0.1:1234/v1"
LLM_MODEL = "nvidia/nemotron-3-nano-4b"

# EXACT list of python files that contain 'E:\WEB CASE STUDY'
ACTIVE_FILES = [
    r"C:\WEB CASE STUDY\mcp_rag_serverOG.py",
    r"C:\WEB CASE STUDY\ray_monty_codebase_sweep.py",
    r"C:\WEB CASE STUDY\restore_vibe_table_v2.py",
    r"C:\WEB CASE STUDY\run_swarm.py",
    r"C:\WEB CASE STUDY\train_vision_brain_titan.py",
    r"C:\WEB CASE STUDY\ray_matrix_node.py",
    r"C:\WEB CASE STUDY\rag-v2\mcp_rag_server.py",
    r"C:\WEB CASE STUDY\mcp_rag_server_v1.py",
    r"C:\WEB CASE STUDY\legion_vision_orchestrator_v2.py",
    r"C:\WEB CASE STUDY\legion_boot.py",
    r"C:\WEB CASE STUDY\legion_agent_deploy\legion_boot.py",
    r"C:\WEB CASE STUDY\find_ml.py",
    r"C:\WEB CASE STUDY\contractor_rag_search.py",
    r"C:\WEB CASE STUDY\analyze_all_databases.py",
    r"C:\WEB CASE STUDY\adamscarmccoy-rag-v2\mcp_rag_server.py",
    r"C:\WEB CASE STUDY\adamscarmccoy-rag-v2\mcp_rag_server_enhanced.py",
    r"C:\WEB CASE STUDY\native_ray_pipeline.py"  # Added because you were just viewing it!
]

# ─── STATE ────────────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# ═══════════════════════════════════════════════════════════════════════════════
# TOOL: replace_string_in_files
# ═══════════════════════════════════════════════════════════════════════════════
@tool
def replace_string_in_files(old_string: str, new_string: str) -> str:
    """Replaces a specific string in the known active Python files."""
    print(f"\n✍️ [TOOL] Replacing '{old_string}' with '{new_string}' in {len(ACTIVE_FILES)} files...")
    fixed_count = 0
    errors = []
    
    for path in ACTIVE_FILES:
        try:
            if not os.path.exists(path):
                continue
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if old_string in content:
                new_content = content.replace(old_string, new_string)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                fixed_count += 1
        except Exception as e:
            errors.append(f"{path}: {str(e)}")
            
    return json.dumps({
        "status": "SUCCESS" if not errors else "PARTIAL_SUCCESS",
        "fixed_count": fixed_count,
        "errors": errors
    })

tools = [replace_string_in_files]

# ═══════════════════════════════════════════════════════════════════════════════
# LANGGRAPH ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════════════════
SYSTEM_PROMPT = (
    "You are an expert autonomous developer and cognitive router. "
    "Your goal is to repair hardcoded paths in the user's workspace. "
    "The workspace moved from the E: drive to the C: drive. "
    "Use your replace_string_in_files tool to fix the paths, then summarize the result."
)

def _get_model():
    llm = ChatOpenAI(
        base_url=LM_STUDIO_URL,
        api_key="lmstudio",
        model=LLM_MODEL,
        temperature=0.0,
        timeout=60.0
    )
    return llm.bind_tools(tools)

def call_model(state: AgentState) -> dict:
    llm_with_tools = _get_model()
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(state["messages"])
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def should_continue(state: AgentState) -> Literal["continue", "end"]:
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

app = workflow.compile()

if __name__ == "__main__":
    print("=" * 80)
    print("🤖 INITIATING LANGGRAPH AUTO-CODER (VENV PATH REPAIR)")
    print("=" * 80)
    
    prompt = "Please use your tool to replace 'E:\\\\WEB CASE STUDY' with 'C:\\\\WEB CASE STUDY' across the active files."
    print(f"\n📡 Sending prompt to Agent...")
    
    result = app.invoke({"messages": [HumanMessage(content=prompt)]})
    
    final_msg = result["messages"][-1].content if result.get("messages") else "No output."
    print("\n🏁 [COMPLETE] VENV path repair completed successfully!")
    print("\n" + "="*50 + "\n" + final_msg + "\n" + "="*50)
