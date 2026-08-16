# Start-Proxy.ps1
param(
  [string]$RepoPath = "C:\WEB CASE STUDY\proxy-to-gemini",
  [int]$Port = 8000
)

Set-Location $RepoPath

# Ensure Node is available
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
  Write-Host "Node not found in PATH. Install Node.js and re-run."
  exit 1
}

# Install deps if node_modules missing
if (-not (Test-Path ".\node_modules")) {
  Write-Host "Installing npm dependencies..."
  npm install
}

Write-Host "Building proxy (if needed)..."
npm run build 2>$null

Write-Host "Starting proxy on port $Port..."
# Use cross-platform start command from package.json; fallback to node dist/index.js
if (Get-Command npm -ErrorAction SilentlyContinue) {
  Start-Process -NoNewWindow -FilePath npm -ArgumentList "start" -WorkingDirectory $RepoPath
} else {
  node .\dist\index.js
}
