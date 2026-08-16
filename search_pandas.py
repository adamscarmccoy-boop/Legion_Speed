import pandas as pd
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

df = pd.read_parquet(r"C:\WEB CASE STUDY\takeout_raw.parquet")
print("Columns:", df.columns)

text_col = [c for c in df.columns if c in ['text', 'content', 'raw_text', 'body', 'text_chunk', 'html', 'document']][0]
matches = df[df[text_col].str.contains('ai studio|gemma|junction', case=False, na=False)]

print(f"Found {len(matches)} matches in column {text_col}.")

for idx, row in matches.iterrows():
    print(f"\n[{row.get('filename', 'unknown')} | {row.get('filepath', 'unknown')}]")
    text = row[text_col]
    import re
    # Extract the window around match
    for m in re.finditer(r'.{0,350}(?:ai studio|gemma|junction).{0,350}', text, flags=re.IGNORECASE|re.DOTALL):
        print("..." + m.group(0).replace('\n', ' ') + "...")

