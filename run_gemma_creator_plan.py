"""
Run Gemma/Gemini CreatorPlan
============================

Antigravity-style version:
1. Loads GOOGLE_API_KEY explicitly from C:\\WEB CASE STUDY\\.env
2. Reads creator_context.json
3. Uses google-genai chat.send_message_stream(), not generate_content()
4. Forces CreatorPlan JSON response
5. Validates with Pydantic
6. Writes creator_plan.json next to creator_context.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field, ConfigDict, ValidationError


# -----------------------------
# Console encoding
# -----------------------------
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# -----------------------------
# Hard-set project env path
# This is the important Antigravity-style fix.
# Do not let Python guess which .env to use.
# -----------------------------
PROJECT_ROOT = Path(r"C:\WEB CASE STUDY")
ENV_PATH = PROJECT_ROOT / ".env"


def load_project_env() -> None:
    if not ENV_PATH.exists():
        die(f".env not found at: {ENV_PATH}")

    load_dotenv(dotenv_path=ENV_PATH, override=True)

    if not os.getenv("GOOGLE_API_KEY"):
        die(f"GOOGLE_API_KEY is missing inside {ENV_PATH}")


# -----------------------------
# Pydantic output contract
# -----------------------------
class CreatorPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    new_file_name: str
    purpose: str

    source_files_used: list[str] = Field(default_factory=list)
    symbols_used: list[str] = Field(default_factory=list)
    imports_to_use: list[str] = Field(default_factory=list)
    ray_calls_allowed: list[str] = Field(default_factory=list)
    paths_to_parameterize: list[str] = Field(default_factory=list)
    classes_or_functions_to_reuse_as_patterns: list[str] = Field(default_factory=list)
    code_sections_to_generate: list[str] = Field(default_factory=list)
    tests_to_run: list[str] = Field(default_factory=list)
    rejection_risks: list[str] = Field(default_factory=list)


# -----------------------------
# Helpers
# -----------------------------
def die(message: str, code: int = 1) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def extract_json_object(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output.")

    return cleaned[start : end + 1]


def build_compact_context(context_data: dict[str, Any]) -> dict[str, Any]:
    verified_sources = []

    for src in context_data.get("verified_sources", []):
        verified_sources.append(
            {
                "source_file": src.get("source_file"),
                "normalized_path": src.get("normalized_path"),
                "symbol_name": src.get("symbol_name"),
                "imports": src.get("imports", []),
                "classes": src.get("classes", []),
                "functions": src.get("functions", []),
                "ray_calls": src.get("ray_calls", []),
                "lancedb_mentions": src.get("lancedb_mentions", []),
                "paths_found": src.get("paths_found", []),
                "relevance_reason": src.get("relevance_reason", ""),
            }
        )

    return {
        "run_id": context_data.get("run_id", ""),
        "query": context_data.get("query", ""),
        "target_file_kind": context_data.get("target_file_kind", ""),
        "selected_db": context_data.get("selected_db", ""),
        "selected_tables": context_data.get("selected_tables", []),
        "verified_sources": verified_sources,
        "rejected_sources": context_data.get("rejected_sources", []),
        "allowed_imports": context_data.get("allowed_imports", []),
        "allowed_ray_calls": context_data.get("allowed_ray_calls", []),
        "hardcoded_paths_to_parameterize": context_data.get(
            "hardcoded_paths_to_parameterize", []
        ),
        "creation_rules": context_data.get("creation_rules", []),
    }


def build_prompt(compact_context: dict[str, Any]) -> str:
    context_text = json.dumps(compact_context, indent=2, ensure_ascii=False)

    return f"""
You are a deterministic code planning model.

You receive a CreatorContext JSON object created by a verified Ray/Pydantic/RAG pipeline.

Return only valid JSON matching this exact schema:

{{
  "run_id": "string",
  "new_file_name": "string",
  "purpose": "string",
  "source_files_used": ["string"],
  "symbols_used": ["string"],
  "imports_to_use": ["string"],
  "ray_calls_allowed": ["string"],
  "paths_to_parameterize": ["string"],
  "classes_or_functions_to_reuse_as_patterns": ["string"],
  "code_sections_to_generate": ["string"],
  "tests_to_run": ["string"],
  "rejection_risks": ["string"]
}}

Rules:
- Return JSON only.
- Do not use markdown.
- Do not wrap JSON in code fences.
- Do not write Python code yet.
- Do not invent source files.
- Do not invent symbols.
- Do not invent imports.
- Use only verified_sources from CreatorContext.
- Use only allowed_imports from CreatorContext.
- Use only allowed_ray_calls from CreatorContext.
- Parameterize hardcoded paths.
- Do not create mock data.
- Do not create placeholder rows.
- Prefer a small, testable file over a giant system.

