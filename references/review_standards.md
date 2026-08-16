# Review Standards: Sonic Core Pipeline

## 1. The Architect (Logic & DSP)
- [ ] Mathematical correctness of VAE implementation (KL divergence, reparameterization).
- [ ] DSP feature consistency (RMS dB conversion, normalization).
- [ ] Mastering head output range validation (gain, ratio, threshold).
- [ ] Latency/Computation efficiency of the `generate` method.

## 2. The Auditor (Telemetry & Testing)
- [ ] Data ingestion robustness (handling missing columns in LanceDB/DuckDB).
- [ ] Training loop stability (KL warmup, learning rate decay).
- [ ] Log/Artifact persistence (saving .pt weights, loss curves).
- [ ] Reproducibility (seed management, data shuffling).

## 3. The Critic (Destructive Review)
- [ ] Identification of hardcoded paths (e.g., C:\STUDIES_BACKUP\...).
- [ ] Memory bottleneck analysis (tensor sizes, batching).
- [ ] Edge case failures (empty dataframes, NaN values in DSP).
- [ ] Predictability of generated samples (diversity check).

## 4. The Editor (Sales & Narrative)
- [ ] Professionalism of the Generation Demo output.
- [ ] Clarity of the training curve visualizations.
- [ ] Value mapping: How does this VAE improve mastering over baselines?

## 5. The Reviewer (Validation & Compliance)
- [ ] Synthesis of all role feedback.
- [ ] Final "Ready for Deployment" or "Critical Discrepancies" status.
- [ ] Verification of `ruff` / `pytest` (if applicable).
