import os
import sys
import time
import json

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from legion_graph import app, HumanMessage

print("=" * 65)
print("RUNNING STREAMING LEGION AGENT TURN")
print("=" * 65)

prompt = """
Expose the tools (query_sonic_core, search_vibe_vectors, analyze_parquet, list_available_data, kernel_health) as a ToolsProvider.
Write 'src/toolsProvider.ts' and update 'src/index.ts' in C:\\Users\\adams\\.lmstudio\\extensions\\plugins\\lmstudio\\rag-v2.
"""

print(f"🚀 Prompt: '{prompt.strip()}'\n")

# Use app.stream() to process nodes and streaming tokens dynamically
for event in app.stream(
    {"messages": [HumanMessage(content=prompt)], "active_dna_context": {"tempo": 128, "key": "G", "rms_target": -13.9}},
    stream_mode="values"
):
    if "messages" in event:
        last_msg = event["messages"][-1]
        if last_msg.type == "ai":
            # Print content incrementally if present
            if hasattr(last_msg, "content") and last_msg.content:
                sys.stdout.write(last_msg.content)
                sys.stdout.flush()
            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                print(f"\n⚡ [Tool Calls Detected]: {last_msg.tool_calls}")

print(f"\n📥 [COMPLETED]")
