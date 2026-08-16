
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

"""
Ask Gemini: Grounded Job Finder Actor Codegen
=============================================

This script uses the same explicit upload style as the working Antigravity codegen script.

It uploads:
1. the generated source pack if present
2. real local source files if present
3. RAG exports if present
4. the strict job-finder prompt

It is designed to prevent Gemini/Gemma from hallucinating missing sources.

Run:
cd "C:\\WEB CASE STUDY"
.venv\\Scripts\\python.exe ask_gemini_job_finder_grounded.py
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# =============================================================================
# Gemini API setup
# =============================================================================

load_dotenv()
client = genai.Client()

contents_to_send = []


# =============================================================================
# Paths
# =============================================================================

PROJECT_ROOT = r"C:\WEB CASE STUDY"

SOURCE_PACK = r"C:\WEB CASE STUDY\job_finder_gemini_source_pack.md"

CURRENT_SESSION_CHAT = r"C:\WEB CASE STUDY\current_session_chat.md"
AI_MODE = r"C:\WEB CASE STUDY\AI_MODE.md"

MCP_RAG_SERVER = r"C:\WEB CASE STUDY\mcp_rag_server.py"
WHAT_WE_GOT = r"C:\WEB CASE STUDY\WHAT-WE-GOT.txt"
AUDIO_APP_CREATION = r"C:\WEB CASE STUDY\Audio App Creation.txt"
LANGGRAPH_ONNX_AGENT = r"C:\WEB CASE STUDY\langgraph_onnx_agent.py"
RUN_PRO_TRAINING = r"C:\WEB CASE STUDY\run_pro_training.py"

# Existing project source references. These may or may not exist.
DYNAMIC_SEGMENT_MASTER = r"C:\WEB CASE STUDY\dynamic_segment_master.py"
WEAPONIZE = r"C:\WEB CASE STUDY\weaponize.py"
CRAWL_AND_VECTORIZE_ALL_RAY = r"C:\WEB CASE STUDY\crawl_and_vectorize_all_ray.py"
DOWNLOADS_PREMASTER_AUDIT = r"C:\WEB CASE STUDY\downloads_premaster_audit.py"
MARKETING_SCORER = r"C:\WEB CASE STUDY\marketing_scorer.py"
ADAM_QUERY_RAG = r"C:\WEB CASE STUDY\ADAMSCARMCCOY_QUERY_RAG.PY"

# RAG exports that actually prove correct DB paths / Ray / DSP / scraper context.
RAG_SCRAPER_MD = r"C:\WEB CASE STUDY\rag_export_20260703_015501_scraper_website_website_actor.md"
RAG_SCRAPER_JSON = r"C:\WEB CASE STUDY\rag_export_20260703_015501_scraper_website_website_actor.json"
RAG_SCRAPER_TXT = r"C:\WEB CASE STUDY\rag_export_20260703_015501_scraper_website_website_actor.txt"

RAG_RAY_MD = r"C:\WEB CASE STUDY\rag_export_20260702_234726_ray_actors_ray_get_actor_namespace_legion.md"
RAG_RAY_JSON = r"C:\WEB CASE STUDY\rag_export_20260702_234726_ray_actors_ray_get_actor_namespace_legion.json"
RAG_RAY_TXT = r"C:\WEB CASE STUDY\rag_export_20260702_234726_ray_actors_ray_get_actor_namespace_legion.txt"

RAG_ACOUSTIC_MD = r"C:\WEB CASE STUDY\rag_export_20260702_233228_acousticdnaengine_pedalboard_spectral_centroid_crest_factor.md"
RAG_SONIC_MD = r"C:\WEB CASE STUDY\rag_export_20260702_233619_sonic_dna_dsp_cols_transient_density_chroma_semantic_dim_latent_dim_omni_vector_.md"
RAG_SOUNDDEVICE_MD = r"C:\WEB CASE STUDY\rag_export_20260702_233646_sounddevice_stream_channels_2_callback_pyqt_distortion_fuzz_warp_blackhole.md"

SPEED_REPORT = r"C:\WEB CASE STUDY\Snoop_Stylizer_App\training_audio\ray_beast_speed_report.md"


# =============================================================================
# Explicit upload helper, same behavior as your working script but less repetitive
# =============================================================================

def upload_text_file(path: str, display_name: str, label: str):
    if os.path.exists(path):
        print(f"Uploading {label}: {os.path.basename(path)}")
        print(f"  path: {path}")

        uploaded = client.files.upload(
            file=path,
            config=types.UploadFileConfig(
                mime_type="text/plain",
                display_name=display_name,
            ),
        )

        contents_to_send.append(uploaded)
        return True

    print(f"⚠️ Missing {label}: {path}")
    return False


# =============================================================================
# Upload sources using explicit visible blocks
# =============================================================================

print("\n" + "=" * 80)
print("Uploading grounded sources")
print("=" * 80)

# 1. Upload generated source pack first, if you created it.
upload_text_file(
    SOURCE_PACK,
    "job_finder_gemini_source_pack.md",
    "grounded source pack",
)

# 2. Upload current chat/session context.
upload_text_file(
    CURRENT_SESSION_CHAT,
    "current_session_chat.md",
    "current session chat",
)

# 3. Upload AI mode.
upload_text_file(
    AI_MODE,
    "AI_MODE.md",
    "AI_MODE",
)

# 4. Upload existing MCP server.
upload_text_file(
    MCP_RAG_SERVER,
    "mcp_rag_server.py",
    "existing MCP RAG server",
)

# 5. Upload RAG usage notes.
upload_text_file(
    WHAT_WE_GOT,
    "WHAT-WE-GOT.txt",
    "RAG usage/output notes",
)

# 6. Upload original master reference exactly like your old script.
original_master_script = DYNAMIC_SEGMENT_MASTER
if os.path.exists(original_master_script):
    print(f"Uploading original master reference: {os.path.basename(original_master_script)}...")
    py_ref = client.files.upload(
        file=original_master_script,
        config=types.UploadFileConfig(
            mime_type="text/plain",
            display_name="dynamic_segment_master.py",
        ),
    )
    contents_to_send.append(py_ref)
else:
    print(f"⚠️ Missing original master reference: {original_master_script}")

# 7. Upload job-finder-adjacent source files if they exist.
upload_text_file(
    WEAPONIZE,
    "weaponize.py",
    "weaponize orchestrator source",
)

upload_text_file(
    CRAWL_AND_VECTORIZE_ALL_RAY,
    "crawl_and_vectorize_all_ray.py",
    "crawler/vectorizer source",
)

upload_text_file(
    DOWNLOADS_PREMASTER_AUDIT,
    "downloads_premaster_audit.py",
    "download/audit source",
)

upload_text_file(
    MARKETING_SCORER,
    "marketing_scorer.py",
    "marketing scorer source",
)

upload_text_file(
    ADAM_QUERY_RAG,
    "ADAMSCARMCCOY_QUERY_RAG.PY",
    "local RAG query tool",
)

# 8. Upload agent/model source references.
upload_text_file(
    LANGGRAPH_ONNX_AGENT,
    "langgraph_onnx_agent.py",
    "LangGraph ONNX agent source",
)

upload_text_file(
    RUN_PRO_TRAINING,
    "run_pro_training.py",
    "training pipeline source",
)

upload_text_file(
    AUDIO_APP_CREATION,
    "Audio App Creation.txt",
    "audio app/product notes",
)

# 9. Upload scraper RAG exports if present.
upload_text_file(
    RAG_SCRAPER_MD,
    "rag_export_scraper_website_actor.md",
    "scraper RAG markdown export",
)

upload_text_file(
    RAG_SCRAPER_JSON,
    "rag_export_scraper_website_actor.json",
    "scraper RAG JSON export",
)

upload_text_file(
    RAG_SCRAPER_TXT,
    "rag_export_scraper_website_actor.txt",
    "scraper RAG text export",
)

# 10. Upload Ray RAG exports.
upload_text_file(
    RAG_RAY_MD,
    "rag_export_ray_actors_namespace_legion.md",
    "Ray actors markdown export",
)

upload_text_file(
    RAG_RAY_JSON,
    "rag_export_ray_actors_namespace_legion.json",
    "Ray actors JSON export",
)

upload_text_file(
    RAG_RAY_TXT,
    "rag_export_ray_actors_namespace_legion.txt",
    "Ray actors text export",
)

# 11. Upload DSP/audio proof references.
upload_text_file(
    RAG_ACOUSTIC_MD,
    "rag_export_acousticdna_pedalboard.md",
    "AcousticDNA / Pedalboard RAG export",
)

upload_text_file(
    RAG_SONIC_MD,
    "rag_export_sonic_dna_models.md",
    "Sonic DNA model RAG export",
)

upload_text_file(
    RAG_SOUNDDEVICE_MD,
    "rag_export_sounddevice_audio.md",
    "sounddevice realtime audio RAG export",
)

upload_text_file(
    SPEED_REPORT,
    "ray_beast_speed_report.md",
    "Ray speed proof report",
)


# =============================================================================
# Upload sanity check
# =============================================================================

print("\n" + "=" * 80)
print(f"Uploaded source count: {len(contents_to_send)}")
print("=" * 80)

if len(contents_to_send) < 3:
    print(
        "\n⚠️ WARNING: Very few sources uploaded. Gemini will probably hallucinate.\n"
        "Fix missing paths before trusting output.\n"
    )


# =============================================================================
# Prompt
# =============================================================================

prompt = """
You are building a REAL local-first independent contract/work finder for Adam's existing system.

