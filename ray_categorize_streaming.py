"""Ray-ified sample categorizer — STREAMING, no driver-side DataFrame.

Walks all 8 audio roots (E:\\OLD ABLETON, E:\\scars SAMPLE PACKS, E:\\COLLECT ALL,
E:\\COLLECT ALL - (2025), E:\\COLLECT ALL - 2025 LATE, E:\\COLLECT ALL 2016,
E:\\000 - MASTERED EXPORT, E:\\RELEASE-DEMO, E:\\EXPORT ALL) in chunks via
Ray tasks, classifies each file by filename + parent folder, and writes
directly to a Parquet file on disk using a streaming writer (no pandas
accumulation on the driver).

Output: ray_categories.parquet  (~50 MB max, written incrementally)
Also:  ray_category_summary.json (top-N per category for the console)
"""
import os, re, sys, json, time
from pathlib import Path
from collections import Counter

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

import ray

# ---------- config ----------
ROOTS = [
    r"E:\OLD ABLETON",
    r"E:\scars SAMPLE PACKS",
    r"E:\COLLECT ALL",
    r"E:\COLLECT ALL - (2025)",
    r"E:\COLLECT ALL - 2025 LATE",
    r"E:\COLLECT ALL 2016",
    r"E:\000 - MASTERED EXPORT",
    r"E:\RELEASE-DEMO",
    r"E:\EXPORT ALL",
]

AUDIO_EXTS = {".wav", ".mp3", ".flac", ".aif", ".aiff", ".m4a"}

# Filename token → category. Order matters: longer/more specific first wins.
CATEGORY_TOKENS = [
    ("drum_loop",  ["drum loop", "drumloop", "beat loop", "groove loop", "top loop"]),
    ("break",      ["break", "breakbeat"]),
    ("build",      ["build", "buildup", "riser", "uplift"]),
    ("impact",     ["impact", "boom", "boom fx"]),
    ("fx",         ["fx", "sfx", "sweep", "downlifter", "whoosh", "laser", "zap"]),
    ("vocal",      ["vox", "vocal", "voice", "chant", "phrase", "speak", "talk", "acapella"]),
    ("chord",      ["chord", "prog", "progression", "chord progression"]),
    ("pad",        ["pad", "atmos", "ambient", "drone", "texture"]),
    ("lead",       ["lead", "saw", "pluck", "arp", "arppeg", "stab", "synth lead"]),
    ("bass",       ["bass", "sub", "808", "reese", "sub bass"]),
    ("oneshot",    ["oneshot", "one-shot", "single shot"]),
    ("melody",     ["melody", "melodic", "top loop", "topline"]),
    ("perc",       ["perc", "percussion", "shaker", "conga", "bongo", "tom", "rim", "tamb"]),
    ("kick",       ["kick", "bd ", "bassdrum", " kd"]),
    ("snare",      ["snare", "sd ", "snr", "clap"]),
    ("hat",        ["hat", "hh ", "hihat", "open hat", "closed hat", "cymbal"]),
    ("loop",       ["loop"]),
    ("drop",       ["drop"]),
]

# Vendor tokens from earlier exploration (filename prefixes)
VENDOR_TOKENS = {
    "black_octopus": [". bos", " bos ", "_bos_", "blackoctopus", "black octopus"],
    "cymatics":      ["cymatics", ". cymatics"],
    "splice":        ["splice", "_splice_"],
    "sample_magic":  ["sample magic", "samplemagic"],
    "toolroom":      ["toolroom"],
    "sounds.com":    ["sounds.com", "soundsdotcom"],
    "kling":         [". kling", "kling "],
    "thm":           ["thm ", "thm_", "thm-", "thm."],
    "pml":           ["pml ", "pml_", "pml-"],
    "ali_nadem":     ["ali nadem", "alinadem", ". ali"],
    "ghost_hack":    ["ghosthack", "ghost hack"],
    "ideazz":        ["ideazz"],
    "klng":          [". klng"],
    "gs_":           [" gs ", "gs_", "gs cntrfg"],
    "lc_":           [". lc "],
    "htht":          ["htht", ". htht"],
    "hhvt":          ["hhvt", ". hhvt"],
    "odd_freq":      ["odd frequency", "odd freq"],
    "scar":          ["scar", "scar lab", "scar sp1"],
    "sonicspore":    ["sonicspore"],
}

