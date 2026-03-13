$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $root "..\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Error "Python venv not found at $pythonExe"
}

$dashboardPort = if ($env:DASHBOARD_PORT) { $env:DASHBOARD_PORT } else { "5026" }
Set-Location $root

Write-Host "[INFO] Launching monitor only on http://localhost:$dashboardPort/quant_dashboard_v26"
& $pythonExe -m panel serve ui/quant_dashboard_v26.py --port $dashboardPort --show
