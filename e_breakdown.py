"""E:\\ breakdown by file type and category. Ray-parallel for speed. Read-only."""
import os, json, sys, time
from pathlib import Path
from collections import defaultdict
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


if not ray.is_initialized():
    ray.init(num_cpus=os.cpu_count(), ignore_reinit_error=True, log_to_driver=False)

E = Path("E:/")

# What we're scanning - avoid system noise
SKIP_DIRS = {"$recycle.bin", "system volume information", ".spotlight-v100",
             ".fseventsd", ".trashes", "__pycache__"}

# File-type categories
TYPE_RULES = [
    ("audio_wav",    {".wav"}),
    ("audio_aif",    {".aif", ".aiff"}),
    ("audio_mp3",    {".mp3"}),
    ("audio_flac",   {".flac"}),
    ("audio_other",  {".m4a", ".ogg", ".opus", ".wma", ".aac", ".alac"}),
    ("video",        {".mov", ".mp4", ".mkv", ".avi", ".wmv", ".m4v", ".webm"}),
    ("image",        {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".heic"}),
    ("ml_model",     {".bin", ".pt", ".pth", ".th", ".onnx", ".safetensors", ".ckpt", ".h5", ".gguf", ".tflite"}),
    ("installer",    {".dmg", ".pkg", ".exe", ".msi", ".iso", ".img"}),
    ("archive",      {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"}),
    ("doc",          {".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt"}),
    ("project_als",  {".als", ".alp"}),  # Ableton
    ("project_alsx", {".alsx"}),
    ("project_logic",{".logicx"}),
    ("project_flp",  {".flp"}),
    ("preset_vst",   {".vst", ".vst3", ".au", ".component"}),
    ("preset_adg",   {".adg"}),  # Ableton instrument preset
    ("preset_adv",   {".adv"}),  # Ableton MIDI/effect preset
    ("preset",       {".fxp", ".fxb", ".nksf", ".nksr", ".nki", ".nkm"}),
    ("midi",         {".mid", ".midi"}),
    ("lyrics",       {".lrc"}),
    ("code",         {".py", ".js", ".ts", ".json", ".html", ".css", ".cpp", ".h", ".java"}),
    ("font",         {".ttf", ".otf", ".woff", ".woff2"}),
    ("disk_image",   {".toast", ".sparseimage", ".dmg"}),
    ("subtitle",     {".srt", ".ass", ".ssa", ".vtt"}),
]

def classify(ext):
    e = ext.lower()
    for name, exts in TYPE_RULES:
        if e in exts:
            return name
    return "other"

# Ray task: scan one subdir tree, return list of (path, size, mtime, ext)
@ray.remote
def scan_tree(root_str):
    out = []
    root = Path(root_str)
    for dp, dns, fns in os.walk(root, onerror=lambda e: None):
        dns[:] = [d for d in dns if d.lower() not in SKIP_DIRS]
        for fn in fns:
            fp = Path(dp) / fn
            try:
                st = fp.stat()
                out.append((str(fp), st.st_size, int(st.st_mtime), fp.suffix.lower()))
            except (OSError, PermissionError):
                pass
    return out

# Get top-level dirs under E
sys.stdout.write("Listing top-level dirs on E:\\...\n"); sys.stdout.flush()
top = [p for p in E.iterdir() if p.is_dir() and p.name.lower() not in SKIP_DIRS]

# Fan out
sys.stdout.write(f"Dispatching {len(top)} Ray tasks across {os.cpu_count()} CPUs...\n"); sys.stdout.flush()
t0 = time.time()
futures = [scan_tree.remote(str(p)) for p in top]
all_files = []
done = 0
remaining = list(futures)
while remaining:
    ready, remaining = ray.wait(remaining, num_returns=min(8, len(remaining)), timeout=10)
    for f in ready:
        all_files.extend(ray.get(f))
        done += 1
    sys.stdout.write(f"  {done}/{len(futures)} dirs scanned ({len(all_files):,} files, {time.time()-t0:.1f}s)\n"); sys.stdout.flush()

sys.stdout.write(f"Scan done. {len(all_files):,} files in {time.time()-t0:.1f}s\n")

# Aggregate by type
by_type = defaultdict(lambda: {"count": 0, "bytes": 0, "files": []})
for path, size, mtime, ext in all_files:
    cat = classify(ext)
    d = by_type[cat]
    d["count"] += 1
    d["bytes"] += size
    d["files"].append((path, size, mtime, ext))

# Per-dir breakdown
by_dir = defaultdict(lambda: defaultdict(int))
for path, size, mtime, ext in all_files:
    rel = Path(path).relative_to(E)
    top_dir = rel.parts[0] if len(rel.parts) > 1 else "."
    cat = classify(ext)
    by_dir[top_dir][cat] += size

# Build output
type_summary = []
for cat, d in by_type.items():
    d["files"].sort(key=lambda x: -x[1])
    type_summary.append({
        "category": cat,
        "count": d["count"],
        "total_bytes": d["bytes"],
        "total_h": f"{d['bytes']/1e9:.2f}GB" if d["bytes"] > 1e9 else f"{d['bytes']/1e6:.2f}MB",
        "top_20_largest": [
            {"path": p, "size": s, "size_h": f"{s/1e9:.2f}GB" if s>1e9 else f"{s/1e6:.2f}MB",
             "mtime": m, "ext": e}
            for (p, s, m, e) in d["files"][:20]
        ],
    })
type_summary.sort(key=lambda x: -x["total_bytes"])

dir_summary = []
for d, cats in by_dir.items():
    total = sum(cats.values())
    dir_summary.append({
        "dir": d,
        "total_bytes": total,
        "total_h": f"{total/1e9:.2f}GB" if total > 1e9 else f"{total/1e6:.2f}MB",
        "by_category": {c: {"bytes": s, "h": f"{s/1e9:.2f}GB" if s>1e9 else f"{s/1e6:.2f}MB"}
                        for c, s in sorted(cats.items(), key=lambda kv: -kv[1])},
    })
dir_summary.sort(key=lambda x: -x["total_bytes"])

result = {
    "scan_time_s": round(time.time() - t0, 2),
    "files_scanned": len(all_files),
    "by_type": type_summary,
    "by_top_dir": dir_summary[:25],
}
out = Path("C:/WEB CASE STUDY/e_breakdown.json")
out.write_text(json.dumps(result, indent=2))
print(f"\nWrote {out}")
print(f"\n=== TOP 10 FILE TYPES BY TOTAL SIZE ON E:\\ ===")
for t in type_summary[:10]:
    print(f"  {t['total_h']:>10}  {t['count']:>9,} files  {t['category']}")

print(f"\n=== TOP 10 DIRS BY TOTAL SIZE ===")
for d in dir_summary[:10]:
    print(f"  {d['total_h']:>10}  {d['dir']}")
ray.shutdown()