Use the uploaded files as the source of truth.

Critical source behavior:
- If a source file is uploaded, inspect it and use it.
- If a referenced source is missing, say it is missing.
- Do not invent code from missing files.
- Do not fabricate behavior.
- Do not use mock data.
- Do not use example.com.
- Do not use placeholder rows.
- Do not create fake leads.
- Do not fabricate CSV rows.
- Do not claim tests passed unless proof files are written.
- If zero leads are found, export empty proof files with headers and write the failure reason.

This is not a full-time job search tool.
This is not a cloud SaaS.
This is not a DJ mastering website.
This is not a generic AI agency site.

Build a local-first independent short-contract lead finder.

Target work:
- MCP API setup
- local RAG over private docs
- website scraping/report pipeline
- Squarespace intake automation
- local AI assistant prototype
- audio batch processing
- ONNX/local inference wrapper
- data cleanup and table export
- private workflow automation
- Ray actor pipeline debugging
- Python automation
- document/search assistant

Reject/penalize:
- full-time
- onsite
- relocation
- unpaid
- internship
- equity only
- generic marketing
- DJ mastering
- music mastering only
- enterprise cloud migration
- AWS-only/cloud-only
- no contact route
- no project detail

Use these exact paths:

PROJECT_ROOT:
C:\\WEB CASE STUDY

