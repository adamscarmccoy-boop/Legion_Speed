import os
import sys
import shutil
import subprocess

print("=== STARTING AGENT NODE CLEANUP ===")

# 1. Kill all Node.js processes related to npx / data-agent-kit
print("\n[*] Hunting and killing runaway Node.js processes...")
try:
    # Get all node processes
    cmd = 'Get-CimInstance Win32_Process | Where-Object {$_.Name -match "node" -and $_.CommandLine -match "npx|data-agent-kit"} | Select-Object -ExpandProperty ProcessId'
    process = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
    pids = process.stdout.strip().split('\n')
    
    killed_count = 0
    for pid in pids:
        pid = pid.strip()
        if pid:
            subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
            killed_count += 1
            print(f"  -> Killed Node Process ID: {pid}")
    print(f"Total runaway nodes killed: {killed_count}")
except Exception as e:
    print(f"Error killing nodes: {e}")

# 2. Find and delete the data-agent-kit NPM cache instances
print("\n[*] Hunting down data-agent-kit module folders...")
npm_cache_dir = os.path.expanduser(r"~\AppData\Local\npm-cache\_npx")
deleted_modules = 0

if os.path.exists(npm_cache_dir):
    for root, dirs, files in os.walk(npm_cache_dir):
        for d in dirs:
            if "data-agent-kit" in d or "mcp" in d.lower():
                target_path = os.path.join(root, d)
                try:
                    shutil.rmtree(target_path, ignore_errors=True)
                    deleted_modules += 1
                    print(f"  -> Deleted Node Module: {target_path}")
                except Exception as e:
                    print(f"  -> Failed to delete {target_path}: {e}")

print(f"Total Node instances deleted: {deleted_modules}")

# 3. Find and delete IDE Agent skills that are launching this
print("\n[*] Hunting down rogue IDE agent skills...")
skills_dir = os.path.expanduser(r"~\.gemini\config\skills")
deleted_skills = 0

if os.path.exists(skills_dir):
    for root, dirs, files in os.walk(skills_dir):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if "data-agent-kit" in content or "npx" in content:
                        print(f"  -> Found offending skill file: {file_path}")
                        os.remove(file_path)
                        deleted_skills += 1
                        print(f"     [DELETED] {file_path}")
            except Exception as e:
                pass

print(f"Total Rogue Skills deleted: {deleted_skills}")
print("\n=== CLEANUP COMPLETE ===")
