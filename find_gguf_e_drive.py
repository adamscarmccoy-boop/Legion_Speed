import json
import os

json_path = r"C:\WEB CASE STUDY\e_drive_audit.json"

def find_ggufs_in_audit():
    if not os.path.exists(json_path):
        print(f"Audit file not found: {json_path}")
        return

    print(f"Scanning {json_path} for GGUF files...")
    try:
        with open(json_path, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
            
        ggufs = []
        # The audit is likely a list of files or a dict with a list
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # Try to find a list in the dict
            items = []
            for val in data.values():
                if isinstance(val, list):
                    items.extend(val)
                elif isinstance(val, dict):
                    for v in val.values():
                        if isinstance(v, list):
                            items.extend(v)
        
        for item in items:
            # Handle both string paths and dict entries
            path = ""
            if isinstance(item, str):
                path = item
            elif isinstance(item, dict):
                path = item.get('path') or item.get('filepath') or item.get('name', '')
            
            if path and path.lower().endswith('.gguf'):
                ggufs.append(path)
        
        if ggufs:
            print(f"FOUND {len(ggufs)} GGUF files on E: drive:")
            for g in ggufs:
                print(g)
        else:
            print("No .gguf files found in e_drive_audit.json.")
            
    except Exception as e:
        print(f"Error parsing JSON: {e}")

if __name__ == "__main__":
    find_ggufs_in_audit()