Correct LanceDB path:
C:\\STUDIES_BACKUP\\Legion-Jacked-Pipeline\\ableton-session-intelligence\\lancedb_web_intel_rag

Do NOT use this as primary:
E:\\WEB CASE STUDY\\Legion-Jacked-Pipeline\\ableton-session-intelligence\\lancedb_web_intel_rag

Existing known tables:
- chris_lake_speed_test
- chris_lake_web_intel
- mined_code_vectors
- mined_documentation_vectors

New tables to create:
- independent_work_leads
- independent_work_runs

Export directory:
C:\\WEB CASE STUDY\\work_finder_exports

Required output files:
1. C:\\WEB CASE STUDY\\work_lead_schemas.py
2. C:\\WEB CASE STUDY\\work_lead_tables.py
3. C:\\WEB CASE STUDY\\indie_work_finder_actor.py
4. C:\\WEB CASE STUDY\\work_finder_mcp_server.py
5. C:\\WEB CASE STUDY\\run_work_finder_test.py
6. C:\\WEB CASE STUDY\\WORK_FINDER_README.md

Required proof exports after run_work_finder_test.py:
1. C:\\WEB CASE STUDY\\work_finder_exports\\work_leads_latest.csv
2. C:\\WEB CASE STUDY\\work_finder_exports\\work_leads_latest.md
3. C:\\WEB CASE STUDY\\work_finder_exports\\work_leads_latest.json
4. C:\\WEB CASE STUDY\\work_finder_exports\\work_finder_run_summary.md