CreatorContext JSON:
{context_text}
""".strip()


def list_models(client: genai.Client) -> None:
    print("Available models visible to this API key:")

    for model in client.models.list():
        name = getattr(model, "name", "")
        supported = getattr(model, "supported_actions", None)
        print(f"- {name}" + (f" | supported_actions={supported}" if supported else ""))


def call_model_chat_stream(
    client: genai.Client,
    model_name: str,
    prompt: str,
) -> str:
    """
    Antigravity-style send.

    This avoids client.models.generate_content(), because that is exactly
    where your traceback is freezing like a haunted printer.
    """

    contents_to_send: list[Any] = []
    contents_to_send.append(prompt)

    print(f"\nInitializing stateful chat session with model: {model_name}")
    chat = client.chats.create(model=model_name)

    response_parts: list[str] = []

    print("\nStreaming model response...\n" + "=" * 70)

    try:
        response = chat.send_message_stream(contents_to_send)

        for chunk in response:
            text = chunk.text or ""
            print(text, end="", flush=True)
            response_parts.append(text)

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        raise

    except Exception as exc:
        raise RuntimeError(f"Chat stream failed: {type(exc).__name__}: {exc}") from exc

    print("\n" + "=" * 70)

    full_text = "".join(response_parts).strip()

    if not full_text:
        raise RuntimeError("Model returned empty text.")

    return full_text


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate CreatorPlan from CreatorContext.")

    parser.add_argument(
        "--context",
        required=False,
        default=r"C:\WEB CASE STUDY\code_truth_exports\code_truth_20260703_032702_76c969\creator_context.json",
        help="Path to creator_context.json",
    )

    parser.add_argument(
        "--model",
        required=False,
        default="gemini-2.5-flash",
        help="Exact AI Studio model name to call",
    )

    parser.add_argument(
        "--output",
        required=False,
        default=None,
        help="Optional output path for creator_plan.json. Defaults next to creator_context.json.",
    )

    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List models visible to your API key and exit.",
    )

    parser.add_argument(
        "--tiny-test",
        action="store_true",
        help="Run a tiny test prompt against the selected model and exit.",
    )

    args = parser.parse_args()

    load_project_env()

    # Explicit key wiring.
    # This makes it use the same GOOGLE_API_KEY from C:\\WEB CASE STUDY\\.env.
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    if args.list_models:
        list_models(client)
        return

    if args.tiny_test:
        text = call_model_chat_stream(
            client=client,
            model_name=args.model,
            prompt="Return exactly this text: model works",
        )
        print("\nTINY TEST RESULT:")
        print(text)
        return

    context_path = Path(args.context)

    if not context_path.exists():
        die(f"creator_context.json not found: {context_path}")

    output_path = Path(args.output) if args.output else context_path.parent / "creator_plan.json"
    failed_raw_path = output_path.with_name("creator_plan_failed_raw.txt")

    print(f"USING ENV: {ENV_PATH}")
    print(f"USING MODEL: {args.model}")
    print(f"READING CONTEXT: {context_path}")
    print(f"WRITING PLAN: {output_path}")

    context_data = json.loads(context_path.read_text(encoding="utf-8", errors="replace"))
    compact_context = build_compact_context(context_data)

    print(f"RUN ID: {compact_context.get('run_id')}")
    print(f"VERIFIED SOURCES: {len(compact_context.get('verified_sources', []))}")

    prompt = build_prompt(compact_context)

    raw_output = call_model_chat_stream(
        client=client,
        model_name=args.model,
        prompt=prompt,
    )

    print("\n--- RAW MODEL OUTPUT ---\n")
    print(raw_output)
    print("\n--- END RAW MODEL OUTPUT ---\n")

    try:
        json_text = extract_json_object(raw_output)
        plan = CreatorPlan.model_validate_json(json_text)

    except (ValueError, ValidationError) as exc:
        failed_raw_path.write_text(raw_output, encoding="utf-8", errors="replace")
        print(f"FAILED RAW OUTPUT WRITTEN: {failed_raw_path}")
        raise

    output_path.write_text(
        plan.model_dump_json(indent=2),
        encoding="utf-8",
        errors="replace",
    )

    print("\nVALIDATED CREATOR PLAN WRITTEN:")
    print(output_path)
    print(plan.model_dump_json(indent=2))


if __name__ == "__main__":
    main()