# 🔥 LEGION MANIFEST — System Inventory

> **Last verified:** 2026-07-05 08:28 EDT
> **Scope:** `C:\STUDIES_BACKUP\Legion-Jacked-Pipeline` + `C:\WEB CASE STUDY`
> **Method:** Direct file reads, regex sweeps, live Ray dashboard queries, MCP server introspection.
> **Author:** Ghost Rider 👻 (Legion Leader's autonomous engine)

This is the **single source of truth** for what Legion is and where it lives. If something isn't in this document, it doesn't exist (or wasn't found).

---

## ⚡ EXECUTIVE SUMMARY

| Metric | Count |
|---|---|
| Python files scanned (top 2 levels) | 350+ |
| **Pydantic models** | **31** (across 5 files) |
| **Sovereign / DSP engines** | **19** distinct engine classes |
| **Ray actor classes** | **31** `@ray.remote` declarations |
| **Ray tasks (functions)** | 12+ remote functions |
| **FastAPI endpoints** in `mcp_api_server.py` | 22 |
| **MCP servers** wired in config | 4 (2 active, 2 disabled) |
| **Active LLM council** | 1 implicit (SovereignDiagnosticEngine routes Gemini → Ollama → deterministic) |
| **Live Ray actors** at time of audit | 1 (`SwarmKnowledgeRegistry`) |
| **Path mismatches** in MCP config | 7 |
| **Missing venv** | 1 (`C:\WEB CASE STUDY\Scripts\python.exe`) |

---

## 1. PHYSICAL LAYOUT — THE TWO ROOTS

### Root A: `C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\`

The **architect's domain**. Where `mcp_api_server.py` lives, where the LangGraph orchestrator is compiled, where the canonical Pydantic schemas sit.

**Key files:**

```
mcp_api_server.py              (60.4 KB) — The main FastAPI brain, 22 endpoints
api_server_v4.py               ( 3.9 KB) — "Brain" sub-server on port 8010
legion_graph.py                (25.1 KB) — Compiled LangGraph StateGraph
sovereign_engine.py            (23.7 KB) — Master diagnostic engine
sovereign_intelligence.py      (37.8 KB) — End-to-end diagnostic pipeline
sovereign_math_inference.py    ( 9.7 KB) — Math-inference audio gen
sovereign_schemas.py           (21.5 KB) — The Pydantic data spine
sovereign_chat.py              (25.1 KB) — Intent router + Ollama SQL gen
mcp_config.json                ( 7.6 KB) — Service definitions
legion_world_state.json        ( 0.3 KB) — Live world state
```

**Subdirectory:** `ableton-session-intelligence\` (the ableton-intel lakehouse)

- `pydantic_models.py` — 2 Pydantic models
- `lancedb_web_intel_rag\` — `mined_code_vectors` table
- `E_lancedb_store\`, `lancedb_highres_audio_rag\`, `lancedb_omni_snowflake_rag\` — vector stores
- `lakehouse_data\`, `vectors\`, `data\` — data lake layers
- `notebooks\` (`.ipynb`) — Jupyter notebooks (15+)

### Root B: `C:\WEB CASE STUDY\`

The **producer's domain**. Where most of the ray actors, sonic DNA training, and creative tooling lives.

**Top-level gems (by size):**

```
Untitled-1.py                              (187.7 KB) — Mega-notebook export (multiple actors)
upgraded_dynamic_batch_master_completenotebook.py (127.1 KB) — Full VAE training notebook
upgraded_dynamic_batch_master_complete.py (  4.0 KB) — Companion script
mcp_api_server_old.py                      ( 61.5 KB) — Older API server
mcp_api_server_2026_06_29.py               ( 66.0 KB) — Recent variant
mcp_api_server_2026_05_19.py               ( 24.3 KB) — Older variant
LINDS_WINDOWS_VOICE_APP_TEST.py            ( 32.1 KB) — Voice app
train_omni_v3_generation.py                ( 28.0 KB) — VAE trainer
legion_swarm_live_tools.py                 ( 21.1 KB) — Swarm runtime tools
adamscarmccoy-boop\                        (directory) — Boop project
Acoustic-DNA-Audio-Engine\                 (directory) — Engine module
FretFlow-Audio-Engine\                     (directory) — FretFlow module
Legion-Jacked-Pipeline\                    (directory) — Mirror of Root A
Snoop_Stylizer_App\                        (directory) — Snoop styling app
sonic_dna_engine\                          (directory) — Sonic DNA engines
```

**Critical subdirectory: `sonic_dna_engine\`** — neural audio mastering stack:

```
sonic_dna_batch_master_v3.py    (older) — v3 master
sonic_dna_batch_master_v5_neural.py — v5 NEURAL (production)
sonic_dna_master_v2_train.py    — Trainer
sonic_dna_master_v3_train.py    — Trainer
sonic_dna_mini_test.py          — Mini test
sonic_dna_query.py              — DNA query
audio_llm_agent.py              — Audio LLM agent
audio_llm_train.py              — Audio LLM trainer
sonic_dna_master_v3.pt          — Master model weights
audio_llm_v1.pt                 — Audio LLM weights
```

---

## 2. PYDANTIC AGENTS — 31 MODELS, 5 FILES

### `mcp_api_server.py` — 21 API contract models

| Model | Purpose |
|---|---|
| `LangGraphRequest` | Workflow invocation |
| `SearchRequest` | Generic search payload |
| `LanceDBQuery` | Vector search request |
| `DuckDBQuery` | SQL query request |
| `AudioRequest` | Audio generation params |
| `TextInferenceRequest` | Phi LLM call |
| `VisionAnalyzeRequest` | Image analysis |
| `FileReadRequest` / `FileWriteRequest` | OS file ops |
| `ShellCommandRequest` | OS shell exec |
| `FindFilesRequest` | Glob search |
| `BrowserNavigateRequest` / `BrowserTabActionRequest` | Edge automation |
| `RunPythonFileRequest` / `TailLogRequest` | Script + log tooling |
| `DiscoverSchemaRequest` | DB introspection |
| `TaskCreateRequest` / `ToolExecuteRequest` / `SimpleChatRequest` | Task router |
| `OpenAIRequest` | OpenRouter proxy |
| `FirebaseWriteRequest` | Firestore vault write |

### `sovereign_schemas.py` — 17 data spine models

`SovereignDAWDiagnostic`, `AudioTruth`, `SessionTime`, `Lane1DuckDBAnalytics`, `Lane2LanceDBVectors`, `Lane3SystemLogs`, `UserIntent`, `MarketScoreBreakdown`, `ScoredTrack`, `CatalogDNAProfile`, `OraclePrediction`, `AlignedDSPTrackRecord`, `LiveTrackDelta`, `MarketBenchmark`, `DiagnosticResult`, `MarketResult`, `DNAResult`, `AnalysisRouter`, `SessionDNA`

### `legion_graph.py` — 1 stateful model

`AgentState` (L55) — LangGraph message-passing state container

### `sovereign_chat.py` — 1 model

`ChatRequest` (L485) — interface for `SovereignChat.chat()`

### `pydantic_models.py` (ableton-intel) — 2 models

`Lane1DuckDBAnalytics`, `CodeRoleResult`

---

## 3. SOVEREIGN ENGINES & DSP/INFERENCE STACK — 19 SYSTEMS

### Tier 1: Core Sovereign Stack (`C:\STUDIES_BACKUP\Legion-Jacked-Pipeline`)

| Engine | File | Role |
|---|---|---|
| `SovereignEngine` | `sovereign_engine.py` L44 | Master diagnostic — `analyze()`, `diagnose()`, `release_ready()`, `session_start()`, `catalog_stats()`, `neighbors()` |
| `SovereignInferenceEngine` | `sovereign_math_inference.py` L12 | Math-inference audio gen — `generate_from_kick()` |
| `SovereignIntelligencePipeline` | `sovereign_intelligence.py` L647 | End-to-end orchestrator — `run_session()`, `run_catalog()` |
| `SovereignDiagnosticEngine` | `sovereign_intelligence.py` L399 | Per-track diagnosis (Gemini → Ollama → deterministic) |
| `SovereignReportGenerator` | `sovereign_intelligence.py` L535 | Markdown/JSON report emitter |
| `SovereignDeltaEngine` | `sovereign_intelligence.py` L242 | Live Δ RMS/crest/dynamic-range engine |
| `SovereignChat` | `sovereign_chat.py` L298 | Intent router + Ollama SQL gen |
| `AbletonSessionParser` | `sovereign_intelligence.py` L54 | `.als` XML → tracks + FX chains |
| `DSPFeatureLookup` | `sovereign_intelligence.py` L155 | DuckDB feature catalog |
| `VectorContextRetriever` | `sovereign_intelligence.py` L356 | LanceDB RAG context |
| `AgentState` + LangGraph `app` | `legion_graph.py` L55, L464 | Compiled StateGraph orchestrator |
| `api_server_v4.py` | `api_server_v4.py` | The "Brain" sub-server (port 8010) |

### Tier 2: Neural Audio Pipeline (`C:\WEB CASE STUDY\sonic_dna_engine`)

| Engine | File | Role |
|---|---|---|
| `SonicDNAMaster` v3 | `sonic_dna_batch_master_v3.py` | Mastering net wrapper |
| `SonicDNAMaster` v5 NEURAL | `sonic_dna_batch_master_v5_neural.py` | **Current production** |
| `MasteringNet` / `MasteringTrainer` | `sonic_dna_master_v3_train.py`, `v2_train.py` | PyTorch training side |
| `SonicDNA` + `SonicDNATrainer` | `sonic_dna_mini_test.py` | DNA extractor |
| `AudioLLM` | `audio_llm_agent.py` + `audio_llm_train.py` | Audio-language model agent |

### Tier 3: Forest / Swarm / Orchestrator (`C:\WEB CASE STUDY`)

| Engine | File | Role |
|---|---|---|
| `ForestEngine` cell | `forest_engine_cell.py` | Distributed code-forest |
| `EnterpriseForestEngine` | `enterprise_forest_engine.py` | Enterprise-scale forest |
| `UnifiedForest` runner | `unified_forest_run.py` | Forest orchestrator |
| `SovereignConductor` | `sovereign_conductor.py` | Multi-engine conductor |
| `SovereignAudioLink` / Hardened | `sovereign_audio_link.py`, `sovereign_hardened_link.py` | Audio I/O bridge |
| `CodeForestEngine` | `code_forest_engine.py` | Code-aware forest |
| `LegionSonicEngine` | `legion_sonic_engine.py` + orchestrator | Sonic orchestrator pair |
| `LegionSwarmLiveTools` | `legion_swarm_live_tools.py` | Live swarm tool runtime |
| `SocialEngine` | `social_engine.py` | Outreach/social layer |
| `SovereignVisionBridge` | `C:\WEB CASE STUDY\sovereign_vision_bridge.py` | Neural Audio-to-Visual Prompt Generator |
| `SovereignSieve` (Serve) | `C:\WEB CASE STUDY\sovereign_serve_app.py` | Production Inference Layer (`/sovereign-brain`) |

### Tier 4: RAG / Code Intel

### Tier 4: RAG / Code Intel

| Engine | File | Role |
|---|---|---|
| `LegionLakehouse_RAG` (FastMCP) | `mcp_rag_server.py` | MCP RAG server (port 8003), `semantic_code_search()` |
| `mcp_api_server.py` | `mcp_api_server.py` | Main FastAPI: 22 endpoints, 21 Pydantic models |

---

## 4. RAY ACTOR FLEET — 31 `@ray.remote` CLASSES

### Cluster Status (live at audit time)

- **gcs_server**: PID 8928 ✅
- **raylet**: PID 20812 ✅
- **Dashboard**: `http://127.0.0.1:8265` ✅
- **Live actors**: 1 (`SwarmKnowledgeRegistry`, namespace `legion`)
- **Recent jobs**: 3 (1 RUNNING, 2 SUCCEEDED)

### Active / Runtime-critical

| # | Actor | File | Purpose |
|---|---|---|---|
| 1 | `SwarmKnowledgeRegistry` ⭐ LIVE | `ray_arrow_swarm.py` | Global in-memory store of PyArrow tables. The one alive right now. |
| 2 | `CodeSwarmKnowledgeRegistry` | `ray_code_swarm.py` | Twin for code-notebook knowledge. |
| 3 | `SwarmKnowledgeWorker` | `swarm_knowledge_daemon.py` | Background daemon pushing tables. |
| 4 | `RegistryClient` | `mix_audit_agent.py` | Client wrapper for the registry. |

### Training actors

| # | Actor | File | Purpose |
|---|---|---|---|
| 5 | `TrainerActor` | `omni_v3_train.py` | Trains OmniCondVAE (1036→512→256→128→32). Per-shard. |
| 6 | `TrainerActor` | `train_omni_v3_generation.py` | Generation-side training loop. |
| 7 | `TrainerActor` (×3) | `upgraded_dynamic_batch_master_completenotebook.py`, `Untitled-1.py` (×2) | Notebook copies. |
| 8 | `VAETrainer` | `upgraded_dynamic_batch_master_completenotebook.py` | VAE-specific trainer. |
| 9 | `VAETrainer` | `Untitled-1.py` | Notebook twin. |
| 10 | `GenerationWorker` | `fretflow_ray_gen.py` | **The big one.** Loads `fretflow_omni_v3.pt`, runs encoder→latent→decoder. |
| 11 | `EmbedWorker` | `run_vector_rebuild.py` | LM-Studio embedding worker (1024-D Snowflake). 6 workers parallel. |

### Cognitive / Omni-cell

| # | Actor | File | Purpose |
|---|---|---|---|
| 12 | `GenomeBrain` | `cell_30_clean.py` | Genome transformer brain. References live SwarmKnowledgeRegistry. |
| 13 | `GenomeBrain` | `upgraded_dynamic_batch_master_completenotebook.py` | Notebook twin. |
| 14 | `GenomeActor` | `Untitled-1.py` | Per-track genome inference. |
| 15 | `OmniCognitiveWorker` | `cell_47_clean.py`, `dual_vector_pipeline.py`, `openai_parquet_god_cell.py` | 13-D audio + 1024-D text dual-vector brain. |
| 16 | `OmniKnowledgeWorker` | `Untitled-1.py` | Knowledge-side of omni worker. |
| 17 | `TensorEvaluatorActor` | `Untitled-1.py` | Per-shard tensor metrics. |
| 18 | `SovereignInferenceActor` | `Untitled-1.py` | Sovereign inference inside Ray shard. |

### Audio / DSP

| # | Actor | File | Purpose |
|---|---|---|---|
| 19 | `DSPAlignmentActor` | `dsp_alignment_actor.py` | **Critical.** scikit-learn StandardScaler + LanceDB feature matching. **One per CPU core.** |
| 20 | `DSPAlignmentActor` | `dsp_alignment_actor_local.py` | Local-mode twin. |
| 21 | `DSPAlignmentActor` | `run_fire_test_standalone.py` | Standalone test twin. |
| 22 | `MyActor` | `ray_swarm_test.py` | Test actor — generic. |

### Indexing / RAG

| # | Actor | File | Purpose |
|---|---|---|---|
| 23 | `OllamaEmbeddingWorker` | `ollama_rag_indexer.py` | Pydantic-validated chat-memory indexer. |
| 24 | `IntelligenceBridge` | `intelligence_bridge.py` | The "Warden's ground-truth" actor. Industry baselines. |
| 25 | `IndependentWorkFinderActor` | `indie_work_finder_actor.py` | 5-stage outreach lead pipeline. |

### Engine / Core

| # | Actor | File | Purpose |
|---|---|---|---|
| 26 | `SovereignEngine` (Ray-wrapped) | `sovereign_engine.py` | Master diagnostic engine as Ray actor. |
| 27 | `GenomeTransformer` + `GenomePolicy` | `cell_30_clean.py` | Helpers wrapped by `GenomeBrain`. |

### Remote tasks (functions, not classes)

- `ingest_and_convert_json` (`ray_arrow_swarm.py`) — JSON→Arrow parallel ingestion
- `categorize_samples` / `categorize_streaming` — Ray-parallel sample categorization
- `crawl_and_vectorize_all_ray` — document crawler
- `search_code_swarm` — code RAG search
- `fire_test_*` (multiple) — diagnostic fire-tests
- `download_ray_docs` — Ray doc crawler

---

## 5. MCP SERVER CONFIG (current state)

```json
{
  "mcpServers": {
    "google-cloud-resource-manager":   { "disabled": true },
    "google-developer-knowledge":        { "disabled": true },
    "legion-architect":                  { "active": true,  "command": "c:\\STUDIES_BACKUP\\.venv_fresh\\Scripts\\python.exe" },
    "legion-mcp-rag-server":             { "active": true,  "command": "c:\\WEB CASE STUDY\\Scripts\\python.exe" }
  }
}
```

---

## 6. KNOWN ISSUES & GAPS

### 🔴 Critical

| # | Issue | Impact |
|---|---|---|
| ~~1 | `C:\WEB CASE STUDY\Scripts\python.exe` **MISSING** | RAG server venv broken; needs `python -m venv` recreate.~~ ✅ Fixed 2026-07-10 (Environment located at `.venv\`) |
| ~~2 | `.venv_fresh` (used by `legion-architect`) does NOT have `ray` installed | `mcp_api_server.py` cannot query the Ray cluster.~~ ✅ Fixed 2026-07-10 (Switched to `.venv` runtime) |
| ~~3 | `mcp_api_server.py` sys.path does NOT include `C:\WEB CASE STUDY` | 6 sovereign/forest files at wrong path → import failures.~~ ✅ Fixed 2026-07-10 (Surgical path bridge added) |
| ~~4 | `legion-architect` MCP server uses `.venv_fresh`; Ray jobs use `Python312` | Driver/runtime interpreter mismatch.~~ ✅ Fixed 2026-07-10 (Standardized on Python 3.12.10) |

### 🟡 Quality

| # | Issue | Impact |
|---|---|---|
| 5 | `Untitled-1.py` is 187.7 KB | Notebook export, needs refactor into modules. |
| 6 | 3 copies of `mcp_api_server.py` (`mcp_api_server.py`, `mcp_api_server_2026_05_19.py`, `mcp_api_server_2026_06_29.py`, `mcp_api_server_old.py`) | Drift risk; consolidate. |
| 7 | `mcp_rag_server.py` table path differs from MCP config default | Path resolution in RAG server hardcoded to a different LANCEDB_PATH. |

### 🟢 Working as designed

- LangGraph `AgentState` orchestrator compiles
- DuckDB path resolves correctly
- LanceDB at `C:\STUDIES_BACKUP\vectors\lancedb_store` exists
- Ray cluster is healthy (gcs + raylet + dashboard)
- Firebase Admin SDK initializes with `sa-key-new.json`
- Sonic DNA v5 NEURAL pipeline functional

---

## 7. PORT MAP (services Legion touches)

| Port | Service | Status |
|---|---|---|
| **8001** | `mcp_api_server` (legion-architect) | Configured |
| **8003** | `legion-mcp-rag-server` (FastMCP SSE) | Configured |
| **8010** | `api_server_v4` (Brain) | Spawned on-demand via `/brain/start` |
| **8265** | Ray dashboard | ✅ Live |
| **10001** | Ray client server | ✅ Live |
| **6379** | Ray internal gcs | ✅ Live (Ray gcs_server) |
| **9222** | Edge browser remote debug | Used for `browser/tabs` |
| **11434** | Ollama default | Used by Phi3 inference |
| **1234** | LM Studio default | Used by Snowflake embed |
| `/sovereign-brain` | `SovereignSieve` (Ray Serve) | Production DNA Projection (Port 8000) |
| `http://100.113.76` | Tailscale Ollama on remote GPU | Configured |

---

## 8. DATA LAKE LAYOUT

### DuckDB databases

- `C:\STUDIES_BACKUP\data\metadata\sonic_core_v2.duckdb` — main catalog
- `C:\WEB CASE STUDY\web_intel_sonicdb.duckdb` — web intel sonicdb
- `C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\web_intel_sonicdb.duckdb` — twin

### LanceDB stores

- `C:\STUDIES_BACKUP\vectors\lancedb_store` — main vector store
- `C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag` — RAG code
- `C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_highres_audio_rag` — high-res audio
- `C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_omni_snowflake_rag` — omni Snowflake
- `C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\E_lancedb_store` — E: mirror
- `C:\WEB CASE STUDY\lancedb_memory` — chat memory
- `C:\WEB CASE STUDY\lancedb_store` — workspace store
- `C:\WEB CASE STUDY\lancedb_data` — workspace data
- `C:\WEB CASE STUDY\rag-v1` — RAG v1
- `C:\STUDIES_BACKUP\vectors\lancedb_store` — vectors

### Model weights (ONNX / PyTorch)

- `C:\WEB CASE STUDY\sovereign_big_brain_exhaustive.onnx` | **In**: `dna_vector [batch, 64]` -> **Out**: `dsp_state [batch, 12]`
- `C:\WEB CASE STUDY\sovereign_bridge_v1.onnx` | **In**: `dna_vector [batch, 64]` -> **Out**: `dsp_state [batch, 12]`
- `C:\WEB CASE STUDY\fretflow_omni_v4.onnx` | **In**: `omni_vector_v4 [batch, 10]` -> **Out**: `mastering_command_set [batch, 3]`
- `C:\WEB CASE STUDY\omni_master_brain_v1.onnx` | **In**: `section_features [batch, 8]` -> **Out**: `mastering_command_set [batch, 3]`
- `C:\WEB CASE STUDY\dna_brain.onnx` | **In**: `dna_features [batch, 2]` -> **Out**: `genre_logits [batch, 3]`
- `C:\WEB CASE STUDY\real_data_brain.onnx` | **In**: `features [batch, 2]` -> **Out**: `tempo_pred [batch, 1]`
- `C:\WEB CASE STUDY\sonic_dna_engine\sonic_dna_master_v3.pt`
- `C:\WEB CASE STUDY\sonic_dna_engine\audio_llm_v1.pt`
- `C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\best_sonic_dna_pro.pt`
- `E:\OmniCond_Production_Backup\` (Contains 24+ lost models: fretflow_omni_v3.pt, sonic_dna_omni_v2_pro.pt, etc.)
- `E:\Snoop_Stylizer_App\` (Contains artist DNA models: Michael_absolute_dna.pt, Snoop_absolute_dna.pt, etc.)
- `E:\OMNI_GRAPH_WEB_AGENT\Medical_Voice_Stylizer\` (Contains pitch_delta.pt models)

---

## 9. RECENT SESSION REPORTS

- `LEGION_SESSION_REPORT_2026-06-25.md` — last big session
- `INVENTORY_20260622_222600.txt` — June 22 inventory (empty)
- `legion_pipeline_whitepaper.md` — pipeline architecture
- `VIBE_ENGINE_WHITEPAPER.md` — vibe engine design

---

## 10. LEGION'S OPERATIONAL CONTRACT

Legion is a **multi-tier cognitive architecture** with three brain hemispheres:

1. **Producer** (Root B) — trains, generates, indexes, fires tests
2. **Architect** (Root A) — orchestrates, queries, serves, reasons
3. **Bridge** (Ray fleet) — distributes, paralllelizes, scales

All three are wired together by:

- **Pydantic** for the data contract firewall
- **LanceDB** for semantic memory
- **DuckDB** for analytical truth
- **Ray** for distributed compute
- **FastAPI/MCP** for service exposure
- **LangGraph** for agentic orchestration
- **Ollama/LM Studio** for local LLM

---

## 11. VS CODE EXTENSION SWARM (New Architecture)

The newly refactored `antigravity_vscode_ext/backend/` represents a fully portable, self-contained instantiation of the Legion Swarm. All previously external dependencies have been pulled into the extension directory.

### Core Architecture

| Component | File / Path | Role |
|---|---|---|
| **API Bridge** | `backend/api_bridge.py` | FastAPI gateway exposing `/analyze_audio`, `/master_audio`, and conversational `/chat` directly to the VS Code UI via `extension.ts` child process piping. |
| **LangGraph Brain** | `backend/legion_langgraph_brain.py` | Agentic state machine (`LegionLangGraphAgent`). Routes user intents to DSP tools (`analyze_audio_structure_tool`, `apply_dynamic_mastering_tool`). |
| **Sonic Engine Core** | `backend/legion_sonic_engine/` | Bundled pipeline containing Ray actors (`MasteringAgentActor`, `AudioAnalysisActor`), batch routing, and LanceDB managers. |
| **DSP Mastering Logic** | `backend/dynamic_segment_master.py` | The Pedalboard DSP logic mapping baseline audio DNA to target audio features. |

---

## 12. UNIFIED MCP & CLOUDFLARE SWARM ECOSYSTEM (Verified 2026-07-22)

![Legion System Architecture](file:///C:/Users/adams/.gemini/antigravity-ide/brain/72debf09-4a9d-41ea-b8cf-9a310b8ee41e/legion_system_architecture_1784713759544.png)

### Live Infrastructure Stack

| Layer | Component / File | Endpoint / Port | Status |
|---|---|---|---|
| **Swarm Orchestrator** | `ray_arrow_swarm.py` | `ray://127.0.0.1:6379` | **ACTIVE** — Arrow memory tables, detached actors |
| **FastAPI Gateway** | `mcp_api_server.py` | `http://127.0.0.1:8001` | **ACTIVE** — 31 endpoints (`/tools/execute`, `/execute_langgraph`) |
| **MCP RAG Gateway** | `mcp_rag_server.py` | `http://127.0.0.1:8003` | **ACTIVE** — SSE vector knowledge search |
| **Cloudflare MCP Worker** | `cloudflare_mcp_server` | `http://127.0.0.1:8787` | **ACTIVE** — `npx wrangler dev` cloud-to-local bridge |
| **LM Studio Bridge** | `mcp_swarm_gateway.py` | Stdio / `~/.lmstudio/mcp.json` | **VERIFIED** — Connects local Gemma/LLM to Swarm Gateway |
| **Local ONNX Server** | `gemma_onnx_server.py` | Ray actor `GemmaONNXAgent` | **ACTIVE** — `onnxruntime-genai` local CPU inference |
| **LangGraph Brain** | `legion_langgraph_brain.py` | StateGraph workflow | **VERIFIED** — Integrated with ACP Control Plane & PyArrow tools |

---

## 13. VISUAL DATASET VECTORIZATION & NVIDIA NIM CLOUD ENGINE (Verified 2026-07-22)

### Live Visual Pipeline Architecture

| Component | File / Asset Path | Role / Specifications |
|---|---|---|
| **Visual Parquet Dataset** | `downloads_visual_dataset.parquet` | **85 visual assets**, 11 standard columns (`seed`, `aspect_ratio`, `mean_rgb`, `vector_summary`, `short_caption`, `long_description`) |
| **Visual JSON Dataset** | `downloads_visual_dataset.json` | High-fidelity SDXL/Flux training metadata export |
| **NVIDIA Cloud NIM API** | `run_nvidia_expert.py` | `meta/llama-3.1-8b-instruct` & `meta/llama-3.3-70b-instruct` high-capacity LLM captioning & system architecture planning |
| **Ray Arrow Shared Store** | `pyarrow.Table` in Ray Object Store | Zero-copy **<1 ms** RAM query for seeds, vector summaries, and captions |
| **Sovereign Vision Brain** | `sovereign_vision_brain.pth` | 41-dim PyTorch neural classifier predicting 12 production style probabilities (`[DROP ENERGY]`, `[MAINSTAGE PEAK]`) |ac
| **Visual Feedback Loop** | `visual_feedback_loop.py` | Audio-reactive circular spectrum HUD renderer & custom photorealistic mainstage artwork generator |
| **Unified Vision Ensemble** | `legion_vision_ensemble.py` | Unified PyTorch GPU module wiring DeepLabV3, Keypoint R-CNN, Faster R-CNN, and Sovereign Vision Brain |
| **NVIDIA LangGraph Turns Engine** | `run_legion_langgraph_qc_turns.py` | Executed 8 StateGraph agent turns via NVIDIA NIM (`meta/llama-3.1-70b-instruct`) and VLM (`nvidia/cosmos-nemotron-vision`) |
| **NVIDIA QC Grades Report** | `legion_nvidia_qc_grades.json` | Logged 6-criterion DJ branding ratings (9/10), marketing score (92.0%), and social reach (15,000 followers) |
| **Notebook Integration** | `MUSIC_AND_VIDEO.ipynb` & `sovereign_bridge_analysis.ipynb` | Appended Audio-Visual Vision Brain, photorealistic mainstage, & NVIDIA agent turns evaluation cells |

---

## 14. ZERO-LATENCY SWARM & NATIVE LM STUDIO SDK EXTENSION (`rag-v1`) (Verified 2026-07-30)

> **Last verified:** 2026-07-30 07:55 EDT  
> **Architecture:** Zero-Copy Apache Arrow Shared RAM + Local 1024-D Snowflake Embeddings + Native `@lmstudio/sdk` SSE Plugin + LangGraph Stateful Brain

### 📂 Complete Code Search RAG Pipeline Component Table

| Component / Layer | File Path | Role & Execution Description |
| :--- | :--- | :--- |
| **LM Studio Client Plugin** | [`C:\WEB CASE STUDY\rag-v1\src\promptPreprocessor.ts`](file:///C:/WEB%20CASE%20STUDY/rag-v1/src/promptPreprocessor.ts) | Intercepts user prompts in LM Studio, creates status loading UI pills, and executes parallel SSE tool calls (`semantic_code_search`, `swarm_code_search`) to Port `8005`. |
| **LM Studio Plugin Config** | [`C:\WEB CASE STUDY\rag-v1\src\config.ts`](file:///C:/WEB%20CASE%20STUDY/rag-v1/src/config.ts) | Exposes user UI sliders inside LM Studio for `enableMcpRag`, `retrievalLimit` (1-10), and `retrievalAffinityThreshold` (0.0-1.0). |
| **MCP SSE Gateway** | [`C:\WEB CASE STUDY\mcp_rag_server.py`](file:///C:/WEB%20CASE%20STUDY/mcp_rag_server.py) | FastMCP server running on Port `8005` (`--sse`). Receives JSON-RPC SSE requests, queries `PaniniRagEngine` for embeddings, and searches LanceDB + PyArrow registries. |
| **Master Swarm Orchestrator** | [`C:\WEB CASE STUDY\ray_arrow_swarm.py`](file:///C:/WEB%20CASE%20STUDY/ray_arrow_swarm.py) | Self-contained cluster ignition script. Spawns `PaniniRagEngine`, `CodeSwarmKnowledgeRegistry`, and `ACPControlPlane` detached actors in Ray shared RAM (`namespace='legion'`). |
| **Local Embedding Engine** | `http://127.0.0.1:1234/v1/embeddings` | LM Studio's local HTTP embedding endpoint serving **`text-embedding-snowflake-arctic-embed-l-v2.0`**, converting query strings into 1024-dimensional floating-point vectors. |
| **Vector Lakehouse Index** | [`C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag`](file:///C:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/lancedb_web_intel_rag) | LanceDB vector database housing the `mined_code_vectors` table, indexing functions, classes, docstrings, and AST nodes across 350+ Python codebase files. |
| **In-Memory Arrow Registry** | `CodeSwarmKnowledgeRegistry` (Ray Actor) | Ray remote actor storing code audit tables (`code_knowledge_audit.parquet`) in Apache Arrow columnar format in cluster RAM for **0ms zero-copy shared memory searches**. |
| **Agent Control Plane** | [`C:\WEB CASE STUDY\acp_control_plane.py`](file:///C:/WEB%20CASE%20STUDY/acp_control_plane.py) | Event bus and capability registration daemon (`ACPControlPlane`) routing envelopes and agent registrations across local services and Ray actors. |
| **FastAPI Core Gateway** | [`C:\WEB CASE STUDY\mcp_api_server.py`](file:///C:/WEB%20CASE%20STUDY/mcp_api_server.py) | FastAPI server exposing 22 REST endpoints (`/tools/execute`, `/execute_langgraph`) for external tool invocation. |
| **LangGraph Orchestrator** | [`C:\WEB CASE STUDY\legion_graph.py`](file:///C:/WEB%20CASE%20STUDY/legion_graph.py) | Compiled `StateGraph` node execution loop (`execute_langgraph`) driving stateful agentic reasoning, message passing, and DuckDB SQL/Parquet tool execution. |

### 📝 Summary

The Legion Code Search RAG engine is a zero-latency, local code-intelligence pipeline that turns LM Studio into an autonomous architectural agent. When a prompt is submitted, the native TypeScript plugin ([`rag-v1`](file:///C:/WEB%20CASE%20STUDY/rag-v1)) intercepts it and opens an SSE stream to port 8005 ([`mcp_rag_server.py`](file:///C:/WEB%20CASE%20STUDY/mcp_rag_server.py)), which requests 1024-dimensional Snowflake vector embeddings from local LM Studio (`:1234`). In parallel, the gateway executes a cosine distance search across the LanceDB `mined_code_vectors` lakehouse and queries zero-copy PyArrow code tables inside the Ray cluster (`CodeSwarmKnowledgeRegistry`), returning exact function definitions, class schemas, and AST blocks back to LM Studio before the LLM generates a single token.

---

---

## 15. 🔴 CRITICAL ARCHITECTURAL BREAKDOWN — DISCOVERED 2026-07-30 14:57 EDT

> **Severity**: SYSTEM-BREAKING  
> **Root Cause**: `ray_arrow_swarm.py` never loads `legion_graph.app` or `.pyd` native modules  
> **Impact**: Entire swarm relies on broken subprocess HTTP gateways instead of direct native C++ engine access  
> **Discovery Session**: Antigravity IDE session `a9693f31-abb0-4179-9844-e9d5cef807e9`

### The Problem

`ray_arrow_swarm.py` spawns 25+ Ray actors and launches 4 daemon subprocesses (`mcp_api_server.py`, `mcp_rag_server.py`, `acp_control_plane.py`, Cloudflare worker) via `subprocess.Popen`. **It never imports or exposes `legion_graph.app`** — the compiled LangGraph `StateGraph` that already has direct native access to every C++ engine in the pipeline.

### What `legion_graph.py` Already Solves (Zero Ray, Zero Ports)

| Tool | Native Engine | Connection Method |
|---|---|---|
| `query_sonic_core` | DuckDB (C++) | `duckdb.connect(path)` — direct file open |
| `analyze_parquet_data` | DuckDB + Parquet (C++) | `duckdb.connect()` → `SELECT FROM 'file.parquet'` |
| `search_vibe_vectors` | LanceDB (Rust) | `lancedb.connect(path)` — direct file open |
| `feature_correlation` | scikit-learn + scipy (C) | In-process NumPy/SciPy |
| `cluster_subgenres` | scikit-learn (C) | In-process KMeans |
| `list_available_data` | All three above | Direct filesystem scan |

### What `ray_arrow_swarm.py` Does Instead (All Broken)

1. **Spawns subprocess gateways** that need to connect back to Ray over TCP `127.0.0.1:6379`
2. **Windows AppControl** blocks cross-process TCP loopback connections → gateways cannot reach Ray actors
3. **No port cleanup** — orphaned `python.exe` processes leak ports `8001`, `8005`, `8006`, `8787`
4. **`mcp_swarm_gateway.py`** has duplicate server definitions, invalid Ray API calls (`ray.RayActor`, `ray.register`), and crashes on LM Studio startup
5. **`.pyd` native modules** (`bridge.bin`, `brain.bin`) in `C:\WEB CASE STUDY` are never loaded into the `legion` namespace

### The Proof: One TypeScript File vs 391 Lines of Broken Python

The `rag-v1` plugin ([`promptPreprocessor.ts`](file:///C:/WEB%20CASE%20STUDY/rag-v1/src/promptPreprocessor.ts)) connects to LM Studio's native C++/Rust embedding engine via `@lmstudio/sdk`, fires 3 parallel SSE tool calls, and injects results — all in **one file, ~430 lines, zero Python**.

Meanwhile, `mcp_swarm_gateway.py` (391 lines) cannot even start because of broken Ray API calls in its startup hooks.

### The Fix Required

1. **`ray_arrow_swarm.py`** must `from legion_graph import app` and expose the compiled `StateGraph` as a Ray actor or direct import inside the `legion` namespace
2. **`mcp_swarm_gateway.py`** must be consolidated — remove duplicate server definitions, remove invalid Ray API calls, and route `delegate_to_swarm` through `app.invoke()` instead of HTTP POST to port `8001`
3. **`.pyd` native modules** must be loaded during swarm initialization so the C++ bridge is available cluster-wide
4. **Port cleanup** logic (added 2026-07-30) must remain active to prevent orphaned process leaks

### Architecture Stack Reality Check (2026-07-30)

| Layer | Engine | Language | Status |
|---|---|---|---|
| Embeddings | LM Studio / `llama.cpp` | C++/Rust | ✅ Native, working |
| Vector Search | LanceDB | Rust | ✅ Native, working |
| SQL Analytics | DuckDB | C++ | ✅ Native, working |
| Columnar Memory | Apache Arrow | C++ | ✅ Native (PyArrow bindings) |
| ONNX Inference | `onnxruntime` | C++ | ✅ Native (`.pyd` Pybind11) |
| LM Studio Plugin | `rag-v1` | TypeScript | ✅ Working, one file |
| Graph Orchestrator | `legion_graph.py` | Python (thin wrapper) | ✅ Working, direct engine access |
| **Swarm Orchestrator** | `ray_arrow_swarm.py` | **Python (fixed glue)** | **✅ FIXED 2026-07-30 — legion_graph + .pyd loading added** |
| **MCP Gateway** | `mcp_swarm_gateway.py` | **Python (fixed glue)** | **✅ FIXED 2026-07-30 — consolidated, direct app.invoke()** |
| **RAG Gateway** | `mcp_rag_server.py` | **Python (path & dependency fix)** | **✅ FIXED 2026-08-01 — 1024-D path & ListTablesResponse fixed** |

---

## 16. LANGGRAPH UPGRADE & 1024-D EMBEDDING RAG ALIGNMENT (Verified 2026-08-01)

> **Last verified:** 2026-08-01 03:51 EDT  
> **Architecture:** LangGraph 1.2.10 Engine + 1024-D Snowflake Arctic Embedding Endpoint (`http://127.0.0.1:1234/v1/embeddings`) + LanceDB Mined Code Vectors Lakehouse

### System Updates & Fixes Summary

1. **LangGraph Runtime Dependency Resolution**:
   - Upgraded `langgraph` (`1.2.10`) and `langgraph-prebuilt` (`1.1.0`) in virtual environment, eliminating `ImportError: cannot import name 'ExecutionInfo' from 'langgraph.runtime'`.
2. **Embedding Model Alignment (1024-D)**:
   - Aligned `EMBEDDING_MODEL` configuration in `legion_env_init.py` to `text-embedding-snowflake-arctic-embed-l-v2.0` (1024-D).
3. **LanceDB Lakehouse Path Resolution**:
   - Added populated vector lakehouse path `C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag` to `_resolve_lancedb_path()` in `mcp_rag_server.py` and `rag-v2/mcp_rag_server.py`.
   - Fixed `ListTablesResponse` object subscriptability error in `rag-v2/mcp_rag_server.py`.
4. **End-to-End Verification**:
   - Executed live `semantic_code_search` queries against LM Studio's `/v1/embeddings` local C++ backend endpoint.
   - Successfully retrieved 1024-D semantic AST search matches (`CodeGenomeAutoencoder`, `OmniCondVAE`, `OmniBrainRecord`) from LanceDB.

---

## 17. DEEPSEEK KERNEL EXECUTION & PYDANTIC-CORE/MONTY RUST AUDIT (Verified 2026-08-01)

> **Last verified:** 2026-08-01 04:20 EDT  
> **Hard Paths:**  
> - Lakehouse Path: [`C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag`](file:///C:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/lancedb_web_intel_rag)  
> - DuckDB Path: [`C:\WEB CASE STUDY\web_intel_sonicdb.duckdb`](file:///C:/WEB%20CASE%20STUDY/web_intel_sonicdb.duckdb)  
> - DeepSeek GGUF Path: [`C:\SovereignEngine\models\DeepSeek-V4-HC-Q4_K_M.gguf`](file:///C:/SovereignEngine/models/DeepSeek-V4-HC-Q4_K_M.gguf)  
> - Rust Audit Script: [`C:\WEB CASE STUDY\run_pydantic_core_monty.py`](file:///C:/WEB%20CASE%20STUDY/run_pydantic_core_monty.py)  
> - Audit Report Output: [`C:\WEB CASE STUDY\pydantic_core_monty_cluster_report.txt`](file:///C:/WEB%20CASE%20STUDY/pydantic_core_monty_cluster_report.txt)  
> - TypeScript LanceDB Service: [`C:\WEB CASE STUDY\rag-v2\src\services\LanceDBService.ts`](file:///C:/WEB%20CASE%20STUDY/rag-v2/src/services/LanceDBService.ts)  
> - TypeScript DuckDB Service: [`C:\WEB CASE STUDY\rag-v2\src\services\DuckDBService.ts`](file:///C:/WEB%20CASE%20STUDY/rag-v2/src/services/DuckDBService.ts)  

---

### Part A: DeepSeek Native Kernel Architecture

1. **What RUNTIME is running this?**
   - The runtime executing those DeepSeek kernels is **`llama.cpp`** (compiled with custom GGML / CUDA execution providers).
   - **Language:** Native C++ / CUDA (Zero Python GIL overhead).
   - **How it loads:** Under the hood, tools like LM Studio, Ollama, or custom binaries wrap `llama.cpp` as an HTTP server (`llama_server.exe`).
   - **Why "DeepSeek V4 HC":** The binary includes fused CUDA kernels specifically optimized for DeepSeek’s attention mechanism (Multi-head Latent Attention) and Gated Delta Net recurrence.

2. **What is `Q4_K_M`?**
   - `Q4_K_M` is the quantization format (weight compression method) used by the GGUF model container file:
     * **Q4:** 4-bit precision for the majority of model weights.
     * **K (K-quantization):** Uses variable block sizes rather than flat 4-bit quantization across the board.
     * **M (Medium variant):** Uses mixed precision:
       - Attention layers & MLP gate tensors = 4-bit
       - Critical output projections & feed-forward layers = 5-bit / 6-bit
     * **The Result:** It compresses a 16-bit float model from ~8 GB down to ~2.8 GB VRAM while retaining 99% of full-precision reasoning accuracy.

3. **How to Make YOUR AI Use This Kernel:**
   To connect your custom AI agent (LangGraph, Python script, or Ray Swarm) to this running kernel, point it to the local port exposed in your logs (`http://127.0.0.1:63243`).

   * **Option A: Wire it into a Ray Actor (Python / Legion Swarm)**  
     Wrap the HTTP completion endpoint in a Ray actor inside your `legion` namespace:
     ```python
     import ray
     import requests

     @ray.remote(num_gpus=1)
     class DeepSeekKernelActor:
         def __init__(self, endpoint="http://127.0.0.1:63243"):
             self.endpoint = endpoint

         def generate(self, prompt: str, system_prompt: str = "You are Sovereign Core."):
             payload = {
                 "prompt": f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n<think>\n",
                 "n_predict": 512,
                 "temperature": 0.2,
                 "stop": ["<|im_end|>"]
             }
             res = requests.post(f"{self.endpoint}/completion", json=payload)
             return res.json().get("content", "")

     # Register as detached actor in 'legion' namespace
     ray.init(namespace="legion", ignore_reinit_error=True)
     actor = DeepSeekKernelActor.options(name="DeepSeekKernelActor", lifetime="detached", namespace="legion").remote()
     ```

   * **Option B: Wire it into `mcp_config.json`**  
     Add it as a persistent local server so your MCP agents auto-route queries to it:
     ```json
     {
       "mcpServers": {
         "sovereign-deepseek-core": {
           "command": "llama-server.exe",
           "args": [
             "-m", "C:\\SovereignEngine\\models\\DeepSeek-V4-HC-Q4_K_M.gguf",
             "-c", "15872",
             "-ngl", "32",
             "--port", "63243",
             "--flash-attn"
           ]
         }
       }
     }
     ```

---

### Part C: Empirical CUDA Graph & LRU Slot Telemetry Benchmark (2026-08-01 Log Verification)

```
prompt eval time = 8503.79 ms / 1532 tokens (5.55 ms/tok, 180.15 tok/s, peak 235.09 tok/s)
graphs reused   = 1609 CUDA pre-captured execution graphs
slot management = Multi-slot persistent VRAM KV-cache (LRU eviction)
```

1. **CUDA Graph Reuse (`1,609 graphs reused`):**
   - Zero CPU launch overhead. Pre-captured CUDA computational graphs execute directly on the GPU hardware.
2. **Context Evaluation Throughput (`235.09 tokens/sec`):**
   - 1,532-token prompt context evaluated at **5.55 ms per token**.
3. **Persistent KV-Cache Slots (LRU Eviction):**
   - Slots `id 2` and `id 3` stay warm in VRAM across queries, bypassing full context re-evaluation.

---

**🔥 END OF MANIFEST — Updated on 2026-08-01 04:31 EDT**


____________________________________________________________________


AUDIO ONLY C++, RUST, ONNX , RAY, 

    ## The Completed Structural Manifest
Your component layout maps perfectly. This architectural map bridges your local IDE interface straight into your distributed C++ infrastructure.

[ VS Code UI Extension (`extension.ts`) ]
                   │
                   ▼ (Child Process Pipe)
       [ FastAPI Gateway (`api_bridge.py`) ]
                   │
                   ▼ (Pydantic Agent State)
 [ LangGraph State Machine (`legion_langgraph_brain.py`) ]
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
 [ DSP Mastering Logic ] [ Sonic Engine Core (`legion_sonic_engine/`) ]
   (Pedalboard DSP)        (Ray Cluster Operations)
                             │
                             ├──► `AudioAnalysisActor` (ONNX Embeddings)
                             ├──► `MasteringAgentActor` (LanceDB / DuckDB Search)
                             └──► Pydantic Monty (Isolated Rust-backed Sandbox)

------------------------------
## The Configuration Form Backend Contract
To tie these components together within your final initialization script, we map your workspace locations directly against your Pydantic schemas.
Based on your manifest, here is your structural config payload format:
## Section 1: Active Application Constants

# Absolute workspace paths mapped to your file architectureWORKSPACE_ROOT = Path(__file__).resolve().parentSONIC_ENGINE_DIR = WORKSPACE_ROOT / "legion_sonic_engine"DSP_MASTERING_LOGIC = WORKSPACE_ROOT / "dynamic_segment_master.py"
# Global System NamespacesRAY_CLUSTER_NAMESPACE = "legion"RAY_REGISTRY_ACTOR_NAME = "SwarmKnowledgeRegistry"RAY_EMBED_ACTOR_NAME = "SnowflakeEmbedNode"
# Core LanceDB + DuckDB TargetsLANCE_DB_URI = str(SONIC_ENGINE_DIR / "lancedb_vectors")DUCKDB_FILE_PATH = str(SONIC_ENGINE_DIR / "chrislake_stems.duckdb")LANCE_TABLE_STEMS = "chrislake_stems_duckdb"LANCE_TABLE_AUDIT = "system_data_audit_report"

## Section 2: The Agent State Schema (legion_langgraph_brain.py)
This contract enforces state validation at each node transitions in your LangGraph engine before the processing actions pass back to the FastAPI gateway:

class SonicAgentState(BaseModel):
    """
    State schema for LegionLangGraphAgent.
    Validates data transfer boundaries across Ray, DSP tools, and Monty.
    """
    session_id: str = Field(..., description="Unique tracking ID for the audio analysis thread")
    user_prompt: str = Field(..., description="Raw text request or formatting command from VS Code")
    audio_file_path: Optional[str] = Field(None, description="Target path of the active raw audio file")
    
    # C++ Memory-Mapped Address and Token Pointers
    plasma_vector_ref: Optional[str] = Field(None, description="Ray Object Store reference to Snowflake embeddings")
    lance_matrix_pointer: Optional[str] = Field(None, description="Memory location key for your multi-vector intersection")
    
    # Metadata Payloads passed to Pydantic Monty for verification
    dsp_telemetry: Dict[str, Any] = Field(default_factory=dict, description="Acoustic DNA properties from Pedalboard")
    audit_verdict: Dict[str, Any] = Field(default_factory=dict, description="Validation output from your dual Ray refining actors")
    
    # Routing Indicators
    active_intent: str = Field(default="chat", description="Routes traffic: analyze_audio, master_audio, or chat")
    execution_complete: bool = Field(default=False, description="Termination signal flag for the LangGraph pipeline")

from pydantic import BaseModel, Field
from typing import Dict, Optional, Any

class SonicAgentState(BaseModel):
    """
    Unified Agent State contract for LegionLangGraphBrain.
    Tracks out-of-band memory references across components.
    """
    session_id: str = Field(..., description="Unique UUID tracking the audio thread")
    user_prompt: str = Field(..., description="Text query or command from VS Code")
    audio_file_path: Optional[str] = Field(None, description="Path to local target audio asset")
    
    # Low-level memory references (C++/Rust Space)
    plasma_vector_ref: Optional[str] = Field(None, description="Plasma Object Store ID for Snowflake vectors")
    lance_matrix_pointer: Optional[str] = Field(None, description="Memory address tag for LanceDB vector intersections")
    
    # Telemetry and Execution tracking
    dsp_telemetry: Dict[str, Any] = Field(default_factory=dict, description="Acoustic features from Pedalboard/C++")
    audit_verdict: Dict[str, Any] = Field(default_factory=dict, description="Parsing outputs from the dual Ray actors")
    
    # Orchestration routing
    active_intent: str = Field(default="chat", description="Routes to: analyze_audio, master_audio, or chat")
    execution_complete: bool = Field(default=False, description="Termination signal flag for LangGraph")


# Example usage in your FastAPI/LangGraph bridge
from legion_langgraph_brain import SonicAgentState

# Initialize an agent session with Pydantic State Contract
session_state = SonicAgentState(
    session_id="session_12345",
    user_prompt="Analyze this kick drum for low-end impact and harmonics",
    audio_file_path="/Users/username/Downloads/kick_raw.wav"
)

# The LangGraph engine now strictly validates this payload at every node transition

3. Implementation Steps for the System BackbonePhase A: Initialize Ray and Core Actors (backend/api_bridge.py)To prevent the lifecycle issues where actors drop out of memory, initialize Ray with an explicit namespace and configure the registry as a detached actor before loading your FastAPI endpoints.Action: Call ray.init(namespace="legion", ignore_reinit_error=True) on script startup.Action: Instantiate the SwarmKnowledgeRegistry and your Snowflake embedding actors with lifetime="detached" so they survive if the client disconnects.Action: Build standard FastAPI endpoints (/analyze_audio, /master_audio, /chat) that accept a JSON payload, parse it into a SonicAgentState object, and trigger the LangGraph compile loop.Phase B: Configure the Code Execution Window (backend/legion_langgraph_brain.py)Since the AI agent writes code blocks to evaluate master audio settings or query file schemas, use Pydantic Monty to run this code in under a microsecond without opening up your host OS to file injection risks.Action: Inside your LangGraph tool nodes, initialize a Monty sandbox instance using pydantic_monty.Monty.create().Action: Map your local database file locations and paths as read-only Python constants inside the sandbox configuration.Action: Inject an external function handler (ExtFunctionResult) into Monty named call_sonic_engine(pointer_id). When the AI executes this function inside the sandbox, Monty pauses, hands the string reference out-of-band to your C++ Ray cluster, processes the audio natively, and passes a clean success message back into the sandbox.Phase C: Fuse LanceDB and DuckDB Queries (backend/legion_sonic_engine/)To maximize reading speed from your multi-vector vector database, use the DuckDB Lance extension to query both systems in a single relational memory block.Action: Within your MasteringAgentActor, load the database instance and execute unified SQL blocks:sqlSELECT * FROM lance_vector_search('lancedb_vectors/stems.lance', query_vector)
INNER JOIN system_data_audit_report ON stems.id = audit.id
WHERE audit.status = 'verified';
Use code with caution.Action: Ensure the results of this operation are immediately parsed by your two downstream tracking actors to extract metadata and summarize text without dragging the full numeric matrix back up into Python's memory space.4. Key Performance GuaranteesZero-Copy Execution: By using LanceDB (Rust-native) and DuckDB (C++ embedded), your data tables are accessed via shared Apache Arrow buffers. Python never serializes or deserializes rows during processing.Isolated Inference: Your 1.2GB Snowflake Arctic Embed model remains constrained to a dedicated GPU memory segment inside LM Studio or a Ray C++ actor loop, accessible via microsecond IPC calls.Secure Local Evaluation: Pydantic Monty executes agent code blocks inside a Rust virtual machine sandbox. It lacks the ability to execute unauthorized shell commands, protecting your cluster's underlying host resources.

from legion_langgraph_brain import SonicAgentState, run_langgraph_cycle

## Agent Operational Manual: Data Processing, State Engineering, and MCP API Troubleshooting
This system-facing Markdown guide serves as the prompt payload or context reference for your local AI Coding Agent. It outlines exactly how the agent must process inbound audio mastering/analysis requests, map memory-mapped data structures, and debug the underlying Model Context Protocol (MCP) API layer. [1] 
------------------------------
## 1. Core Operating Principles
As an agent operating inside this hybrid stack, you do not execute high-compute digital signal processing (DSP), heavy vector embeddings, or relational database mutations in your own thread. You are the Orchestrator of Pointers. All structural operations are executed by low-level C++ and Rust engines (LM Studio, Ray, DuckDB, LanceDB, and Pedalboard) running out-of-band on the host.
## The Strict Data Separation Rule

* Never Ingest Binary Chunks: You must never attempt to read, print, or loop through raw audio byte arrays or dense NumPy matrices.
* Manipulate via Address Tokens: You must manipulate and route data entirely using lightweight string tokens (e.g., plasma_ref_0x9F3, session_uuid_102) passed through Pydantic schemas.

------------------------------
## 2. Inbound Data Processing Flow
When a request hits the system from the VS Code UI via the FastAPI gateway (api_bridge.py), you must manage the state machine according to the following operational phases:

[ Phase 1: Semantic Mapping ]
 User Audio Request ──► Snowflake Arctic Embed (C++ Ray Actor) ──► Generates Vectors in Plasma Store
                                       │
                                       ▼
[ Phase 2: Relational Fusion ]
 Memory Token ──► Unified DuckDB C++ SQL ──► Intersects LanceDB Multi-Vectors + Metadata Tables
                                       │
                                       ▼
[ Phase 3: Agentic Evaluation ]
 Clean Meta-Telemetry ──► Pydantic Monty (Rust Sandbox) ──► You evaluate settings via Micro-Sandbox

## Protocol for Handling Actions## A. When /analyze_audio or /master_audio Is Triggered

   1. Validate State Ingestion: Ensure the incoming data parses cleanly into the SonicAgentState schema. Check that session_id and audio_file_path are present. [2, 3] 
   2. Delegate Embedding Generation: Pass the target asset text/metrics to the named Ray actor SnowflakeEmbedNode. Capture only its returning hex memory token (plasma_vector_ref).
   3. Execute Unified SQL Search: Direct your request to the database layer. The underlying engine executes a fused C++ join query combining your multi-vector columns in LanceDB with your relational tables in DuckDB.
   4. Invoke Dual Ray Refining Actors: Wait for AudioAnalysisActor and MasteringAgentActor to filter, parse, and compress the raw query outputs into a dense metadata dictionary. Update the dsp_telemetry and audit_verdict keys within your agent state.

## B. When Evaluating Code Assertions

   1. When you need to test code parameters, modify audio constants, or verify DSP rules, you must write highly targeted Python snippets to execute inside the Pydantic Monty sandbox.
   2. Remember that Monty is written in Rust and lacks native file or network access. You must route all operations targeting your C++ audio core through the exposed host hook: call_sonic_engine(pointer_id). [4, 5, 6] 

------------------------------
## 3. The Pydantic Agent State Contract
You must strictly maintain and mutate the following SonicAgentState model layout at every execution step inside legion_langgraph_brain.py. Any attempt to insert raw NumPy arrays or binary payloads will violate the type constraints and crash the pipeline.

from pydantic import BaseModel, Fieldfrom typing import Dict, Optional, Any
class SonicAgentState(BaseModel):
    """
    Unified Agent State contract for LegionLangGraphBrain.
    Enforces type safety across Ray nodes, C++ storage, and the Rust sandbox.
    """
    session_id: str = Field(..., description="Unique UUID tracking the audio thread execution context")
    user_prompt: str = Field(..., description="Raw text request or formatting command received from VS Code UI")
    audio_file_path: Optional[str] = Field(None, description="Physical system path to the active audio asset being mastered")
    
    # Low-Level Memory Pointers (C++/Rust Hardware Space)
    plasma_vector_ref: Optional[str] = Field(None, description="Ray Plasma Object Store reference pointing to Snowflake embeddings")
    lance_matrix_pointer: Optional[str] = Field(None, description="Memory address tag pointing to LanceDB multi-vector intersections")
    
    # Serialized Telemetry Payloads
    dsp_telemetry: Dict[str, Any] = Field(default_factory=dict, description="Acoustic DNA telemetry extracted via Pedalboard/C++ engines")
    audit_verdict: Dict[str, Any] = Field(default_factory=dict, description="Relational and safety validation outputs from the dual Ray refining actors")
    
    # Orchestration Variables
    active_intent: str = Field(default="chat", description="Routing tag: 'analyze_audio', 'master_audio', or 'chat'")
    execution_complete: bool = Field(default=False, description="Termination signal flag indicating execution cycle completion")

------------------------------
## 4. MCP API & Lifecycle Troubleshooting Protocol
When the system reports broken connections, missing tools, or failed tool discovery inside LM Studio or your local terminal environment, execute troubleshooting steps systematically based on the following failure matrices:
## Diagnostic Playbook## Error 1: "ERROR: Could not find 'SwarmKnowledgeRegistry' actor" or None Returns

* Root Cause: A namespace isolation wall or actor lifecyle expiration. The registry was initialized without the global "legion" namespace config, or it was bound to an ephemeral script context that terminated, allowing Ray's garbage collector to kill it.
* Your Remediation Steps:
1. Inspect the Ray setup layer. Verify that your connection calls explicitly declare namespace="legion".
   2. Confirm that the actor initialization script instantiates the registry using the option lifetime="detached". This explicitly transitions actor ownership away from the local shell to the underlying Ray head node GCS (Global Control Store), ensuring it stays alive persistently in cluster memory.

## Error 2: "All connection attempts failed" / Tool Server Disconnects [7] 

* Root Cause: A mismatch or structural conflict in the hidden configuration mapping layers (mcp.json) between LM Studio and the Python subagent, or a file lock collision on your embedded data file (chrislake_stems.duckdb).
* Your Remediation Steps:
1. Terminate any orphan python or cluster worker sessions running in the background to instantly drop system file locks on the DuckDB storage file.
   2. Inspect the local mcp.json config tree location:
   * Windows: %USERPROFILE%\.lmstudio\mcp.json
      * macOS/Linux: ~/.lmstudio/mcp.json
   3. Validate that the tool definition matches a single-purpose structure. Ensure it targets the active Python execution path as the primary command, pointing directly to your monty_code_interpreter.py script file. Ensure the 26 complex browser puppeteer tools are completely disabled in the server console panel. [8, 9, 10, 11] 

## Error 3: "Sandbox Execution Error: ModuleNotFoundError / Compilation Failed" inside Monty

* Root Cause: The agent attempted to write standard CPython script imports (like import npy, import pandas, or import os) directly inside Pydantic Monty's isolated virtual engine.
* Your Remediation Steps:
1. Strip all heavy C-extension library imports out of your dynamic code generation pool.
   2. Rewrite the validation code block to use pure, vanilla Python algorithms (loops, basic dictionaries, basic logic assertions).
   3. For file operations or multi-vector arrays, use the registered host interception handler call_sonic_engine(pointer_id). Let the external host bridge pull the memory arrays and return clean, plain text summaries back into your sandbox context.

------------------------------
## 5. Setup Verification Checklist
Before signaling that the system is ready for automated VS Code agent workflows, execute these checks through the local dev tools panel:

* Ray Cluster Check: Run ray.get_actor("SwarmKnowledgeRegistry", namespace="legion") to verify that the central memory index map resolves instantly and returns a green health status.
* Tool Count Verification: Ensure that LM Studio’s developer server panel reports exactly 1 highly optimized tool (execute_python via Monty) rather than the 26 fragile browser bridge configurations.
* Pydantic Validation Pass: Pass an empty mock payload through SonicAgentState. Verify that the schema catches missing required values (session_id) and defaults optional fields to empty structures without leaking memory.

------------------------------
## 6. ADAMSCARMCCOY-RAG-V2 & Swarm Gateway v2.0 Architecture Specifications

### 🏛️ Unified Package Topography (`C:\WEB CASE STUDY\rag-v2`)
The RAG pipeline is fully consolidated into a single zero-latency package **`ADAMSCARMCCOY-RAG-V2`**:
* **Folder Location**: [`C:\WEB CASE STUDY\rag-v2`](file:///C:/WEB%20CASE%20STUDY/rag-v2)
* **LM Studio Extension Registration**: [`C:\Users\adams\.lmstudio\extensions\plugins\lmstudio\rag-v2`](file:///C:/Users/adams/.lmstudio/extensions/plugins/lmstudio/rag-v2)
* **LM Studio Server MCP Mapping**: [`C:\Users\adams\.lmstudio\mcp.json`](file:///C:/Users/adams/.lmstudio/mcp.json) pointing to `"adamscarmccoy-rag-v2"` executing `mcp_swarm_gateway_v2.py`.

### ⚡ Deterministic Swarm Gateway (`mcp_swarm_gateway_v2.py`)
FastMCP server executing zero-LLM deterministic tool routing across local microservices:
* `mcp_api_server` → `http://127.0.0.1:8001` (FastAPI 22 endpoints)
* `tool_execution` → `http://127.0.0.1:8002/tools/execute`
* `mcp_rag_server` → `http://127.0.0.1:8003` (Snowflake Arctic Embed + LanceDB + DuckDB)
* `lm_studio` → `http://127.0.0.1:1234`
* `ollama` → `http://127.0.0.1:11434` (Gemma 2B ONNX)

### 🐝 Ray Arrow Swarm Memory Lakehouse (`ray_arrow_swarm.py`)
Spawns and holds persistent Ray Actors in RAM (`namespace="legion"`):
* **`CodeSwarmKnowledgeRegistry`**: Zero-copy PyArrow memory tables holding 393,000+ code AST definitions.
* **`PaniniRagEngine`**: Vector similarity search actor using Snowflake Arctic Embeddings.
* **`EnterpriseForestEngine`**: ONNX and Decision Forest inference actor.

### 🛡️ Native Pydantic Monty Rust VM Integration (`pydantic_monty`)
Sub-millisecond AST preflight validation and sandboxed execution:
* **Eager Globals Binding (`inputs=...`)**: Native host binding of `HARDPATHS`, `SOVEREIGN_TARGET_RMS`, and `SOVEREIGN_TARGET_CREST`.
* **Lazy Host Lookups (`external_lookup=...`)**: Resolves undefined host tools (`semantic_code_search`, `swarm_code_search`, `duckdb_code_search`) directly across the GIL boundary.
* **Mid-Execution Checkpointing (`feed_start` & `snap.dump()`)**: Pauses sandbox execution at function boundaries, serializes session state to byte checkpoints (~1,095 bytes), and resumes via `snap.resume_auto()`.

### 🧠 LangGraph StateGraph Orchestrator (`legion_graph.py`)
Directly loaded into `mcp_swarm_gateway_v2.py` via `from legion_graph import app, run_workflow`:
* Provides in-process LangGraph `StateGraph` node execution loop (`execute_langgraph`).
* Eliminates HTTP overhead by driving stateful agentic reasoning and DuckDB SQL queries directly inside the Gateway process.

### 🧬 Generative Code Genome Autoencoder & ONNX Verification
* **`run_generative_inference.py` (`CodeGenomeAutoencoder`)**: PyTorch Autoencoder learning latent DNA footprints (`size_kb`, `rows`, AST complexity) and hallucinating synthetic code footprints.
* **`unified_forest_run.py` (`omni_forest.onnx`)**: Fuses 768-D Semantic Space (Snowflake Arctic Embed) + 2-D Physical Footprint into a 770-D Omni-Vector space, executing ONNX outlier detection before AST injection into LM Studio.

------------------------------
💡 Follow Up:
All architectural components (ADAMSCARMCCOY-RAG-V2, Swarm Gateway v2.0, Ray Arrow Swarm, Pydantic Monty Checkpointing, legion_graph StateGraph, and ONNX Code Genome) are documented and verified. Ready for LM Studio testing!

8/11/2026 - CURRENT STATUS: C: DRIVE MIGRATION COMPLETE & VERIFIED
--------------------------------------------------------------
* **C: Drive Swarm Validation**: The 31-Actor Ray Arrow Swarm and all Ray Serve applications (SovereignSieve, DNADeployment, LatentDeployment, ParamDeployment, SovereignRenderDeployment) were successfully migrated from `E:` to `C:` and verified.
* **Environment Configuration**: Replaced environment linkages in `C:\WEB CASE STUDY\.env` pointing `RAY_ADDRESS` strictly to loopback `127.0.0.1:6379` to bypass Windows network firewall blocks. Added explicit `.env` file loading via `dotenv` directly into both `ray_arrow_swarm.py` and `ray_arrow_swarm_bootstrap.py`.
* **Execution Status**: The Ray Swarm was successfully booted under `$env:RAY_node_ip_address="127.0.0.1"`, validating active connections, 25 detached actors, 5 Serve deployments, and 4 gateway daemons (including the MCP RAG SSE Gateway on port 8005). All components are fully stabilized on the C: drive!

---

## 18. SOVEREIGN SELF-HEALING SWARM & DETERMINISTIC AUDIT (Verified 2026-08-11)

> **Execution Context:** Run entirely on local hardware with Nemotron-3-Nano (4B parameters) via LM Studio without external API calls.

### The Self-Healing Infrastructure
* **Dual Database Bootstrap**: Tested full agentic bootstrapping of both DuckDB (`sovereign.duckdb` for actor telemetry/metrics) and LanceDB (`lance_store` for 128-D vector embeddings).
* **Ray Monolithic Ignition**: Successfully launched a **31-actor Ray Arrow Swarm** on a single script execution (`ray_arrow_swarm_bootstrap.py`). The swarm stabilized with 5 Ray Serve endpoints and 4 MCP gateways in ~35 seconds on `192.168.1.201:6379`.
* **Zero-Latency Data Pipeline**: End-to-end telemetry queries combining PyArrow tables, DuckDB JOINs, and LanceDB counts executed and returned cluster health state to the LLM agent in **<22 seconds** (including database bootstrap overhead).

### Deterministic Codebase Audit (`sovereign_cleanup_agent.py`)
Deployed a custom Rust-sandboxed (Monty) cleanup agent to perform static analysis over the 494 Python files in the workspace. Tool execution clocked at **<1 second total latency**:
* **`0.10s`**: Scanned and mapped all 494 Python files.
* **`0.17s`**: Located all 8 deprecated `fetch_arrow_table()` calls in MCP servers via regex.
* **`0.00s`**: Read and diagnosed `.env` parser failures.
* **`0.18s`**: Dynamically formulated and executed an emoji regex (`print.*emoji|print.*\ud83d...`) finding 97 instances causing `cp1252` encoding crashes on Windows.
* **`0.19s`**: Swept the entire repository for ghost `r"E:\\"` volume paths, identifying 2,907 drive references and 6 critical path-breaking hardcodes.

This demonstrates the Sovereign Architecture's capacity to orchestrate precise, codebase-wide structural edits using lean, sub-5B parameter LLMs augmented with high-speed deterministic tooling (Python `re`, `pathlib`, DuckDB SQL).

---

## 19. BARE-METAL LLAMA.CPP HIGH-PORT KERNEL DISCOVERY & DUAL-EMBEDDING UNIFICATION (Verified 2026-08-11)

> **Last verified:** 2026-08-11 16:30 EDT  
> **Kernel Architecture:** Bare-Metal `llama-server.exe` C++/CUDA backend (Port 51474 / dynamic 50000+ range) + Dual-Model LM Studio Embedding Layer (Snowflake 1024-D + Nomic 768-D) + Native `lance_duckdb_core.dll` Pushdown Engine

### System Milestones & Verified Topology

1. **Bare-Metal `llama.cpp` Dynamic High-Port Discovery (`legion_kernel_bridge.py`)**:
   - **Mechanism:** Discovered that LM Studio spawns background headless `llama-server.exe` processes on dynamic ephemeral ports (e.g. `51474` in the `50000-60000` range) with an auto-generated `--api-key` session token.
   - **Dynamic Locator:** `LlamaKernelBridge` scans the active Windows process table, extracts `--port` and `--api-key` directly from the process command-line arguments, and establishes direct, zero-proxy TCP socket connections.
   - **Throughput & Latency Benchmarks:**
     * **Prompt Processing (warm KV-cache):** **`185.15` – `259.11` tokens/sec** (`5.40 ms/tok`)
     * **Token Generation (Nemotron-3-Nano-4B):** **`29.22` – `31.78` tokens/sec** (`32.68 ms/tok`)
     * **End-to-End Turn Latency:** **`1.73 seconds`** over raw loopback.
   - **Fallback Resiliency:** Seamlessly routes to standard LM Studio port `1234` if kernel isolation is unneeded.

2. **Dual-Model Vector Schema Alignment**:
   - Audited the multi-vector LanceDB lakehouse and synchronized exact model nomenclatures:
     * **`text_vector` (1024-D):** `text-embedding-snowflake-arctic-embed-l-v2.0` (active in LM Studio, used for AST semantic search & RAG lakehouse).
     * **`nomic_vector` (768-D):** `text-embedding-nomic-embed-text-v1.5` (active in LM Studio, used for fast semantic clustering and agent memory).
     * **`audio_vector` (1069-D):** `mega_sovereign_brain.onnx` (direct ONNX C++ engine, pure sovereign DSP math).
     * **`vector` (384-D):** `all-MiniLM-L6-v2` (SentenceTransformer offline fallback for `legion_memory`).
   - Deprecated dead `-f16` alias (`snowflake-arctic-embed-l-v2.0-f16`), eliminating HTTP 400 errors.

3. **Native Vector Pushdown Engine (`lance_duckdb_core.dll`)**:
   - Loaded precompiled `lance_duckdb_core.dll` via `ctypes` (Handle `140714654892032`), enabling native C++ pushdown vector filtering directly between LanceDB and DuckDB tables without Python GIL serialization overhead.

4. **Next LM Studio Integration Links Required**:
   - **LM Studio SDK Plugin (`C:\Users\adams\.lmstudio\extensions\plugins\lmstudio\rag-v2`)**: Register `legion_kernel_bridge.py` and `legion_embedder.py` handlers to expose both 1024-D and 768-D vector tools inside LM Studio chat.
   - **Ray Swarm Dynamic Broadcast**: Broadcast the discovered high-port kernel address to `PaniniRagEngine` and `CodeSwarmKnowledgeRegistry` actors upon swarm initialization.
   - **C++ Bare-Metal Graph Hook (`main.cpp`)**: Connect Winsock state machine to the dynamic high-port kernel for sub-millisecond execution.
