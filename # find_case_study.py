# find_case_study.py
#
# Scans:
#     "C:\web case study"
#
# Uses:
#   - ripgrep (rg) when available for fast native text search
#   - Python ast for Python source structure
#   - optional clang AST JSON for C/C++
#   - optional LM Studio at http://127.0.0.1:1234/v1
#
# Examples:
#   python find_case_study.py
#   python find_case_study.py --query "Ray DuckDB ONNX"
#   python find_case_study.py --lmstudio
#   python find_case_study.py --clang
#   python find_case_study.py --query "write_file" --lmstudio
#
# Optional tools:
#   winget install BurntSushi.ripgrep.MSVC
#   clang must be available as "clang++"

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any


# IMPORTANT: the quoted Windows path is intentional.
ROOT = Path(r"C:\web case study")

OUTPUT_FILE = ROOT / "case_study_inventory.json"
SEARCH_OUTPUT_FILE = ROOT / "case_study_search.json"
LM_OUTPUT_FILE = ROOT / "case_study_lmstudio.json"

TEXT_EXTENSIONS = {
    ".py", ".pyw", ".js", ".jsx", ".ts", ".tsx",
    ".cpp", ".cc", ".cxx", ".c", ".h", ".hpp", ".hh",
    ".java", ".kt", ".rs", ".go", ".cs",
    ".sql", ".cmake", ".md", ".markdown", ".txt",
    ".json", ".yaml", ".yml", ".toml", ".xml",
    ".gradle", ".properties", ".sh", ".bat", ".ps1",
}

SKIP_DIRECTORIES = {
    ".git", ".hg", ".svn",
    "node_modules", "__pycache__",
    ".venv", "venv", "env",
    "dist", "build", "target",
    ".idea", ".vscode",
    ".pytest_cache", ".mypy_cache",
}

DEFAULT_TERMS = [
    "ray",
    "ray serve",
    "duckdb",
    "lance",
    "lancedb",
    "onnx",
    "onnxruntime",
    "forest",
    "ast",
    "lm studio",
    "monty",
    "write_file",
    "run_command",
    "embedding",
    "vector",
    "context",
    "preprocessor",
    "registerpreprocessor",
    "1234",
]


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def safe_read_text(path: Path, limit: int = 2_000_000) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            return f.read(limit)
    except Exception:
        return ""


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def should_skip(path: Path) -> bool:
    return any(part.lower() in SKIP_DIRECTORIES for part in path.parts)


def iter_files() -> list[Path]:
    files = []

    if not ROOT.exists():
        raise FileNotFoundError(f'Folder does not exist: "{ROOT}"')

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if should_skip(path):
            continue
        if path.suffix.lower() in TEXT_EXTENSIONS:
            files.append(path)

    return sorted(files)


def file_metadata(path: Path) -> dict[str, Any]:
    try:
        stat = path.stat()
        content = safe_read_text(path)
        return {
            "path": relative(path),
            "absolute_path": str(path),
            "extension": path.suffix.lower(),
            "bytes": stat.st_size,
            "modified": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ",
                time.gmtime(stat.st_mtime),
            ),
            "lines": content.count("\n") + (1 if content else 0),
            "characters_read": len(content),
        }
    except Exception as exc:
        return {
            "path": relative(path),
            "error": str(exc),
        }


