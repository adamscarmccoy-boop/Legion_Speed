
import os
import sys
import json
import asyncio
from typing import Annotated, List, Literal, Union
import operator
from google import genai
from google.genai import types
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from dotenv import load_dotenv

# Ensure we are in the workspace root
os.chdir('C:/WEB CASE STUDY')
load_dotenv('.env')

# Add engine to path
sys.path.append(os.path.abspath('C:/WEB CASE STUDY/FretFlow-Audio-Engine'))

# ─── 1. TOOL DEFINITIONS ──────────────────────────────────────────────────────

def get_engine_status() -> dict:
    return {
        "status": "active",
        "sample_rate": 44100,
        "buffer_size": 1024,
        "latency_ms": 23.2,
        "conditioning": "Pedalboard Gain(+6dB)"
    }

def get_forest_engine_summary() -> dict:
    return {
        "model_type": "Multi-class RandomForest",
        "artist_classes": ["Chris Lake", "Fisher", "Charlotte de Witte", "Sam Shure", "Eli Brown"],
        "dsp_features": ["tempo", "rms_db", "crest_factor", "sub_bass_energy", "bass_energy", "mid_energy", "high_energy"],
        "market_fusion": ["popularity", "trending_score"],
        "status": "Ready for inference"
    }

def list_data_jsons() -> dict:
    data_dir = "C:/WEB CASE STUDY/data"
    if os.path.exists(data_dir):
        files = [f for f in os.listdir(data_dir) if f.endswith(".json")]
        return {"status": "success", "files": files}
    return {"status": "error", "message": "Data directory not found"}

def inspect_json_structure(filename: str) -> dict:
    file_path = f"C:/WEB CASE STUDY/data/{filename}"
    if not os.path.exists(file_path):
        return {"status": "error", "message": f"File '{filename}' not found."}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            sample = data[:2] if isinstance(data, list) else {k: data[k] for k in list(data.keys())[:2]}
            return {
                "status": "success",
                "filename": filename,
                "record_count": len(data) if isinstance(data, list) else 1,
                "structure_sample": sample
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

TOOLS_REGISTRY = {
    "get_engine_status": get_engine_status,
    "get_forest_engine_summary": get_forest_engine_summary,
    "list_data_jsons": list_data_jsons,
    "inspect_json_structure": inspect_json_structure,
}

# ─── 2. STATE DEFINITIONS ─────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[List[types.Content], operator.add]

# ─── 3. NORMALIZER HELPER ─────────────────────────────────────────────────────

def normalize_messages(messages: List[Union[types.Content, dict, any]]) -> List[types.Content]:
    normalized = []
    for msg in messages:
        if isinstance(msg, types.Content):
            normalized.append(msg)
        elif isinstance(msg, dict):
            role = msg.get("role", "user")
            if role == "assistant": role = "model"
            content = msg.get("content", "")
            normalized.append(types.Content(role=role, parts=[types.Part.from_text(text=content)]))
    return normalized

# ─── 4. NODE DEFINITIONS ──────────────────────────────────────────────────────

async def call_gemini_agent(state: AgentState):
    client = genai.Client()
    contents = normalize_messages(state["messages"])
    config = types.GenerateContentConfig(
        system_instruction=(
            "You are the FretFlow Intelligence Agent. Your goal is to analyze the "
            "Acoustic DNA signatures and coordinate with the Forest Engine and "
            "local JSON data assets. Use your tools to check engine status, "
            "inspect data structures, and query the Forest model capabilities."
        ),
        temperature=0.0,
        tools=[get_engine_status, get_forest_engine_summary, list_data_jsons, inspect_json_structure]
    )
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=contents,
        config=config
    )
    model_content = response.candidates[0].content
    if not model_content.role: model_content.role = "model"
    return {"messages": [model_content]}

async def execute_tools(state: AgentState):
    last_message = state["messages"][-1]
    tool_responses = []
    for part in last_message.parts:
        if part.function_call:
            call = part.function_call
            tool_func = TOOLS_REGISTRY.get(call.name)
            result = tool_func(**call.args) if tool_func else {"error": "Tool not found"}
            tool_responses.append(types.Part.from_function_response(name=call.name, response={"result": result}))
    return {"messages": [types.Content(role="user", parts=tool_responses)]}

def should_continue(state: AgentState) -> Literal["tools", "end"]:
    last_message = state["messages"][-1]
    if last_message.parts and any(p.function_call for p in last_message.parts):
        return "tools"
    return "end"

# ─── 5. COMPILE WORKFLOW ──────────────────────────────────────────────────────

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_gemini_agent)
workflow.add_node("tools", execute_tools)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
workflow.add_edge("tools", "agent")
app = workflow.compile()

# ─── 6. EXECUTION ─────────────────────────────────────────────────────────────

async def main():
    track_sig = [0.559, 0.558, 0.512, 0.542, 0.573, 0.562, 0.446, 0.436, 0.434, 0.449, 0.527, 0.542]
    query = types.Content(
        role="user",
        parts=[types.Part.from_text(text=(
            f"1. Summarize the Forest Engine capabilities.\n"
            f"2. List the JSON files and inspect 'duckdb_audio_features.json'.\n"
            f"3. Relate these to this track signature: {track_sig}"
        ))]
    )
    state = await app.ainvoke({"messages": [query]})
    last_msg = state["messages"][-1]
    print("--- AGENT START ---")
    print(''.join(p.text for p in last_msg.parts if p.text))
    print("--- AGENT END ---")

if __name__ == "__main__":
    asyncio.run(main())
