"""
Send full pipeline context to Gemini 2.5 Pro with live registry data.
Ask it to query its own knowledge and generate code for all remaining phases.
"""
import os, sys, json, ray
from google import genai
from google.genai import types
from dotenv import load_dotenv

# ==============================================================================
# SOVEREIGN LIFE-CYCLE STABILIZER (AUTO-INJECTED)
# Prevents dangling stdout/stdio pipes and GCS registry locks on Windows exit
# ==============================================================================
import atexit
import signal

def clean_exit_handler(*args, **kwargs):
    import sys
    sys.stderr.write("\n[LMS LIFECYCLE] Exit triggered. Flushing system streams...\n")
    sys.stderr.flush()
    try:
        import ray
        if ray.is_initialized():
            sys.stderr.write("[LMS LIFECYCLE] Active Ray session detected. Disconnecting...\n")
            ray.shutdown()
    except Exception:
        pass
    sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================


if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

load_dotenv()
client = genai.Client()

contents_to_send = []

# ----------------------------------------------------------------
# 1. Pull LIVE registry summary from Ray (what's actually in memory)
# ----------------------------------------------------------------
print("Pulling live registry summary from Ray...")
ray.init(address='auto', ignore_reinit_error=True)
registry = ray.get_actor('SwarmKnowledgeRegistry', namespace='legion')
summary = ray.get(registry.get_registered_tables_summary.remote())

# Dump a readable snapshot for Gemini
registry_snapshot = {
    "total_tables": len(summary),
    "audio_pipeline_tables": {
        k: v for k, v in summary.items()
        if any(x in k.lower() for x in [
            'audio', 'vibe', 'sonic', 'mined', 'enriched', 'collision',
            'segment', 'manifest', 'chris_lake', 'stem', 'dsp',
            'track', 'sample', 'master', 'forest', 'omni', 'lancedb', 'duckdb'
        ])
    }
}

registry_json_path = r"C:\WEB CASE STUDY\live_registry_snapshot.json"
with open(registry_json_path, "w", encoding="utf-8") as f:
    json.dump(registry_snapshot, f, indent=2)
print(f"  -> {len(registry_snapshot['audio_pipeline_tables'])} audio/pipeline tables snapshotted")

