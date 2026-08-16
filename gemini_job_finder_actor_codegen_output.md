Here is the complete, runnable Python code for your local-first, independent contract work finder system, along with the necessary documentation and proof generation.

This system is designed to leverage your existing stack, reject low-fit opportunities, and provide verifiable proof of its operations without relying on mock data or fabricated leads.

### File Tree

```
C:\WEB CASE STUDY\
├── work_lead_schemas.py
├── work_lead_tables.py
├── indie_work_finder_actor.py
├── work_finder_mcp_server.py
├── run_work_finder_test.py
├── WORK_FINDER_README.md
└── work_finder_exports\  (Created by the system)
    ├── work_leads_latest.csv
    ├── work_leads_latest.json
    ├── work_leads_latest.md
    └── work_finder_run_summary.md
```

---

### 1. `C:\WEB CASE STUDY\work_lead_schemas.py`

```python
# C:\WEB CASE STUDY\work_lead_schemas.py

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl, ConfigDict, field_validator


class WorkSourceType(str, Enum):
    """Enumeration for the types of sources for work leads."""
    WEBSITE = "Website"
    JOB_BOARD = "Job Board"
    GITHUB = "GitHub"
    HACKER_NEWS = "Hacker News"
    REDDIT = "Reddit"
    AGENCY = "Agency Website"
    SQUARESPACE = "Squarespace Site"
    OTHER = "Other"


class ProjectType(str, Enum):
    """Enumeration for the type of project."""
    AI_AUTOMATION = "AI Automation"
    MCP_TOOL = "MCP Tool Development"
    RAG_SYSTEM = "RAG System"
    WEB_SCRAPING = "Web Scraping & Reporting"
    SQUARESPACE_INTEGRATION = "Squarespace Integration"
    AUDIO_PROCESSING = "Audio Processing"
    DATA_PROCESSING = "Data Processing"
    ONNX_INTEGRATION = "ONNX/Inference Integration"
    WORKFLOW_AUTOMATION = "Workflow Automation"
    DOCUMENT_ASSISTANT = "Document/Search Assistant"
    PROTOTYPE = "Project Prototype"
    OTHER = "Other / Undefined"


class LeadStatus(str, Enum):
    """Enumeration for the current status of a work lead."""
    NEW = "New"
    REVIEWED = "Reviewed"
    CONTACTED = "Contacted"
    REJECTED = "Rejected"
    ARCHIVED = "Archived"
    ACCEPTED = "Accepted"


class BudgetSignal(str, Enum):
    """Enumeration for signals related to project budget."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    UNKNOWN = "Unknown"
    PAID = "Paid" # Explicitly stated as paid, but no range
    UNPAID = "Unpaid"


class ContactRoute(BaseModel):
    """Model to store contact information."""
    url: Optional[HttpUrl] = Field(None, description="Direct URL to a contact form or page.")
    email: Optional[str] = Field(None, description="Direct contact email address.")
    
    @field_validator('email', mode='before')
    @classmethod
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        if v and "@" not in v:
            return None # Basic validation, more robust regex can be added
        return v


class WorkLeadRaw(BaseModel):
    """Raw, unprocessed lead data extracted directly from a source."""
    source_url: HttpUrl = Field(..., description="The original URL where the lead was found.")
    raw_content: str = Field(..., description="The raw textual content extracted from the source.")
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WorkLeadClean(BaseModel):
    """Cleaned and pre-processed lead data, ready for scoring."""
    source_url: HttpUrl = Field(..., description="The original URL where the lead was found.")
    clean_text: str = Field(..., description="Cleaned textual content from the source.")
    potential_title: Optional[str] = Field(None, max_length=250, description="Inferred job/project title.")
    potential_company: Optional[str] = Field(None, max_length=150, description="Inferred company or person name.")
    contact_details: Optional[ContactRoute] = Field(None, description="Extracted contact information.")


class WorkLeadScore(BaseModel):
    """Detailed scoring components for a work lead."""
    fit_score: float = Field(0.0, ge=0.0, le=100.0, description="How well the lead fits Adam's capabilities (0-100).")
    urgency_score: float = Field(0.0, ge=0.0, le=100.0, description="How urgent the project appears (0-100).")
    contact_score: float = Field(0.0, ge=0.0, le=100.0, description="Ease and clarity of contact route (0-100).")
    rejection_score: float = Field(0.0, ge=0.0, le=100.0, description="Score indicating reasons for rejection (0-100).")
    final_score: float = Field(0.0, ge=0.0, le=100.0, description="The aggregated final score (0-100).")
    why_fit: str = Field(..., description="Explanation of why the lead is a good fit.")
    outreach_angle: str = Field(..., description="Suggested angle for initial outreach.")
    evidence_text: str = Field(..., description="Snippet of text evidence supporting the lead and its scores.")
    matched_keywords: List[str] = Field(default_factory=list, description="Keywords from positive signals found.")
    rejection_reasons: List[str] = Field(default_factory=list, description="Reasons for potential rejection.")

    @field_validator('fit_score', 'urgency_score', 'contact_score', 'rejection_score', 'final_score', mode='before')
    @classmethod
    def clamp_scores(cls, v: float) -> float:
        return max(0.0, min(100.0, v))


class WorkLeadRecord(BaseModel):
    """A comprehensive record of a single work lead."""
    model_config = ConfigDict(validate_assignment=True)

    lead_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier for the lead.")
    source: WorkSourceType = Field(..., description="The type of source where the lead was found.")
    title: str = Field(..., max_length=500, description="The title or brief description of the project/opportunity.")
    company_or_person: Optional[str] = Field(None, max_length=250, description="Name of the company or person offering the work.")
    url: HttpUrl = Field(..., description="Direct URL to the project or job listing.")
    source_url: Optional[HttpUrl] = Field(None, description="The original page URL if different from 'url'.")
    contact_url: Optional[HttpUrl] = Field(None, description="Direct URL for contact if available.")
    contact_email: Optional[str] = Field(None, description="Direct email for contact if available.")
    
    remote: bool = Field(False, description="True if the work explicitly states it is remote.")
    contract: bool = Field(False, description="True if the work is explicitly a contract/freelance role.")
    full_time: bool = Field(False, description="True if the work is explicitly a full-time role.")
    short_project: bool = Field(False, description="True if the work appears to be a short-term project.")
    
    project_type: ProjectType = Field(ProjectType.OTHER, description="Categorization of the project type.")
    budget_signal: BudgetSignal = Field(BudgetSignal.UNKNOWN, description="Signal about the project's budget.")

    # Scores from WorkLeadScore
    fit_score: float = Field(..., ge=0.0, le=100.0)
    urgency_score: float = Field(..., ge=0.0, le=100.0)
    contact_score: float = Field(..., ge=0.0, le=100.0)
    rejection_score: float = Field(..., ge=0.0, le=100.0)
    final_score: float = Field(..., ge=0.0, le=100.0)
    why_fit: str = Field(...)
    outreach_angle: str = Field(...)
    evidence_text: str = Field(...)
    matched_keywords: List[str] = Field(default_factory=list)
    rejection_reasons: List[str] = Field(default_factory=list)

    status: LeadStatus = Field(LeadStatus.NEW, description="Current status of the lead.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp when the lead record was created.")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp when the lead record was last updated.")

    @field_validator('url', 'source_url', 'contact_url', mode='before')
    @classmethod
    def validate_http_url(cls, v: Optional[str]) -> Optional[HttpUrl]:
        if v is None or v == "":
            return None
        return HttpUrl(v)

    def to_csv_row(self) -> dict:
        """Converts the WorkLeadRecord to a dictionary suitable for CSV export."""
        return {
            "lead_id": self.lead_id,
            "source": self.source.value,
            "title": self.title,
            "company_or_person": self.company_or_person,
            "url": str(self.url),
            "source_url": str(self.source_url) if self.source_url else "",
            "contact_url": str(self.contact_url) if self.contact_url else "",
            "contact_email": self.contact_email,
            "remote": self.remote,
            "contract": self.contract,
            "full_time": self.full_time,
            "short_project": self.short_project,
            "project_type": self.project_type.value,
            "budget_signal": self.budget_signal.value,
            "fit_score": round(self.fit_score, 2),
            "urgency_score": round(self.urgency_score, 2),
            "contact_score": round(self.contact_score, 2),
            "rejection_score": round(self.rejection_score, 2),
            "final_score": round(self.final_score, 2),
            "why_fit": self.why_fit,
            "outreach_angle": self.outreach_angle,
            "evidence_text": self.evidence_text.replace('\n', ' ').strip(),
            "matched_keywords": ", ".join(self.matched_keywords),
            "rejection_reasons": ", ".join(self.rejection_reasons),
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class WorkLeadRunSummary(BaseModel):
    """Summary statistics for a single execution run of the work finder."""
    run_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique ID for this specific run.")
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp when the run started.")
    end_time: Optional[datetime] = Field(None, description="Timestamp when the run ended.")
    seed_urls_attempted: List[HttpUrl] = Field(default_factory=list, description="List of URLs that were scraped in this run.")
    leads_found: int = Field(0, description="Total number of leads identified.")
    leads_saved: int = Field(0, description="Number of leads saved to the database (after filtering/scoring).")
    leads_rejected: int = Field(0, description="Number of leads rejected during the scoring process.")
    total_processing_time_sec: float = Field(0.0, description="Total wall-clock time for the run in seconds.")
    errors_encountered: List[str] = Field(default_factory=list, description="List of errors or warnings during the run.")
    query: Optional[str] = Field(None, description="The query string used for this run.")

    @field_validator('seed_urls_attempted', mode='before')
    @classmethod
    def validate_http_url_list(cls, v: List[str]) -> List[HttpUrl]:
        return [HttpUrl(url) for url in v]

    def finalize(self):
        self.end_time = datetime.now(timezone.utc)
        self.total_processing_time_sec = (self.end_time - self.start_time).total_seconds()


class WorkLeadExportManifest(BaseModel):
    """Manifest of files generated by an export operation."""
    exported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    csv_path: Optional[str] = None
    md_path: Optional[str] = None
    json_path: Optional[str] = None
    summary_md_path: Optional[str] = None
    total_leads_exported: int = 0
    run_summary_id: Optional[str] = None
```

