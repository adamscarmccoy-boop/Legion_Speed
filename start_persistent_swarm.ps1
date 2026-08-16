#!/usr/bin/env powershell

Write-Host "Starting persistent Ray cluster in the background..."
# This starts the Ray head node and DETACHES from the terminal. 
# It will stay alive even if you close this terminal.
ray start --head --port=6379 --object-store-memory=1572864000

Write-Host ""
Write-Host "✅ Persistent Ray cluster is now running!"
Write-Host "You can now safely run 'python ray_arrow_swarm.py'."
Write-Host "When ray_arrow_swarm.py finishes (or you hit Ctrl+C), this Ray cluster will STAY ALIVE."
