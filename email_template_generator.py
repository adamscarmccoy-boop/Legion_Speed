"""Email draft generator — uses PackReport fields, no LLM."""

from textwrap import dedent
from outreach_schemas import PackReport, EmailDraft


def generate_email_draft(report: PackReport, to_email: str | None = None) -> EmailDraft:
    pct = report.alignment_pass_rate * 100
    style = report.forest_verdict.top_style_match
    conf = report.forest_verdict.style_confidence

    subject = f"I analyzed {report.pack_name} in 5s — {pct:.0f}% alignment to {style}"

    body = dedent(f"""\
    Hi,

    I ran a quick deterministic audit of "{report.pack_name}" against our commercial reference baseline (Chris Lake "Somebody (2024)" — 66 segments).

    Highlights:
    - Alignment pass rate: {pct:.1f}%
    - Top style match: {style} (confidence {conf:.2f})
    - Key findings: {', '.join(report.key_findings[:3])}

    I've attached a short one-page report with the full breakdown. Want me to run the same audit on your latest release or full catalog?

    Best,
    Legion Intelligence
    """)

    cta = "Reply to request a full audit"
    return EmailDraft(
        subject=subject,
        body=body,
        cta=cta,
        send_to=to_email or report.prospect.contact_email or "",
    )