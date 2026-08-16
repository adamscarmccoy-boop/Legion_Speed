import os
import time

def find_lost_weights(directories_to_scan):
    # Extensions we consider to be "model weights"
    weight_extensions = {'.pt', '.pth', '.onnx'}
    
    # Extensions that MIGHT be weights, but need filtering (like raw .bin arrays)
    ambiguous_extensions = {'.bin'}
    
    # Folders we should completely ignore to avoid spam
    ignore_folders = {'node_modules', '.venv', '.venv_fresh', '.git', '__pycache__', 'env', 'venv'}

    found_weights = []

    print(f"Scanning for lost AI weights across {len(directories_to_scan)} directories...")
    print("-" * 60)

    for base_dir in directories_to_scan:
        if not os.path.exists(base_dir):
            continue
            
        for root, dirs, files in os.walk(base_dir):
            # Modify 'dirs' in-place to skip ignored folders
            dirs[:] = [d for d in dirs if d not in ignore_folders]
            
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                
                is_weight = False
                if ext in weight_extensions:
                    is_weight = True
                elif ext in ambiguous_extensions:
                    # For .bin files, we only want them if they aren't part of an npm / node_modules hidden bin
                    if ".bin" not in root.split(os.sep): 
                        is_weight = True
                        
                if is_weight:
                    full_path = os.path.join(root, file)
                    size_mb = os.path.getsize(full_path) / (1024 * 1024)
                    mod_time = time.ctime(os.path.getmtime(full_path))
                    found_weights.append({
                        'path': full_path,
                        'name': file,
                        'size': size_mb,
                        'modified': mod_time,
                        'ext': ext
                    })

    # Sort by size (largest first)
    found_weights.sort(key=lambda x: x['size'], reverse=True)

    # Print Report
    print(f"Found {len(found_weights)} total weight files.\n")
    
    for w in found_weights:
        print(f"[{w['ext'].upper()}] {w['size']:.2f} MB")
        print(f"      Path: {w['path']}")
        print(f"      Last Modified: {w['modified']}")
        print("-" * 60)
        
    # Write to a report file so it's easy to read
    with open("LOST_WEIGHTS_REPORT.txt", "w", encoding="utf-8") as f:
        f.write(f"FOUND {len(found_weights)} WEIGHT FILES:\n")
        f.write("=" * 60 + "\n")
        for w in found_weights:
            f.write(f"[{w['ext'].upper()}] {w['size']:.2f} MB\n")
            f.write(f"Path: {w['path']}\n")
            f.write("-" * 60 + "\n")
            
    print(f"\nSaved full list to: {os.path.abspath('LOST_WEIGHTS_REPORT.txt')}")

if __name__ == "__main__":
    # Add any other root directories you want to scan here!
    scan_targets = [
        r"C:\WEB CASE STUDY",
        r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline",
        r"C:\.genkit",
        "E:\\"
    ]
    find_lost_weights(scan_targets)
