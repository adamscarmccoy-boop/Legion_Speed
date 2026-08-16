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
print("LEGION AGENT: EXECUTING TOOLSPROVIDER REWRITE WORKFLOW")
print("=" * 65)

# Prompt detailing the exact changes for index.ts, toolsProvider.ts, packages, and file removals
prompt = """
Your goal is to transition the plugin 'rag-v2' at 'C:\\Users\\adams\\.lmstudio\\extensions\\plugins\\lmstudio\\rag-v2' from a PromptPreprocessor model to a native ToolsProvider model.

Execute the following steps using your available tools:
1. Write 'src/toolsProvider.ts' exposing the core tools (query_sonic_core, search_vibe_vectors, analyze_parquet, list_available_data, kernel_health) using the @lmstudio/sdk tool() pattern.
2. Rewrite 'src/index.ts' to register context.withToolsProvider(toolsProvider). Remove any prompt preprocessor or lifecycle hooks that crash or are unused.
3. Clean up the directory structure.
4. Execute Monty sandbox runs to verify that the generated code is clean.

Begin implementation.
"""

print(f"🚀 Dispatching Prompt to LangGraph...")
t0 = time.time()

result = app.invoke({
    "messages": [HumanMessage(content=prompt)],
    "active_dna_context": {"tempo": 128, "key": "G", "rms_target": -13.9}
})

dt = (time.time() - t0) * 1000
print(f"\n📥 [AGENT WORKFLOW COMPLETED] Executed in {dt/1000:.2f} seconds ({dt:.2f}ms)")
print("=" * 65)
print("EXECUTION STEPS & TRANSCRIPTS:")
print("=" * 65)

for idx, m in enumerate(result["messages"]):
    print(f"\n[{idx}] {m.type.upper()}:")
    if hasattr(m, "content") and m.content:
        print(m.content)
    if hasattr(m, "tool_calls") and m.tool_calls:
        print("  ⚡ Tool Calls:")
        for tc in m.tool_calls:
            print(f"     ▶ {tc['name']}({tc['args']})")

