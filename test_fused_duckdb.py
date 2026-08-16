import duckdb

print("=== Probing web_intel_sonicdb.duckdb for Streaming Stats ===")
try:
    conn = duckdb.connect("C:/WEB CASE STUDY/web_intel_sonicdb.duckdb")
    
    # Check spotify_charts_daily
    print("\n--- spotify_charts_daily ---")
    row_count = conn.execute("SELECT COUNT(*) FROM spotify_charts_daily").fetchone()[0]
    print(f"Total Rows: {row_count}")
    if row_count > 0:
        cols = conn.execute("PRAGMA table_info('spotify_charts_daily')").fetchall()
        print("Columns:", [c[1] for c in cols])
        print("First 5 rows:")
        rows = conn.execute("SELECT * FROM spotify_charts_daily LIMIT 5").fetchall()
        for r in rows:
            print(" ", r)
            
    # Check listenbrainz_ground_truth
    print("\n--- listenbrainz_ground_truth ---")
    row_count_lb = conn.execute("SELECT COUNT(*) FROM listenbrainz_ground_truth").fetchone()[0]
    print(f"Total Rows: {row_count_lb}")
    if row_count_lb > 0:
        cols_lb = conn.execute("PRAGMA table_info('listenbrainz_ground_truth')").fetchall()
        print("Columns:", [c[1] for c in cols_lb])
        print("First 5 rows:")
        rows_lb = conn.execute("SELECT * FROM listenbrainz_ground_truth LIMIT 5").fetchall()
        for r in rows_lb:
            print(" ", r)
            
    # Check if there is any other table with 'score' or 'spotify' or 'apple' in it
    tables = conn.execute("SHOW TABLES").fetchall()
    print("\nAll Available Tables in DB:", [t[0] for t in tables])
    
except Exception as e:
    print("Database probe failed:", e)
