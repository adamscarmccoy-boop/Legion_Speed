# Start-OpenClaw.ps1
param(
  [string]$OpenClawPath = "C:\WEB CASE STUDY\openclaw",
  [string]$PythonExe = "python"
)

Set-Location $OpenClawPath

# Ensure .env exists
if (-not (Test-Path ".env")) {
  Write-Host ".env not found in $OpenClawPath. Create .env with OPENAI_API_KEY and OPENAI_BASE_URL"
  exit 1
}

Write-Host "Starting OpenClaw using environment in .env..."
# Use a simple approach: load .env into environment then run openclaw CLI
Get-Content .env | ForEach-Object {
  if ($_ -match "^\s*([^#=]+)=(.*)$") {
    $name = $matches[1].Trim()
    $value = $matches[2].Trim()
    [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
  }
}

# If openclaw is an npm or python CLI, call it. Try common locations.
if (Get-Command openclaw -ErrorAction SilentlyContinue) {
  Start-Process -NoNewWindow -FilePath openclaw -ArgumentList "chat" -WorkingDirectory $OpenClawPath
} elseif (Test-Path ".\openclaw.cmd") {
  Start-Process -NoNewWindow -FilePath ".\openclaw.cmd" -WorkingDirectory $OpenClawPath
} else {
  & $PythonExe -m openclaw
}