def python_ast_summary(path: Path) -> dict[str, Any]:
    source = safe_read_text(path)

    result = {
        "path": relative(path),
        "language": "python",
        "imports": [],
        "classes": [],
        "functions": [],
        "async_functions": [],
        "calls": [],
        "errors": [],
    }

    if not source:
        return result

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        result["errors"].append({
            "type": "SyntaxError",
            "line": exc.lineno,
            "offset": exc.offset,
            "message": exc.msg,
        })
        return result

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                result["imports"].append(alias.name)

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                result["imports"].append(
                    f"{module}.{alias.name}".strip(".")
                )

        elif isinstance(node, ast.ClassDef):
            result["classes"].append({
                "name": node.name,
                "line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
            })

        elif isinstance(node, ast.FunctionDef):
            result["functions"].append({
                "name": node.name,
                "line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
                "async": False,
            })

        elif isinstance(node, ast.AsyncFunctionDef):
            result["async_functions"].append({
                "name": node.name,
                "line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
                "async": True,
            })

        elif isinstance(node, ast.Call):
            name = None

            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                parts = []
                current = node.func
                while isinstance(current, ast.Attribute):
                    parts.append(current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    parts.append(current.id)
                name = ".".join(reversed(parts))

            if name:
                result["calls"].append({
                    "name": name,
                    "line": getattr(node, "lineno", None),
                })

    result["imports"] = sorted(set(result["imports"]))
    result["calls"] = sorted(
        result["calls"],
        key=lambda item: (item["line"] or 0, item["name"]),
    )

    return result


def clang_ast_summary(path: Path) -> dict[str, Any]:
    clang = shutil.which("clang++")

    result = {
        "path": relative(path),
        "language": "cpp",
        "clang_available": bool(clang),
        "classes": [],
        "functions": [],
        "records": [],
        "errors": [],
    }

    if not clang:
        result["errors"].append("clang++ not found on PATH")
        return result

    command = [
        clang,
        "-Xclang",
        "-ast-dump=json",
        "-fsyntax-only",
        "-std=c++17",
        str(path),
    ]

    try:
        proc = subprocess.run(
            command,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except Exception as exc:
        result["errors"].append(str(exc))
        return result

    if proc.returncode != 0 and not proc.stdout.strip():
        result["errors"].append(proc.stderr[-4000:])
        return result

    try:
        tree = json.loads(proc.stdout)
    except json.JSONDecodeError:
        result["errors"].append(
            "clang returned non-JSON output; compile flags may be required"
        )
        return result

    def walk(node: Any) -> None:
        if not isinstance(node, dict):
            return

        kind = node.get("kind")
        name = node.get("name")

        if kind in {"CXXRecordDecl", "RecordDecl", "ClassTemplateDecl"}:
            if name:
                result["records"].append({
                    "name": name,
                    "kind": kind,
                    "line": (
                        node.get("loc", {}).get("line")
                        if isinstance(node.get("loc"), dict)
                        else None
                    ),
                })

        elif kind in {
            "FunctionDecl",
            "CXXMethodDecl",
            "CXXConstructorDecl",
            "CXXDestructorDecl",
        }:
            if name:
                result["functions"].append({
                    "name": name,
                    "kind": kind,
                    "line": (
                        node.get("loc", {}).get("line")
                        if isinstance(node.get("loc"), dict)
                        else None
                    ),
                })

        for child in node.get("inner", []) or []:
            walk(child)

    walk(tree)

    result["records"] = dedupe_dicts(result["records"])
    result["functions"] = dedupe_dicts(result["functions"])

    return result


def dedupe_dicts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    output = []

    for item in items:
        key = json.dumps(item, sort_keys=True)
        if key not in seen:
            seen.add(key)
            output.append(item)

    return output


def run_ripgrep(query: str) -> list[dict[str, Any]]:
    rg = shutil.which("rg")

    if not rg:
        return []

    command = [
        rg,
        "--json",
        "--hidden",
        "--no-ignore",
        "-i",
        "--glob", "!**/.git/**",
        "--glob", "!**/node_modules/**",
        "--glob", "!**/__pycache__/**",
        query,
        str(ROOT),
    ]

    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
    except Exception:
        return []

    results = []

    for line in proc.stdout.splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue

        if item.get("type") != "match":
            continue

        data = item.get("data", {})
        path_data = data.get("path", {})
        text_data = data.get("lines", {})
        line_number = data.get("line_number")

        path_text = path_data.get("text", "")
        line_text = text_data.get("text", "").rstrip("\n")

        if path_text:
            results.append({
                "path": relative(Path(path_text)),
                "line": line_number,
                "text": line_text[:1000],
            })

    return results


def fallback_search(query: str, files: list[Path]) -> list[dict[str, Any]]:
    results = []
    pattern = re.compile(re.escape(query), re.IGNORECASE)

    for path in files:
        source = safe_read_text(path)

        for line_number, line in enumerate(source.splitlines(), 1):
            if pattern.search(line):
                results.append({
                    "path": relative(path),
                    "line": line_number,
                    "text": line[:1000],
                })

    return results


def build_inventory(files: list[Path], use_clang: bool) -> dict[str, Any]:
    inventory = {
        "generated_at": now(),
        "root": str(ROOT),
        "file_count": len(files),
        "extensions": dict(
            Counter(path.suffix.lower() or "<no_extension>" for path in files)
        ),
        "files": [],
        "python_ast": [],
        "cpp_ast": [],
    }

    for path in files:
        inventory["files"].append(file_metadata(path))

        if path.suffix.lower() in {".py", ".pyw"}:
            inventory["python_ast"].append(python_ast_summary(path))

        elif use_clang and path.suffix.lower() in {
            ".cpp", ".cc", ".cxx", ".c", ".h", ".hpp", ".hh"
        }:
            inventory["cpp_ast"].append(clang_ast_summary(path))

    return inventory


def make_lmstudio_prompt(
    query: str,
    inventory: dict[str, Any],
    search_results: list[dict[str, Any]],
) -> str:
    compact_inventory = {
        "root": inventory["root"],
        "file_count": inventory["file_count"],
        "extensions": inventory["extensions"],
        "python_ast": inventory["python_ast"][:100],
        "cpp_ast": inventory["cpp_ast"][:100],
    }

    compact_results = search_results[:200]

    return f"""
You are analyzing a local code workspace.

Workspace:
{inventory["root"]}

User request:
{query}

Inventory:
{json.dumps(compact_inventory, indent=2)}

Search results:
{json.dumps(compact_results, indent=2)}

Return JSON with exactly these top-level keys:
{{
  "relevant_files": [],
  "relevant_symbols": [],
  "architecture": [],
  "missing_connections": [],
  "recommended_next_steps": [],
  "confidence": 0.0
}}

Focus on:
- LM Studio JavaScript integration
- Ray or Ray Serve communication
- Forest/ONNX inference
- DuckDB and Lance integration
- AST-aware code retrieval
- Monty file writing and command execution
- the smallest useful code context
""".strip()


def call_lmstudio(prompt: str, model: str | None) -> dict[str, Any]:
    try:
        import urllib.request
        import urllib.error
    except ImportError:
        return {"error": "urllib unavailable"}

    endpoint = "http://127.0.0.1:1234/v1/chat/completions"

    payload = {
        "model": model or "local-model",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You analyze local source repositories. "
                    "Return valid JSON only."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.1,
        "stream": False,
    }

    body = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = response.read().decode("utf-8", errors="replace")
            parsed = json.loads(raw)

        choices = parsed.get("choices", [])
        if not choices:
            return {
                "raw_response": parsed,
                "error": "No choices returned by LM Studio",
            }

        content = choices[0].get("message", {}).get("content", "")
        result = {
            "endpoint": endpoint,
            "model": model or "local-model",
            "content": content,
        }

        try:
            result["json"] = json.loads(content)
        except json.JSONDecodeError:
            result["json_error"] = "LM response was not valid JSON"

        return result

    except urllib.error.HTTPError as exc:
        return {
            "error": f"LM Studio HTTP error {exc.code}",
            "details": exc.read().decode("utf-8", errors="replace"),
        }

    except Exception as exc:
        return {
            "error": str(exc),
            "endpoint": endpoint,
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inventory and search C:\\web case study"
    )

    parser.add_argument(
        "--query",
        default=" ".join(DEFAULT_TERMS),
        help="Text or terms to search for",
    )

    parser.add_argument(
        "--lmstudio",
        action="store_true",
        help="Send inventory and search results to LM Studio on port 1234",
    )

    parser.add_argument(
        "--model",
        default=None,
        help="LM Studio model identifier; omit to use local-model",
    )

    parser.add_argument(
        "--clang",
        action="store_true",
        help="Run clang++ JSON AST extraction for C/C++ files",
    )

    parser.add_argument(
        "--no-search",
        action="store_true",
        help="Only build the inventory and AST report",
    )

    args = parser.parse_args()

    print(f'Root: "{ROOT}"')

    if not ROOT.exists():
        print(
            f'\nERROR: The folder does not exist:\n"{ROOT}"',
            file=sys.stderr,
        )
        return 1

    files = iter_files()
    print(f"Files found: {len(files)}")

    inventory = build_inventory(files, use_clang=args.clang)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)

    print(f'Inventory written to "{OUTPUT_FILE}"')

    search_results = []

    if not args.no_search:
        rg_available = shutil.which("rg") is not None

        if rg_available:
            print("Search engine: ripgrep")
            search_results = run_ripgrep(args.query)
        else:
            print("Search engine: Python fallback")
            search_results = fallback_search(args.query, files)

        search_report = {
            "generated_at": now(),
            "root": str(ROOT),
            "query": args.query,
            "match_count": len(search_results),
            "matches": search_results,
        }

        with SEARCH_OUTPUT_FILE.open("w", encoding="utf-8") as f:
            json.dump(search_report, f, indent=2, ensure_ascii=False)

        print(f"Matches found: {len(search_results)}")
        print(f'Search report written to "{SEARCH_OUTPUT_FILE}"')

    if args.lmstudio:
        print("Sending report to LM Studio at http://127.0.0.1:1234")

        prompt = make_lmstudio_prompt(
            query=args.query,
            inventory=inventory,
            search_results=search_results,
        )

        lm_result = call_lmstudio(
            prompt=prompt,
            model=args.model,
        )

        with LM_OUTPUT_FILE.open("w", encoding="utf-8") as f:
            json.dump(lm_result, f, indent=2, ensure_ascii=False)

        print(f'LM Studio report written to "{LM_OUTPUT_FILE}"')

        if "error" in lm_result:
            print(f'LM Studio error: {lm_result["error"]}')
        else:
            print("LM Studio analysis completed.")

    print("\nTop matching files:")

    counts = Counter(item["path"] for item in search_results)

    for path, count in counts.most_common(30):
        print(f"{count:4}  {path}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
