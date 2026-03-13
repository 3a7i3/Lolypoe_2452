param(
    [switch]$Visible,
    [switch]$LoadEnv
)

$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root '.venv\Scripts\python.exe'
$WindowStyle = if ($Visible) { 'Normal' } else { 'Minimized' }
$EnvFile = Join-Path $Root '.env'

function Write-Section {
    param([string]$Text)
    Write-Host ''
    Write-Host $Text
}

function Load-DotEnv {
    param([string]$FilePath)

    if (-not (Test-Path $FilePath)) {
        Write-Host "[WARN] No .env found at $FilePath"
        return
    }

    Write-Host "[INFO] Loading environment from $FilePath"
    Get-Content -Path $FilePath | ForEach-Object {
        $line = $_.Trim()
        if (-not $line) { return }
        if ($line.StartsWith('#') -or $line.StartsWith(';')) { return }

        $parts = $line -split '=', 2
        if ($parts.Count -ne 2) { return }

        $key = $parts[0].Trim()
        $val = $parts[1]
        if ($key) {
            [Environment]::SetEnvironmentVariable($key, $val, 'Process')
        }
    }

    if ([string]::IsNullOrWhiteSpace($env:TELEGRAM_BOT_TOKEN)) {
        Write-Host '[WARN] TELEGRAM_BOT_TOKEN is empty'
    } else {
        Write-Host '[OK] TELEGRAM_BOT_TOKEN loaded'
    }

    if ([string]::IsNullOrWhiteSpace($env:TELEGRAM_CHAT_ID)) {
        Write-Host '[WARN] TELEGRAM_CHAT_ID is empty'
    } else {
        Write-Host '[OK] TELEGRAM_CHAT_ID loaded'
    }
}

function Test-PortListening {
    param([int]$Port)

    try {
        $sock = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction Stop | Select-Object -First 1
        return $null -ne $sock
    } catch {
        return $false
    }
}

function Ensure-PanelService {
    param(
        [int]$Port,
        [string]$Title,
        [string]$WorkingDir,
        [string]$ScriptPath
    )

    if (Test-PortListening -Port $Port) {
        Write-Host "[$Title] already running on port $Port, skipping."
        return
    }

    $cmd = "cd /d `"$WorkingDir`" && `"$Python`" -m panel serve $ScriptPath --port $Port --show --autoreload"
    Write-Host "[$Title] starting on port $Port ..."
    Start-Process -FilePath 'cmd.exe' -ArgumentList '/k', $cmd -WindowStyle $WindowStyle | Out-Null
    Start-Sleep -Seconds 2
}

function Ensure-BackgroundPython {
    param(
        [string]$Title,
        [string]$Match,
        [string]$WorkingDir,
        [string]$Command
    )

    $running = Get-CimInstance Win32_Process |
        Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match $Match } |
        Select-Object -First 1

    if ($running) {
        Write-Host "[$Title] already running, skipping."
        return
    }

    $cmd = "cd /d `"$WorkingDir`" && `"$Python`" $Command"
    Write-Host "[$Title] starting ..."
    Start-Process -FilePath 'cmd.exe' -ArgumentList '/k', $cmd -WindowStyle $WindowStyle | Out-Null
}

if (-not (Test-Path $Python)) {
    throw "Python executable not found: $Python"
}

Write-Host '============================================================'
Write-Host '  AI Quant Platform - PowerShell Launcher'
Write-Host '  V12 (5010) / V16 (5011) / V13 (5013) / V26 (5026) + Alerts'
Write-Host '============================================================'

if ($LoadEnv) {
    Load-DotEnv -FilePath $EnvFile
}

Ensure-PanelService -Port 5010 -Title 'V12 Dashboard' -WorkingDir (Join-Path $Root 'quant-hedge-ai') -ScriptPath 'dashboard\quant_terminal_v12.py'
Ensure-PanelService -Port 5011 -Title 'V16 Dashboard' -WorkingDir (Join-Path $Root 'crypto_quant_v16') -ScriptPath 'ui\quant_dashboard.py'
Ensure-PanelService -Port 5013 -Title 'V13 Dashboard' -WorkingDir (Join-Path $Root 'crypto_quant_v16') -ScriptPath 'ui\quant_dashboard_v13.py'
Ensure-PanelService -Port 5026 -Title 'V26 Dashboard' -WorkingDir (Join-Path $Root 'crypto_quant_v16') -ScriptPath 'ui\quant_dashboard_v26.py'

Ensure-BackgroundPython -Title 'V13 Autonomous Loop' -Match 'main_v13.py' -WorkingDir (Join-Path $Root 'crypto_quant_v16') -Command 'main_v13.py'
Ensure-BackgroundPython -Title 'Binance Alert App' -Match 'binance_alert_app.py' -WorkingDir (Join-Path $Root 'crypto_quant_v16') -Command 'binance_alert_app.py --symbol BTC/USDT --timeframe 1h --poll 45'

Write-Section 'Services state checked:'
Write-Host '  V12 Dashboard   : http://localhost:5010/quant_terminal_v12'
Write-Host '  V16 Dashboard   : http://localhost:5011/quant_dashboard'
Write-Host '  V13 Dashboard   : http://localhost:5013/quant_dashboard_v13'
Write-Host '  V26 Dashboard   : http://localhost:5026/quant_dashboard_v26'
Write-Host '  V13 Autonomous  : (background terminal)'
Write-Host '  Binance Alerts  : (background terminal)'
Write-Host "  Window Mode     : $WindowStyle"
Write-Host ''
Write-Host 'Use stop_all.bat to stop everything cleanly.'
