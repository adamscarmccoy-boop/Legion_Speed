"""Preflight: kill stale Ray processes before starting a cluster."""

import subprocess
import os
import time


def kill_stale_ray_processes_windows():
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "raylet.exe"],
            check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        subprocess.run(
            ["powershell", "-Command",
             "Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.StartTime -lt (Get-Date).AddMinutes(-10) } | Stop-Process -Force"],
            check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception:
        pass


def preflight_check():
    if os.name == "nt":
        kill_stale_ray_processes_windows()
    time.sleep(0.5)