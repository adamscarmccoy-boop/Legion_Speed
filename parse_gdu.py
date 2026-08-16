"""Parse gdu JSON output and show top offenders by category."""
import json
from pathlib import Path

data = json.loads(Path(r"C:\WEB CASE STUDY\e_gdu.json").read_text(encoding="utf-8"))

# Root tree
def walk(node, depth=0, max_depth=3):
    if depth > max_depth: return
    name = node.get("name", "")
    size = node.get("size", 0)
    item_count = node.get("item_count", 0)
    is_dir = node.get("is_dir", False)
    if not is_dir and depth == 0: return
    if depth == 0:
        print(f"{size/1e9:>10.2f}GB  ({item_count:>7,} items)  {name or '<root>'}")
    else:
        indent = "  " * depth
        print(f"{size/1e9:>10.2f}GB  ({item_count:>7,} items)  {indent}{name}")
    if is_dir:
        children = sorted(node.get("children", []) or [], key=lambda x: -x.get("size", 0))
        for c in children[:30]:
            walk(c, depth+1, max_depth)

# Aggregate by extension
ext_total = {}
ext_count = {}
def walk_ext(node):
    n = node.get("name", "")
    s = node.get("size", 0)
    is_dir = node.get("is_dir", False)
    if is_dir:
        for c in node.get("children", []) or []:
            walk_ext(c)
    else:
        ext = Path(n).suffix.lower() or "<no-ext>"
        ext_total[ext] = ext_total.get(ext, 0) + s
        ext_count[ext] = ext_count.get(ext, 0) + 1

# Aggregate by category (better rules)
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
    return f"Other ({e})"

cat_total = {}
cat_files = {}
def walk_cat(node):
    n = node.get("name", "")
    s = node.get("size", 0)
    is_dir = node.get("is_dir", False)
    if is_dir:
        for c in node.get("children", []) or []:
            walk_cat(c)
    else:
        cat = classify(n)
        cat_total[cat] = cat_total.get(cat, 0) + s
        cat_files.setdefault(cat, []).append((n, s))

print("=== TOP 30 BY EXTENSION ===")
for ext, total in sorted(ext_total.items(), key=lambda x: -x[1])[:30]:
    cnt = ext_count[ext]
    avg = total / cnt if cnt else 0
    print(f"  {total/1e9:>8.2f}GB  {cnt:>9,} files  (avg {avg/1e6:>6.2f}MB)  {ext}")

print("\n=== TOP CATEGORIES ===")
for cat, total in sorted(cat_total.items(), key=lambda x: -x[1])[:25]:
    cnt = len(cat_files[cat])
    print(f"  {total/1e9:>8.2f}GB  {cnt:>9,} files  {cat}")

print("\n=== TOP 10 BIGGEST SINGLE FILES ===")
all_files = []
def gather_files(node):
    if not node.get("is_dir", False):
        all_files.append((node.get("name",""), node.get("size",0), node.get("path","")))
    else:
        for c in node.get("children", []) or []:
            gather_files(c)
gather_files(data)
all_files.sort(key=lambda x: -x[1])
for n, s, p in all_files[:20]:
    print(f"  {s/1e9:>8.2f}GB  {p}")

# Old Ableton deep dive - top subdirs by size
print("\n=== OLD ABLETON TOP-LEVEL SUBDIRS ===")
root_children = data.get("children", []) or []
for top in root_children:
    if top.get("name") == "OLD ABLETON":
        for c in sorted(top.get("children", []) or [], key=lambda x: -x.get("size",0))[:15]:
            print(f"  {c.get('size',0)/1e9:>8.2f}GB  ({c.get('item_count',0):>7,} items)  OLD ABLETON\\{c.get('name','')}")
        break

# APP folder deep dive (where ML models live)
print("\n=== APP FOLDER DEEP DIVE ===")
for top in root_children:
    if top.get("name") == "APP":
        def show(n, d=0):
            if d > 3: return
            print(f"  {n.get('size',0)/1e9:>8.2f}GB  ({n.get('item_count',0):>7,} items)  " + ("  "*d) + n.get("name",""))
            for c in sorted(n.get("children", []) or [], key=lambda x: -x.get("size",0))[:10]:
                show(c, d+1)
        for c in sorted(top.get("children", []) or [], key=lambda x: -x.get("size",0))[:15]:
            show(c)
        break
