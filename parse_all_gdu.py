"""Aggregate per-dir gdu JSON outputs into a global breakdown."""
import json, os
from pathlib import Path
from collections import defaultdict

PER_DIR_DIR = Path(r"C:\WEB CASE STUDY\gdu_per_dir")
files = []
errors = []
for jf in PER_DIR_DIR.glob("*.json"):
    try:
        raw = json.loads(jf.read_text(encoding="utf-8"))
        # gdu schema: [v1, v2, header, [files...]]
        for entry in raw[3]:
            if not isinstance(entry, dict): continue
            if "asize" not in entry and "dsize" not in entry: continue
            files.append({
                "name": entry.get("name", ""),
                "size": entry.get("asize", 0) or entry.get("dsize", 0),
                "mtime": entry.get("mtime", 0),
                "source_dir": jf.stem,
            })
    except Exception as e:
        errors.append(f"{jf.name}: {e}")

print(f"Loaded {len(files):,} files from {len(list(PER_DIR_DIR.glob('*.json')))} per-dir scans")
if errors:
    print(f"Errors: {len(errors)}")

# By category
def classify(n):
    e = Path(n).suffix.lower()
    if e in {".wav"}: return "Audio - WAV"
    if e in {".aif", ".aiff"}: return "Audio - AIFF"
    if e in {".mp3"}: return "Audio - MP3"
    if e in {".flac"}: return "Audio - FLAC"
    if e in {".m4a",".ogg",".opus",".wma",".aac",".alac"}: return "Audio - Other"
    if e in {".mov",".mp4",".mkv",".avi",".wmv",".m4v",".webm"}: return "Video"
    if e in {".jpg",".jpeg",".png",".gif",".bmp",".tiff",".webp",".heic"}: return "Image"
    if e in {".bin",".pt",".pth",".th",".onnx",".safetensors",".ckpt",".h5",".gguf",".tflite"}: return "ML Model"
    if e in {".dmg",".pkg",".exe",".msi",".iso",".img"}: return "Installer"
    if e in {".zip",".rar",".7z",".tar",".gz",".bz2",".xz"}: return "Archive"
    if e in {".als",".alp"}: return "Ableton Project"
    if e in {".alsx"}: return "Ableton Project (new)"
    if e in {".logicx"}: return "Logic Project"
    if e in {".flp"}: return "FL Studio Project"
    if e in {".vst",".vst3",".au",".component"}: return "Plugin"
    if e in {".adg"}: return "Ableton Preset"
    if e in {".adv"}: return "Ableton Preset (MIDI/FX)"
    if e in {".fxp",".fxb",".nksf",".nksr",".nki",".nkm"}: return "Instrument Preset"
    if e in {".mid",".midi"}: return "MIDI"
    if e in {".pdf",".doc",".docx",".txt",".md",".rtf",".odt"}: return "Document"
    if e in {".py",".js",".ts",".json",".html",".css",".cpp",".h",".java"}: return "Code"
    if e in {".ttf",".otf",".woff",".woff2"}: return "Font"
    if e in {".lrc"}: return "Lyrics"
    if e in {".srt",".ass",".ssa",".vtt"}: return "Subtitle"
    if e in {".tmp",".temp",".bak",".old",".log",".cache",".crdownload",".part",".swp",".chk"}: return "Temp/Cache"
    return "Other"

cat_total = defaultdict(int)
cat_files = defaultdict(list)
ext_total = defaultdict(int)
ext_count = defaultdict(int)

for f in files:
    cat = classify(f["name"])
    cat_total[cat] += f["size"]
    cat_files[cat].append((f["size"], f["name"], f["source_dir"]))
    ext = Path(f["name"]).suffix.lower() or "<no-ext>"
    ext_total[ext] += f["size"]
    ext_count[ext] += 1

print()
print("=" * 80)
print("TOP 25 CATEGORIES (LOGICAL TYPES) BY TOTAL SIZE ON E:\\")
print("=" * 80)
for cat, total in sorted(cat_total.items(), key=lambda x: -x[1])[:25]:
    cnt = len(cat_files[cat])
    print(f"  {total/1e9:>9.2f}GB  {cnt:>9,} files  {cat}")

print()
print("=" * 80)
print("TOP 25 EXTENSIONS BY TOTAL SIZE ON E:\\")
print("=" * 80)
for ext, total in sorted(ext_total.items(), key=lambda x: -x[1])[:25]:
    cnt = ext_count[ext]
    avg = total / cnt if cnt else 0
    print(f"  {total/1e9:>9.2f}GB  {cnt:>9,} files  (avg {avg/1e6:>6.2f}MB)  {ext}")

print()
print("=" * 80)
print("TOP 30 BIGGEST SINGLE FILES ON E:\\")
print("=" * 80)
top_files = sorted(files, key=lambda x: -x["size"])
for f in top_files[:30]:
    print(f"  {f['size']/1e9:>9.2f}GB  [{f['source_dir'][:25]:<25}]  {f['name']}")

print()
print("=" * 80)
print("RECLAIMABLE BY CATEGORY (REVIEW BEFORE DELETING)")
print("=" * 80)
for cat in ["ML Model", "Installer", "Archive", "Video", "Temp/Cache", "Other"]:
    if cat in cat_total:
        fl = cat_files[cat]
        print(f"\n--- {cat}: {cat_total[cat]/1e9:.2f}GB across {len(fl)} files ---")
        for s, n, sd in sorted(fl, key=lambda x: -x[0])[:15]:
            print(f"  {s/1e9:>9.2f}GB  [{sd[:20]:<20}]  {n}")
