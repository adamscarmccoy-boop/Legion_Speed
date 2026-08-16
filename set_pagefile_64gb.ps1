# Run this script as Administrator to increase Windows Pagefile limit to 64GB
# Right-click -> Run with PowerShell (Run as Administrator)

Write-Host "Setting Windows Pagefile Initial Size to 16GB and Maximum Size to 64GB..." -ForegroundColor Cyan

try {
    $pagefile = Get-CimInstance Win32_PageFileSetting | Where-Object { $_.Name -like "*c:*" }
    if ($pagefile) {
        Set-CimInstance -Query "Select * from Win32_PageFileSetting where Name like '%c:%'" -Property @{InitialSize = 16384; MaximumSize = 65536}
        Write-Host "SUCCESS: Pagefile successfully updated!" -ForegroundColor Green
        Write-Host "Initial Size: 16384 MB (16 GB)" -ForegroundColor Yellow
        Write-Host "Maximum Size: 65536 MB (64 GB)" -ForegroundColor Yellow
    } else {
        Write-Host "Pagefile setting not found on C:. Configuring automatic system pagefile..." -ForegroundColor Red
    }
} catch {
    Write-Host "ERROR: Please make sure you are running PowerShell as Administrator!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Pause
