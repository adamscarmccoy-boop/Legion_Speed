import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def scan_native_files():
    start_time = time.time()
    
    search_roots = [
        r"C:\WEB CASE STUDY",
        r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline"
    ]
    
    valid_exts = {".cpp", ".hpp", ".h", ".cu", ".cuh", ".c", ".cxx", ".bin", ".pyd"}
    skip_dirs = {".venv", ".venv_314", "node_modules", ".git", "build", "dist", "__pycache__"}
    
    discovered = []
    for root_dir in search_roots:
        if not os.path.exists(root_dir):
            continue
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".venv")]
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in valid_exts:
                    full_p = os.path.join(root, f)
                    try:
                        sz = os.path.getsize(full_p)
                    except Exception:
                        sz = 0
                    discovered.append({
                        "filename": f,
                        "extension": ext,
                        "size_bytes": sz,
                        "full_path": full_p
                    })
                    
    elapsed_ms = round((time.time() - start_time) * 1000, 2)
    
    print("=" * 70)
    print(f"🏛️ SOVEREIGN C++ & NATIVE SOURCE MANIFEST (SCAN TIME: {elapsed_ms} ms)")
    print("=" * 70)
    print(f"Total Native Source/Header Files Discovered: {len(discovered)}\n")
    
    # Group by extension
    ext_groups = {}
    for d in discovered:
        ext_groups.setdefault(d["extension"], []).append(d)
        
    for ext, items in sorted(ext_groups.items()):
        print(f"📦 [{ext.upper()}] — {len(items)} files:")
        for item in items[:15]:
            print(f"   • {item['filename']} ({item['size_bytes']} bytes) -> {item['full_path']}")
        if len(items) > 15:
            print(f"   ... and {len(items) - 15} more {ext} files.")
        print("-" * 50)
        
    print("=" * 70)

if __name__ == "__main__":
    scan_native_files()
