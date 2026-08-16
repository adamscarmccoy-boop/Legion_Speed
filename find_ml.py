"""Walk E:\\ looking for ML model files of any size."""
import os, json, sys
from pathlib import Path

ML_EXTS = {".bin", ".pt", ".pth", ".th", ".onnx", ".safetensors", ".ckpt", ".h5", ".gguf", ".tflite"}
SKIP_DIRS = {"$RECYCLE.BIN", "System Volume Information", ".Spotlight-V100",
             ".fseventsd", ".Trashes", "node_modules", ".venv"}

# Also search the canonical ML model spots
SEARCH_ROOTS = [
    Path(r"E:\APP"),
    Path(r"E:\APP\WEIGHTS"),
    Path(r"E:\APP\SANDBOX\workspace\models"),
    Path(r"E:\APP\SANDBOX"),
    Path(r"E:\OLD ABLETON"),
    Path(r"E:\OTHER"),
    Path(r"E:\DOWNLOAD"),
    Path(r"E:\ableton-session-intelligence"),
    Path(r"C:\WEB CASE STUDY"),
    Path(r"E:\AGENTS"),
]

hits = []
bytes_total = 0

for root in SEARCH_ROOTS:
    if not root.exists():
        continue
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS and not d.startswith("__pycache__")]
        for fn in fns:
            ext = Path(fn).suffix.lower()
            if ext in ML_EXTS:
                fp = Path(dp) / fn
                try:
                    sz = fp.stat().st_size
                except (OSError, PermissionError):
                    continue
                hits.append((sz, str(fp), ext))
                bytes_total += sz

hits.sort(key=lambda x: -x[0])

print(f"ML models found on E:\\: {len(hits)} files, {bytes_total/1e9:.2f} GB total\n")
print(f"{'Size':>10}  {'Ext':<12}  Path")
print("-" * 100)
for sz, path, ext in hits:
    print(f"{sz/1e9:>9.2f}GB  {ext:<12}  {path}")

# Also dump a JSON
Path(r"C:\WEB CASE STUDY\ml_models_found.json").write_text(
    json.dumps([{"path": p, "size": s, "ext": e, "size_h": f"{s/1e9:.2f}GB"} for s,p,e in hits], indent=2)
)
print(f"\nWrote ml_models_found.json")
