import os
import sys

TARGET_DIR = r"C:\WEB CASE STUDY"
OLD_STRINGS = [
    "text-embedding-snowflake-arctic-embed-l-v2.0",
    "text-embedding-snowflake-arctic-embed-l-v2.0",
]
NEW_STRING = "text-embedding-snowflake-arctic-embed-l-v2.0"

modified_files = []
scanned_count = 0

for root, dirs, files in os.walk(TARGET_DIR):
    # Skip virtual environments and hidden dirs
    if any(skip in root for skip in [".venv", "node_modules", ".git", ".gemini"]):
        continue
        
    for fname in files:
        if fname.endswith((".py", ".ts", ".js", ".json", ".ipynb")):
            scanned_count += 1
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                new_content = content
                changed = False
                for old in OLD_STRINGS:
                    if old in new_content:
                        new_content = new_content.replace(old, NEW_STRING)
                        changed = True
                
                if changed:
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    modified_files.append(fpath)
            except Exception as e:
                print(f"Error processing {fpath}: {e}")

print(f"=== REPLACEMENT COMPLETE ===")
print(f"Scanned: {scanned_count} code files")
print(f"Updated: {len(modified_files)} files with standardized identifier '{NEW_STRING}':")
for mf in modified_files:
    print(f"  - {mf}")
