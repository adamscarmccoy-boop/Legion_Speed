"""Audit what's actually wired up vs what's dead code."""
import os, re, json
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(r"C:\WEB CASE STUDY")

py_files = []
for p in ROOT.rglob("*.py"):
    parts = set(p.parts)
    if parts & {"__pycache__", ".venv", "venv", "node_modules", ".git", ".pytest_cache"}:
        continue
    py_files.append(p)

print(f"Total .py files in C:\\WEB CASE STUDY: {len(py_files):,}\n")

# Track usage
imports_of = defaultdict(set)
ray_files = set()
sched_files = {}
entry_points = []
cron_files = set()
main_loop_files = set()
subprocess_spawners = set()

# Heuristics
SCHED_RE = re.compile(r"apscheduler|AsyncIOScheduler|BackgroundScheduler|BlockingScheduler|cron|schedule\.|CronTrigger", re.I)
ENTRY_RE = re.compile(r"if\s+__name__\s*==\s*['\"]__main__['\"]")
RAY_RE = re.compile(r"@ray\.remote|\bray\.init\(|\bray\.get\(|\bray\.put\(|\.remote\(")
LOOP_RE = re.compile(r"while\s+True|while\s+not\s+")
SUBPROC_RE = re.compile(r"subprocess\.(?:run|Popen|call|check_output|check_call)")

for p in py_files:
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    sp = str(p)
    if RAY_RE.search(t):
        ray_files.add(sp)
    if SCHED_RE.search(t):
        sched_files[sp] = "scheduler/cron"
    if ENTRY_RE.search(t):
        entry_points.append(sp)
    if SUBPROC_RE.search(t):
        subprocess_spawners.add(sp)
    if LOOP_RE.search(t):
        main_loop_files.add(sp)

    # imports
    for m in re.finditer(r"^(?:from\s+([\w.]+)|import\s+([\w.]+))", t, re.M):
        mod = (m.group(1) or m.group(2)).split(".")[0]
        if mod and mod != "__future__":
            imports_of[mod].add(sp)

print("=" * 78)
print("FILES THAT USE RAY (currently the only 'parallel runner' you have)")
print("=" * 78)
for f in sorted(ray_files):
    print(f"  {f}")
print(f"\n  Total: {len(ray_files)}")

print()
print("=" * 78)
print("FILES WITH SCHEDULING / CRON / ASYNCIO LOOPS")
print("=" * 78)
for f, kind in sched_files.items():
    print(f"  [{kind}]  {f}")
for f in main_loop_files:
    if f not in sched_files:
        print(f"  [while-True]  {f}")
for f in subprocess_spawners:
    print(f"  [subprocess]  {f}")
print(f"\n  Total scheduled/loops: {len(sched_files) + len(main_loop_files)}")

print()
print("=" * 78)
print("ENTRY POINTS (if __name__ == '__main__')")
print("=" * 78)
for f in sorted(entry_points):
    print(f"  {f}")
print(f"\n  Total entry points: {len(entry_points)}")
