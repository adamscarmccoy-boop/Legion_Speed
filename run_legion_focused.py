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
print("RUNNING FOCUSED LEGION AGENT TURN")
print("=" * 65)

# Focused instruction to execute the ToolsProvider code write directly
prompt = """
Expose the tools (query_sonic_core, search_vibe_vectors, analyze_parquet, list_available_data, kernel_health) as a ToolsProvider.
Write 'src/toolsProvider.ts' and update 'src/index.ts' in C:\\Users\\adams\\.lmstudio\\extensions\\plugins\\lmstudio\\rag-v2.
"""

print(f"🚀 Prompt: '{prompt.strip()}'")

result = app.invoke({
    "messages": [HumanMessage(content=prompt)],
    "active_dna_context": {"tempo": 128, "key": "G", "rms_target": -13.9}
})

print(f"\n📥 [COMPLETED]")
for idx, m in enumerate(result["messages"]):
    print(f"\n[{idx}] {m.type.upper()}:")
    if hasattr(m, "content") and m.content:
        print(m.content)
    if hasattr(m, "tool_calls") and m.tool_calls:
        print("  ⚡ Tool Calls:")
        for tc in m.tool_calls:
            print(f"     ▶ {tc['name']}({tc['args']})")
