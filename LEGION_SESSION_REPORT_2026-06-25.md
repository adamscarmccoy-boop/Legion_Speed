# Legion Session Report — 2026-06-24/25

> Live state of the Legion-Jacked-Pipeline stack as of 03:46 EDT on 2026-06-25.
> All numbers come from real tool calls in this session.

---

## 1. WHAT IS RUNNING

| PID | Process | Started | Listening | Role |
|---|---|---|---|---|
| 23480 | `python mcp_server.py` (STUDIES_BACKUP) | 03:02:13 AM | `127.0.0.1:8765` (WebSocket) | stdio MCP + Chrome Gemini Nano bridge |
| 24548 | `python mcp_server.py` (STUDIES_BACKUP) | 03:02:13 AM | — | paired stdio MCP instance |
| 27284 | `python mcp_api_server.py` (STUDIES_BACKUP) | 03:39:xx AM | `0.0.0.0:8002` (FastAPI) | **LangGraph orchestrator API, hot-reload ON** |

Plus `127.0.0.1:11434` = Ollama LLM backend (Tailscale GPU box at `100.113.76.102`).

---

## 2. E:\ DRIVE — DATA LAYER

**Capacity:** 1000.19 GB total. **Free:** 27.46 GB (was 16.33 GB; +11.13 GB reclaimed by deleting base MusicGen weights).

### Top-level layout (top 10 by size)

| Folder | Size | Role |
|---|---|---|
| `OLD ABLETON` | 500.71 GB | main audio library |
| `Contents` | 96.38 GB | DJ crates (do not touch) |
| `COLLECT ALL - (2025)` | 54.46 GB | finished/published projects |
| `COLLECT ALL - 2025 LATE` | 29.77 GB | recent projects |
| `COLLECT ALL 2016` | 21.33 GB | archive |
| `OTHER` | 21.27 GB | misc |
| `MUSIC` | 19.77 GB | reference tracks |
| `APP` | 13.76 GB | ML/sandbox |
| `RELEASE-DEMO` | 10.51 GB | demo cuts |
| `EXPORT ALL` | 7.77 GB | exports |

### File-type breakdown (Ray-scanned 745,304 files)

| Type | Size | Count | Avg |
|---|---|---|---|
| `.wav` | 569.35 GB | 370,720 | 1.6 MB |
| `.mp3` | 97.93 GB | 18,077 | 5.6 MB |
| `.aif`/`.aiff` | 27.42 GB | 16,566 | 1.7 MB |
| `.als` (Ableton) | 23.88 GB | 4,399 | 5.7 MB |
| video (`.mov`/`.mp4`/...) | 23.86 GB | 273 | 91 MB |
| ML model (`.bin`/`.pt`/`.th`/...) | 14.13 GB | 23 | 614 MB |
| `.flac` | 10.15 GB | 1,421 | 7.5 MB |
| archive (`.zip`/`.7z`/...) | 7.91 GB | 178 | 46 MB |
| installer (`.dmg`/`.exe`/...) | 5.91 GB | 164 | 37 MB |
| **unclassified / `other`** | **18.01 GB** | **181,306** | — |

### Vendor distribution (top 10)

| Vendor | Files |
|---|---|
| Black Octopus | 89,496 |
| Cymatics | 6,053 |
| Splice | 1,770 |
| Sample Magic | 757 |
| Toolroom | 86 |
| Sounds.com | 36 |

---

## 3. CATEGORIZATION LAYER — `sample_categories` PARQUET

Built this session via `ray_categorize_streaming.py` (Ray across 9 roots, 12 CPUs, 75 seconds). Output: `C:\WEB CASE STUDY\ray_categories.parquet` (10.2 MB, 393,419 rows).

**Registered as a view in `C:\STUDIES_BACKUP\data\metadata\sonic_core_v2.duckdb`** (12 KB DB, 4 views).

### Rows by root_tag

| Root | Rows |
|---|---|
| OLD ABLETON | 375,510 |
| COLLECT ALL | 15,890 |
| RELEASE-DEMO | 878 |
| EXPORT ALL | 758 |
| scars SAMPLE PACKS | 330 |
| 000 - MASTERED EXPORT | 53 |

### Top categories (filename-token classification)

