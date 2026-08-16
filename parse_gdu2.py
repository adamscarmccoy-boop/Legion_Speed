"""Parse gdu JSON output (flat list format)."""
import json
from pathlib import Path
from collections import defaultdict

raw = json.loads(Path(r"C:\WEB CASE STUDY\e_gdu.json").read_text(encoding="utf-8"))
files = raw[3]  # flat list of {name, asize, dsize, mtime}

print(f"Total entries in gdu output: {len(files):,}\n")

# Aggregate by extension
ext_total = defaultdict(int)
ext_count = defaultdict(int)
ext_files = defaultdict(list)

for f in files:
    name = f.get("name", "")
    size = f.get("asize", 0) or f.get("dsize", 0)
    ext = Path(name).suffix.lower() or "<no-ext>"
    ext_total[ext] += size
    ext_count[ext] += 1
    ext_files[ext].append((size, name, f.get("mtime", 0)))

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
    if e in {".tmp",".temp",".bak",".old",".log",".cache",".crdownload",".part",".swp"}: return "Temp/Cache"
    return f"Other"

cat_total = defaultdict(int)
cat_files = defaultdict(list)

for f in files:
    name = f.get("name", "")
    size = f.get("asize", 0) or f.get("dsize", 0)
    cat = classify(name)
    cat_total[cat] += size
    cat_files[cat].append((size, name))

print("=" * 78)
print("TOP 30 FILE EXTENSIONS BY TOTAL SIZE")
print("=" * 78)
for ext, total in sorted(ext_total.items(), key=lambda x: -x[1])[:30]:
    cnt = ext_count[ext]
    avg = total / cnt if cnt else 0
    print(f"  {total/1e9:>8.2f}GB  {cnt:>9,} files  (avg {avg/1e6:>6.2f}MB)  {ext}")

print()
print("=" * 78)
print("TOP CATEGORIES (LOGICAL TYPES)")
print("=" * 78)
for cat, total in sorted(cat_total.items(), key=lambda x: -x[1])[:25]:
    cnt = len(cat_files[cat])
    print(f"  {total/1e9:>8.2f}GB  {cnt:>9,} files  {cat}")

print()
print("=" * 78)
print("TOP 25 BIGGEST SINGLE FILES ON E:\\")
print("=" * 78)
sorted_files = sorted(files, key=lambda x: -(x.get("asize", 0) or 0))
for f in sorted_files[:25]:
    s = f.get("asize", 0)
    n = f.get("name", "")
    print(f"  {s/1e9:>8.2f}GB  {n}")

print()
print("=" * 78)
print("ML MODELS (likely reclaimable)")
print("=" * 78)
ml_files = [(f.get("asize",0), f.get("name","")) for f in files
            if Path(f.get("name","")).suffix.lower() in
            {".bin",".pt",".pth",".th",".onnx",".safetensors",".ckpt",".h5",".gguf",".tflite"}]
ml_files.sort(reverse=True)
for s, n in ml_files:
    print(f"  {s/1e9:>8.2f}GB  {n}")
print(f"  TOTAL ML: {sum(s for s,_ in ml_files)/1e9:.2f}GB across {len(ml_files)} files")

print()
print("=" * 78)
print("INSTALLERS (often safe to delete after install)")
print("=" * 78)
inst_files = [(f.get("asize",0), f.get("name","")) for f in files
              if Path(f.get("name","")).suffix.lower() in {".dmg",".pkg",".exe",".msi",".iso",".img"}]
inst_files.sort(reverse=True)
for s, n in inst_files[:20]:
    print(f"  {s/1e9:>8.2f}GB  {n}")
print(f"  TOTAL INSTALLERS (top {len(inst_files[:20])}): {sum(s for s,_ in inst_files[:20])/1e9:.2f}GB")

print()
print("=" * 78)
print("VIDEO FILES (often safe to delete if not current projects)")
print("=" * 78)
vid_files = [(f.get("asize",0), f.get("name","")) for f in files
             if Path(f.get("name","")).suffix.lower() in {".mov",".mp4",".mkv",".avi",".wmv",".m4v",".webm"}]
vid_files.sort(reverse=True)
for s, n in vid_files[:20]:
    print(f"  {s/1e9:>8.2f}GB  {n}")
print(f"  TOTAL VIDEO (top {len(vid_files[:20])}): {sum(s for s,_ in vid_files[:20])/1e9:.2f}GB of {sum(s for s,_ in vid_files)/1e9:.2f}GB total")

print()
print("=" * 78)
print("ARCHIVES (often safe to delete if extracted)")
print("=" * 78)
arc_files = [(f.get("asize",0), f.get("name","")) for f in files
             if Path(f.get("name","")).suffix.lower() in {".zip",".rar",".7z",".tar",".gz",".bz2",".xz"}]
arc_files.sort(reverse=True)
for s, n in arc_files[:20]:
    print(f"  {s/1e9:>8.2f}GB  {n}")
print(f"  TOTAL ARCHIVES (top {len(arc_files[:20])}): {sum(s for s,_ in arc_files[:20])/1e9:.2f}GB of {sum(s for s,_ in arc_files)/1e9:.2f}GB total")

print()
print("=" * 78)
print("TEMP/CACHE FILES (almost always safe to delete)")
print("=" * 78)
tmp_files = [(f.get("asize",0), f.get("name","")) for f in files
             if Path(f.get("name","")).suffix.lower() in {".tmp",".temp",".bak",".old",".log",".cache",".crdownload",".part",".swp",".chk"}]
tmp_files.sort(reverse=True)
for s, n in tmp_files[:15]:
    print(f"  {s/1e9:>8.2f}GB  {n}")
print(f"  TOTAL TEMP (top {len(tmp_files[:15])}): {sum(s for s,_ in tmp_files[:15])/1e9:.2f}GB of {sum(s for s,_ in tmp_files)/1e9:.2f}GB total")
