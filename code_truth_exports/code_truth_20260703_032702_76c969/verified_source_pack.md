# Verified Source Pack: code_truth_20260703_032702_76c969

Created: 2026-07-03T03:27:26.287782

## Intent

Retrieve and verify Ray actor, LanceDB, and code-truth source files using local RAG.

## Truth Summary

- **selected_db**: `C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag`
- **selected_tables**: `['chris_lake_speed_test', 'chris_lake_web_intel', 'mined_code_vectors', 'mined_documentation_vectors']`
- **rag_results**: `1`
- **rag_code_hits**: `3`
- **path_proofs**: `3`
- **usage_proofs**: `3`
- **errors**: `0`
- **verified_files**: `3`

## Verified Files

### OK: `C:/WEB CASE STUDY/mix_audit_agent.py`

- symbol: `__init__`
- exists: `True`
- readable: `True`
- contains_symbol: `True`
- size_bytes: `13835`
- error: `None`

### OK: `C:/WEB CASE STUDY/legion_sonic_engine_orchestrator.py`

- symbol: `boot_swarm`
- exists: `True`
- readable: `True`
- contains_symbol: `True`
- size_bytes: `5406`
- error: `None`

### OK: `C:/WEB CASE STUDY/mix_audit_agent.py`

- symbol: `RegistryClient`
- exists: `True`
- readable: `True`
- contains_symbol: `True`
- size_bytes: `13835`
- error: `None`


## Usage Proofs

### `C:/WEB CASE STUDY/mix_audit_agent.py`

- parsed: `True`
- imports: `os, json, subprocess, librosa, numpy, time, ray, pandas, pydantic, typing`
- classes: `StemAudit, AuditReportData, RegistryClient`
- functions: `extract_stem_features_ray, run_mix_audit_agent, __init__, get_table, coerce_value`
- ray_calls: `ray.is_initialized, ray.init, ray.remote, ray.get_actor, ray.get, ray.kill`
- lancedb_mentions: ``
- paths_found: `C:\WEB CASE STUDY\demucs_bridge.py, C:\Users\adams\Downloads, C:\WEB CASE STUDY\Acoustic-DNA-Audio-Engine\assets, C:\STUDIES_BACKUP\separated_stems, c:\STUDIES_BACKUP\.venv_fresh\Scripts\python.exe, C:\Users\adams\Downloads\putting in the work.wav`
- risk_flags: ``
- error: `None`

### `C:/WEB CASE STUDY/legion_sonic_engine_orchestrator.py`

- parsed: `True`
- imports: `os, sys, asyncio, ray, json, typing, datetime, schemas, legion_mcp_client, intelligence_bridge, legion_sonic_engine_actors, subprocess`
- classes: `LegionOrchestrator`
- functions: `__init__, boot_swarm, run_turn, _save_state, trigger_antigravity_audit, shutdown`
- ray_calls: `ray.is_initialized, ray.init, ray.get, ray.shutdown`
- lancedb_mentions: ``
- paths_found: `C:\WEB CASE STUDY\data\chris_lake_fused_raw.json, C:\WEB CASE STUDY\simulation_log.json`
- risk_flags: ``
- error: `None`

### `C:/WEB CASE STUDY/mix_audit_agent.py`

- parsed: `True`
- imports: `os, json, subprocess, librosa, numpy, time, ray, pandas, pydantic, typing`
- classes: `StemAudit, AuditReportData, RegistryClient`
- functions: `extract_stem_features_ray, run_mix_audit_agent, __init__, get_table, coerce_value`
- ray_calls: `ray.is_initialized, ray.init, ray.remote, ray.get_actor, ray.get, ray.kill`
- lancedb_mentions: ``
- paths_found: `C:\WEB CASE STUDY\demucs_bridge.py, C:\Users\adams\Downloads, C:\WEB CASE STUDY\Acoustic-DNA-Audio-Engine\assets, C:\STUDIES_BACKUP\separated_stems, c:\STUDIES_BACKUP\.venv_fresh\Scripts\python.exe, C:\Users\adams\Downloads\putting in the work.wav`
- risk_flags: ``
- error: `None`

