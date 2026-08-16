import json
from collections import Counter
data = json.loads(open(r'C:\WEB CASE STUDY\junk_candidates.json', encoding='utf-8').read())
by_cat = Counter(d['category'] for d in data)
total = sum(d['size'] for d in data)
print(f'Total entries: {len(data):,}')
print(f'Total bytes:  {total/1e9:.2f} GB')
print()
for cat, n in by_cat.most_common():
    sz = sum(d['size'] for d in data if d['category']==cat)
    print(f'  {n:>8,} entries  {sz/1e6:>8.2f} MB  {cat}')

# sample of mac_resource_fork entries
print()
print('=== sample mac_resource_fork entries ===')
samples = [d for d in data if d['category']=='mac_resource_fork'][:20]
for d in samples:
    size = d['size']
    path = d['path']
    print(f'  {size:>8} bytes  {path}')

# Distribution by top-level dir
print()
print('=== top-level dir distribution of mac_resource_fork entries ===')
topdirs = Counter()
for d in data:
    if d['category'] == 'mac_resource_fork':
        parts = d['path'].split('\\', 3)
        top = parts[3] if len(parts) > 3 else (parts[-1] if parts else '?')
        topdirs[top] += 1
for t, n in topdirs.most_common(15):
    print(f'  {n:>8,}  E:\\{t}')
