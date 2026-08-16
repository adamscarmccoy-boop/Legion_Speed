"""Ray worker: explore OLD ABLETON (and adjacent roots) from N angles in parallel.
Each actor takes a different strategy. We don't commit to one answer —
we collect all attempts and look at the spread."""

import os
import sys
import time
import json
from pathlib import Path
from collections import Counter, defaultdict
import ray

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


ROOT_CANDIDATES = [
    r"E:\OLD ABLETON",
    r"D:\OLD ABLETON",
    r"E:\scars SAMPLE PACKS",
    r"D:\scars SAMPLE PACKS",
    r"E:\COLLECT ALL",
    r"D:\COLLECT ALL - (2025)",
    r"D:\COLLECT ALL - 2025 LATE",
    r"D:\000 - MASTERED EXPORT",
]

AUDIO_EXTS = {".wav", ".mp3", ".flac", ".aif", ".aiff", ".m4a"}

KNOWN_COMPANIES = [
    "splice", "loopmasters", "cymatics", "landr", "beatport", "splice originals",
    "samplephonics", "prime loops", "sounds.com", "capsun", "wavsupply", "loopcloud",
    "ghetto house", "toolroom", "repkn", "black octopus", "industrial strength",
    "sample magic", "sounds of anomalies", "splice originals",
]


def quick_audio_count(root: str) -> dict:
    if not os.path.isdir(root):
        return {"root": root, "exists": False}
    counts = Counter()
    top_dirs = Counter()
    total_size = 0
    file_count = 0
    for dp, dn, fn in os.walk(root):
        rel = dp[len(root):].lstrip("\\/") if dp.startswith(root) else dp
        first_seg = rel.split("\\")[0].split("/")[0] if rel else "<root>"
        for f in fn:
            ext = os.path.splitext(f)[1].lower()
            if ext in AUDIO_EXTS:
                counts[ext] += 1
                top_dirs[first_seg] += 1
                try:
                    total_size += os.path.getsize(os.path.join(dp, f))
                except OSError:
                    pass
                file_count += 1
    return {
        "root": root,
        "exists": True,
        "total_audio": file_count,
        "total_size_gb": round(total_size / 1024**3, 2),
        "ext_breakdown": dict(counts),
        "top_15_subdirs": top_dirs.most_common(15),
    }


@ray.remote
def strategy_1_walk_all(root: str) -> dict:
    """Strategy 1: walk the entire tree, count audio files, top subdirs."""
    return quick_audio_count(root)


@ray.remote
def strategy_2_company_match(root: str) -> dict:
    """Strategy 2: walk, count how many files have known company names in path."""
    if not os.path.isdir(root):
        return {"root": root, "exists": False}
    hits = Counter()
    total_audio = 0
    for dp, dn, fn in os.walk(root):
        path_lower = dp.lower()
        for f in fn:
            ext = os.path.splitext(f)[1].lower()
            if ext not in AUDIO_EXTS:
                continue
            total_audio += 1
            full_lower = (os.path.join(dp, f)).lower()
            for co in KNOWN_COMPANIES:
                if co in full_lower:
                    hits[co] += 1
                    break
    return {"root": root, "total_audio": total_audio, "company_hits": dict(hits.most_common(20))}


@ray.remote
def strategy_3_two_level_layout(root: str) -> dict:
    """Strategy 3: get the 2-level deep layout (e.g., E:\\OLD ABLETON\\Splice\\Bass)."""
    if not os.path.isdir(root):
        return {"root": root, "exists": False}
    layout = {}
    for entry in os.listdir(root):
        sub = os.path.join(root, entry)
        if not os.path.isdir(sub):
            continue
        second = []
        try:
            for e2 in os.listdir(sub):
                if os.path.isdir(os.path.join(sub, e2)):
                    second.append(e2)
                elif os.path.splitext(e2)[1].lower() in AUDIO_EXTS:
                    second.append(f"[file] {e2}")
        except PermissionError:
            second = ["<permission denied>"]
        layout[entry] = second[:30]
    return {"root": root, "two_level": layout}


@ray.remote
def strategy_4_filename_patterns(root: str) -> dict:
    """Strategy 4: extract common filename prefixes — these often encode vendor/pack."""
    if not os.path.isdir(root):
        return {"root": root, "exists": False}
    prefixes = Counter()
    for dp, dn, fn in os.walk(root):
        for f in fn:
            ext = os.path.splitext(f)[1].lower()
            if ext not in AUDIO_EXTS:
                continue
            name = os.path.splitext(f)[0]
            # common patterns: "Splice_Originals_Bass_001.wav" → prefix "Splice Originals"
            parts = name.replace("_", " ").replace("-", " ").split()
            if len(parts) >= 2:
                prefixes[" ".join(parts[:2])] += 1
            elif parts:
                prefixes[parts[0]] += 1
    return {"root": root, "top_30_filename_prefixes": prefixes.most_common(30)}


@ray.remote
def strategy_5_shortcut_inspection(root: str) -> dict:
    """Strategy 5: list .lnk files in OLD ABLETON (Vital - Shortcut.lnk suggests shortcut-driven structure)."""
    if not os.path.isdir(root):
        return {"root": root, "exists": False}
    lnks = []
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if f.lower().endswith(".lnk"):
                lnks.append(os.path.join(dp, f))
    return {"root": root, "shortcut_count": len(lnks), "shortcuts": lnks[:50]}


def main():
    if not ray.is_initialized():
        ray.init(num_cpus=8, ignore_reinit_error=True, log_to_driver=False)
    print(f"=== Ray parallel exploration across {len(ROOT_CANDIDATES)} roots, 5 strategies ===\n")
    t0 = time.perf_counter()

    futures = []
    for root in ROOT_CANDIDATES:
        futures.append(("walk_all", root, strategy_1_walk_all.remote(root)))
        futures.append(("company_match", root, strategy_2_company_match.remote(root)))
        futures.append(("two_level", root, strategy_3_two_level_layout.remote(root)))
        futures.append(("filename_patterns", root, strategy_4_filename_patterns.remote(root)))
        futures.append(("shortcuts", root, strategy_5_shortcut_inspection.remote(root)))

    print(f"Launched {len(futures)} parallel tasks...")
    results = ray.get([f for _, _, f in futures])
    elapsed = time.perf_counter() - t0

    out = {}
    for (strategy, root, _), result in zip(futures, results):
        if root not in out:
            out[root] = {}
        out[root][strategy] = result

    out_path = "ray_exploration_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n=== DONE in {elapsed:.2f}s ===")
    print(f"Results: {out_path}")
    print("\n--- Quick summary ---")
    for root, strategies in out.items():
        walk = strategies.get("walk_all", {})
        if not walk.get("exists"):
            print(f"  {root}: does not exist")
            continue
        print(f"\n  {root}")
        print(f"    audio files: {walk.get('total_audio', 0)}  size: {walk.get('total_size_gb', 0)}GB")
        print(f"    ext: {walk.get('ext_breakdown', {})}")
        co = strategies.get("company_match", {}).get("company_hits", {})
        if co:
            print(f"    company hits: {co}")
        sc = strategies.get("shortcuts", {}).get("shortcut_count", 0)
        if sc:
            print(f"    shortcut count: {sc}")
    ray.shutdown()


if __name__ == "__main__":
    main()