---

### 2. `C:\WEB CASE STUDY\work_lead_tables.py`

```python
# C:\WEB CASE STUDY\work_lead_tables.py

import os
import json
import pandas as pd
import lancedb
from lancedb.table import LanceTable
from datetime import datetime, timezone
from typing import List, Optional

from work_lead_schemas import WorkLeadRecord, WorkLeadRunSummary, WorkLeadExportManifest

# Correct LanceDB RAG path
LANCEDB_ROOT_PATH = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag"
EXPORT_DIR = r"C:\WEB CASE STUDY\work_finder_exports"

class WorkLeadTableManager:
    """Manages LanceDB tables for independent work leads and run summaries."""

    def __init__(self):
        os.makedirs(LANCEDB_ROOT_PATH, exist_ok=True)
        os.makedirs(EXPORT_DIR, exist_ok=True)
        self.db = lancedb.connect(LANCEDB_ROOT_PATH)
        self.leads_table_name = "independent_work_leads"
        self.runs_table_name = "independent_work_runs"

        self._ensure_tables_exist()

    def _ensure_tables_exist(self):
        """Ensures the LanceDB tables are created if they don't exist."""
        # For WorkLeadRecord
        if self.leads_table_name not in self.db.table_names():
            # Create an empty DataFrame matching WorkLeadRecord structure
            empty_df = pd.DataFrame([WorkLeadRecord(
                title="placeholder",
                url="http://example.com",
                source="Website",
                fit_score=0.0, urgency_score=0.0, contact_score=0.0, rejection_score=0.0, final_score=0.0,
                why_fit="", outreach_angle="", evidence_text=""
            ).to_csv_row()]) # Use to_csv_row to get a flat dict schema
            self.db.create_table(self.leads_table_name, data=empty_df.iloc[0:0]) # Create with schema but no data
            print(f"LanceDB table '{self.leads_table_name}' created.")
        else:
            print(f"LanceDB table '{self.leads_table_name}' already exists.")

        # For WorkLeadRunSummary
        if self.runs_table_name not in self.db.table_names():
            empty_df_run = pd.DataFrame([WorkLeadRunSummary(
                seed_urls_attempted=["http://example.com"]
            ).model_dump()])
            self.db.create_table(self.runs_table_name, data=empty_df_run.iloc[0:0])
            print(f"LanceDB table '{self.runs_table_name}' created.")
        else:
            print(f"LanceDB table '{self.runs_table_name}' already exists.")

    def add_lead(self, record: WorkLeadRecord):
        """Adds a WorkLeadRecord to the independent_work_leads table."""
        table = self.db.open_table(self.leads_table_name)
        # Convert Pydantic model to a flat dictionary for LanceDB
        data_to_insert = record.to_csv_row()
        table.add(pd.DataFrame([data_to_insert]))
        print(f"Added lead '{record.title}' to LanceDB.")

    def add_run_summary(self, summary: WorkLeadRunSummary):
        """Adds a WorkLeadRunSummary to the independent_work_runs table."""
        summary.finalize() # Ensure end_time and total_processing_time_sec are set
        table = self.db.open_table(self.runs_table_name)
        data_to_insert = summary.model_dump()
        # Convert HttpUrl objects to strings for LanceDB compatibility if necessary
        data_to_insert['seed_urls_attempted'] = [str(url) for url in summary.seed_urls_attempted]
        table.add(pd.DataFrame([data_to_insert]))
        print(f"Added run summary '{summary.run_id}' to LanceDB.")

    def get_all_leads(self) -> List[WorkLeadRecord]:
        """Retrieves all WorkLeadRecords from the database."""
        table = self.db.open_table(self.leads_table_name)
        df = table.to_pandas()
        return [WorkLeadRecord.model_validate(row.to_dict()) for _, row in df.iterrows()]

    def get_latest_run_summary(self) -> Optional[WorkLeadRunSummary]:
        """Retrieves the latest WorkLeadRunSummary."""
        table = self.db.open_table(self.runs_table_name)
        df = table.to_pandas()
        if not df.empty:
            latest_run_df = df.sort_values(by='start_time', ascending=False).iloc[0]
            # Convert string URLs back to HttpUrl for Pydantic validation
            latest_run_dict = latest_run_df.to_dict()
            latest_run_dict['seed_urls_attempted'] = [
                str(url) for url in latest_run_dict['seed_urls_attempted']
            ] if isinstance(latest_run_dict['seed_urls_attempted'], list) else []
            return WorkLeadRunSummary.model_validate(latest_run_dict)
        return None
    
    def search_leads(self, query: str, limit: int = 10) -> List[WorkLeadRecord]:
        """
        Performs a simple text search on lead titles and evidence text.
        (Can be enhanced with LanceDB vector search if an embedding model is integrated).
        """
        table = self.db.open_table(self.leads_table_name)
        # Basic filter for now, for vector search, an embedding model would be needed.
        # Assuming query could match in title or why_fit or evidence_text
        results_df = table.to_pandas()
        
        # Filter rows that contain the query string (case-insensitive)
        filtered_df = results_df[
            results_df['title'].str.contains(query, case=False, na=False) |
            results_df['why_fit'].str.contains(query, case=False, na=False) |
            results_df['evidence_text'].str.contains(query, case=False, na=False)
        ]
        
        return [WorkLeadRecord.model_validate(row.to_dict()) for _, row in filtered_df.head(limit).iterrows()]

    def export_latest(self) -> WorkLeadExportManifest:
        """Exports all current leads to CSV, Markdown, and JSON files."""
        all_leads = self.get_all_leads()
        
        manifest = WorkLeadExportManifest()
        manifest.total_leads_exported = len(all_leads)
        
        if all_leads:
            df = pd.DataFrame([lead.to_csv_row() for lead in all_leads])
            
            # Export to CSV
            csv_path = os.path.join(EXPORT_DIR, "work_leads_latest.csv")
            df.to_csv(csv_path, index=False)
            manifest.csv_path = csv_path
            print(f"Exported {len(all_leads)} leads to CSV: {csv_path}")

            # Export to JSON
            json_path = os.path.join(EXPORT_DIR, "work_leads_latest.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump([lead.model_dump_json() for lead in all_leads], f, indent=2)
            manifest.json_path = json_path
            print(f"Exported {len(all_leads)} leads to JSON: {json_path}")
            
            # Export to Markdown
            md_path = os.path.join(EXPORT_DIR, "work_leads_latest.md")
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write("# Independent Work Leads\n\n")
                f.write(f"Exported on: {datetime.now(timezone.utc).isoformat()}\n\n")
                f.write(df.to_markdown(index=False))
            manifest.md_path = md_path
            print(f"Exported {len(all_leads)} leads to Markdown: {md_path}")
        else:
            print("No leads found to export. Exporting empty files.")
            # Still create empty files with headers
            csv_path = os.path.join(EXPORT_DIR, "work_leads_latest.csv")
            with open(csv_path, 'w', encoding='utf-8') as f:
                f.write(",".join(WorkLeadRecord(
                    title="placeholder",
                    url="http://example.com",
                    source="Website",
                    fit_score=0.0, urgency_score=0.0, contact_score=0.0, rejection_score=0.0, final_score=0.0,
                    why_fit="", outreach_angle="", evidence_text=""
                ).to_csv_row().keys()))
            manifest.csv_path = csv_path

            json_path = os.path.join(EXPORT_DIR, "work_leads_latest.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2)
            manifest.json_path = json_path

            md_path = os.path.join(EXPORT_DIR, "work_leads_latest.md")
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write("# Independent Work Leads\n\n")
                f.write(f"Exported on: {datetime.now(timezone.utc).isoformat()}\n\n")
                f.write("No leads found.\n")
            manifest.md_path = md_path


        # Export run summary
        latest_run = self.get_latest_run_summary()
        if latest_run:
            summary_md_path = os.path.join(EXPORT_DIR, "work_finder_run_summary.md")
            with open(summary_md_path, 'w', encoding='utf-8') as f:
                f.write(f"# Work Finder Run Summary (ID: {latest_run.run_id})\n\n")
                f.write(f"- **Start Time:** {latest_run.start_time.isoformat()}\n")
                f.write(f"- **End Time:** {latest_run.end_time.isoformat() if latest_run.end_time else 'N/A'}\n")
                f.write(f"- **Total Processing Time:** {latest_run.total_processing_time_sec:.2f} seconds\n")
                f.write(f"- **Query Used:** {latest_run.query if latest_run.query else 'None'}\n")
                f.write(f"- **Seed URLs Attempted:**\n")
                for url in latest_run.seed_urls_attempted:
                    f.write(f"  - {url}\n")
                f.write(f"- **Leads Found (Scraped):** {latest_run.leads_found}\n")
                f.write(f"- **Leads Saved (to DB):** {latest_run.leads_saved}\n")
                f.write(f"- **Leads Rejected (by scoring):** {latest_run.leads_rejected}\n")
                if latest_run.errors_encountered:
                    f.write(f"- **Errors Encountered:**\n")
                    for error in latest_run.errors_encountered:
                        f.write(f"  - {error}\n")
            manifest.summary_md_path = summary_md_path
            manifest.run_summary_id = latest_run.run_id
            print(f"Exported run summary to Markdown: {summary_md_path}")
        else:
            print("No run summary found to export.")
            summary_md_path = os.path.join(EXPORT_DIR, "work_finder_run_summary.md")
            with open(summary_md_path, 'w', encoding='utf-8') as f:
                f.write("# Work Finder Run Summary\n\n")
                f.write("No run summaries have been recorded yet.\n")
            manifest.summary_md_path = summary_md_path

        return manifest

if __name__ == "__main__":
    print("Initializing WorkLeadTableManager...")
    manager = WorkLeadTableManager()
    print("Table manager initialized. LanceDB paths ensured.")
    print(f"LanceDB Root: {LANCEDB_ROOT_PATH}")
    print(f"Export Directory: {EXPORT_DIR}")

    # Example: Add a dummy lead (will be replaced by actual actor logic)
    # from work_lead_schemas import WorkSourceType, ProjectType, BudgetSignal
    # dummy_lead = WorkLeadRecord(
    #     title="Need help with Python automation",
    #     company_or_person="Acme Corp",
    #     url=HttpUrl("https://example.com/project"),
    #     source=WorkSourceType.WEBSITE,
    #     remote=True, contract=True, short_project=True,
    #     project_type=ProjectType.WORKFLOW_AUTOMATION,
    #     budget_signal=BudgetSignal.PAID,
    #     fit_score=90.0, urgency_score=80.0, contact_score=70.0, rejection_score=0.0, final_score=85.0,
    #     why_fit="Strong match for Python and automation skills.",
    #     outreach_angle="Offer a 2-day prototype for their automation needs.",
    #     evidence_text="Looking for a Python expert to automate internal reports."
    # )
    # manager.add_lead(dummy_lead)

    # Example: Export leads
    # manifest = manager.export_latest()
    # print(f"Export manifest: {manifest.model_dump_json(indent=2)}")
```

