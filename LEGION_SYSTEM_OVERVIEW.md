# LEGION INTELLIGENCE — System Overview

Generated: 2026-06-22

---

## What This Is

A distributed multi-modal intelligence pipeline built by Adam McCoy for audio, web, and visual data processing. Runs locally on consumer hardware (5B class models). Connects to any AI assistant via MCP protocol.

---

## Core Capabilities

### 1. Audio Intelligence
- **Ingestion**: 9,000+ tracks vectorized in DuckDB + LanceDB
- **DSP Analysis** (librosa + essentia): BPM, Key, RMS, Crest Factor, Sub-bass/Mid/High energy, Spectral Centroid/Bandwidth/Rolloff/Flatness
- **Fire Test**: Ray-parallel alignment against Chris Lake reference — **99.6% accuracy** in 12ms per 50-segment track
- **Mastering Math**: Pure math (Pedalboard C++ → scipy → StandardScaler alignment), sovereign engine
- **Generation**: Hijacked MediaGen — pushes LanceDB math into tensors (~6 min for 10s of sound)
- **Stem Separation**: Demucs (hasn't worked; using Google Flow.app credits instead)

### 2. Web Intelligence
- `web_intel_pipeline.ipynb` — Scraping pipeline
- `search_swarm.py` — Web search swarm
- `forest_engine_cell.py` — RAG pipeline

### 3. Vision Pipeline
- `agent_vision.py` — Screenshot analysis
- `vision_pipeline.py` — Visual processing
- `dynamic_segment_alignment_ray.py` — Ray-parallel vision

### 4. Distributed Computing (Ray)
- **Ray-Arrow Swarm**: 635 JSON files → 609 PyArrow tables in **3.1 seconds**
- **SwarmKnowledgeRegistry Actor**: Persistent in-memory table registry (namespace: legion)
- **DSPAlignmentActor**: 4 actors, 1 CPU each, scipy C-extensions, 150 segments in ~30ms
- **Ray Dashboard**: http://127.0.0.1:8265

### 5. PHI Tool (Moat)
Pydantic + LangGraph validation BEFORE the LLM, not after.
- Data enters → Pydantic validates schema → Deterministic math (scipy/numpy) → Optional LLM reasoning
- No hallucinations on structured data, no prompt injection, GPU-free for most operations

### 6. MCP Gateway
- `legion-mcp` (stdio, working)
- `legion-api` (HTTP at localhost:8002, working)
- `legion-architect` (stdio, broken — path missing)

---

## Key Files

| File | Location | Purpose |
|------|----------|---------|
| `mcp_server.py` | `C:\STUDIES_BACKUP\` | Legion MCP server (search_tracks, query_neural_core) |
| `fire_test.py` | `C:\WEB CASE STUDY\` | Ray-parallel DSP alignment vs Chris Lake baseline |
| `dsp_alignment_actor.py` | `C:\WEB CASE STUDY\` | Ray Actor: scipy cdist alignment + self-verification |
| `legion_schema.py` | `C:\WEB CASE STUDY\` | Pydantic models (SegmentPhysics, AlignmentQuery, AlignmentResult) |
| `ray_arrow_swarm.py` | `C:\WEB CASE STUDY\` | Ray + PyArrow distributed JSON ingestion |
| `web_intel_pipeline.ipynb` | `C:\WEB CASE STUDY\` | Web scraping intelligence |
| `god_eye.py` | `C:\STUDIES_BACKUP\` | System audit (Docker, ports, code integrity) |
| `swarm_controller.py` | `C:\STUDIES_BACKUP\` | Swarm orchestration |

---

## Target Markets

1. **Record Labels** — Catalog search + AI querying ($15-30k)
2. **Sample Pack Companies** — Semantic vibe search ($10-25k)
3. **Ad Agencies** — Scrape + analyze competitor audio ($20-40k)
4. **Film/TV Post** — Stem separation + spectral analysis ($15-35k)
5. **Gaming Studios** — Dynamic audio generation ($40-80k)
6. **Enterprise** — Air-gapped MCP AI gateway ($80-200k+)

---

## Structure: You + Cline

"The Ray actors arent talkable so i always need someone like you" — The Ray Actors are stateful Python processes. They don't have a chat interface. They speak through:
- `ray.get()` calls (programmatic)
- Ray Dashboard (http://127.0.0.1:8265, visual)
- MCP tools (natural language, but only through an AI that calls them)

So your workflow is: You talk to an AI → AI calls MCP tools → MCP calls Ray actors → results come back.

---

## Hardware Limit

Consumer hardware, 5B class models max. Gemma 4 26B MoE (3.8B active) works. Ray keeps CPU at 100%. GPU used for Gemma Forge generation (6 min for 10s audio).


## The Stack

| Layer | Technology | Status |
|-------|-----------|--------|
| Ingestion | DuckDB + LanceDB | ✅ 9,000+ tracks |
| Vector Search | LanceDB GPU embeddings | ✅ 2,010 vectors |
| Parallel Processing | Ray + PyArrow | ✅ 635 files → 609 tables in 3.1s |
| AI Generation | Gemma 4 (hijacked MediaGen) | ✅ ~6 min for 10s audio |
| Analysis | Librosa + Essentia + Pedalboard | ✅ Full DSP pipeline |
| Stem Separation | Demucs (broken) / Google Flow.app | ⚠️ Using credits |
| Quality Audit | Agent scoring system | ✅ 88-98% accuracy |
| MCP Integration | 3 server variants (1 broken) | ✅ 11 MCP servers registered |
| Web Scraping | web_intel_pipeline | ✅ Working |
| Vision | agent_vision.py | ✅ Screenshot analysis |
| Validation | Pydantic + LangGraph (PHI tool) | ✅ Data-first before LLM |

---

## How It All Connects

```
You (Cline / Claude / Gemini)
  │
  ├── MCP Protocol ── legion-mcp ── DuckDB + LanceDB (search_tracks, query_neural_core)
  │                 └─ legion-api ── HTTP localhost:8002
  │
  ├── Ray Workers (not directly chat-able)
  │     ├── SwarmKnowledgeRegistry (in-memory table registry)
  │     ├── DSPAlignmentActor (scipy math on 4 CPUs)
  │     └── Ingest workers (parallel JSON → PyArrow)
  │
  ├── Local GPU
  │     ├── Gemma 4 Audio (generation / forge)
  │     └── [Future: vision models]
  │
  └── Filesystem
        ├── C:\STUDIES_BACKUP (Legion-Jacked-Pipeline)
        ├── C:\WEB CASE STUDY (notebooks, fire test, swarm)
        └── D:\MUSIC, E:\music (source audio)
```

---

## The Real Talk

### What Works
- Audio DSP pipeline with 99.6% alignment accuracy
- Ray-parallel ingestion (635 files in 3.1s)
- MCP gateway to any AI assistant
- Pydantic validation before LLM (PHI tool)
- Scraping + vision + audio all connected

### What Doesn''t (Yet)
- **Stem separation** (Demucs broken, using Google Flow credits)
- **legion-architect MCP** (path missing)
- **Ray actors not directly chat-able** — they''re Python processes, not APIs
- **Generation is slow** (6 min for 10s audio on consumer GPU)
- **UI/UX** — notebooks are the frontend, client dashboard missing

### The Core Insight

> "The Ray actors arent talkable so i always need someone like you"

This is the key structural constraint: Ray Actors are stateful Python processes that speak `ray.get()` — not HTTP, not MCP, not chat. They need a bridge. Currently that bridge is:

1. You talk to Cline (or any AI)
2. Cline calls MCP tools
3. MCP tools call Ray actors
4. Results come back through the chain

### The Hardware Limit

Consumer hardware, 5B parameter class models max. Gemma 4 26B MoE (3.8B active per token) works. Ray keeps CPU at 100%. GPU runs hot during Gemma Forge generation. No budget for cloud GPUs.

---

## Action Items

1. **Fix stem separation** or accept Flow.app as the workaround
2. **Fix legion-architect path** (point to working mcp_server.py)
3. **Build one MCP tool that wraps Ray** ("query_swarm_registry")
4. **Package for clients** — .env config, one-line setup
5. **Pick a company name** — Legion Intelligence is already in your namespace
6. **Export this chat** — use Cline Export Chat button in the IDE

---

## Pricing Model

| Tier | What They Get | Price |
|------|--------------|-------|
| Audit | One-time catalog ingestion + analysis report | $2k-5k |
| Deploy | Install MCP servers + Ray cluster + dashboard | $5k-15k |
| Custom | Pipeline tailored to their specific stack | $15k-50k+ |
| Retainer | Ongoing model tuning, new features, support | $2k-5k/mo |