# ----------------------------------------------------------------
# 2. Upload context files
# ----------------------------------------------------------------
uploads = [
    (r"C:\WEB CASE STUDY\AI_MODE.md",                  "AI_MODE.md — core architecture spec"),
    (r"C:\WEB CASE STUDY\data_discovery_guide.md",      "data_discovery_guide.md — Gemini's prior analysis & phase roadmap"),
    (r"C:\WEB CASE STUDY\dynamic_segment_master.py",    "dynamic_segment_master.py — current mastering engine"),
    (r"C:\WEB CASE STUDY\forest_engine_cell.py",        "forest_engine_cell.py — Random Forest classifier + Isolation Forest"),
    (r"C:\WEB CASE STUDY\ray_arrow_swarm.py",           "ray_arrow_swarm.py — Ray actor registry (SwarmKnowledgeRegistry)"),
    (r"C:\WEB CASE STUDY\split_and_master_pipeline.py", "split_and_master_pipeline.py — Demucs stem separation + mix audit"),
    (r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\mcp_server.py", "mcp_server.py — MCP tool server (query_knowledge_registry now live)"),
    (registry_json_path,                                "live_registry_snapshot.json — LIVE in-memory Ray registry (609 tables)"),
]

for path, label in uploads:
    if os.path.exists(path):
        print(f"Uploading: {label}")
        f = client.files.upload(
            file=path,
            config=types.UploadFileConfig(mime_type="text/plain", display_name=label)
        )
        contents_to_send.append(f)
    else:
        print(f"  SKIP (not found): {path}")

# ----------------------------------------------------------------
# 3. The prompt
# ----------------------------------------------------------------
prompt = """
You are a senior DSP engineer and Python architect embedded in an AI audio production system called the Legion-Jacked-Pipeline.

I am giving you the COMPLETE context of this system:
- AI_MODE.md: full architecture spec (the authoritative source of truth)
- data_discovery_guide.md: YOUR OWN prior analysis of this pipeline and the prioritized 3-phase roadmap
- The actual Python source files for the key scripts
- mcp_server.py: the MCP tool server — notably, `query_knowledge_registry` is now LIVE and working
- live_registry_snapshot.json: a live dump of what's currently loaded in Ray shared memory (609 tables, 21 audio/pipeline datasets confirmed)

## WHAT'S ALREADY DONE (as of this moment):
- Phase 1, Step 1: `query_knowledge_registry` MCP tool is live. SwarmKnowledgeRegistry runs as a detached Ray actor (namespace="legion") with 609 tables. `enriched_audio_dataset` (4,570 rows), `duckdb_audio_features` (1,084 rows), `chris_lake_omni_baseline` (22 segments), `lancedb_audio_vibe_gpu` (2,010 vectors) are all queryable.

## YOUR JOB — Generate the code for ALL remaining phases:

### Phase 1, Step 2: "Smart Mastering" — Classifier-Driven Dynamic Mastering
Integrate the Random Forest Classifier (from `forest_engine_cell.py`) and the PyTorch Synthesis Network into `dynamic_segment_master.py`.
- The RF classifier should run as a Ray actor, querying `chris_lake_omni_baseline` from the SwarmKnowledgeRegistry
- The PyTorch synthesis network should generate limiter/compressor params from the predicted style vector
- Output: a NEW file `smart_mastering_pipeline.py` that wires all three together end-to-end

### Phase 1, Step 3: Essentia C++ via WSL
- Write a WSL launcher script + a Python bridge (`essentia_wsl_bridge.py`) that:
  - Calls `wsl python3 -c "import essentia..."` to extract onset/beat/structural features
  - Returns results as a Python dict back to the Windows caller
  - Falls back gracefully to librosa if WSL is unavailable

### Phase 2, Step 4: Mastering Playbooks
- Write `generate_mastering_playbooks.py` that reads `mastering_swarm_summary.json`, finds the top 10 rated mastering scripts, and outputs a structured JSON `mastering_playbooks.json` with: effects chain, input/output params, target audio features, mastering goal

### Phase 2, Step 5: Mix Audit & Correction Agent
- Write `mix_audit_agent.py` that:
  1. Takes a stereo mix file path
  2. Separates stems via Demucs (reuse `split_and_master_pipeline.py` logic)
  3. Compares each stem's acoustic features against `chris_lake_omni_baseline` in LanceDB
  4. Outputs actionable corrections: "Reduce kick drum gain by X dB", "Apply phase rotation to bass"

For each file you generate, include:
- Full working Python code (no stubs, no placeholders)
- Imports, Ray actor setup, error handling
- A `if __name__ == "__main__":` test block that demonstrates it working

Output all four files as clearly labelled code blocks. Be specific — use actual table names, actual column names, and actual Ray actor names from the live registry snapshot I provided.
"""

contents_to_send.append(prompt)

# ----------------------------------------------------------------
# 4. Stream response — save each generated file
# ----------------------------------------------------------------
print("\nInitializing stateful chat session (model: google/gemma-4-31b-it)...")
chat = client.chats.create(model="google/gemma-4-31b-it")

# Determine a unique output filename that won't overwrite existing reports
base_out_file = r"C:\WEB CASE STUDY\gemini_phase_codegen.md"
out_file = base_out_file
if os.path.exists(out_file):
    base, ext = os.path.splitext(base_out_file)
    i = 1
    while os.path.exists(f"{base}_{i}{ext}"):
        i += 1
    out_file = f"{base}_{i}{ext}"

print(f"Streaming Response (saving code to: {os.path.basename(out_file)})...\n" + "="*70)

with open(out_file, "w", encoding="utf-8") as out:
    try:
        response = chat.send_message_stream(contents_to_send)
        for chunk in response:
            text = chunk.text or ""
            print(text, end="", flush=True)
            out.write(text)
    except Exception as e:
        print(f"\nError: {e}")

print("\n" + "="*70)
print(f"Full response saved to: {out_file}")