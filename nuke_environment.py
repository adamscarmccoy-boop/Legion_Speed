import os
import subprocess

def nuke():
    processes_to_kill = ["raylet.exe", "gcs_server.exe", "python.exe"]
    print("🚀 Initiating Sovereign Environment Nuke...")
    
    for proc in processes_to_kill:
        print(f"Killing {proc}...")
        # /F = Force, /IM = Image Name, /T = Tree (kill child processes)
        subprocess.run(["taskkill", "/F", "/T", "/IM", proc], capture_output=True)

    print("✅ Environment cleared. Memory locks released.")

if __name__ == "__main__":
    nuke()
