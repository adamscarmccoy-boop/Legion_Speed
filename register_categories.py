"""Register ray_categories.parquet as a DuckDB view in sonic_core_v2.duckdb
so the LangGraph orchestrator's query_sonic_core tool can read it.

Also: register mined_code.parquet and audio_features.parquet (the other
two lakehouse files the fire test showed existed).
"""
import os, duckdb
from pathlib import Path

DB = r"C:\STUDIES_BACKUP\data\metadata\sonic_core_v2.duckdb"
LAKEHOUSE = Path(r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lakehouse_data")
CATEGORIES = Path(r"C:\WEB CASE STUDY\ray_categories.parquet")

# Open writable (we're adding views)
con = duckdb.connect(DB)
print(f"Connected to: {DB}")
print(f"Existing tables/views:")
for row in con.execute(
    "SELECT table_type, table_name FROM information_schema.tables "
    "WHERE table_schema='main' ORDER BY table_type, table_name"
).fetchall():
    print(f"  [{row[0]:<5}] {row[1]}")

# Register each Parquet as a view
views = {
    "mined_code":       str(LAKEHOUSE / "mined_code.parquet"),
    "audio_features":   str(LAKEHOUSE / "audio_features.parquet"),
    "mined_music":      str(LAKEHOUSE / "mined_music.parquet"),
    "sample_categories": str(CATEGORIES),
}

print("\nRegistering views:")
for name, path in views.items():
    if not os.path.exists(path):
        print(f"  SKIP {name}: {path} not found")
        continue
    # Drop & recreate so re-runs are idempotent
    con.execute(f'DROP VIEW IF EXISTS "{name}"')
    con.execute(
        f"CREATE VIEW \"{name}\" AS SELECT * FROM read_parquet('{path}')"
    )
    n = con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
    print(f"  OK  {name:<20} -> {n:>9,} rows  ({path})")

# Sanity: can we actually query it like the LangGraph would?
print("\n=== SAMPLE LANGGRAPH-STYLE QUERIES ===")
for q, label in [
    ('SELECT COUNT(*) FROM sample_categories', 'total categorized files'),
    ('SELECT root_tag, COUNT(*) AS n FROM sample_categories '
     'GROUP BY root_tag ORDER BY n DESC LIMIT 10', 'by root'),
    ('SELECT TRIM(c) AS cat, COUNT(*) AS n FROM sample_categories, '
     'UNNEST(STRING_SPLIT(categories, \',\')) AS t(c) '
     'WHERE LENGTH(TRIM(c))>0 GROUP BY cat ORDER BY n DESC LIMIT 10', 'top categories'),
    ('SELECT TRIM(v) AS vnd, COUNT(*) AS n FROM sample_categories, '
     'UNNEST(STRING_SPLIT(vendors, \',\')) AS t(v) '
     'WHERE LENGTH(TRIM(v))>0 GROUP BY vnd ORDER BY n DESC LIMIT 10', 'top vendors'),
    ('SELECT bpm, COUNT(*) AS n FROM sample_categories WHERE bpm>0 '
     'GROUP BY bpm ORDER BY n DESC LIMIT 5', 'top BPMs'),
    ('SELECT * FROM sample_categories WHERE categories LIKE \'%kick%\' '
     'AND bpm BETWEEN 124 AND 130 LIMIT 3', '128-bpm kicks (sample rows)'),
]:
    print(f"\n  -- {label}")
    rows = con.execute(q).fetchall()
    if not rows:
        print("    (no rows)")
        continue
    cols = [d[0] for d in con.execute(q).description]
    widths = [max(len(str(c)), max((len(str(r[i])) for r in rows), default=0)) for i, c in enumerate(cols)]
    print("    " + " | ".join(c.ljust(w) for c, w in zip(cols, widths)))
    print("    " + "-+-".join("-" * w for w in widths))
    for r in rows[:5]:
        print("    " + " | ".join(str(x).ljust(w) for x, w in zip(r, widths)))

print("\n=== FINAL DB STATE ===")
for row in con.execute(
    "SELECT table_type, table_name FROM information_schema.tables "
    "WHERE table_schema='main' ORDER BY table_type, table_name"
).fetchall():
    print(f"  [{row[0]:<5}] {row[1]}")

new_size = os.path.getsize(DB)
print(f"\nDB size after: {new_size:,} bytes  ({new_size/1024:.1f} KB)")
con.close()
