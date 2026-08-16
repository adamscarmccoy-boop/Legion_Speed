import os
import sys
import time
import json

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from legion_graph import app, HumanMessage

print("=" * 70)
print("LEGION GRAPH ONNX BRAIN AUDIT (via LM Studio + LangChain)")
print("=" * 70)

# 1. Gather context locally first so the LLM doesn't need to touch the disk.
TARGET_DIR = r"C:\WEB CASE STUDY"
brains = []
for root, _, files in os.walk(TARGET_DIR):
    for f in files:
        if f.lower().endswith(".onnx"):
            brains.append(os.path.join(root, f))

print(f"🔍 Discovered {len(brains)} ONNX brains in {TARGET_DIR}")
for b in brains[:10]:
    print(f"   • {os.path.relpath(b, TARGET_DIR)}")
if len(brains) > 10:
    print(f"   ... and {len(brains) - 10} more")

context_payload = {
    "task": "onnx_brain_audit",
    "target_dir": TARGET_DIR,
    "brain_count": len(brains),
    "brain_paths": brains,
    "note": (
        "List every brain, infer its purpose from filename + the manifest, "
        "report which ones are safe to load into the Legion swarm, "
        "and flag any duplicates, stale f16 aliases, or path mismatches. "
        "Use any tool you need (analyze_parquet_data, search_vibe_vectors, "
        "query_sonic_core, list_available_data)."
    ),
}

prompt = (
    "Audit the Legion ONNX brains. Here is the local inventory as JSON:\n"
    f"```json\n{json.dumps(context_payload, indent=2)}\n```\n"
    "Confirm what each brain does, whether it should be loaded into the "
    "legion Ray namespace, and whether the active LM Studio model "
    "(nvidia/nemotron-3-nano-4b) can drive tool calls reliably."
)

print(f"\n🚀 Dispatching prompt to legion_graph via LM Studio ({len(prompt)} chars)")

t0 = time.time()
result = app.invoke({
    "messages": [HumanMessage(content=prompt)],
    "active_dna_context": {"tempo": 128, "key": "G", "rms_target": -13.9},
})
dt = (time.time() - t0) * 1000

print(f"\n📥 [GRAPH COMPLETED] {dt:.2f}ms")
print("=" * 70)
print("TURN TRANSCRIPTS:")
print("=" * 70)
for idx, m in enumerate(result["messages"]):
    print(f"\n[{idx}] {m.type.upper()}:")
    if hasattr(m, "content") and m.content:
        print(m.content)
    if hasattr(m, "tool_calls") and m.tool_calls:
        print("  ⚡ Tool Calls:")
        for tc in m.tool_calls:
            print(f"     ▶ {tc['name']}({tc['args']})")