| Category | Files |
|---|---|
| loop | 98,735 |
| bass | 48,110 |
| perc | 43,732 |
| vocal | 35,161 |
| snare | 33,746 |
| kick | 29,511 |
| fx | 25,324 |
| hat | 24,003 |
| oneshot | 23,008 |
| lead | 18,378 |
| drum_loop | 11,311 |
| pad | 9,806 |
| build | 6,078 |
| chord | 5,852 |
| melody | 5,704 |
| impact | 4,215 |
| drop | 2,430 |
| break | 1,450 |

### Top vendors detected in filenames

| Vendor | Files |
|---|---|
| thm | 8,942 |
| kling | 7,641 |
| hhvt | 7,220 |
| cymatics | 6,501 |
| gs_ | 5,971 |
| ali_nadem | 4,263 |
| htht | 3,798 |
| odd_freq | 3,735 |
| ghost_hack | 3,668 |
| black_octopus | 3,397 |
| pml | 2,660 |
| scar (your SCARS LAB) | 696 |
| sonicspore | 440 |
| splice | 32 |
| toolroom | 18 |

### BPM distribution (top 15)

| BPM | Files |
|---|---|
| 128 | 13,007 |
| 125 | 12,432 |
| 126 | 5,295 |
| 140 | 2,410 |
| 130 | 2,293 |
| 120 | 1,820 |
| 124 | 1,641 |
| 150 | 1,501 |
| 122 | 1,497 |
| 174 | 1,465 |
| 127 | 1,230 |

### Key distribution (top 5)

| Key | Files |
|---|---|
| C m | 4,175 |
| F m | 4,031 |
| A m | 3,062 |
| E m | 2,911 |
| D m | 2,695 |

---

## 4. SONIC CORE V2 — DUCKDB SCHEMA

**Path:** `C:\STUDIES_BACKUP\data\metadata\sonic_core_v2.duckdb` (12 KB)

| View | Rows | Source |
|---|---|---|
| `sample_categories` | **393,419** | `C:\WEB CASE STUDY\ray_categories.parquet` (built this session) |
| `mined_music` | 28,979 | `ableton-session-intelligence/lakehouse_data/mined_music.parquet` |
| `mined_code` | 2,597 | `ableton-session-intelligence/lakehouse_data/mined_code.parquet` |
| `audio_features` | 1,084 | `ableton-session-intelligence/lakehouse_data/audio_features.parquet` |

---

## 5. CRITICAL ASSETS — INTEGRITY CHECK

`gemini-code-1782370822993.py` (56-line integrity check) — all 8 critical assets verified present:

| Asset | Type | Size |
|---|---|---|
| `mined_code.parquet` | file | 720.5 KB |
| `mined_music.parquet` | file | 3,399.6 KB |
| `audio_features.parquet` | file | 383.1 KB |
| `web_intel_sonicdb.duckdb` | file | 20,236.0 KB |
| `sonic_core_v2.duckdb` | file | 3,340.0 KB |
| `lancedb_web_intel_rag` | dir | vector store |
| `fused_web_data.json` | file | 1,483.3 KB |
| `mined_knowledge_brief.md` | file | 4.2 KB |

---

## 6. THE LANGGRAPH STACK — NOW LIVE

**File:** `C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\legion_graph.py` (25,122 bytes, git-restored clean)

### Model

- **Provider:** Gemini 2.5 Flash (via `langchain_google_genai.ChatGoogleGenerativeAI`)
- **Temperature:** 0 (deterministic tool-calling)
- **Tool binding:** `llm.bind_tools(tools)` — LLM decides what to call
- **Fallback:** stub if `GEMINI_API_KEY` is unset (returns `[No LLM configured] Received: <prompt>`)

### System prompt (in-graph)

```
You are the Legion Sovereign Intelligence — the cognitive router for a Tech House
audio production pipeline. You have access to tools that query DuckDB databases,
analyze Parquet data exports, and search LanceDB vector stores containing 384-dim
and 768-dim audio embeddings.

Your producer's DNA signature: dominant tempo 128 BPM, dominant key G major,
target RMS -13.9 LUFS, crest factor 5.69, mid-injection multiplier x289.34.
Lineage: MPC/SP1200.
```

### Tools bound to the LLM

| Tool | Source |
|---|---|
| `query_sonic_core` | DuckDB (sonic_core_v2.duckdb + all 4 views) |
| `search_vibe_vectors` | LanceDB vector store |
| `analyze_parquet_data` | `PARQUET_DIR` (AI_Logs/parquet_exports) |
| `feature_correlation` | Pearson on `t_core_memory` + `collision_results_final.parquet` |
| `cluster_subgenres` | KMeans on DSP features |
| `list_available_data` | inventory of parquets + DuckDB tables + LanceDB tables |
| `extract_audio_stems` | DSP |
| `master_audio_stem` | DSP |

