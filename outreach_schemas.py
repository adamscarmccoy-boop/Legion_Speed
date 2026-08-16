from pydantic import BaseModel, HttpUrl
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

class ProspectInfo(BaseModel):
    name: str
    slug: str
    website: HttpUrl

class SegmentAlignment(BaseModel):
    segment_name: str
    matched_baseline: str          # "Drop / High Energy 15"
    alignment_score: float         # 0.0-1.0
    pass_threshold: bool           # True if score >= 0.82

class ForestVerdict(BaseModel):
    top_style_match: str           # "Chris Lake"
    style_confidence: float        # 0.0-1.0
    is_anomaly: bool
    marketing_score: float

class PackReport(BaseModel):
    prospect: ProspectInfo         # name, slug, website
    pack_name: str
    pack_url: HttpUrl
    analyzed_at: datetime
    total_segments: int
    alignment_pass_rate: float     # 0.82 = 82%
    avg_alignment: float           # 0.94
    best_segment_score: float
    fire_test_duration_ms: float
    forest_verdict: ForestVerdict
    segment_breakdown: List[SegmentAlignment]
    category_distribution: Dict[str, int]  # {"drops": 9, "builds": 23, ...}
    key_findings: List[str]        # auto-generated bullet points
    comparable_to: List[str]       # ["Chris Lake - Somebody (2024)", ...]

class EmailDraft(BaseModel):
    subject: str                   # "I analyzed your Splice pack in 5 seconds"
    body: str                      # personalized with pack findings
    cta: str                       # "Want a free audit of your next release?"
    send_to: str
    attachment_paths: List[Path]

class OutreachPacket(BaseModel):
    prospect: ProspectInfo
    report: PackReport
    email: EmailDraft
    html_report_path: Path
    pdf_report_path: Path