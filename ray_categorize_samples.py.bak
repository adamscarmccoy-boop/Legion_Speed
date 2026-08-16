"""Ray worker: categorize 375k+ samples by WHAT THEY ARE, not who made them.
Folder structure + filename patterns → category taxonomy.

The output is the categorization schema. That's what makes the weapon:
'Across 375,510 samples, here's the category map of the industry.'
"""

import os
import sys
import time
import json
import re
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


ROOT = r"E:\OLD ABLETON"
AUDIO_EXTS = {".wav", ".mp3", ".flac", ".aif", ".aiff", ".m4a"}

# Common sample category tokens (filename + folder heuristics)
CATEGORY_TOKENS = {
    "kick":       ["kick", "bd", "bassdrum", "boom"],
    "snare":      ["snare", "sd", "snr", "clap"],
    "hat":        ["hat", "hh", "hihat", "cymbal"],
    "perc":       ["perc", "percussion", "shaker", "conga", "bongo", "tom", "rim"],
    "bass":       ["bass", "sub", "808", "reese", "low"],
    "lead":       ["lead", "synth", "saw", "pluck", "arp", "arppeg", "stab"],
    "pad":        ["pad", "atmos", "ambient", "drone", "texture"],
    "fx":         ["fx", "sfx", "riser", "uplift", "downlifter", "sweep", "impact", "whoosh"],
    "vocal":      ["vox", "vocal", "voice", "chant", "phrase", "speak", "talk"],
    "loop":       ["loop"],
    "oneshot":    ["oneshot", "one-shot", "single", "shot"],
    "chord":      ["chord", "prog", "progression"],
    "melody":     ["melody", "melodic", "top"],
    "build":      ["build", "buildup", "riser"],
    "drop":       ["drop"],
    "break":      ["break", "breakbeat"],
    "drum_loop":  ["drum loop", "drumloop", "beat loop", "groove"],
}


def classify_name(name: str) -> list:
    """Return all category tokens matching this filename."""
    n = name.lower()
    hits = []
    for cat, tokens in CATEGORY_TOKENS.items():
        for t in tokens:
            if t in n:
                hits.append(cat)
                break
    return hits


@ray.remote
def strategy_top_level_folders(root: str) -> dict:
    """Strategy 1: depth-1 folder list — the user's mental taxonomy."""
    if not os.path.isdir(root):
        return {"exists": False}
    top = []
    for entry in os.listdir(root):
        full = os.path.join(root, entry)
        if os.path.isdir(full):
            n_audio = 0
            try:
                for dp, dn, fn in os.walk(full):
                    for f in fn:
                        if os.path.splitext(f)[1].lower() in AUDIO_EXTS:
                            n_audio += 1
            except (PermissionError, OSError):
                pass
            top.append({"name": entry, "audio_files": n_audio})
    top.sort(key=lambda x: x["audio_files"], reverse=True)
    return {"root": root, "top_level": top[:50]}


@ray.remote
def strategy_depth_two_folders(root: str) -> dict:
    """Strategy 2: depth-2 folder tree (root\\sub\\subsub)."""
    if not os.path.isdir(root):
        return {"exists": False}
    tree = defaultdict(lambda: defaultdict(int))
    for dp, dn, fn in os.walk(root):
        rel = os.path.relpath(dp, root)
        parts = rel.split(os.sep)
        if len(parts) >= 2:
            tree[parts[0]][parts[1]] += sum(1 for f in fn if os.path.splitext(f)[1].lower() in AUDIO_EXTS)
        elif len(parts) == 1:
            tree[parts[0]]["<root_files>"] += sum(1 for f in fn if os.path.splitext(f)[1].lower() in AUDIO_EXTS)
    return {"root": root, "two_level": {k: dict(v) for k, v in tree.items()}}


@ray.remote
def strategy_filename_tokens(root: str, sample_size: int = 50000) -> dict:
    """Strategy 3: filename token analysis — what does the sample library CALL its sounds?"""
    if not os.path.isdir(root):
        return {"exists": False}
    cat_counts = Counter()
    total = 0
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if os.path.splitext(f)[1].lower() not in AUDIO_EXTS:
                continue
            total += 1
            if total > sample_size:
                break
            hits = classify_name(f)
            for c in hits:
                cat_counts[c] += 1
        if total > sample_size:
            break
    return {"root": root, "sampled_files": min(total, sample_size), "category_hits": dict(cat_counts.most_common(30))}


@ray.remote
def strategy_bpm_keys_filename(root: str, sample_size: int = 30000) -> dict:
    """Strategy 4: pull BPM and key tags from filenames (e.g., 'loop_128bpm_Amin.wav')."""
    if not os.path.isdir(root):
        return {"exists": False}
    bpm_re = re.compile(r"(\d{2,3})\s*bpm", re.IGNORECASE)
    key_re = re.compile(r"\b([A-G][#b]?)\s*(min|maj|m|minor|major)\b", re.IGNORECASE)
    bpm_counts = Counter()
    key_counts = Counter()
    total = 0
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if os.path.splitext(f)[1].lower() not in AUDIO_EXTS:
                continue
            total += 1
            if total > sample_size:
                break
            m = bpm_re.search(f)
            if m:
                bpm = int(m.group(1))
                if 60 <= bpm <= 200:
                    bpm_counts[bpm] += 1
            m = key_re.search(f)
            if m:
                key_counts[m.group(1).upper() + " " + m.group(2).lower()] += 1
        if total > sample_size:
            break
    return {
        "root": root,
        "sampled_files": min(total, sample_size),
        "bpm_distribution": dict(bpm_counts.most_common(30)),
        "key_distribution": dict(key_counts.most_common(30)),
    }


def main():
    if not ray.is_initialized():
        ray.init(num_cpus=8, ignore_reinit_error=True, log_to_driver=False)
    print(f"=== CATEGORY ANALYSIS on {ROOT} ===\n")
    t0 = time.perf_counter()

    # Launch all 4 strategies in parallel
    f1 = strategy_top_level_folders.remote(ROOT)
    f2 = strategy_depth_two_folders.remote(ROOT)
    f3 = strategy_filename_tokens.remote(ROOT)
    f4 = strategy_bpm_keys_filename.remote(ROOT)

    r1, r2, r3, r4 = ray.get([f1, f2, f3, f4])
    elapsed = time.perf_counter() - t0

    out = {"root": ROOT, "elapsed_s": round(elapsed, 2), "results": {
        "top_level": r1,
        "two_level": r2,
        "filename_tokens": r3,
        "bpm_keys": r4,
    }}

    out_path = "ray_category_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n=== DONE in {elapsed:.2f}s ===\n")

    print("--- TOP-LEVEL FOLDERS ---")
    for entry in r1.get("top_level", [])[:20]:
        print(f"  {entry['audio_files']:>8}  {entry['name']}")

    print("\n--- FILENAME CATEGORY HITS (50k sample) ---")
    for cat, n in r3.get("category_hits", {}).items():
        print(f"  {n:>6}  {cat}")

    print("\n--- BPM DISTRIBUTION (top 15) ---")
    for bpm, n in list(r4.get("bpm_distribution", {}).items())[:15]:
        print(f"  {n:>5}  {bpm} bpm")

    print("\n--- KEY DISTRIBUTION (top 15) ---")
    for k, n in list(r4.get("key_distribution", {}).items())[:15]:
        print(f"  {n:>5}  {k}")

    print(f"\nResults written: {out_path}")
    ray.shutdown()


if __name__ == "__main__":
    main()