---

### 3. `C:\WEB CASE STUDY\indie_work_finder_actor.py`

```python
# C:\WEB CASE STUDY\indie_work_finder_actor.py

import os
import time
import requests
import re
from uuid import uuid4
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import ray
from bs4 import BeautifulSoup, Comment
from pydantic import HttpUrl

from work_lead_schemas import (
    WorkSourceType, ProjectType, LeadStatus, BudgetSignal, ContactRoute,
    WorkLeadRaw, WorkLeadClean, WorkLeadScore, WorkLeadRecord, WorkLeadRunSummary
)
from work_lead_tables import WorkLeadTableManager, EXPORT_DIR # Import EXPORT_DIR for actor

# Initialize Ray if not already done
if not ray.is_initialized():
    ray.init(namespace="legion", ignore_reinit_error=True)

@ray.remote(num_cpus=1) # Run on CPU, scraping is not GPU-bound
class IndependentWorkFinderActor:
    """
    Ray Actor for finding, classifying, and scoring independent contract work leads
    from various web sources.
    """
    def __init__(self):
        self.table_manager = WorkLeadTableManager()
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        print(f"📦 IndependentWorkFinderActor initialized with LanceDB manager and UA: {self.user_agent}")

        # --- Scoring Keywords ---
        self.positive_keywords = {
            "remote": {"remote", "work from home", "wfh", "distributed team"},
            "contract": {"contract", "freelance", "independent contractor", "project-based", "consulting", "gig"},
            "short_project": {"short project", "prototype", "proof of concept", "quick turnaround", "1-2 week", "3-month", "temporary engagement"},
            "automation": {"automation", "automate", "workflow", "process improvement"},
            "python": {"python", "pytorch", "tensorflow", "fastapi"},
            "scraping": {"scraping", "web scraping", "data extraction", "crawler"},
            "ai_ml": {"ai assistant", "machine learning", "rag system", "local ai", "ollama", "llm", "genai", "nlp"},
            "lancedb_rag": {"lancedb", "rag", "retrieval augmented generation", "vector database", "private data"},
            "ray_actors": {"ray actors", "distributed computing", "ray core", "ray cluster", "actor model", "parallel processing"},
            "mcp_api": {"mcp api", "multi-channel platform", "tool development", "custom api", "external tools"},
            "web_ui": {"squarespace", "wix", "webflow", "website automation", "intake form", "front-door integration", "low-code platform"},
            "audio_data": {"audio processing", "dsp", "sound analysis", "waveform", "spectral", "mastering", "speech"},
            "data_cleanup": {"data cleanup", "data transformation", "etl", "csv export", "table export"},
            "urgent": {"urgent", "immediate start", "fast turn", "critical", "deadline", "help needed"},
            "small_business": {"small business", "startup", "local company", "private workflow", "boutique agency"},
            "api_integration": {"api integration", "third-party api", "webhook", "system connection"},
        }

        self.negative_keywords = {
            "full_time": {"full-time", "permanent position", "senior role", "employment", "salaried"},
            "onsite": {"onsite", "relocation", "in-person", "office-based", "hybrid (mostly onsite)"},
            "enterprise_cloud": {"aws", "azure", "gcp", "enterprise migration", "cloud architect", "devops (cloud)"},
            "unpaid": {"unpaid", "equity only", "volunteer"},
            "generic_dj": {"dj mastering", "music mastering", "audio engineering (generic)", "sound design (generic)"},
            "no_contact": {"apply button", "no contact", "email not found", "application form only"}, # Heuristic for hard-to-contact
        }
        
        # Mapping common phrases to ProjectType
        self.project_type_mapping = {
            "ai_ml": ProjectType.AI_AUTOMATION,
            "lancedb_rag": ProjectType.RAG_SYSTEM,
            "ray_actors": ProjectType.WORKFLOW_AUTOMATION, # Ray is more about workflow automation
            "mcp_api": ProjectType.MCP_TOOL,
            "web_ui": ProjectType.SQUARESPACE_INTEGRATION, # Broader web/Squarespace related
            "audio_data": ProjectType.AUDIO_PROCESSING,
            "data_cleanup": ProjectType.DATA_PROCESSING,
            "automation": ProjectType.WORKFLOW_AUTOMATION,
            "scraping": ProjectType.WEB_SCRAPING,
        }

    def _scrape_page(self, url: HttpUrl) -> Optional[WorkLeadRaw]:
        """Downloads and extracts raw text content from a given URL."""
        try:
            headers = {"User-Agent": self.user_agent}
            response = requests.get(str(url), headers=headers, timeout=15)
            response.raise_for_status() # Raise an exception for HTTP errors
            
            # Simple content type check to avoid non-HTML files
            if 'text/html' not in response.headers.get('Content-Type', '').lower():
                print(f"Skipping non-HTML content at {url}")
                return None

            return WorkLeadRaw(source_url=url, raw_content=response.text)
        except requests.exceptions.RequestException as e:
            print(f"Error scraping {url}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error scraping {url}: {e}")
            return None

    def _clean_text(self, raw_html_content: str, base_url: HttpUrl) -> WorkLeadClean:
        """
        Cleans HTML content by removing irrelevant tags and extracts readable text.
        Inspired by crawl_and_vectorize_all_ray.py's download_and_clean.
        """
        soup = BeautifulSoup(raw_html_content, 'html.parser')

        # Remove script, style, navigation, footer, header, aside elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "form", "svg", "button"]):
            element.decompose()
        
        # Remove comments
        for comment in soup(text=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Remove common "contact us" or "privacy policy" links if they are not primary contact
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href'].lower()
            if "privacy" in href or "terms" in href or "legal" in href:
                a_tag.decompose()

        # Extract text
        clean_text = soup.get_text(separator=' ', strip=True)
        
        # Try to infer potential title (e.g., from <title> or <h1>)
        potential_title = soup.title.string.strip() if soup.title and soup.title.string else None
        if not potential_title and soup.h1:
            potential_title = soup.h1.get_text(strip=True)

        # Try to infer company name from title or URL
        potential_company = None
        if potential_title and ' - ' in potential_title:
            potential_company = potential_title.split(' - ')[0].strip()
        elif base_url:
            potential_company = urlparse(str(base_url)).netloc.split('.')[0] # e.g. "example" from example.com

        # Extract contact details (basic regex for email, look for contact links)
        contact_url = None
        contact_email = None
        
        # Find email addresses
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', clean_text)
        if emails:
            contact_email = emails[0] # Take the first one

        # Find contact links (simple approach, could be improved with recursive search)
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if 'contact' in href.lower() or 'apply' in href.lower() or 'jobs' in href.lower():
                # Resolve relative URL
                absolute_url = urljoin(str(base_url), href)
                try:
                    contact_url = HttpUrl(absolute_url)
                    break # Take the first relevant contact link
                except Exception:
                    continue


        return WorkLeadClean(
            source_url=base_url,
            clean_text=clean_text,
            potential_title=potential_title,
            potential_company=potential_company,
            contact_details=ContactRoute(url=contact_url, email=contact_email)
        )

    def _extract_and_score_leads(self, clean_lead: WorkLeadClean, query: str) -> List[WorkLeadRecord]:
        """
        Identifies potential leads within the clean text, scores them, and
        returns a list of WorkLeadRecord objects.
        This is heuristic-based, looking for paragraphs/sentences matching keywords.
        """
        leads: List[WorkLeadRecord] = []
        
        # Combine query with relevant positive keywords for extraction
        extraction_keywords = set(query.lower().split())
        for group in self.positive_keywords.values():
            extraction_keywords.update(group)
        
        # Split text into potential "sections" or "paragraphs"
        # We try to create granular chunks for scoring, avoiding entire page as one lead
        text_sections = re.split(r'(?<=[.!?])\s+|\n\s*\n', clean_lead.clean_text)
        text_sections = [s.strip() for s in text_sections if len(s.strip()) > 50] # Filter very short sections
        
        if not text_sections:
            text_sections = [clean_lead.clean_text] # Fallback to whole text if no natural breaks

        # Scoring parameters for weighted sums
        keyword_weights = {
            "remote": 10, "contract": 15, "short_project": 12, "urgent": 20,
            "automation": 8, "python": 7, "scraping": 8, "ai_ml": 10,
            "lancedb_rag": 12, "ray_actors": 12, "mcp_api": 15, "web_ui": 9,
            "audio_data": 10, "data_cleanup": 6, "small_business": 5, "api_integration": 7,
            "query_match": 25 # High weight for direct query matches
        }
        
        negative_weights = {
            "full_time": 30, "onsite": 25, "enterprise_cloud": 20, "unpaid": 50,
            "generic_dj": 10, "no_contact": 15
        }

        # Iterate through identified sections to find and score potential leads
        for i, section_text in enumerate(text_sections):
            section_lower = section_text.lower()
            
            matched_pos_keywords = []
            rejection_reasons = []
            
            temp_fit_score = 0.0
            temp_urgency_score = 0.0
            temp_contact_score = 0.0
            temp_rejection_score = 0.0
            
            is_remote = False
            is_contract = False
            is_full_time = False
            is_short_project = False
            budget_signal = BudgetSignal.UNKNOWN
            project_type = ProjectType.OTHER

            # Score positive signals
            for kw_type, keywords in self.positive_keywords.items():
                for kw in keywords:
                    if kw in section_lower:
                        matched_pos_keywords.append(kw)
                        temp_fit_score += keyword_weights.get(kw_type, 1) # Add base weight
                        
                        if kw_type == "remote": is_remote = True
                        if kw_type == "contract": is_contract = True
                        if kw_type == "short_project": is_short_project = True
                        if kw_type == "urgent": temp_urgency_score += 30 # urgency directly influences this score
                        
                        # Infer ProjectType
                        if kw_type in self.project_type_mapping and project_type == ProjectType.OTHER:
                            project_type = self.project_type_mapping[kw_type]
            
            # Score direct query matches
            if query.lower() in section_lower:
                temp_fit_score += keyword_weights.get("query_match", 25)
                if query.lower() not in matched_pos_keywords:
                    matched_pos_keywords.append(query.lower())

            # Score negative signals
            for kw_type, keywords in self.negative_keywords.items():
                for kw in keywords:
                    if kw in section_lower:
                        rejection_reasons.append(kw)
                        temp_rejection_score += negative_weights.get(kw_type, 10)
                        
                        if kw_type == "full_time": is_full_time = True
                        if kw_type == "onsite": temp_rejection_score += 20 # strong negative for Adam
                        if kw_type == "unpaid": budget_signal = BudgetSignal.UNPAID; temp_rejection_score += 50

            # --- Budget Signal from text ---
            if "paid" in section_lower and budget_signal != BudgetSignal.UNPAID:
                budget_signal = BudgetSignal.PAID
                if any(b in section_lower for b in ["budget", "dollars", "€", "$", "£"]):
                    budget_signal = BudgetSignal.MEDIUM # Could be more specific with regex
            
            if any(b in section_lower for b in ["high budget", "significant investment", "generous compensation"]):
                budget_signal = BudgetSignal.HIGH
            elif any(b in section_lower for b in ["low budget", "tight budget", "cost-effective"]):
                budget_signal = BudgetSignal.LOW


            # --- Heuristic for contact_score ---
            # If explicit email or contact URL is found from initial scrape, boost contact score
            if clean_lead.contact_details and (clean_lead.contact_details.email or clean_lead.contact_details.url):
                temp_contact_score = 80.0
            else:
                # If "apply" or "careers" in text but no direct contact, penalize
                if any(re.search(r'\b' + pattern + r'\b', section_lower) for pattern in ["apply", "careers", "job opening"]):
                     temp_contact_score = 40.0 # Likely application form, not direct contact
                     if "no_contact" not in rejection_reasons:
                         rejection_reasons.append("Application form only / no direct contact")
                     temp_rejection_score += negative_weights.get("no_contact", 15)
                else:
                    temp_contact_score = 20.0 # No clear contact info

            # --- Final Score Calculation ---
            # Clamp intermediate scores to 0-100 before weighted sum
            temp_fit_score = max(0.0, min(100.0, temp_fit_score))
            temp_urgency_score = max(0.0, min(100.0, temp_urgency_score))
            temp_contact_score = max(0.0, min(100.0, temp_contact_score))
            temp_rejection_score = max(0.0, min(100.0, temp_rejection_score))

            final_score = (
                0.40 * temp_fit_score
                + 0.25 * temp_contact_score
                + 0.20 * temp_urgency_score
                + 0.15 * (100 - temp_rejection_score) # Invert rejection score for positive contribution
            )
            final_score = max(0.0, min(100.0, final_score)) # Final clamp

            # Only consider as a lead if some positive signal exists and not primarily rejected
            if final_score > 30 and (temp_rejection_score < 70 or is_contract or is_short_project): # If strongly contract, allow lower overall score
                why_fit = f"Keywords: {', '.join(matched_pos_keywords)}. " + \
                          ("Appears remote. " if is_remote else "") + \
                          ("Looks like a contract/short project. " if is_contract or is_short_project else "") + \
                          (f"Matches query '{query}'. " if query.lower() in section_lower else "")
                
                outreach_angle = "Focus on rapid prototype/automation capabilities. "
                if project_type == ProjectType.RAG_SYSTEM:
                    outreach_angle += "Highlight LanceDB/private RAG expertise."
                elif project_type == ProjectType.MCP_TOOL:
                    outreach_angle += "Emphasize MCP API tools."
                elif project_type == ProjectType.AUDIO_PROCESSING:
                    outreach_angle += "Suggest Ray actor pipelines for large-scale audio."
                elif project_type == ProjectType.SQUARESPACE_INTEGRATION:
                    outreach_angle += "Offer Squarespace intake automation."
                
                # Truncate evidence text for brevity
                evidence_text_snippet = section_text[:500] + ("..." if len(section_text) > 500 else "")

                # Set title based on keywords or original page title
                inferred_title = clean_lead.potential_title or f"Project opportunity from {clean_lead.source_url.host}"
                if matched_pos_keywords:
                    inferred_title = f"Project with keywords: {', '.join(matched_pos_keywords[:3])}"
                
                # Ensure it's not full-time unless it's also strongly contract
                if is_full_time and not is_contract and not is_short_project:
                    rejection_reasons.append("Primarily a full-time role without strong contract signals.")
                    final_score *= 0.1 # Heavily penalize
                    
                if final_score < 30 and "Primarily a full-time role" not in rejection_reasons:
                    rejection_reasons.append("Low overall score and fit.")

                # If the lead is explicitly a full-time role, reject unless it also strongly indicates contract work
                if is_full_time and not is_contract and not is_short_project:
                    rejection_reasons.append("Rejected: Identified as a full-time role with no contract option.")
                    final_score = 0.0 # Force rejection

                # If rejected, mark status
                status = LeadStatus.NEW
                if final_score <= 10: # Very low score, effectively rejected
                    status = LeadStatus.REJECTED
                    if not rejection_reasons:
                        rejection_reasons.append("Low final score; no clear fit.")


                # Create WorkLeadRecord
                leads.append(WorkLeadRecord(
                    source=WorkSourceType.WEBSITE, # Default, could be refined
                    title=inferred_title[:500], # Max length
                    company_or_person=clean_lead.potential_company,
                    url=clean_lead.source_url, # For now, the entire page URL is the project URL
                    source_url=clean_lead.source_url,
                    contact_url=clean_lead.contact_details.url,
                    contact_email=clean_lead.contact_details.email,
                    remote=is_remote,
                    contract=is_contract or is_short_project, # Treat short_project as contract-like
                    full_time=is_full_time,
                    short_project=is_short_project,
                    project_type=project_type,
                    budget_signal=budget_signal,
                    fit_score=temp_fit_score,
                    urgency_score=temp_urgency_score,
                    contact_score=temp_contact_score,
                    rejection_score=temp_rejection_score,
                    final_score=final_score,
                    why_fit=why_fit,
                    outreach_angle=outreach_angle,
                    evidence_text=evidence_text_snippet,
                    matched_keywords=list(set(matched_pos_keywords)), # Unique keywords
                    rejection_reasons=list(set(rejection_reasons)), # Unique reasons
                    status=status
                ))
        return leads

    def run_search(self, seed_urls: List[str], query: str, limit: int = 50) -> dict:
        """
        Accepts search seeds, scrapes pages, extracts and scores leads,
        and saves them to LanceDB.
        """
        run_summary = WorkLeadRunSummary(seed_urls_attempted=[HttpUrl(url) for url in seed_urls], query=query)
        print(f"📡 Initiating search run ID: {run_summary.run_id} for query: '{query}'")
        
        found_leads_count = 0
        saved_leads_count = 0
        rejected_leads_count = 0
        
        processed_urls = set()

        for raw_url_str in seed_urls:
            url = HttpUrl(raw_url_str) # Ensure it's a valid Pydantic HttpUrl
            if url in processed_urls:
                continue
            processed_urls.add(url)

            print(f"Scraping: {url}")
            raw_lead = self._scrape_page(url)
            if raw_lead:
                clean_lead = self._clean_text(raw_lead.raw_content, url)
                potential_leads = self._extract_and_score_leads(clean_lead, query)
                
                found_leads_count += len(potential_leads)
                
                for lead in potential_leads:
                    if lead.status == LeadStatus.REJECTED or lead.final_score <= 10:
                        rejected_leads_count += 1
                        run_summary.errors_encountered.append(f"Rejected lead from {url}: {lead.title} (Score: {lead.final_score:.2f}) - Reasons: {', '.join(lead.rejection_reasons)}")
                    else:
                        self.table_manager.add_lead(lead)
                        saved_leads_count += 1
                        if saved_leads_count >= limit:
                            print(f"Limit of {limit} leads reached. Stopping search.")
                            break
            else:
                run_summary.errors_encountered.append(f"Failed to scrape or process {url}.")

            if saved_leads_count >= limit:
                break
        
        run_summary.leads_found = found_leads_count
        run_summary.leads_saved = saved_leads_count
        run_summary.leads_rejected = rejected_leads_count
        self.table_manager.add_run_summary(run_summary) # Save final run summary
        
        print(f"✅ Search run {run_summary.run_id} completed.")
        return run_summary.model_dump()

    def score_url(self, url: str, query: str) -> dict:
        """Scores a single URL for potential lead fit and returns the WorkLeadScore."""
        url_pydantic = HttpUrl(url) # Validate URL
        raw_lead = self._scrape_page(url_pydantic)
        if not raw_lead:
            return {"error": f"Failed to scrape {url}", "url": url}

        clean_lead = self._clean_text(raw_lead.raw_content, url_pydantic)
        potential_leads = self._extract_and_score_leads(clean_lead, query)
        
        if potential_leads:
            # Return the highest-scoring lead from this URL
            best_lead = max(potential_leads, key=lambda l: l.final_score)
            return {
                "url": url,
                "scored_lead": best_lead.model_dump(),
                "all_potential_leads_count": len(potential_leads)
            }
        else:
            return {"message": f"No potential leads found on {url} matching query '{query}'.", "url": url}

    def export_latest(self) -> dict:
        """Triggers the export of all current leads to CSV, Markdown, and JSON files."""
        print(f"Initiating export to {EXPORT_DIR}...")
        manifest = self.table_manager.export_latest()
        return manifest.model_dump()

    def get_run_summary(self) -> dict:
        """Retrieves the latest run summary from the LanceDB."""
        summary = self.table_manager.get_latest_run_summary()
        if summary:
            return summary.model_dump()
        return {"message": "No run summaries found."}

    def search_existing_work_leads(self, query: str, limit: int = 10) -> List[dict]:
        """Searches existing leads in LanceDB for a given query."""
        leads = self.table_manager.search_leads(query, limit)
        return [lead.model_dump() for lead in leads]
```

