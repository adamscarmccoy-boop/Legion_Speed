#!/usr/bin/env python3
"""
=============================================================================
⚡ SOVEREIGN LANGSMITH FEEDBACK LOOP & EVALUATION HARNESS
=============================================================================
Pulls run traces, scores compliance extraction fidelity, logs error diffs,
and auto-synthesizes corrective few-shot context into DuckDB.
=============================================================================
"""

import os
import sys
import json
import duckdb
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# LangSmith Client
from langsmith import Client
from langsmith.schemas import Run

# Ensure local environment paths
WORKSPACE_ROOT = r"C:\WEB CASE STUDY"
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

for env_path in [r"C:\WEB CASE STUDY\.env", r"C:\STUDIES_BACKUP\.env"]:
    if os.path.exists(env_path):
        load_dotenv(env_path)

DUCKDB_PATH = os.path.join(WORKSPACE_ROOT, "web_intel_sonicdb.duckdb")
PROJECT_NAME = os.getenv("LANGCHAIN_PROJECT", "rfp-compliance-engine")

# -----------------------------------------------------------------------------
# 1. EVALUATION RULES & SCORERS
# -----------------------------------------------------------------------------
def evaluate_run_fidelity(run: Run) -> Dict[str, Any]:
    """
    Deterministically evaluates extraction outputs without needing a judge model.
    Checks schema integrity, missing mandatory flags, and empty critical fields.
    """
    score = 1.0
    reasons = []

    if run.error:
        return {"score": 0.0, "status": "EXECUTION_ERROR", "feedback": run.error}

    output = run.outputs
    if not output:
        return {"score": 0.0, "status": "EMPTY_OUTPUT", "feedback": "No output payload returned"}

    # Handle string-wrapped JSON or dict
    if isinstance(output, str):
        try:
            output = json.loads(output)
        except Exception:
            return {"score": 0.1, "status": "INVALID_JSON", "feedback": "Output failed JSON decoding"}

    # 1. Check Root Metadata
    project_title = output.get("project_title") or output.get("title")
    if not project_title or project_title.strip() in ["N/A", "Unknown", ""]:
        score -= 0.25
        reasons.append("Missing project_title")

    # 2. Check Compliance Matrix
    clauses = output.get("compliance_matrix", [])
    if not clauses or len(clauses) == 0:
        score -= 0.50
        reasons.append("Zero compliance clauses extracted")
    else:
        mandatory_count = sum(1 for c in clauses if c.get("requirement_type", "").upper() == "MANDATORY")
        if mandatory_count == 0:
            score -= 0.25
            reasons.append("No mandatory (SHALL/MUST) clauses flagged")

    score = max(0.0, score)
    status = "PASSED" if score >= 0.85 else "NEEDS_CORRECTION"

    return {
        "score": round(score, 2),
        "status": status,
        "feedback": "; ".join(reasons) if reasons else "All schema invariants satisfied"
    }

