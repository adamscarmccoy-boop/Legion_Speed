---
name: technical-review-council
description: Multi-agent technical review council. Use when you need a rigorous, multi-agent audit (Architect, Auditor, Critic, Editor, Reviewer) for any codebase to ensure technical integrity, performance, and professional presentation.
---

# Technical Review Council Skill

## Usage

To trigger the council review on your current project:
1. Ensure a `references/review_standards.md` exists in your project.
2. Run the council orchestration workflow to dispatch review agents.
3. Validate with the Reviewer loop (`pytest` + `ruff`).
4. View feedback in `logs/council/`.

See `references/review_standards.md` for role-specific checklists.
