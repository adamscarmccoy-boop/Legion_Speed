# Technical Review Council: Review Standards

This protocol ensures all project assets are production-ready.

## 1. The Architect (Logic & DSP)
- [ ] Are buffers sized for <20ms latency?
- [ ] Is signal conditioning correct?
- [ ] Is feature extraction deterministic (does it use the same hop_length)?
- [ ] Are class names and internal logic generic and production-ready?

## 2. The Auditor (Telemetry & Testing)
- [ ] Do `pytest` tests pass with 100% success?
- [ ] Are logs persisting to `logs/engine_YYYYMMDD.log`?
- [ ] Is there proper error-handling for buffer mismatches?

## 3. The Critic (Destructive Review)
- [ ] Where is the biggest latency bottleneck?
- [ ] What is the most likely failure point (e.g., input noise, file missing)?
- [ ] Are there any hardcoded values that should be configurable?

## 4. The Editor (Sales & Narrative)
- [ ] Does the `README.md` focus on Business Value/ROI?
- [ ] Are the notebook visualizations clear?
- [ ] Is the tone authoritative and consultant-led?

## 5. The Reviewer (Validation & Compliance)
- [ ] Are all agent outputs written to `logs/council/{role}_feedback.txt`?
- [ ] **Validation Step:** Run `pytest` and `ruff`. If fail, send to Architect/Auditor.
- [ ] Does the final proposal align with "Acoustic DNA" branding?

---
## The Reviewer's Validation Loop
The Reviewer is the *only* agent empowered to finalize.
1. Receives feedback from Council.
2. Runs: `pytest FretFlow-Audio-Engine/tests/` and `ruff check FretFlow-Audio-Engine/`.
3. If failures found:
    - Writes `logs/council/validation_error.log`.
    - Returns to Architect/Auditor with the error report.
4. If pass:
    - Writes `logs/council/final_approval.txt`.
    - Signals final package readiness.
