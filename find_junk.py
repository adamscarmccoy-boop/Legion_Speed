"""Find temp/cache/hidden/macOS metadata on E:\\."""
import os, json
from pathlib import Path
from collections import defaultdict

E = Path("E:/")
SKIP = {"$RECYCLE.BIN", "System Volume Information"}

# Categories of "safe to delete" files
TEMP_EXTS = {".tmp", ".temp", ".bak", ".old", ".orig", ".crdownload",
             ".part", ".swp", ".swo", ".chk", ".log"}
CACHE_EXTS = {".cache"}
# Hidden files (start with .) — but exclude .well-known, .git (handled in dirs)
# Mac resource forks: filename starts with "._"
# Mac metadata: .DS_Store, ._filename, .Spotlight-V100, .fseventsd, .Trashes
MAC_FILES = {".DS_Store", ".AppleDouble", ".AppleDesktop", ".LSOverride",
             "._.DS_Store", "Thumbs.db", "ehthumbs.db", "ehthumbs_vista.db",
             "Desktop.ini", "folder.ico"}
# Hidden dirs (skip most, scan some)
JUNK_DIRS = {".Spotlight-V100", ".fseventsd", ".Trashes",
             "$RECYCLE.BIN", "System Volume Information",
             "FOUND.000", "FOUND.001", "FOUND.002", "FOUND.003",
             "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache",
             "node_modules", ".cache"}

categories = defaultdict(list)
total_bytes = 0

# Build the delete list separately so JSON write always works
delete_list = []

for dp, dns, fns in os.walk(E, onerror=lambda e: None):
    # Filter junk dirs but record them
    real_dns = []
    for d in dns:
        if d in SKIP or d.startswith("$"):
            categories["junk_dir"].append((0, str(Path(dp) / d) + "\\"))
            continue
        if d in JUNK_DIRS:
            # peek inside? Just record the dir as junk
            categories["junk_dir"].append((0, str(Path(dp) / d) + "\\"))
            continue
        real_dns.append(d)
    dns[:] = real_dns

    for fn in fns:
        fp = Path(dp) / fn
        low = fn.lower()
        size = 0
        try:
            st = fp.stat()
            size = st.st_size
        except (OSError, PermissionError):
            continue

        # 1. macOS resource forks (._filename)
        if fn.startswith("._") and len(fn) > 2:
            categories["mac_resource_fork"].append((size, str(fp)))
            total_bytes += size
            continue

        # 2. macOS / Windows metadata files
        if fn in MAC_FILES:
            categories["system_metadata_file"].append((size, str(fp)))
            total_bytes += size
            continue

        # 3. Temp extensions
        ext = fp.suffix.lower()
        if ext in TEMP_EXTS:
            categories[f"temp_ext_{ext}"].append((size, str(fp)))
            total_bytes += size
            continue

        # 4. Cache extensions
        if ext in CACHE_EXTS:
            categories["cache_ext"].append((size, str(fp)))
            total_bytes += size
            continue

        # 5. Hidden files (Unix-style, .foo)
        if fn.startswith(".") and fn not in MAC_FILES and not fn.startswith(".."):
            categories["hidden_dotfile"].append((size, str(fp)))
            total_bytes += size
            continue

print(f"Total junk candidates: {total_bytes/1e9:.2f} GB across "
      f"{sum(len(v) for v in categories.values()):,} items\n")

# Sort each category by size, descending
print("=" * 80)
print("JUNK BREAKDOWN BY CATEGORY")
print("=" * 80)
for cat in sorted(categories, key=lambda c: -sum(s for s,_ in categories[c])):
    items = categories[cat]
    total = sum(s for s,_ in items)
    print(f"\n--- {cat}: {total/1e6:.2f} MB across {len(items)} items ---")
    for s, p in sorted(items, key=lambda x: -x[0])[:15]:
        # Replace non-encodable chars
        p_safe = p.encode('ascii', 'replace').decode('ascii')
        print(f"  {s/1024:>10.1f} KB  {p_safe}")
    if len(items) > 15:
        print(f"  ... and {len(items)-15} more")

# Save detailed JSON for deletion script
out_path = Path(r"C:\WEB CASE STUDY\junk_candidates.json")
import io
buf = io.StringIO()
json.dump(out, buf, indent=2, ensure_ascii=False)
out_path.write_text(buf.getvalue(), encoding='utf-8')
print(f"\nWrote junk_candidates.json with {len(out):,} entries")
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