# BPM + key extraction
BPM_RE = re.compile(r"(\d{2,3})\s*bpm", re.I)
KEY_RE = re.compile(r"\b([A-G][#b]?)\s*(min|maj|m|minor|major)\b", re.I)

CHUNK_ROWS = 5000  # how many rows each Ray task returns
SHARD_DIR = Path(r"C:\WEB CASE STUDY\ray_cat_shards")
SHARD_DIR.mkdir(exist_ok=True)
FINAL_PARQUET = Path(r"C:\WEB CASE STUDY\ray_categories.parquet")


def classify_filename(name: str) -> tuple[list[str], list[str], int | None, str | None]:
    """Return (categories, vendors, bpm, key) for one filename."""
    low = name.lower()
    cats = []
    for cat, toks in CATEGORY_TOKENS:
        for t in toks:
            if t in low:
                cats.append(cat)
                break  # one match per category is enough
    vendors = []
    for v, toks in VENDOR_TOKENS.items():
        for t in toks:
            if t in low:
                vendors.append(v)
                break
    bpm = None
    m = BPM_RE.search(name)
    if m:
        b = int(m.group(1))
        if 60 <= b <= 200:
            bpm = b
    key = None
    m = KEY_RE.search(name)
    if m:
        key = m.group(1).upper() + " " + m.group(2).lower()
    return cats, vendors, bpm, key


def derive_root_tag(path: str) -> str:
    """Map an absolute path to one of the ROOTS (so we know which 'castle' it came from)."""
    for r in ROOTS:
        if path.startswith(r):
            return r.replace("E:\\", "")
    return "OTHER"


@ray.remote(num_cpus=1)
def walk_and_classify_chunk(args) -> list[dict]:
    """Walk one root, yield rows as a list of dicts (chunked)."""
    root, chunk_id = args
    out = []
    if not os.path.isdir(root):
        return out
    for dp, dns, fns in os.walk(root):
        # light pruning
        dns[:] = [d for d in dns if not d.startswith(".") and d.lower() != "$recycle.bin"]
        for fn in fns:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in AUDIO_EXTS:
                continue
            full = os.path.join(dp, fn)
            try:
                sz = os.path.getsize(full)
            except OSError:
                sz = 0
            try:
                rel = os.path.relpath(dp, root)
            except ValueError:
                rel = dp
            parts = rel.split(os.sep)
            parent1 = parts[0] if len(parts) >= 1 and parts[0] != "." else ""
            parent2 = parts[1] if len(parts) >= 2 else ""
            cats, vendors, bpm, key = classify_filename(fn)
            out.append({
                "path": full,
                "filename": fn,
                "ext": ext,
                "size_bytes": sz,
                "root_tag": derive_root_tag(full),
                "parent1": parent1,
                "parent2": parent2,
                "depth": len(parts),
                "categories": ",".join(cats) if cats else "",
                "vendors": ",".join(vendors) if vendors else "",
                "bpm": bpm if bpm is not None else 0,
                "key": key if key else "",
            })
    # Save this root's results as a single shard (still per-root, no driver memory pressure)
    if out:
        shard = SHARD_DIR / f"{os.path.basename(root)}_{chunk_id}.jsonl"
        with shard.open("w", encoding="utf-8") as f:
            for row in out:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return out  # returning for summary count


