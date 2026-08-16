import os
import sys
import time

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

sys.path.append(r"C:\WEB CASE STUDY")
from legion_graph import app, HumanMessage

print("=" * 65)
print("TESTING FULL LEGION_GRAPH WORKFLOW INGESTION")
print("=" * 65)

t0 = time.time()
# Determine prompt dynamically from arguments, environment variable, or default
prompt = "what tools are available to you and what mcp's are available, confirm by using the mcp's tools with query for code/status or tables/code its associated with if issues. make sure monty is active and legion_graph is as well."
if len(sys.argv) > 1:
    prompt = sys.argv[1]
elif os.environ.get("LEGION_PROMPT"):
    prompt = os.environ["LEGION_PROMPT"]

print(f"🚀 Prompt: '{prompt}'")

result = app.invoke({
    "messages": [HumanMessage(content=prompt)],
    "active_dna_context": {"tempo": 128, "key": "G", "rms_target": -13.9}
})

dt = (time.time() - t0) * 1000
print(f"\n📥 [GRAPH COMPLETED] Ingested in {dt:.2f}ms")
print("=" * 65)
print("TURN TRANSCRIPTS:")
print("=" * 65)
for idx, m in enumerate(result["messages"]):
    print(f"\n[{idx}] {m.type.upper()}:")
    if hasattr(m, "content") and m.content:
        print(m.content)
    if hasattr(m, "tool_calls") and m.tool_calls:
        print("  ⚡ Tool Calls:")
        for tc in m.tool_calls:
            print(f"     ▶ {tc['name']}({tc['args']})")
