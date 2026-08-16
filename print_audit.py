import json
j = json.loads(open(r"C:\WEB CASE STUDY\e_drive_audit.json", encoding="utf-8").read())

print("=== DRIVE ===")
print(f"Total: {j['drive_total_gb']} GB  Free: {j['drive_free_gb']} GB\n")

print("=== TOP 15 BIGGEST DIRS ON E ===")
for d in j["big_dirs"][:15]:
    print(f"  {d['size_h']:>10}  {d['dir']}")

print("\n=== TOP 15 LARGEST FILES ===")
for f in j["large_files"][:15]:
    print(f"  {f['size_h']:>10}  {f['path']}")

print("\n=== TRASH SUMMARY ===")
s = j["summary"]
print(f"  Files scanned: {s['files_scanned']:,}")
print(f"  Trash candidates shown: {s['trash_candidates_shown']} (total {s['trash_candidates_total_h']})")
print(f"  Large files shown: {s['large_files_shown']}")
print(f"  Stale files shown: {s['stale_files_shown']}")
print(f"  Errors during scan: {s['errors_during_scan']}")

# Breakdown of trash by reason
from collections import Counter
reasons = Counter()
for t in j["trash_candidates"]:
    reasons[t["reason"]] += 1
print("\n  Trash by reason:")
for r, n in reasons.most_common():
    print(f"    {n:>5}  {r}")
