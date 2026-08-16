"""For each Ray script: is it a long-running loop, a one-shot, or waiting on API?"""
import os, re
from pathlib import Path
from collections import defaultdict

# ==============================================================================
# SOVEREIGN LIFE-CYCLE STABILIZER (AUTO-INJECTED)
# Prevents dangling stdout/stdio pipes and GCS registry locks on Windows exit
# ==============================================================================
import atexit
import signal

def clean_exit_handler(*args, **kwargs):
    import sys
    sys.stderr.write("\n[LMS LIFECYCLE] Exit triggered. Flushing system streams...\n")
    sys.stderr.flush()
    try:
        import ray
        if ray.is_initialized():
            sys.stderr.write("[LMS LIFECYCLE] Active Ray session detected. Disconnecting...\n")
            ray.shutdown()
    except Exception:
        pass
    sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================


ROOT = Path(r"C:\WEB CASE STUDY")

# Only files that actually use Ray
RAY_FILES = [
    r"C:\WEB CASE STUDY\Untitled-2.py",
    r"C:\WEB CASE STUDY\ask_gemini_codegen.py",
    r"C:\WEB CASE STUDY\dsp_alignment_actor.py",
    r"C:\WEB CASE STUDY\dsp_alignment_actor_local.py",
    r"C:\WEB CASE STUDY\dynamic_segment_alignment_ray.py",
    r"C:\WEB CASE STUDY\e_breakdown.py",
    r"C:\WEB CASE STUDY\fire_test.py",
    r"C:\WEB CASE STUDY\fire_test_ray.py",
    r"C:\WEB CASE STUDY\fire_test_visual.py",
    r"C:\WEB CASE STUDY\ghost_rider_demo.py",
    r"C:\WEB CASE STUDY\intelligence_bridge.py",
    r"C:\WEB CASE STUDY\legion_sonic_engine\audio_analysis_actor.py",
    r"C:\WEB CASE STUDY\legion_sonic_engine\batch_master.py",
    r"C:\WEB CASE STUDY\legion_sonic_engine\legion_cli.py",
    r"C:\WEB CASE STUDY\legion_sonic_engine\mastering_agent_actor.py",
    r"C:\WEB CASE STUDY\legion_sonic_engine_orchestrator.py",
    r"C:\WEB CASE STUDY\mix_audit_agent.py",
    r"C:\WEB CASE STUDY\ray_arrow_swarm.py",
    r"C:\WEB CASE STUDY\ray_categorize_samples.py",
    r"C:\WEB CASE STUDY\ray_explore_old_ableton.py",
    r"C:\WEB CASE STUDY\ray_py_analyzer.py",
    r"C:\WEB CASE STUDY\run_fire_test.py",
    r"C:\WEB CASE STUDY\run_fire_test2.py",
    r"C:\WEB CASE STUDY\run_fire_test_standalone.py",
    r"C:\WEB CASE STUDY\run_simulation_with_stem_mastering.py",
    r"C:\WEB CASE STUDY\run_system_audit.py",
    r"C:\WEB CASE STUDY\search_data.py",
    r"C:\WEB CASE STUDY\search_swarm.py",
    r"C:\WEB CASE STUDY\split_and_master_pipeline.py",
    r"C:\WEB CASE STUDY\test_ghost_rider_power.py",
    r"C:\WEB CASE STUDY\test_registry_connection.py",
    r"C:\WEB CASE STUDY\upgraded_dynamic_batch_master.py",
    r"C:\WEB CASE STUDY\upgraded_dynamic_batch_master_v2.py",
    r"C:\WEB CASE STUDY\weaponize.py",
]

LOOP_RE = re.compile(r"while\s+(True|True|not\s+)|for\s+\w+\s+in\s+iter\(|while\s+True|asyncio\.run", re.I)
WAIT_RE = re.compile(r"\.wait\(|\.get\(|\.remote\(.*\.ready|await\s+|ray\.get\(|input\(.*\)|requests\.(get|post|put|patch)|fastapi|Flask\(|uvicorn|websocket|starlette|app\.route|@app\.|aiohttp|httpx|aiohttp", re.I)
RAY_ACTOR_RE = re.compile(r"@ray\.remote\s*\n\s*(?:def|class)\s+(\w+)")
RAY_REMOTE_CALLS = re.compile(r"\.remote\(")
DASHBOARD_RE = re.compile(r"\.put\(|\.get\(|\.wait\(", re.I)

results = []
for fpath in RAY_FILES:
    p = Path(fpath)
    if not p.exists():
        results.append({"file": fpath, "status": "MISSING"})
        continue
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        results.append({"file": fpath, "status": f"READ_ERR: {e}"})
        continue

    n_lines = len(t.splitlines())
    has_loop = bool(LOOP_RE.search(t))
    has_wait = bool(WAIT_RE.search(t))
    n_actors = len(RAY_ACTOR_RE.findall(t))
    n_remote = len(RAY_REMOTE_CALLS.findall(t))
    is_long = n_lines > 200

    # Classify
    if has_loop:
        kind = "LOOP"
    elif has_wait and ("ray.get" in t or ".remote" in t):
        kind = "RAY-WAITING"
    elif "ray.get" in t or ".remote" in t:
        kind = "RAY-ONESHOT"
    elif "ray.init" in t:
        kind = "RAY-INIT-ONLY"
    else:
        kind = "RAY-DECORATIVE"

    results.append({
        "file": fpath.replace("C:\\WEB CASE STUDY\\", ""),
        "lines": n_lines,
        "kind": kind,
        "actors": n_actors,
        "remote_calls": n_remote,
        "has_loop": has_loop,
        "has_wait_api": has_wait,
    })

# Group by kind
by_kind = defaultdict(list)
for r in results:
    by_kind[r["kind"]].append(r)

print("=" * 80)
print("RAY SCRIPT LIFECYCLE MAP (34 files)")
print("=" * 80)
for kind in ["LOOP", "RAY-WAITING", "RAY-ONESHOT", "RAY-INIT-ONLY", "RAY-DECORATIVE", "MISSING", "READ_ERR"]:
    items = by_kind.get(kind, [])
    if not items:
        continue
    print(f"\n{'='*78}")
    print(f"{kind}  ({len(items)} files)")
    print(f"{'='*78}")
    for r in sorted(items, key=lambda x: -x.get("lines", 0)):
        if "lines" not in r:
            print(f"  {r['file']:<60}  [{r['status']}]")
            continue
        actors = f"  actors={r['actors']}" if r["actors"] else ""
        rc = f"  .remote()={r['remote_calls']}" if r["remote_calls"] else ""
        print(f"  {r['file']:<58}  {r['lines']:>5}L{actors}{rc}")

# Show the LOOP cluster detail
print()
print("=" * 80)
print("WHAT THE LOOPING RAY SCRIPTS ARE ACTUALLY DOING")
print("=" * 80)
for r in by_kind.get("LOOP", []):
    p = Path(r["file"] if Path(r["file"]).is_absolute() else ROOT / r["file"])
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    print(f"\n--- {r['file']} ---")
    # Find the while True block + first 5 lines after
    for m in LOOP_RE.finditer(t):
        start = m.start()
        # show this line and next 6
        chunk = t[start:start+400].splitlines()[:8]
        for ln in chunk:
            print(f"    {ln.rstrip()[:120]}")
        break  # only first match per file