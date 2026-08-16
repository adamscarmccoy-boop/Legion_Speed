"""
LEGION CHROME DEVTOOLS AGENT
=============================
Extends the Legion LangGraph orchestrator with Chrome DevTools MCP tools.

Follows the exact AgentState + ToolNode pattern from legion_graph.py.
Uses mcp 1.28.0 (Anthropic SDK, already in .venv) to bridge chrome-devtools-mcp
as native LangChain @tool callables — no new dependencies required.

Usage (standalone):
    E:\\WEB CASE STUDY\\.venv\\Scripts\\python.exe legion_chrome_agent.py

Usage (import into mcp_api_server.py):
    from legion_chrome_agent import run_agent
    result = await run_agent("Navigate to example.com and take a screenshot")

Wired tools (from chrome-devtools-mcp, verified 29 available):
    - navigate_page       : Navigate to URL
    - evaluate_script     : Execute JS in current page context
    - take_screenshot     : Capture PNG of current page
    - get_page_content    : Return DOM/text of current page
    - click_element       : Click on element by selector
    - type_text           : Type text into input element
    - list_tabs           : List all open browser tabs
    - ...and 22 more

Architecture:
    START → ChromeAgent (Gemini 2.5 Flash) → ChromeTools (MCP bridge) → ChromeAgent → ... → END
"""

import os
import sys
import json
import asyncio
import logging
from typing import TypedDict, Annotated, Sequence, Literal, Optional, Any
import operator

# ─── LANGCHAIN / LANGGRAPH ────────────────────────────────────────────────────
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import StructuredTool, BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

# ─── MCP SDK (Anthropic, mcp==1.28.0) ────────────────────────────────────────
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ─── PYDANTIC (2.13.4, already in .venv) ─────────────────────────────────────
from pydantic import BaseModel, create_model

# ─── LOGGING ─────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [CHROME-AGENT] %(levelname)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(LOG_DIR, "chrome_agent.log"), encoding="utf-8"),
    ]
)
log = logging.getLogger("chrome_agent")

# ─── STATE — extends AgentState from legion_graph.py ─────────────────────────
class ChromeAgentState(TypedDict):
    """Legion-compatible state. Mirrors AgentState, adds chrome_context."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    active_dna_context: dict        # kept for compatibility with legion_graph.AgentState
    chrome_context: dict            # last tab URL, title, screenshot path


# ─── MCP → LANGCHAIN TOOL BRIDGE ─────────────────────────────────────────────

# Global session reference — set once inside run_agent() context
_mcp_session: Optional[ClientSession] = None


def _make_langchain_tool(session: ClientSession, mcp_tool) -> BaseTool:
    """
    Wraps a single MCP tool schema into a LangChain StructuredTool.
    Builds a pydantic args_schema from the MCP inputSchema at call time.
    """
    name = mcp_tool.name
    description = mcp_tool.description or f"Chrome DevTools MCP: {name}"
    input_schema = mcp_tool.inputSchema if hasattr(mcp_tool, "inputSchema") else {}
    schema_dict = input_schema if isinstance(input_schema, dict) else {}

    properties = schema_dict.get("properties", {})
    required_fields = schema_dict.get("required", [])

    # Map JSON schema types → Python types
    _type_map = {
        "string": str, "integer": int, "number": float,
        "boolean": bool, "array": list, "object": dict,
    }

    field_defs = {}
    for prop_name, prop_schema in properties.items():
        prop_schema = prop_schema if isinstance(prop_schema, dict) else {}
        py_type = _type_map.get(prop_schema.get("type", "string"), str)
        if prop_name in required_fields:
            field_defs[prop_name] = (py_type, ...)
        else:
            field_defs[prop_name] = (Optional[py_type], None)

    DynamicSchema: Optional[type[BaseModel]] = (
        create_model(f"{name}_schema", **field_defs) if field_defs else None
    )

    async def _async_call(**kwargs) -> str:
        """Invoke the MCP tool and return text content."""
        assert session is not None, "MCP session not initialized"
        # Strip None optional args
        clean_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        result = await session.call_tool(name, arguments=clean_kwargs)
        parts = []
        for c in result.content:
            if hasattr(c, "text") and c.text:
                parts.append(c.text)
            elif hasattr(c, "data"):
                parts.append(f"[binary: {len(c.data)} bytes]")
        return "\n".join(parts) if parts else repr(result)

    return StructuredTool.from_function(
        name=name,
        description=description,
        args_schema=DynamicSchema,
        coroutine=_async_call,
        func=lambda **kwargs: asyncio.run(_async_call(**kwargs)),  # sync fallback
    )


# ─── LLM ─────────────────────────────────────────────────────────────────────

def _load_api_key() -> str:
    # Check env vars first (both names langchain_google_genai accepts)
    for env_name in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
        key = os.environ.get(env_name, "")
        if key:
            # Ensure both are set
            os.environ["GOOGLE_API_KEY"] = key
            os.environ["GEMINI_API_KEY"] = key
            return key
    # Scan .env files — check WEB CASE STUDY first, then Legion-Jacked-Pipeline
    env_candidates = [
        os.path.join(BASE_DIR, ".env"),
        r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\.env",
        r"C:\.genkit\.env",
    ]
    for p in env_candidates:
        if os.path.exists(p):
            with open(p) as f:
                for line in f:
                    line = line.strip()
                    for prefix in ("GOOGLE_API_KEY=", "GEMINI_API_KEY="):
                        if line.startswith(prefix):
                            key = line.split("=", 1)[1].strip().strip('"').strip("'")
                            os.environ["GOOGLE_API_KEY"] = key
                            os.environ["GEMINI_API_KEY"] = key
                            log.info(f"Loaded API key from {p} ({prefix.rstrip('=')}")
                            return key
    return ""


def get_llm_with_tools(tools: list[BaseTool]) -> Any:
    """Gemini 2.5 Flash via langchain-google-genai, bound with all MCP tools."""
    api_key = _load_api_key()
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key or None,
        temperature=0,
    )
    return llm.bind_tools(tools)


# ─── GRAPH NODES ──────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = SystemMessage(content=(
    "You are the Legion Chrome Intelligence Agent — part of the Sovereign Sonic Core. "
    "You have direct access to a live Chrome browser via Chrome DevTools MCP tools. "
    "Use these tools to: navigate pages, evaluate JavaScript, capture screenshots, "
    "inspect DOM content, click elements, type into inputs, and manage tabs. "
    "Always confirm navigation succeeded before reading content. "
    "When complete, summarize clearly what you did and what you found."
))


def make_agent_node(llm_with_tools):
    """LLM reasoning node — emits tool calls or final text."""
    def agent_node(state: ChromeAgentState) -> dict:
        messages = [_SYSTEM_PROMPT] + list(state["messages"])
        response = llm_with_tools.invoke(messages)
        preview = response.content[:120] if response.content else "[tool call]"
        log.info(f"Agent: {preview}")
        return {"messages": [response]}
    return agent_node


def should_continue(state: ChromeAgentState) -> Literal["tools", "end"]:
    """Route after agent node."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return "end"


