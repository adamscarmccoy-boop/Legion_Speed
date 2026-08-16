import duckdb
import pandas as pd

con = duckdb.connect(r'C:\WEB CASE STUDY\web_intel_sonicdb.duckdb', read_only=True)

print('=== Searching core_paths for OLD ABLETON / sample pack roots ===')
roots = con.execute("""
    SELECT 
        split_part(filepath, '\\', 1) AS drive,
        split_part(filepath, '\\', 2) AS root,
        split_part(filepath, '\\', 3) AS sub,
        COUNT(*) AS files
    FROM core_paths
    WHERE filepath LIKE '%ABLETON%'
       OR filepath LIKE '%SAMPLE%'
       OR filepath LIKE '%scars SAMPLE%'
       OR filepath LIKE '%COLLECT%'
       OR filepath LIKE '%MASTERED EXPORT%'
    GROUP BY drive, root, sub
    ORDER BY files DESC
    LIMIT 30
""").fetchall()
for r in roots:
    print(f'  {r[0]:<4}\\{r[1]:<25}\\{r[2]:<30} {r[3]} files')

print()
print('=== Total files matching "OLD ABLETON" anywhere ===')
for kw in ['OLD ABLETON', 'SAMPLE', 'COLLECT', 'scars', 'MASTERED EXPORT']:
    cnt = con.execute(f"SELECT COUNT(*) FROM core_paths WHERE filepath LIKE '%{kw}%'").fetchone()[0]
    print(f'  {kw:<25} {cnt} files')

print()
print('=== audio_features joined with core_paths sample ===')
rows = con.execute("""
    SELECT 
        cp.filepath,
        af.bpm,
        af.key_signature,
        af.genre_class,
        af.vibe_tags,
        af.rms_db,
        af.crest_factor
    FROM core_paths cp
    LEFT JOIN audio_features af ON cp.filepath = af.filepath
    WHERE cp.filepath LIKE '%OLD ABLETON%' OR cp.filepath LIKE '%SAMPLE%'
    LIMIT 10
""").fetchall()
for r in rows:
    print(' ', ' | '.join(str(c)[:50] for c in r))

print()
print('=== sonic_dna sample (real DSP signature data) ===')
rows = con.execute("""
    SELECT * FROM sonic_dna LIMIT 3
""").fetchall()
cols = [d[0] for d in con.execute('DESCRIBE sonic_dna').fetchall()]
print(' cols:', cols)
for r in rows:
    print(' ', ' | '.join(str(c)[:50] for c in r))

con.close()