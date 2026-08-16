import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

# Header
cells.append(nbf.v4.new_markdown_cell("# JULES TEAM Environment & Core Capabilities\nThis notebook sets up the environment, clones the Jules repository, vectorizes it using Ollama and LanceDB, and provides a Pydantic-backed modular representation for all team skills. Each skill has configurable parameters at the top of its cell."))

# Cell 0: Setup and data ingestion
cell0_code = """\
# Setup and Data Ingestion
import os
import subprocess
import sys
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# 1. Install necessary dependencies in the environment
def install_packages():
    packages = ["pydantic", "lancedb", "pyarrow", "pandas", "ollama"]
    print("Checking and installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q"] + packages)
    print("Packages installed successfully.")

install_packages()

import lancedb
import pyarrow as pa
import pandas as pd
import ollama

# 2. Check if the repo has been copied, if not copy it
REPO_URL = "https://github.com/jonathanmalkin/jules.git"
REPO_DIR = "jules_repo"

if not os.path.exists(REPO_DIR):
    print(f"Cloning repo from {REPO_URL} into {REPO_DIR}...")
    subprocess.check_call(["git", "clone", REPO_URL, REPO_DIR])
else:
    print(f"Repo already exists at {REPO_DIR}.")

# 3. Vectorize it using ollama snowflake into skills/code clusters/parquet and lancedb
EMBEDDING_MODEL = "snowflake-arctic-embed:latest"
PARQUET_OUTPUT_DIR = "skills/code clusters/parquet"
PARQUET_FILE_NAME = "repo_vectors.parquet"
LANCEDB_PATH = "skills/code clusters/lancedb"

print(f"Pulling {EMBEDDING_MODEL} via Ollama...")
try:
    ollama.pull(EMBEDDING_MODEL)
except Exception as e:
    print(f"Error pulling model (make sure Ollama is running): {e}")

documents = []
for root, _, files in os.walk(REPO_DIR):
    for file in files:
        if file.endswith(".md"):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    documents.append({"filepath": filepath, "content": content})
            except Exception:
                pass

vectorized_data = []
for doc in documents:
    try:
        response = ollama.embeddings(model=EMBEDDING_MODEL, prompt=doc["content"])
        embedding = response["embedding"]
        vectorized_data.append({
            "filepath": doc["filepath"],
            "content": doc["content"][:1000],
            "vector": embedding
        })
    except Exception as e:
        print(f"Failed to embed {doc['filepath']}: {e}")

if vectorized_data:
    df = pd.DataFrame(vectorized_data)
    
    os.makedirs(PARQUET_OUTPUT_DIR, exist_ok=True)
    parquet_path = os.path.join(PARQUET_OUTPUT_DIR, PARQUET_FILE_NAME)
    df.to_parquet(parquet_path)
    print(f"Saved Parquet file to {parquet_path}")
    
    os.makedirs(LANCEDB_PATH, exist_ok=True)
    db = lancedb.connect(LANCEDB_PATH)
    
    if "jules_repo" in db.table_names():
        db.drop_table("jules_repo")
        
    table = db.create_table("jules_repo", data=df)
    print(f"Saved to LanceDB table 'jules_repo' at {LANCEDB_PATH}")
else:
    print("No data vectorized.")
"""
cells.append(nbf.v4.new_code_cell(cell0_code))