# ─── GRAPH BUILDER ────────────────────────────────────────────────────────────

def build_chrome_graph(tools: list[BaseTool]):
    """
    Compiles the LangGraph StateGraph.
    Identical structure to legion_graph.py:
        START → agent → (tool calls?) → tools → agent → ... → END

    Uses a manual async tool_node instead of langgraph.prebuilt.ToolNode
    to avoid the broken ExecutionInfo import in langgraph 1.0.10.
    """
    # Build a name→tool lookup for the tool node
    tool_map = {t.name: t for t in tools}

    llm_with_tools = get_llm_with_tools(tools)
    agent_node = make_agent_node(llm_with_tools)

    async def tool_node(state: ChromeAgentState) -> dict:
        """Execute all tool calls from the last AIMessage and return ToolMessages."""
        last_msg = state["messages"][-1]
        tool_messages = []
        for tc in last_msg.tool_calls:
            tool_name = tc["name"]
            tool_args = tc["args"]
            tool_call_id = tc["id"]
            t = tool_map.get(tool_name)
            if t is None:
                content = f"Error: tool '{tool_name}' not found."
            else:
                try:
                    if t.coroutine:
                        content = await t.coroutine(**tool_args)
                    else:
                        content = t.func(**tool_args)
                    if not isinstance(content, str):
                        content = str(content)
                except Exception as e:
                    content = f"Tool error ({tool_name}): {e}"
            log.info(f"Tool [{tool_name}]: {content[:120]}")
            tool_messages.append(
                ToolMessage(content=content, tool_call_id=tool_call_id, name=tool_name)
            )
        return {"messages": tool_messages}

    g = StateGraph(ChromeAgentState)
    g.add_node("agent", agent_node)
    g.add_node("tools", tool_node)

    g.set_entry_point("agent")
    g.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
    g.add_edge("tools", "agent")

    return g.compile()


# ─── PUBLIC API ───────────────────────────────────────────────────────────────

async def run_agent(prompt: str) -> str:
    """
    Full lifecycle:
    1. Spawn chrome-devtools-mcp via stdio (manages its own Chrome)
    2. Initialize MCP session, enumerate all tools
    3. Wrap tools as LangChain StructuredTools
    4. Build ChromeAgentState LangGraph
    5. Run agent to completion, return final text
    """
    log.info("=" * 64)
    log.info(f"PROMPT: {prompt}")
    log.info("=" * 64)

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "chrome-devtools-mcp@latest", "--no-usage-statistics"],
        env={**os.environ},
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            log.info("MCP session ready.")

            tools_resp = await session.list_tools()
            mcp_tools = tools_resp.tools
            log.info(f"{len(mcp_tools)} Chrome DevTools MCP tools available:")
            for t in mcp_tools:
                log.info(f"   • {t.name}")

            # Wrap MCP tools as LangChain StructuredTools
            lc_tools = [_make_langchain_tool(session, t) for t in mcp_tools]

            # Build and invoke the LangGraph StateGraph
            chrome_app = build_chrome_graph(lc_tools)

            initial_state: ChromeAgentState = {
                "messages": [HumanMessage(content=prompt)],
                "active_dna_context": {},
                "chrome_context": {},
            }

            final_state = await chrome_app.ainvoke(initial_state)

            # Return last AIMessage with content
            # Gemini 2.5 may return content as a list of parts [{"type":"text","text":"..."}]
            for msg in reversed(final_state["messages"]):
                if isinstance(msg, AIMessage) and msg.content:
                    content = msg.content
                    if isinstance(content, list):
                        parts = [
                            p["text"] for p in content
                            if isinstance(p, dict) and p.get("type") == "text" and p.get("text")
                        ]
                        return "\n".join(parts) if parts else str(content)
                    return str(content)

            return "[Agent completed — no final text response]"


# ─── CLI ENTRYPOINT ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Legion Chrome DevTools LangGraph Agent")
    parser.add_argument(
        "--prompt",
        type=str,
        default=(
            "Navigate to https://example.com, take a screenshot, "
            "then read the page title and main heading from the DOM."
        ),
        help="Task prompt for the Chrome agent.",
    )
    args = parser.parse_args()

    answer = asyncio.run(run_agent(args.prompt))
    print("\n" + "=" * 64)
    print("LEGION CHROME AGENT — FINAL RESULT")
    print("=" * 64)
    print(answer)
