"""Clean surgical patch: swap mock agent -> LLM agent + rewire graph.
Uses exact line-based extraction to avoid whitespace issues.
"""
from pathlib import Path

target = Path(r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\legion_graph.py")
lines = target.read_text(encoding="utf-8").splitlines(keepends=True)

# Find the mock agent block: from line starting with "# --- 2. Define the Agent ---"
# until (not including) the line "# --- 3. Define the New 'Router' Node ---"
start = None
end = None
for i, ln in enumerate(lines):
    if start is None and ln.startswith("# --- 2. Define the Agent ---"):
        start = i
    elif start is not None and ln.startswith("# --- 3. Define the New 'Router' Node ---"):
        end = i
        break

if start is None or end is None:
    raise SystemExit(f"Mock agent block not found: start={start}, end={end}")
print(f"Replacing lines {start+1}..{end} ({end-start} lines)")

new_block = '''# --- 2. SYSTEM PROMPT (from legion_graph_backup.py) ---
SYSTEM_PROMPT = """You are the Legion Sovereign Intelligence - the cognitive router for a Tech House audio production pipeline. You have access to tools that query DuckDB databases, analyze Parquet data exports, and search LanceDB vector stores containing 384-dim and 768-dim audio embeddings.

Your producer DNA signature: dominant tempo 128 BPM, dominant key G major, target RMS -13.9 LUFS, crest factor 5.69, mid-injection multiplier x289.34.
Lineage: MPC/SP1200.

When answering questions:
1. Use list_available_data first if you need to understand what is available.
2. Use query_sonic_core for structured metadata queries (BPM, key, genre).
3. Use analyze_parquet_data for analytics on exported data.
4. Use search_vibe_vectors for semantic audio similarity search.
5. Use feature_correlation and cluster_subgenres for advanced analytics.

Always be precise with numbers. Reference the Sovereign Targets when relevant."""


# --- 3. LLM MODEL (lazy + cached) ---
_llm_with_tools = None

def _get_model():
    """Get the LLM. Uses Gemini 2.5 Flash with temp=0 for deterministic tool-calling.
    Falls back to a stub if no API key is set."""
    global _llm_with_tools
    if _llm_with_tools is not None:
        return _llm_with_tools
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0,
                google_api_key=api_key,
            )
            _llm_with_tools = llm.bind_tools(tools)
            print("[legion_graph] LLM: Gemini 2.5 Flash (live)", file=sys.stderr)
            return _llm_with_tools
        except Exception as e:
            print(f"[legion_graph] Gemini init failed: {e}", file=sys.stderr)
    from langchain_core.messages import AIMessage
    class StubModel:
        def invoke(self, messages):
            last = messages[-1].content if messages else ""
            return AIMessage(content=f"[No LLM configured] Received: {last}. Set GEMINI_API_KEY to enable full agent.")
    _llm_with_tools = StubModel()
    print("[legion_graph] LLM: stub (set GEMINI_API_KEY for live)", file=sys.stderr)
    return _llm_with_tools


# --- 4. Agent node: invoke LLM with system prompt + history ---
def agent(state: AgentState) -> dict:
    """Agent node: invoke LLM with system prompt + conversation history."""
    llm_with_tools = _get_model()
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(state["messages"])
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


# --- 5. Conditional router: if LLM emitted tool_calls, go to tools ---
def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """Edge router: if the last message has tool_calls, continue to tools node."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "__end__"


'''

# Replace: keep the "# --- 3. Define the New 'Router' Node ---" line and everything after
lines = lines[:start] + [new_block] + lines[end:]

# Now find and replace the graph build section
# Find lines starting "# --- 4. Wire the Graph ---" and ending at "graph_builder.compile())"
start2 = None
end2 = None
for i, ln in enumerate(lines):
    if start2 is None and ln.startswith("# --- 4. Wire the Graph ---"):
        start2 = i
    elif start2 is not None and "graph_builder.compile()" in ln:
        end2 = i + 1
        break

if start2 is None or end2 is None:
    raise SystemExit(f"Graph build block not found: start2={start2}, end2={end2}")
print(f"Replacing lines {start2+1}..{end2} ({end2-start2} lines)")

new_graph_block = '''# --- 7. Wire the Graph (LLM-driven; DSP nodes optional) ---
graph_builder = StateGraph(AgentState)

graph_builder.add_node("agent", agent)
graph_builder.add_node("tools", tool_node)
graph_builder.add_node("stem_router", select_stem_and_route)

graph_builder.set_entry_point("agent")
# LLM decides: if it emitted tool_calls, route to tools; otherwise end
graph_builder.add_conditional_edges("agent", should_continue)

# After tools run, if stem extraction succeeded route to stem_router,
# otherwise let agent see the result and decide what to do next
def after_tools(state: AgentState) -> Literal["stem_router", "agent"]:
    last_message = state["messages"][-1]
    if hasattr(last_message, "content") and "Successfully extracted stems" in str(last_message.content):
        return "stem_router"
    return "agent"

graph_builder.add_conditional_edges("tools", after_tools)
graph_builder.add_edge("stem_router", "agent")

# Compile the final graph
app = graph_builder.compile()
'''

lines = lines[:start2] + [new_graph_block] + lines[end2:]

target.write_text("".join(lines), encoding="utf-8")
# Verify
new_bytes = target.read_bytes()
nulls = sum(1 for b in new_bytes if b == 0)
print(f"Patched. Size: {len(new_bytes):,} bytes. Null bytes: {nulls}")