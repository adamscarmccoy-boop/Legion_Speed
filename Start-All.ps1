# Start-All.ps1
param(
  [string]$ProxyPath = "C:\WEB CASE STUDY\proxy-to-gemini",
  [string]$OpenClawPath = "C:\WEB CASE STUDY\openclaw",
  [string]$PythonExe = "python"
)

# Start proxy
Write-Host "Launching proxy..."
Start-Process -NoNewWindow -FilePath pwsh -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$ProxyPath\Start-Proxy.ps1`"" -WindowStyle Hidden
Start-Sleep -Seconds 3

# Start OpenClaw
Write-Host "Launching OpenClaw..."
Start-Process -NoNewWindow -FilePath pwsh -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$OpenClawPath\Start-OpenClaw.ps1`"" -WindowStyle Normal