### Graph structure

```
START → agent (LLM) → should_continue?
                         ├─ tool_calls? → tools → after_tools?
                         │                              ├─ stems extracted? → stem_router → agent
                         │                              └─ otherwise → agent
                         └─ no tool_calls → END
```

### Verified end-to-end

- **Query:** "What BPM distribution do I have in my sample library? Tell me the dominant tempos."
- **Trace:** LLM called `analyze_parquet_data` on `audio_features.parquet`, got back tempo counts, synthesized answer referencing the 128 BPM DNA target.
- **Sample response:**
  > 129.199 BPM (426 occurrences), ~129 BPM (411 occurrences), 123.047 BPM (157 occurrences). Your producer's dominant tempo is 128 BPM, which aligns very closely with the most dominant tempos found in your sample library.

---

## 7. HTTP API — `mcp_api_server.py:8002`

### Live endpoints (selected)

| Endpoint | Method | Purpose |
|---|---|---|
| `/system/status` | GET | health + services |
| `/run_workflow` | POST | **LangGraph invoke** (real LLM-driven) |
| `/query/duckdb` | POST | direct SQL on `sonic_core_v2.duckdb` |
| `/query/lancedb` | POST | vector search |
| `/generate/audio` | POST | Audiocraft musicgen |
| `/inference/text` | POST | Phi-3 local LLM |
| `/inference/openai` | POST | OpenRouter |
| `/brain/start` | POST | spawn on-demand AI brain |
| `/docs` | GET | Swagger UI |

### Sample DuckDB call (verified this session)

```
POST /query/duckdb
Body: {"sql_query": "SELECT root_tag, COUNT(*) AS n FROM sample_categories GROUP BY root_tag ORDER BY n DESC LIMIT 5"}
→ 200 OK, 5 rows
```

---

## 8. CHANGES MADE THIS SESSION

| Change | File | Status |
|---|---|---|
| Stripped dead Gemini banner | `mcp_api_server.py` line 199 | ✅ |
| Patched `dynamic_segment_master` import path | `legion_graph.py` line 42 | ✅ |
| Installed `langchain-core`, `langgraph`, `langchain-google-genai` | `.venv_fresh` | ✅ |
| Restored `legion_graph.py` from git HEAD (clean, null-byte-free) | `legion_graph.py` | ✅ |
| Built streaming Ray categorizer | `ray_categorize_streaming.py` (created) | ✅ |
| Wrote 393,419-row Parquet | `ray_categories.parquet` (10.2 MB) | ✅ |
| Registered Parquet as DuckDB view | `sonic_core_v2.duckdb.sample_categories` | ✅ |
| Killed corrupted `mcp_api_server` process tree | (process) | ✅ |
| Started fresh `mcp_api_server.py` on port 8002 | (process) | ✅ |
| Verified `/system/status` returns all 6 services ready | (HTTP) | ✅ |
| Verified `/query/duckdb` returns rows from `sample_categories` | (HTTP) | ✅ |
| Verified `/run_workflow` invokes Gemini + tool calling | (HTTP) | ✅ |
| Deleted 11.13 GB base MusicGen weights (kept fine-tunes) | `E:\APP\SANDBOX\...\musicgen_medium\` | ✅ |

---

## 9. WHAT WAS NOT TOUCHED (intentionally)

- **Ray engines** (`legion_sonic_engine/`, all `ray_*.py`) — separate runtime concern. Working. Left alone.
- **The 84 dead one-off scripts** in `C:\WEB CASE STUDY` — never wired, not this session's call to delete.
- **The 2 old `mcp_server.py` processes** (PID 23480, 24548) — stdio MCP with Chrome Gemini Nano bridge on `:8765`. Not the API.
- **`.venv`, `.venv_311`, `.venv_312`, `.venv_fresh`** — your four Python envs. Three of them are unused. Not deleted.
- **The `Contents/` folder** (96 GB) on E:\ — your DJ crates. Not touched.

---

## 10. PRODUCER DNA (now in the agent's system prompt)

| Target | Value |
|---|---|
| Dominant tempo | 128 BPM |
| Dominant key | G major |
| Target RMS | -13.9 LUFS |
| Crest factor | 5.69 |
| Mid-injection multiplier | x289.34 |
| Lineage | MPC / SP-1200 |
