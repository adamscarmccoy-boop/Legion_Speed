import sys
sys.stdout.reconfigure(encoding='utf-8')
import duckdb
import pandas as pd

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

con = duckdb.connect()

parquet_path = r'C:\WEB CASE STUDY\ray_categories.parquet'
con.execute(f"CREATE TABLE ray_data AS SELECT * FROM '{parquet_path}'")

print('='*60)
print(' 🚀 DUCKDB ANALYTICS: RAY CATEGORY PARQUET (393,419 FILES)')
print('='*60)

print('\n📊 1. STORAGE DISTRIBUTION BY ROOT FOLDER:')
df1 = con.execute("""
    SELECT root_tag, 
           COUNT(*) as total_files, 
           ROUND(SUM(size_bytes) / 1024 / 1024 / 1024, 2) as size_gb 
    FROM ray_data 
    GROUP BY root_tag 
    ORDER BY size_gb DESC
""").fetchdf()
print(df1.to_string(index=False))

print('\n🎧 2. TOP AUDIO CATEGORIES FOUND:')
df2 = con.execute("""
    SELECT categories, COUNT(*) as count 
    FROM ray_data 
    WHERE categories IS NOT NULL AND categories != '' AND categories != '[]'
    GROUP BY categories 
    ORDER BY count DESC 
    LIMIT 10
""").fetchdf()
print(df2.to_string(index=False))

print('\n🏢 3. TOP SAMPLE VENDORS DETECTED:')
df3 = con.execute("""
    SELECT vendors, COUNT(*) as count 
    FROM ray_data 
    WHERE vendors IS NOT NULL AND vendors != '' AND vendors != '[]'
    GROUP BY vendors 
    ORDER BY count DESC 
    LIMIT 10
""").fetchdf()
print(df3.to_string(index=False))

print('\n🔥 4. BPM DISTRIBUTION:')
df4 = con.execute("""
    SELECT bpm, COUNT(*) as count 
    FROM ray_data 
    WHERE bpm IS NOT NULL AND bpm != '' AND TRY_CAST(bpm AS DOUBLE) BETWEEN 60 AND 180
    GROUP BY bpm 
    ORDER BY count DESC 
    LIMIT 10
""").fetchdf()
print(df4.to_string(index=False))

print('\n📁 5. FILE EXTENSION DISTRIBUTION:')
df5 = con.execute("""
    SELECT ext, COUNT(*) as count 
    FROM ray_data 
    GROUP BY ext 
    ORDER BY count DESC 
    LIMIT 10
""").fetchdf()
print(df5.to_string(index=False))
