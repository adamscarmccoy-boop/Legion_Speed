import os
import json
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

dirs = [
    r"c:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\exported_json",
    r"c:\WEB CASE STUDY\data",
    r"c:\WEB CASE STUDY\gdu_per_dir",
]

def search_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        upper_content = content.upper()
        if 'DIFFUSER' in upper_content:
            print(f"\n[MATCH IN] {filepath}")
            for m in re.finditer(r'.{0,150}diffuser.{0,150}', content, flags=re.IGNORECASE|re.DOTALL):
                print("..." + m.group(0).replace('\n', ' ') + "...")
    except Exception as e:
        pass

if __name__ == "__main__":
    count = 0
    for d in dirs:
        if os.path.exists(d):
            for root, _, files in os.walk(d):
                for file in files:
                    if file.endswith('.json'):
                        count += 1
                        search_json(os.path.join(root, file))
    print(f"\nSearched {count} JSON files directly.")

