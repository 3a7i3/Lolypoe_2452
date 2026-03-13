$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $root "..\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Error "Python venv not found at $pythonExe"
}

Set-Location $root

Write-Host "[INFO] Starting via launch_v30_full.py (loads .env automatically)"
Start-Process -FilePath $pythonExe -ArgumentList "launch_v30_full.py", "--detached" -WindowStyle Normal

Write-Host "[OK] V30 suite started."
