from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from datetime import datetime
from typing import List, Optional

class WorkSourceType(str, Enum):
    WEBSITE = "Website"
    JOB_BOARD = "Job_Board"
    GITHUB = "GitHub"
    HACKER_NEWS = "Hacker_News"
    REDDIT = "Reddit"
    AGENCY = "Agency"
    SQUARESPACE = "Squarespace"
    UNKNOWN = "Unknown"

class ProjectType(str, Enum):
    MCP_API = "MCP_API"
    LOCAL_RAG = "Local_RAG"
    WEBSITE_SCRAPING = "Website_Scraping"
    SQUARESPACE_AUTOMATION = "Squarespace_Automation"
    LOCAL_AI_ASSISTANT = "Local_AI_Assistant"
    AUDIO_BATCH_PROCESSING = "Audio_Batch_Processing"
    ONNX_INFERENCE = "ONNX_Inference"
    DATA_CLEANUP = "Data_Cleanup"
    RAY_PIPELINE = "Ray_Pipeline"
    PYTHON_AUTOMATION = "Python_Automation"
    OTHER = "Other"

class BudgetSignal(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    UNPAID = "Unpaid"
    UNKNOWN = "Unknown"

class LeadStatus(str, Enum):
    NEW = "New"
    SCORED = "Scored"
    CONTACTED = "Contacted"
    REJECTED = "Rejected"

# 1. ScrapeActor Output
class ScrapedPage(BaseModel):
    model_config = ConfigDict(strict=True)
    source_url: str
    status_code: Optional[int]
    fetched_at: datetime
    html_chars: int
    text_chars: int
    cleaned_text: str
    links_found: List[str]
    emails_found: List[str]
    fetch_error: Optional[str] = None

# 2. Parser Output
class CandidateLead(BaseModel):
    model_config = ConfigDict(strict=True)
    candidate_id: str
    source_url: str
    title: Optional[str]
    raw_text: str
    candidate_url: Optional[str]
    contact_email: Optional[str]
    contact_url: Optional[str]
    extraction_method: str
    evidence_text: str

# 3. Raw Validation 
class WorkLeadRaw(BaseModel):
    model_config = ConfigDict(strict=True)
    candidate_id: str
    raw_data: str
    source_url: str

# 4. Cleaner Output (Valid)
class WorkLeadClean(BaseModel):
    model_config = ConfigDict(strict=True)
    clean_id: str
    source_url: str
    title: str
    company_or_person: Optional[str]
    url: str
    contact_email: Optional[str]
    contact_url: Optional[str]
    remote: bool
    contract: bool
    full_time: bool
    short_project: bool
    project_type: ProjectType
    budget_signal: BudgetSignal
    matched_keywords: List[str]
    rejection_reasons: List[str]
    evidence_text: str

# 5. Scorer Output
class WorkLeadScore(BaseModel):
    model_config = ConfigDict(strict=True)
    fit_score: float = Field(ge=0, le=100)
    urgency_score: float = Field(ge=0, le=100)
    contact_score: float = Field(ge=0, le=100)
    contract_score: float = Field(ge=0, le=100)
    rejection_score: float = Field(ge=0, le=100)
    final_score: float = Field(ge=0, le=100)

# 6. Final Record (Allowed into LanceDB)
class WorkLeadRecord(BaseModel):
    model_config = ConfigDict(strict=True)
    lead_id: str
    source: WorkSourceType
    title: str
    company_or_person: Optional[str]
    url: str
    source_url: str
    contact_url: Optional[str]
    contact_email: Optional[str]
    remote: bool
    contract: bool
    full_time: bool
    short_project: bool
    project_type: ProjectType
    budget_signal: BudgetSignal
    fit_score: float = Field(ge=0, le=100)
    urgency_score: float = Field(ge=0, le=100)
    contact_score: float = Field(ge=0, le=100)
    contract_score: float = Field(ge=0, le=100)
    rejection_score: float = Field(ge=0, le=100)
    final_score: float = Field(ge=0, le=100)
    why_fit: str
    outreach_angle: str
    evidence_text: str
    matched_keywords: List[str]
    rejection_reasons: List[str]
    status: LeadStatus
    created_at: datetime
    updated_at: datetime

# 7. Rejection Log
class RejectedLeadRecord(BaseModel):
    model_config = ConfigDict(strict=True)
    source_url: str
    candidate_id: Optional[str]
    failed_stage: str
    validation_error: str
    raw_text_snippet: str
    rejected_at: datetime

# 8. Run Proof
class ScrapeRunProof(BaseModel):
    model_config = ConfigDict(strict=True)
    run_id: str
    start_time: datetime
    end_time: datetime
    urls_attempted: int
    pages_scraped: int
    candidates_parsed: int
    leads_accepted: int
    leads_rejected: int
    errors: List[str]
    status: str