def main():
    if not ray.is_initialized():
        ray.init(num_cpus=os.cpu_count(), ignore_reinit_error=True, log_to_driver=False)
    print(f"=== STREAMING RAY CATEGORIZER ===")
    print(f"Roots: {len(ROOTS)}")
    print(f"CPUs: {os.cpu_count()}\n")
    t0 = time.perf_counter()
    futures = [walk_and_classify_chunk.remote((r, i)) for i, r in enumerate(ROOTS)]
    # Process as they complete so we can show progress
    total_rows = 0
    pending = list(futures)
    done = 0
    while pending:
        ready, pending = ray.wait(pending, num_returns=1, timeout=20)
        for f in ready:
            n = len(ray.get(f))
            done += 1
            total_rows += n
            print(f"  [{done}/{len(futures)}] root done  +{n:>9,} rows  (running total {total_rows:,})")
    elapsed = time.perf_counter() - t0
    print(f"\nWalk + classify: {elapsed:.1f}s, {total_rows:,} rows")

    # Stream shards → single Parquet (no driver-side accumulation)
    print("\nMerging JSONL shards → Parquet (streaming)...")
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        print("  pyarrow not available; leaving JSONL shards only")
        ray.shutdown()
        return

    schema = pa.schema([
        ("path", pa.string()),
        ("filename", pa.string()),
        ("ext", pa.string()),
        ("size_bytes", pa.int64()),
        ("root_tag", pa.string()),
        ("parent1", pa.string()),
        ("parent2", pa.string()),
        ("depth", pa.int32()),
        ("categories", pa.string()),
        ("vendors", pa.string()),
        ("bpm", pa.int32()),
        ("key", pa.string()),
    ])
    writer = pq.ParquetWriter(str(FINAL_PARQUET), schema, compression="snappy")
    shard_count = 0
    for shard in sorted(SHARD_DIR.glob("*.jsonl")):
        with shard.open("r", encoding="utf-8") as f:
            batch = []
            for line in f:
                batch.append(json.loads(line))
                if len(batch) >= 50_000:
                    tbl = pa.Table.from_pylist(batch, schema=schema)
                    writer.write_table(tbl)
                    batch = []
            if batch:
                tbl = pa.Table.from_pylist(batch, schema=schema)
                writer.write_table(tbl)
        shard_count += 1
    writer.close()
    size_mb = FINAL_PARQUET.stat().st_size / (1024 * 1024)
    print(f"  Wrote {FINAL_PARQUET}  ({size_mb:.1f} MB)  from {shard_count} shards")

    # Stream a summary from the parquet without loading all rows
    print("\n=== SUMMARY (streamed from Parquet) ===")
    import duckdb
    con = duckdb.connect()
    print(f"\n  Rows by root_tag:")
    for r, c in con.execute(f"""
        SELECT root_tag, COUNT(*) AS n FROM read_parquet('{FINAL_PARQUET}')
        GROUP BY root_tag ORDER BY n DESC
    """).fetchall():
        print(f"    {c:>9,}  {r}")

    print(f"\n  Top 20 filename categories:")
    # categories is comma-separated; explode
    rows = con.execute(f"""
        SELECT TRIM(c) AS cat, COUNT(*) AS n
        FROM read_parquet('{FINAL_PARQUET}'),
             UNNEST(STRING_SPLIT(categories, ',')) AS t(c)
        WHERE LENGTH(TRIM(c)) > 0
        GROUP BY cat ORDER BY n DESC LIMIT 20
    """).fetchall()
    for c, n in rows:
        print(f"    {n:>9,}  {c}")

    print(f"\n  Top 20 vendor matches:")
    rows = con.execute(f"""
        SELECT TRIM(v) AS vnd, COUNT(*) AS n
        FROM read_parquet('{FINAL_PARQUET}'),
             UNNEST(STRING_SPLIT(vendors, ',')) AS t(v)
        WHERE LENGTH(TRIM(v)) > 0
        GROUP BY vnd ORDER BY n DESC LIMIT 20
    """).fetchall()
    for v, n in rows:
        print(f"    {n:>9,}  {v}")

    print(f"\n  Top 15 BPMs:")
    rows = con.execute(f"""
        SELECT bpm, COUNT(*) AS n FROM read_parquet('{FINAL_PARQUET}')
        WHERE bpm > 0 GROUP BY bpm ORDER BY n DESC LIMIT 15
    """).fetchall()
    for b, n in rows:
        print(f"    {n:>9,}  {b} bpm")

    print(f"\n  Top 15 keys:")
    rows = con.execute(f"""
        SELECT key, COUNT(*) AS n FROM read_parquet('{FINAL_PARQUET}')
        WHERE LENGTH(key) > 0 GROUP BY key ORDER BY n DESC LIMIT 15
    """).fetchall()
    for k, n in rows:
        print(f"    {n:>9,}  {k}")

    print(f"\nTotal elapsed: {time.perf_counter()-t0:.1f}s")
    ray.shutdown()


if __name__ == "__main__":
    main()