Required Pydantic v2 schemas:
- WorkSourceType
- ProjectType
- LeadStatus
- BudgetSignal
- ContactRoute
- WorkLeadRaw
- WorkLeadClean
- WorkLeadScore
- WorkLeadRecord
- WorkLeadRunSummary
- WorkLeadExportManifest

WorkLeadRecord required fields:
- lead_id: str
- source: WorkSourceType
- title: str
- company_or_person: str | None
- url: str
- source_url: str | None
- contact_url: str | None
- contact_email: str | None
- remote: bool
- contract: bool
- full_time: bool
- short_project: bool
- project_type: ProjectType
- budget_signal: BudgetSignal
- fit_score: float 0-100
- urgency_score: float 0-100
- contact_score: float 0-100
- contract_score: float 0-100
- rejection_score: float 0-100
- final_score: float 0-100
- why_fit: str
- outreach_angle: str
- evidence_text: str
- matched_keywords: list[str]
- rejection_reasons: list[str]
- status: LeadStatus
- created_at: datetime
- updated_at: datetime

Scoring formula:
final_score =
  0.40 * fit_score
+ 0.25 * contact_score
+ 0.20 * urgency_score
+ 0.15 * contract_score
- 0.50 * rejection_score

Clamp final_score to 0-100.

Implementation rules:
- Python 3.11+
- Pydantic v2
- Ray actors
- LanceDB
- pandas
- BeautifulSoup
- requests or urllib
- FastMCP for MCP server
- explicit empty schemas, not fake records
- no placeholder rows
- no example.com
- no mock data
- no TODO-only functions
- no "..." placeholders

Generate the complete files in separate fenced code blocks.
Include exact run commands.
Include troubleshooting.
Include a final checklist proving:
- no mock data
- no example.com
- no placeholder rows
- Pydantic schemas included
- Ray actor included
- LanceDB tables included
- MCP tools included
- CSV/MD/JSON proof exports included
"""

contents_to_send.append(prompt)


# =============================================================================
# Run Gemini
# =============================================================================

print("\nInitializing stateful chat session (model: gemini-2.5-flash)...")
chat = client.chats.create(model="gemini-2.5-flash")

base_out_file = r"C:\WEB CASE STUDY\gemini_job_finder_grounded_output.md"
out_file = base_out_file

if os.path.exists(out_file):
    base, ext = os.path.splitext(base_out_file)
    i = 1
    while os.path.exists(f"{base}_{i}{ext}"):
        i += 1
    out_file = f"{base}_{i}{ext}"

print(f"Streaming Gemini response to: {out_file}")
print("=" * 80)

with open(out_file, "w", encoding="utf-8") as out:
    try:
        response = chat.send_message_stream(contents_to_send)
        for chunk in response:
            text = chunk.text or ""
            print(text, end="", flush=True)
            out.write(text)
    except Exception as e:
        msg = f"\n\n[ERROR] Gemini request failed: {type(e).__name__}: {e}\n"
        print(msg)
        out.write(msg)

print("\n" + "=" * 80)
print(f"Saved Gemini grounded output to: {out_file}")