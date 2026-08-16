import os
import json
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

GDU_DIR = r"C:\WEB CASE STUDY\gdu_per_dir"
SEARCH_TERMS = [".cpp", "engine", "sovereign", "wasapi", "pedalboard"]

def scan_gdu_json():
    if not os.path.exists(GDU_DIR):
        print(f"Dir not found: {GDU_DIR}")
        return

    print(f"Scanning {GDU_DIR} for terms...")
    
    files = [os.path.join(root, f) for root, _, fs in os.walk(GDU_DIR) for f in fs if f.endswith('.json')]
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                for term in SEARCH_TERMS:
                    if term.lower() in content.lower():
                        print(f"HIT: {term} in {file_path}")
                        # Print a small snippet
                        idx = content.lower().find(term.lower())
                        print(f"  Snippet: ...{content[max(0, idx-50):idx+100]}...")
        except Exception as e:
            pass

if __name__ == "__main__":
    scan_gdu_json()
