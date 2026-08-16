
"""Save helpers — write pack report, email draft, HTML, and the index.json (the contract for the approval UI)."""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from outreach_schemas import PackReport, EmailDraft


def checksum_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _out_root() -> Path:
    import os
    root = Path(os.environ.get("OUTREACH_ROOT", "outreach"))
    return root


def ensure_outreach_dir(slug: str) -> Path:
    out = _out_root() / slug
    out.mkdir(parents=True, exist_ok=True)
    return out


def save_pack_report(report: PackReport) -> Path:
    out = ensure_outreach_dir(report.prospect.slug)
    json_path = out / "pack_report.json"
    json_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return json_path


def save_email_draft(email: EmailDraft, slug: str) -> Path:
    out = ensure_outreach_dir(slug)
    email_path = out / "email_draft.json"
    email_path.write_text(email.model_dump_json(indent=2), encoding="utf-8")
    return email_path


def save_html_report(html_bytes: bytes, slug: str) -> Path:
    out = ensure_outreach_dir(slug)
    html_path = out / "report.html"
    html_path.write_bytes(html_bytes)
    return html_path


def write_index(slug: str, report_path: Path, html_path: Path, email_path: Path,
                status: str = "pending_review") -> Path:
    out = ensure_outreach_dir(slug)
    meta = {
        "slug": slug,
        "saved_at": datetime.utcnow().isoformat() + "Z",
        "pack_report": report_path.name,
        "report_html": html_path.name,
        "email_draft": email_path.name,
        "report_checksum": checksum_bytes(report_path.read_bytes()),
        "html_checksum": checksum_bytes(html_path.read_bytes()),
        "status": status
    }
    index_path = out / "index.json"
    index_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return index_path