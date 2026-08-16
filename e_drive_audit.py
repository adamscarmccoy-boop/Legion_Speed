"""E:\ cleanup audit. Finds large/old/temp/recyclable files. Read-only, no deletes."""
import os, json, sys
from pathlib import Path
from collections import defaultdict

E = Path("E:/")
LARGE_MB = 100          # files bigger than this are flagged as large
OLD_DAYS = 365          # files not touched in a year are flagged as stale
TOP_N = 50              # how many to surface per category

# Categories that are basically always safe to delete (after review)
TRASH_NAMES = {
    "thumbs.db", "desktop.ini", ".ds_store", "icon\r", "folder.gif",
    "folder.jpg", "usercss.css", "user.js",
}
TRASH_EXTS = {
    ".tmp", ".temp", ".bak", ".old", ".orig", ".log", ".cache",
    ".crdownload", ".part", ".swp", ".swo", ".chk",
}
TRASH_DIR_NAMES = {
    "$recycle.bin", "recycler", "system volume information",
    "found.000", "found.001", "found.002",
    "__pycache__", ".git/objects", ".cache", ".tmp", "temp", "tmp",
    "windows installer cache", "installer",
    ".spotlight-v100", ".fseventsd", ".trashes",
}
# Conservative: don't flag .wav/.aif/.flac/.mp3 in obvious music roots, but DO flag
# orphans (loose files in DOWNLOAD, RELEASE-DEMO, untitled folder, etc.)
MUSIC_ROOT_MARKERS = {"old ableton", "music", "collect all", "export all",
                      "scars sample packs", "000 - mastered export", "download",
                      "pioneer", "pioneer rec", "collect all 2016",
                      "collect all - (2025)", "collect all - 2025 late",
                      "release-demo", "untitled folder", "cache", "other",
                      "adobe", "agents", "apps", "app", "contents",
                      "djsusan", "omni_graph_web_agent", "ableton-session-intelligence",
                      "web case study", "programs", "program files"}

results = {
    "drive": "E:\\",
    "drive_total_gb": None,
    "drive_free_gb": None,
    "scan_root": str(E),
    "trash_candidates": [],   # extension/name/dir based, low-risk delete
    "large_files": [],         # by size, descending
    "stale_files": [],         # by mtime age
    "big_dirs": [],            # directories consuming most space
    "huge_or_duplicate_suspects": [],
    "summary": {},
    "errors": [],
}

def is_music_path(p: Path) -> bool:
    parts = {x.lower() for x in p.parts}
    return bool(parts & MUSIC_ROOT_MARKERS)

def human(n):
    for unit in ["B","KB","MB","GB","TB"]:
        if n < 1024:
            return f"{n:.2f}{unit}"
        n /= 1024
    return f"{n:.2f}PB"

# --- drive stats
try:
    import shutil
    total, used, free = shutil.disk_usage(E)
    results["drive_total_gb"] = round(total/1e9, 2)
    results["drive_free_gb"]  = round(free/1e9, 2)
except Exception as e:
    results["errors"].append(f"disk_usage: {e}")

# --- walk
file_count = 0
dir_sizes = defaultdict(int)
cutoff_ts = None
import time
cutoff_ts = time.time() - OLD_DAYS*86400

sys.stdout.write("Scanning E:\\ ...\n"); sys.stdout.flush()
for dirpath, dirnames, filenames in os.walk(E, onerror=lambda e: results["errors"].append(str(e))):
    # skip system/recycle noise
    dirnames[:] = [d for d in dirnames if d.lower() not in {
        "$recycle.bin","system volume information",
        ".spotlight-v100",".fseventsd",".trashes",
    }]
    dp = Path(dirpath)
    for fn in filenames:
        fp = dp / fn
        try:
            st = fp.stat()
        except (OSError, PermissionError):
            continue
        size = st.st_size
        mtime = st.st_mtime
        file_count += 1
        # accumulate dir size (rough)
        rel = fp.relative_to(E)
        dir_sizes[str(rel.parts[0]) if len(rel.parts) > 1 else "."] += size

        low = fn.lower()
        ext = fp.suffix.lower()

        # TRASH candidates (safe-to-delete-by-type)
        is_trash = False
        reason = None
        if low in TRASH_NAMES:
            is_trash = True; reason = f"system file ({low})"
        elif ext in TRASH_EXTS:
            is_trash = True; reason = f"temp/cache extension ({ext})"
        else:
            # any file inside a known trash dir name (one level)
            for td in TRASH_DIR_NAMES:
                if td in {x.lower() for x in fp.parts}:
                    is_trash = True; reason = f"in trash-ish dir ({td})"
                    break
        if is_trash:
            results["trash_candidates"].append({
                "path": str(fp), "size": size, "size_h": human(size),
                "mtime": int(mtime), "reason": reason,
            })

        # LARGE files
        if size >= LARGE_MB * 1024 * 1024:
            results["large_files"].append({
                "path": str(fp), "size": size, "size_h": human(size),
                "mtime": int(mtime),
            })

        # STALE files (untouched > 1yr) — but only flag non-music paths to avoid
        # suggesting we delete your library
        if mtime < cutoff_ts and not is_music_path(fp):
            results["stale_files"].append({
                "path": str(fp), "size": size, "size_h": human(size),
                "mtime": int(mtime), "age_days": int((time.time()-mtime)/86400),
            })

# --- big dirs (top consumers)
for d, s in sorted(dir_sizes.items(), key=lambda kv: -kv[1])[:TOP_N]:
    if s == 0: continue
    results["big_dirs"].append({"dir": d, "size": s, "size_h": human(s)})

# --- sort + trim
results["trash_candidates"].sort(key=lambda x: -x["size"])
results["large_files"].sort(key=lambda x: -x["size"])
results["stale_files"].sort(key=lambda x: x["mtime"])
results["trash_candidates"] = results["trash_candidates"][:TOP_N*3]
results["large_files"]     = results["large_files"][:TOP_N]
results["stale_files"]     = results["stale_files"][:TOP_N]

# --- summary
trash_total = sum(x["size"] for x in results["trash_candidates"])
results["summary"] = {
    "files_scanned": file_count,
    "trash_candidates_shown": len(results["trash_candidates"]),
    "trash_candidates_total_bytes": trash_total,
    "trash_candidates_total_h": human(trash_total),
    "large_files_shown": len(results["large_files"]),
    "stale_files_shown": len(results["stale_files"]),
    "errors_during_scan": len(results["errors"]),
}

out = Path("C:/WEB CASE STUDY/e_drive_audit.json")
out.write_text(json.dumps(results, indent=2))
print(f"Wrote {out}")
print(f"Scanned {file_count} files")
print(f"Trash candidates: {len(results['trash_candidates'])} shown, "
      f"{human(trash_total)} total")
print(f"Large files: {len(results['large_files'])} shown")
print(f"Stale files: {len(results['stale_files'])} shown")
print(f"Errors (permission/access): {len(results['errors'])}")