# -----------------------------------------------------------------------------
# 2. FEEDBACK COLLECTOR & TRACE MINER
# -----------------------------------------------------------------------------
class SovereignFeedbackLoop:
    def __init__(self, project_name: str = PROJECT_NAME):
        self.client = Client()
        self.project_name = project_name
        self.conn = duckdb.connect(DUCKDB_PATH)
        self._init_lakehouse_tables()

    def _init_lakehouse_tables(self):
        """Initializes telemetry and feedback storage in DuckDB."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS eval_feedback_telemetry (
                run_id VARCHAR PRIMARY KEY,
                timestamp TIMESTAMP,
                model_name VARCHAR,
                latency_ms DOUBLE,
                fidelity_score DOUBLE,
                status VARCHAR,
                feedback_notes VARCHAR,
                input_snippet VARCHAR,
                output_payload JSON
            );
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS eval_prompt_corrections (
                correction_id VARCHAR PRIMARY KEY,
                created_at TIMESTAMP,
                error_category VARCHAR,
                failing_input VARCHAR,
                suggested_rule VARCHAR
            );
        """)

    def process_recent_runs(self, hours_lookback: int = 24) -> List[Dict[str, Any]]:
        """Scans recent LangSmith project runs, scores them, and logs evaluations."""
        start_time = datetime.utcnow() - timedelta(hours=hours_lookback)
        runs = list(self.client.list_runs(
            project_name=self.project_name,
            start_time=start_time,
            execution_order=1
        ))

        results = []
        print(f"🔍 [FEEDBACK LOOP] Found {len(runs)} runs in project '{self.project_name}' over the last {hours_lookback}h.")

        for r in runs:
            eval_res = evaluate_run_fidelity(r)
            
            # Post feedback directly back to LangSmith dashboard
            try:
                self.client.create_feedback(
                    run_id=r.id,
                    key="schema_fidelity",
                    score=eval_res["score"],
                    comment=eval_res["feedback"]
                )
            except Exception as e:
                pass  # Feedback might already exist

            # Extract latency safely
            latency = 0.0
            if r.start_time and r.end_time:
                latency = (r.end_time - r.start_time).total_seconds() * 1000.0

            input_text = ""
            if r.inputs:
                input_text = str(r.inputs.get("rfp_text", r.inputs))[:500]

            # Ingest into DuckDB
            self.conn.execute("""
                INSERT INTO eval_feedback_telemetry VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (run_id) DO UPDATE SET
                    fidelity_score = EXCLUDED.fidelity_score,
                    status = EXCLUDED.status,
                    feedback_notes = EXCLUDED.feedback_notes;
            """, [
                str(r.id),
                r.start_time or datetime.utcnow(),
                r.extra.get("metadata", {}).get("ls_model_name", "gemini-2.5-flash") if r.extra else "gemini-2.5-flash",
                latency,
                eval_res["score"],
                eval_res["status"],
                eval_res["feedback"],
                input_text,
                json.dumps(r.outputs or {})
            ])

            if eval_res["status"] == "NEEDS_CORRECTION":
                self._generate_correction_patch(str(r.id), input_text, eval_res["feedback"])

            results.append({
                "run_id": str(r.id),
                "score": eval_res["score"],
                "status": eval_res["status"],
                "latency_ms": latency,
                "notes": eval_res["feedback"]
            })

        return results

    def _generate_correction_patch(self, run_id: str, failing_input: str, error_reason: str):
        """Creates a targeted few-shot correction prompt constraint based on failure mode."""
        correction_id = f"PATCH_{run_id[:8]}"
        rule = f"MANDATORY INVARIANT: Resolve error '{error_reason}'. Explicitly flag all SHALL/MUST verbs as MANDATORY."

        self.conn.execute("""
            INSERT INTO eval_prompt_corrections VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (correction_id) DO NOTHING;
        """, [
            correction_id,
            datetime.utcnow(),
            error_reason,
            failing_input[:200],
            rule
        ])
        print(f"⚠️ [AUTO-PATCH GENERATED] Added patch {correction_id} to DuckDB prompt corrections.")

    def export_active_prompt_patches(self) -> str:
        """Retrieves active auto-generated prompt rules to inject into your next run."""
        rows = self.conn.execute("""
            SELECT DISTINCT suggested_rule FROM eval_prompt_corrections
            ORDER BY created_at DESC LIMIT 5;
        """).fetchall()

        if not rows:
            return ""

        patch_text = "\n=== RECENT MODEL CORRECTION INVARIANTS (From LangSmith Telemetry) ===\n"
        for r in rows:
            patch_text += f"- {r[0]}\n"
        return patch_text

    def close(self):
        self.conn.close()

# -----------------------------------------------------------------------------
# 3. CLI DISPATCHER
# -----------------------------------------------------------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Sovereign LangSmith Evaluation & Feedback Engine")
    parser.add_argument("--lookback", type=int, default=24, help="Hours to look back in LangSmith run history")
    parser.add_argument("--show-patches", action="store_true", help="Display active dynamic prompt patches")
    args = parser.parse_args()

    print("=" * 75)
    print(" ⚡ SOVEREIGN LANGSMITH FEEDBACK LOOP & EVALUATION HARNESS")
    print("=" * 75)

    loop = SovereignFeedbackLoop()
    
    if args.show_patches:
        patches = loop.export_active_prompt_patches()
        print(patches if patches else "No active prompt patches currently needed.")
        loop.close()
        return

    evals = loop.process_recent_runs(hours_lookback=args.lookback)
    
    print("\n" + "=" * 75)
    print(f"{'RUN ID':<36} | {'SCORE':<6} | {'STATUS':<16} | {'LATENCY (ms)'}")
    print("-" * 75)
    for e in evals:
        print(f"{e['run_id']:<36} | {e['score']:<6} | {e['status']:<16} | {e['latency_ms']:.1f}ms")
    print("=" * 75)
    
    loop.close()

if __name__ == "__main__":
    main()