---

### 4. `C:\WEB CASE STUDY\work_finder_mcp_server.py`

```python
# C:\WEB CASE STUDY\work_finder_mcp_server.py

import json
import os
import sys
import logging
import ray

# Configure debug logging to stderr for the IDE output console
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logging.getLogger("mcp").setLevel(logging.INFO) # Adjust MCP log level

try:
    from mcp.server.fastmcp import FastMCP
    # LanceDB is managed by the actor, not directly here for tools
    # import lancedb 
except ImportError:
    print("Please run: pip install mcp[cli]")
    sys.exit(1)

# Initialize Ray if not already running for the MCP server to find actors
if not ray.is_initialized():
    ray.init(namespace="legion", ignore_reinit_error=True)
    print("Ray initialized for MCP server (namespace: legion).")
else:
    print("Ray already initialized for MCP server.")

# Ensure the actor is available or create it if not
try:
    # Attempt to get the actor if it's already running
    work_finder_actor = ray.get_actor("IndependentWorkFinderActor", namespace="legion")
    print("IndependentWorkFinderActor already running.")
except ValueError:
    # If not running, import and create it
    print("IndependentWorkFinderActor not found, creating a new instance...")
    from indie_work_finder_actor import IndependentWorkFinderActor
    work_finder_actor = IndependentWorkFinderActor.options(name="IndependentWorkFinderActor", namespace="legion", lifetime='detached').remote()
    print("IndependentWorkFinderActor created.")

# Initialize the MCP Server
mcp = FastMCP("LegionWorkFinder", port=8004) # Using a different port to avoid conflict with RAG server

@mcp.tool()
def find_contract_leads(query: str, seed_urls: List[str], limit: int = 25) -> str:
    """
    Searches for independent contract work leads by scraping seed URLs.
    Args:
        query (str): Keywords or phrases to search for (e.g., "python automation", "RAG system").
        seed_urls (List[str]): A list of URLs to start scraping from.
        limit (int): Maximum number of leads to save.
    Returns:
        str: A JSON string containing the run summary and status.
    """
    print(f"MCP Tool: find_contract_leads called with query='{query}' and {len(seed_urls)} seed URLs.")
    try:
        # Call the Ray actor asynchronously
        run_summary_ref = work_finder_actor.run_search.remote(seed_urls, query, limit)
        run_summary = ray.get(run_summary_ref) # Wait for the result
        return json.dumps({"status": "success", "run_summary": run_summary}, indent=2)
    except Exception as e:
        logging.error(f"Error in find_contract_leads tool: {e}", exc_info=True)
        return json.dumps({"status": "error", "message": str(e)}, indent=2)



[ERROR] Gemini request failed: ServerError: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'status': 'UNAVAILABLE'}}
