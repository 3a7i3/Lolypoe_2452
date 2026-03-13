param(
    [int]$TimeoutSec = 12
)

$ErrorActionPreference = 'SilentlyContinue'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root '.venv\Scripts\python.exe'
$timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

$routes = @(
    @{ Name = 'V12'; Port = 5010; Path = 'quant_terminal_v12' },
    @{ Name = 'V16'; Port = 5011; Path = 'quant_dashboard' },
    @{ Name = 'V13'; Port = 5013; Path = 'quant_dashboard_v13' },
    @{ Name = 'V27'; Port = 5026; Path = 'quant_dashboard_v26' }
)

function Test-PortListening {
    param([int]$Port)
    try {
        $conn = Get-NetTCPConnection -State Listen -LocalPort $Port | Select-Object -First 1
        return $null -ne $conn
    } catch {
        return $false
    }
}

function Test-Http {
    param(
        [string]$Url,
        [int]$Timeout = 12
    )
    try {
        $r = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec $Timeout
        return @{ Ok = $true; Code = [int]$r.StatusCode; Error = '' }
    } catch {
        return @{ Ok = $false; Code = 0; Error = ($_.Exception.Message) }
    }
}

Write-Host '============================================================'
Write-Host " V27 Healthcheck - $timestamp"
Write-Host '============================================================'

# Python env check
if (Test-Path $python) {
    Write-Host "[OK] Python venv found: $python"
} else {
    Write-Host "[FAIL] Python venv not found: $python"
}

Write-Host ''
Write-Host '--- Services ---'

$okCount = 0
foreach ($svc in $routes) {
    $rootUrl = "http://localhost:$($svc.Port)/"
    $appUrl = "http://localhost:$($svc.Port)/$($svc.Path)"

    $listening = Test-PortListening -Port $svc.Port
    $appResp = Test-Http -Url $appUrl -Timeout $TimeoutSec

    if ($listening -and $appResp.Ok) {
        $okCount += 1
        Write-Host ("[{0}] {1} port={2} app={3} http={4}" -f 'OK', $svc.Name, $svc.Port, $svc.Path, $appResp.Code)
    } elseif ($listening -and -not $appResp.Ok) {
        Write-Host ("[{0}] {1} port={2} listens but app route failed: {3}" -f 'WARN', $svc.Name, $svc.Port, $appResp.Error)
    } else {
        Write-Host ("[{0}] {1} port={2} not listening" -f 'FAIL', $svc.Name, $svc.Port)
    }

    # Root route is optional but useful telemetry
    $rootResp = Test-Http -Url $rootUrl -Timeout $TimeoutSec
    if ($rootResp.Ok) {
        Write-Host ("      root / -> HTTP {0}" -f $rootResp.Code)
    } else {
        Write-Host "      root / -> FAIL"
    }
}

Write-Host ''
Write-Host '--- Background Processes ---'

$v13 = Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'main_v13.py' }
$alerts = Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'binance_alert_app.py' }

Write-Host ("V13 loop processes: {0}" -f @($v13).Count)
Write-Host ("Alert app processes: {0}" -f @($alerts).Count)

Write-Host ''
Write-Host '--- Summary ---'
if ($okCount -eq $routes.Count) {
    Write-Host ("[OK] All dashboard app routes healthy ({0}/{1})" -f $okCount, $routes.Count)
} else {
    Write-Host ("[WARN] Dashboard health partial ({0}/{1})" -f $okCount, $routes.Count)
    Write-Host 'Tip: run launch_all.bat or launch_all.ps1 then retry.'
}
