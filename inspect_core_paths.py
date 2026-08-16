import duckdb
con = duckdb.connect(r'C:\WEB CASE STUDY\web_intel_sonicdb.duckdb', read_only=True)

print('=== core_paths schema ===')
for r in con.execute('DESCRIBE core_paths').fetchall():
    print(' ', r[0], '|', r[1])
print()

print('=== core_paths sample (5 rows) ===')
cols = [d[0] for d in con.execute('DESCRIBE core_paths').fetchall()]
print(' | '.join(cols))
for r in con.execute('SELECT * FROM core_paths LIMIT 5').fetchall():
    print(' | '.join(str(c)[:60] for c in r))
print()

print('=== E:/ paths ===')
for col in ['filepath', 'path']:
    try:
        cnt = con.execute(f"SELECT COUNT(*) FROM core_paths WHERE CAST({col} AS VARCHAR) LIKE 'E:%'").fetchone()[0]
        print(f'  Rows with {col} LIKE E:% :', cnt)
    except Exception as e:
        print(f'  {col} ERR {e}')

print()
print('=== Distinct folder roots under E:\\ ===')
try:
    rows = con.execute("""
        SELECT 
            split_part(CAST(filepath AS VARCHAR), '\\', 3) AS root
        FROM core_paths 
        WHERE CAST(filepath AS VARCHAR) LIKE 'E:%' OR CAST(filepath AS VARCHAR) LIKE 'e:%'
        GROUP BY root
        ORDER BY root
    """).fetchall()
    for r in rows:
        print(' ', r[0])
except Exception as e:
    print('ERR:', e)

print()
print('=== Counts by file extension ===')
try:
    rows = con.execute("""
        SELECT 
            LOWER(split_part(CAST(filepath AS VARCHAR), '.', -1)) AS ext,
            COUNT(*) AS cnt
        FROM core_paths
        GROUP BY ext
        ORDER BY cnt DESC
    """).fetchall()
    for r in rows:
        print(f'  .{r[0]:<8} {r[1]}')
except Exception as e:
    print('ERR:', e)

print()
print('=== Sample E:\\ rows (first 5) ===')
rows = con.execute("""
    SELECT * FROM core_paths 
    WHERE CAST(filepath AS VARCHAR) LIKE 'E:%' OR CAST(filepath AS VARCHAR) LIKE 'e:%'
    LIMIT 5
""").fetchall()
for r in rows:
    print(' ', ' | '.join(str(c)[:80] for c in r[:6]))

con.close()