# List of skills
skills = [
    {
        "name": "think",
        "desc": "Recursive decomposition + advisory. Altitude system for goals, adversarial review for decisions.",
        "config": 'THINK_OUTPUT_LOG_PATH = "logs/think_decisions.log"',
        "model": """class ThinkRequest(BaseModel):
    goal: str = Field(..., description="The main objective to decompose.")
    context: Optional[str] = Field(None, description="Advisory context.")""",
        "func": """def run_think(req: ThinkRequest):
    print(f"[Think Skill] Analyzing goal: {req.goal}")
    print(f"Writing think logs to: {THINK_OUTPUT_LOG_PATH}")
    return {"status": "success", "altitude": "high", "review": "Adversarial review complete."}"""
    },
    {
        "name": "build",
        "desc": "Software dev end-to-end: scope, plan, execute, deploy.",
        "config": 'BUILD_WORKSPACE_DIR = "workspace/builds"\nBUILD_DEPLOY_ENDPOINT = "http://localhost:8080/deploy"',
        "model": """class BuildRequest(BaseModel):
    scope: str = Field(..., description="Scope of the software to build.")
    plan: List[str] = Field(..., description="Steps to execute.")""",
        "func": """def run_build(req: BuildRequest):
    print(f"[Build Skill] Building scope: {req.scope} with {len(req.plan)} steps.")
    print(f"Workspace: {BUILD_WORKSPACE_DIR}, Deploying to: {BUILD_DEPLOY_ENDPOINT}")
    return {"status": "success", "deployment": "pending"}"""
    },
    {
        "name": "write",
        "desc": "Content production: seed to platform-ready output across all channels.",
        "config": 'WRITE_OUTPUT_DIR = "content/drafts"\nWRITE_PLATFORM_API = "https://api.example.com/publish"',
        "model": """class WriteRequest(BaseModel):
    topic: str = Field(..., description="Topic of the content.")
    platform: str = Field(..., description="Target platform (e.g., blog, X).")""",
        "func": """def run_write(req: WriteRequest):
    print(f"[Write Skill] Producing content for {req.platform} on topic: {req.topic}")
    print(f"Saving to: {WRITE_OUTPUT_DIR}, API: {WRITE_PLATFORM_API}")
    return {"status": "success", "output": f"Content for {req.topic}"}"""
    },
    {
        "name": "research",
        "desc": "Standalone research with persistence and cross-session pickup. Living documents.",
        "config": 'RESEARCH_STORAGE_DIR = "research/living_docs"',
        "model": """class ResearchRequest(BaseModel):
    query: str = Field(..., description="Research query.")
    persistence_id: Optional[str] = Field(None, description="ID for cross-session pickup.")""",
        "func": """def run_research(req: ResearchRequest):
    print(f"[Research Skill] Researching: {req.query}")
    print(f"Saving living documents to: {RESEARCH_STORAGE_DIR}")
    return {"status": "success", "findings": []}"""
    },
    {
        "name": "debug",
        "desc": "Systematic debugging: hypothesize, test, narrow.",
        "config": 'DEBUG_LOGS_DIR = "logs/crash_reports"\nDEBUG_TOOLS_BIN = "/usr/local/bin/debugger"',
        "model": """class DebugRequest(BaseModel):
    issue_description: str = Field(..., description="Description of the bug.")
    logs: Optional[str] = Field(None, description="Relevant error logs.")""",
        "func": """def run_debug(req: DebugRequest):
    print(f"[Debug Skill] Debugging issue: {req.issue_description}")
    print(f"Reading logs from: {DEBUG_LOGS_DIR}")
    return {"status": "success", "hypothesis": "Test required"}"""
    },
    {
        "name": "reply-x",
        "desc": "Check X mentions, draft replies, post approved ones. Multi-account support.",
        "config": 'X_API_ENDPOINT = "https://api.twitter.com/2/tweets"\nX_DRAFTS_PATH = "social/x_drafts.json"',
        "model": """class ReplyXRequest(BaseModel):
    mentions: List[str] = Field(..., description="List of X mentions to check.")
    draft_replies: bool = Field(True, description="Whether to draft replies automatically.")""",
        "func": """def run_reply_x(req: ReplyXRequest):
    print(f"[Reply-X Skill] Checking {len(req.mentions)} mentions.")
    print(f"API Endpoint: {X_API_ENDPOINT}, Drafts: {X_DRAFTS_PATH}")
    return {"status": "success"}"""
    },
    {
        "name": "good-morning",
        "desc": "Interactive walkthrough of the morning briefing (10 sections).",
        "config": 'BRIEFING_INPUT_FILE = "briefings/morning_briefing.md"\nBRIEFING_SOURCES_DIR = "data/sources"',
        "model": """class GoodMorningRequest(BaseModel):
    include_sections: int = Field(10, description="Number of briefing sections to include.")""",
        "func": """def run_good_morning(req: GoodMorningRequest):
    print(f"[Good-Morning Skill] Briefing with {req.include_sections} sections.")
    print(f"Reading briefing from: {BRIEFING_INPUT_FILE}")
    return {"status": "success"}"""
    },
    {
        "name": "wrap-up",
        "desc": "End-of-session: issue capture, report, ship. 3 phases.",
        "config": 'WRAPUP_REPORT_DIR = "reports/end_of_session"\nWRAPUP_ARCHIVE_URL = "https://internal.tools/archive"',
        "model": """class WrapUpRequest(BaseModel):
    phases_completed: int = Field(3, description="Number of end-of-session phases.")
    report_output: str = Field(..., description="Destination for the wrap-up report.")""",
        "func": """def run_wrap_up(req: WrapUpRequest):
    print(f"[Wrap-Up Skill] Wrapping up session. Report: {req.report_output}")
    print(f"Saving to: {WRAPUP_REPORT_DIR}, Archiving at: {WRAPUP_ARCHIVE_URL}")
    return {"status": "success"}"""
    },
    {
        "name": "watch-contacts",
        "desc": "Monitor contacts' X posts, surface engagement opportunities.",
        "config": 'CONTACTS_LIST_PATH = "data/contacts.csv"\nWATCH_POLL_INTERVAL = 600',
        "model": """class WatchContactsRequest(BaseModel):
    contacts: List[str] = Field(..., description="List of contacts to monitor on X.")""",
        "func": """def run_watch_contacts(req: WatchContactsRequest):
    print(f"[Watch-Contacts Skill] Monitoring {len(req.contacts)} contacts.")
    print(f"Loading from: {CONTACTS_LIST_PATH}")
    return {"status": "success"}"""
    },
    {
        "name": "simplify-jules",
        "desc": "On-demand config hygiene — analyzes cold-start bundle for waste and duplication.",
        "config": 'JULES_BUNDLE_DIR = "config/bundles"\nHYGIENE_REPORT_PATH = "logs/hygiene_report.txt"',
        "model": """class SimplifyJulesRequest(BaseModel):
    bundle_path: str = Field(..., description="Path to the cold-start bundle.")""",
        "func": """def run_simplify_jules(req: SimplifyJulesRequest):
    print(f"[Simplify-Jules Skill] Auditing bundle at {req.bundle_path}")
    print(f"Default bundle dir: {JULES_BUNDLE_DIR}, Report: {HYGIENE_REPORT_PATH}")
    return {"status": "success"}"""
    },
    {
        "name": "stop-slop",
        "desc": "Structural audit for AI writing patterns.",
        "config": 'SLOP_DICTIONARY_PATH = "config/slop_words.json"\nSLOP_AUDIT_LOG_DIR = "logs/audits"',
        "model": """class StopSlopRequest(BaseModel):
    content_to_audit: str = Field(..., description="Content to audit for AI writing patterns.")""",
        "func": """def run_stop_slop(req: StopSlopRequest):
    print("[Stop-Slop Skill] Auditing content for AI patterns.")
    print(f"Using dictionary at: {SLOP_DICTIONARY_PATH}")
    return {"status": "success", "slop_detected": False}"""
    },
    {
        "name": "pdf",
        "desc": "PDF operations.",
        "config": 'PDF_WORKSPACE_DIR = "workspace/pdfs"\nPDF_EXTRACTOR_BIN = "/usr/bin/pdftotext"',
        "model": """class PdfRequest(BaseModel):
    pdf_path: str = Field(..., description="Path to the PDF file.")
    operation: str = Field(..., description="Operation to perform (e.g., extract text).")""",
        "func": """def run_pdf(req: PdfRequest):
    print(f"[PDF Skill] Performing {req.operation} on {req.pdf_path}")
    print(f"Workspace: {PDF_WORKSPACE_DIR}, Tool: {PDF_EXTRACTOR_BIN}")
    return {"status": "success"}"""
    },
    {
        "name": "plane",
        "desc": "Plane.so interface: MCP tools + gap scripts + reconciliation.",
        "config": 'PLANE_API_URL = "https://api.plane.so/v1"\nPLANE_API_KEY_ENV = "PLANE_API_KEY"',
        "model": """class PlaneRequest(BaseModel):
    action: str = Field(..., description="Plane.so interface action.")""",
        "func": """def run_plane(req: PlaneRequest):
    print(f"[Plane Skill] Executing action: {req.action}")
    print(f"Using Plane API: {PLANE_API_URL}")
    return {"status": "success"}"""
    },
    {
        "name": "send-email",
        "desc": "Send email via Resend.",
        "config": 'RESEND_API_URL = "https://api.resend.com/emails"\nRESEND_API_KEY_ENV = "RESEND_API_KEY"',
        "model": """class SendEmailRequest(BaseModel):
    to_address: str = Field(..., description="Recipient email address.")
    subject: str = Field(..., description="Email subject.")
    body: str = Field(..., description="Email body content.")""",
        "func": """def run_send_email(req: SendEmailRequest):
    print(f"[Send-Email Skill] Sending email to {req.to_address}")
    print(f"Using Resend API: {RESEND_API_URL}")
    return {"status": "success"}"""
    },
    {
        "name": "financial-advisor",
        "desc": "Personal finance planning.",
        "config": 'FINANCE_DATA_DIR = "finance/records"\nFINANCE_CALCULATOR_API = "http://localhost:8081/calc"',
        "model": """class FinancialAdvisorRequest(BaseModel):
    planning_topic: str = Field(..., description="Personal finance planning topic.")""",
        "func": """def run_financial_advisor(req: FinancialAdvisorRequest):
    print(f"[Financial-Advisor Skill] Planning: {req.planning_topic}")
    print(f"Data directory: {FINANCE_DATA_DIR}")
    return {"status": "success"}"""
    },
    {
        "name": "generate-image-openai",
        "desc": "Image generation with iterative two-phase workflow.",
        "config": 'IMAGE_OUTPUT_DIR = "workspace/images"\nOPENAI_IMAGE_API = "https://api.openai.com/v1/images/generations"',
        "model": """class GenerateImageOpenaiRequest(BaseModel):
    prompt: str = Field(..., description="Image generation prompt.")
    iterative_phases: int = Field(2, description="Number of phases for generation workflow.")""",
        "func": """def run_generate_image(req: GenerateImageOpenaiRequest):
    print(f"[Image-Gen Skill] Generating image for prompt: {req.prompt}")
    print(f"Saving images to: {IMAGE_OUTPUT_DIR}")
    return {"status": "success"}"""
    },
    {
        "name": "search-history",
        "desc": "Search session documents.",
        "config": 'HISTORY_DOCS_DIR = "data/history"\nHISTORY_INDEX_PATH = "data/history/index.db"',
        "model": """class SearchHistoryRequest(BaseModel):
    search_term: str = Field(..., description="Term to search in session documents.")""",
        "func": """def run_search_history(req: SearchHistoryRequest):
    print(f"[Search-History Skill] Searching for: {req.search_term}")
    print(f"Searching index at: {HISTORY_INDEX_PATH}")
    return {"status": "success"}"""
    },
    {
        "name": "skill-creator",
        "desc": "Create and modify skills.",
        "config": 'SKILLS_DIR = ".claude/skills"\nSKILL_TEMPLATES_DIR = "config/templates"',
        "model": """class SkillCreatorRequest(BaseModel):
    skill_name: str = Field(..., description="Name of the new skill.")
    modifications: Optional[Dict[str, Any]] = Field(None, description="Modifications to an existing skill.")""",
        "func": """def run_skill_creator(req: SkillCreatorRequest):
    print(f"[Skill-Creator Skill] Working on skill: {req.skill_name}")
    print(f"Modifying skills in: {SKILLS_DIR}")
    return {"status": "success"}"""
    },
    {
        "name": "agent-browser",
        "desc": "Browser automation.",
        "config": 'BROWSER_CDP_URL = "http://localhost:9222"\nBROWSER_SCREENSHOTS_DIR = "workspace/screenshots"',
        "model": """class AgentBrowserRequest(BaseModel):
    url: str = Field(..., description="URL to automate browser actions on.")
    actions: List[str] = Field(..., description="List of browser actions to perform.")""",
        "func": """def run_agent_browser(req: AgentBrowserRequest):
    print(f"[Agent-Browser Skill] Navigating to {req.url}")
    print(f"Connecting to browser at: {BROWSER_CDP_URL}")
    return {"status": "success"}"""
    }
]

for skill in skills:
    markdown_content = f"## {skill['name']}\n**Description:** {skill['desc']}\n\n*Configure the variables in the code block below to match your environment paths/URLs.*"
    cells.append(nbf.v4.new_markdown_cell(markdown_content))
    
    code_content = f"""# Configuration Options for {skill['name']}
{skill['config']}

{skill['model']}

{skill['func']}
"""
    cells.append(nbf.v4.new_code_cell(code_content))

nb['cells'] = cells

with open('JULES_TEAM.ipynb', 'w') as f:
    nbf.write(nb, f)

print("JULES_TEAM.ipynb generated successfully.")
