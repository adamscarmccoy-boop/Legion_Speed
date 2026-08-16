---
name: technical-review-council
description: Multi-agent technical review council. Use when you need a rigorous, multi-agent audit (Architect, Auditor, Critic, Editor, Reviewer) for any codebase to ensure technical integrity, performance, and professional presentation.
---

# Technical Review Council Skill

## Overview
A comprehensive framework for conducting multi‑agent code audits. The council consists of five specialized agents—Architect, Auditor, Critic, Editor, and Reviewer—each focusing on distinct quality dimensions such as design correctness, security posture, maintainability, style compliance, and overall professionalism.

## Prerequisites
- Python 3.9+ installed on the host system.
- `pip install -r requirements.txt` where `requirements.txt` includes `pytest`, `ruff`, `pylint`, and any project‑specific dependencies.
- A `references/review_standards.md` file containing role‑specific checklists (see example in the repository).

## Setup
1. **Clone the repository** and navigate to the project root.
2. **Create the standards document**: copy `references/template_review_standards.md` to `references/review_standards.md` and fill in the required checklists.
3. **Install the council package** in editable mode: `pip install -e .`.
4. **Run the orchestrator**: `python -m council_orchestrator --project-root .`

## Workflow
1. **Orchestration**: The orchestrator loads the standards, instantiates the five agents, and dispatches review tasks.
2. **Execution**: Each agent runs its specific checks (e.g., Architect validates architecture diagrams, Auditor scans for security vulnerabilities, etc.).
3. **Aggregation**: Results are merged into a single JSON report placed under `logs/council/`.
4. **Validation**: Apply `pytest` and `ruff` to enforce style and test coverage; failures block further processing.
5. **Feedback Loop**: Reviewers comment on findings; developers can acknowledge or address issues.

## Advanced Usage
- **Custom Agent Registration**: Extend `council.agents.base.Agent` to create domain‑specific reviewers.
- **Configuration File**: Provide `council/config.yaml` to tweak thresholds, enable/disable checks, or specify output formats.
- **Parallel Execution**: Use `concurrent.futures` to run agents in parallel for large codebases.
- **CI Integration**: Add a GitHub Action that triggers the council on every pull request.

## Example Checklists
- **Architect Checklist**: Verify diagram consistency, technology stack alignment, and scalability assumptions.
- **Auditor Checklist**: Scan for hardcoded secrets, insecure API usage, and deprecated libraries.
- **Critic Checklist**: Identify performance bottlenecks, memory leaks, and race conditions.
- **Editor Checklist**: Enforce code style, naming conventions, and documentation completeness.
- **Reviewer Checklist**: Validate test coverage, CI pipeline status, and deployment readiness.

## Comprehensive Documentation

### Advanced Configuration
- **Configuration File**: Create `council/config.yaml` to toggle checks, set severity thresholds, and define custom rules.
- **Custom Agent Registration**: Extend `council.agents.base.Agent` to add domain‑specific reviewers (e.g., `DatabaseAgent`, `FrontendAgent`).
- **Parallel Execution**: Use `concurrent.futures` to run agents concurrently for large codebases.
- **CI Integration**: Add a GitHub Action that triggers the council on every pull request.

### Testing & Validation
- **Unit Tests**: All new agents and checklists must have corresponding unit tests under `tests/`.
- **Test Execution**: Run `pytest -q` to ensure all tests pass before merging.
- **Coverage Reports**: Generate coverage reports with `pytest --cov` to maintain high test coverage.

### Contribution Workflow
1. **Fork** the repository and create a feature branch.
2. **Implement** new agents, checklists, or configuration options.
3. **Write Tests**: Add appropriate unit tests to validate new functionality.
4. **Run Test Suite**: Execute `pytest -q` to confirm all tests pass.
5. **Submit** a pull request with a concise description of the enhancement.

### License
This project is licensed under the MIT License. See `LICENSE` for the full text.

---

See `references/review_standards.md` for detailed role‑specific checklists.
