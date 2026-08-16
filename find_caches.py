import os

directories_to_scan = [
    r"C:\WEB CASE STUDY",
    r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline",
    r"C:\Users\adams\AppData\Local\Temp\ray"
]

total_pycache_dirs = 0
total_pyc_files = 0
found_locations = []

for root_dir in directories_to_scan:
    if not os.path.exists(root_dir):
        continue
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip virtual environment folders
        if '.venv' in dirnames:
            dirnames.remove('.venv')
        if 'node_modules' in dirnames:
            dirnames.remove('node_modules')
            
        # Count pycache directories
        if "__pycache__" in dirpath:
            # Avoid duplicate counting of the same pycache dir
            if os.path.basename(dirpath) == "__pycache__":
                total_pycache_dirs += 1
                found_locations.append(dirpath)
        
        # Count .pyc files
        for filename in filenames:
            if filename.endswith(".pyc"):
                total_pyc_files += 1

print("==================================================")
print(" PYTHON & RAY CACHE AUDIT RESULTS")
print("==================================================")
print(f"Total __pycache__ Folders Found: {total_pycache_dirs}")
print(f"Total .pyc Compiled Files Found: {total_pyc_files}")
print("==================================================")
print("Top 10 Locations found:")
for loc in found_locations[:10]:
    print(f" - {loc}")
if len(found_locations) > 10:
    print(f" ... and {len(found_locations) - 10} more.")
