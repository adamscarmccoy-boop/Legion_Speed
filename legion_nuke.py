"""
Legion Environment Nuke
------------------------------------------------
Forcefully kills the Ray cluster, orphaned Ray daemons (raylet, gcs_server),
and absolutely all Python processes to release .venv locks.
"""

import os
import platform
import subprocess
import time

def nuke_everything():
    os_name = platform.system()
    print("☢️ INITIATING TACTICAL NUKE ON RAY AND PYTHON ☢️")

    # 1. Shut down the Ray cluster using native commands first
    print("\n[1] Sending Ray stop command...")
    try:
        subprocess.run(["ray", "stop", "--force"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    time.sleep(1)
    print("[2] Hunting down lingering background Daemons and memory locks...")

    # 2. Execute OS-specific annihilation
    if os_name == "Windows" or "microsoft-standard" in platform.uname().release.lower():
        # Windows / WSL commands
        commands = [
            "taskkill /F /IM raylet.exe /T 2>NUL",
            "taskkill /F /IM gcs_server.exe /T 2>NUL",
            "taskkill /F /IM ray.exe /T 2>NUL",
            "taskkill /F /IM node.exe /T 2>NUL", # Catches any stuck VS Code extension UI bridges
            # WARNING: This final command will kill THIS script as well.
            "taskkill /F /IM python.exe /T 2>NUL"
        ]

        for cmd in commands:
            os.system(cmd)

    else:
        # Pure Linux commands
        commands = [
            "pkill -9 -f ray",
            "pkill -9 -f raylet",
            "pkill -9 -f gcs_server",
            # WARNING: This final command will kill THIS script as well.
            "pkill -9 -f python"
        ]

        for cmd in commands:
            os.system(cmd)

if __name__ == "__main__":
    nuke_everything()
