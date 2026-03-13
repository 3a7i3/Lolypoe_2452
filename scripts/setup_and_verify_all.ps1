param(
    [string]$PythonExe = "C:/Users/WINDOWS/crypto_ai_terminal/.venv/Scripts/python.exe",
    [string]$LogDir = "",
    [switch]$NoLog,
    [int]$KeepLatestLogs = 20
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

if ([string]::IsNullOrWhiteSpace($LogDir)) {
    $LogDir = Join-Path $RepoRoot "logs/setup"
}

$logStarted = $false
$logPath = ""
if (-not $NoLog) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    $runId = Get-Date -Format "yyyyMMdd_HHmmss"
    $logPath = Join-Path $LogDir ("setup_and_verify_{0}.log" -f $runId)
    Start-Transcript -Path $logPath -Force | Out-Null
    $logStarted = $true
    Write-Host "[LOG] Transcript: $logPath" -ForegroundColor DarkCyan
}

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Action
    )
    Write-Host "[STEP] $Name" -ForegroundColor Cyan
    & $Action
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] $Name" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host "[OK] $Name" -ForegroundColor Green
}

try {
    Invoke-Step -Name "Install workspace root requirements" -Action {
        & $PythonExe -m pip install -r (Join-Path $RepoRoot "requirements.txt")
    }

    Invoke-Step -Name "Install crypto_quant_v16 requirements" -Action {
        & $PythonExe -m pip install -r (Join-Path $RepoRoot "crypto_quant_v16/requirements.txt")
    }

    Invoke-Step -Name "Install legacy Python 3.14 compatibility requirements" -Action {
        & powershell -ExecutionPolicy Bypass -File (Join-Path $RepoRoot "scripts/install_legacy_py314.ps1") -PythonExe $PythonExe
    }

    Invoke-Step -Name "Run full system verification" -Action {
        & powershell -ExecutionPolicy Bypass -File (Join-Path $RepoRoot "scripts/verify_all_systems.ps1") -PythonExe $PythonExe
    }

    Write-Host "Setup + verification completed successfully." -ForegroundColor Green
}
finally {
    if ($logStarted) {
        Stop-Transcript | Out-Null
        Write-Host "[LOG] Saved: $logPath" -ForegroundColor DarkCyan
    }

    if ((-not $NoLog) -and ($KeepLatestLogs -gt 0)) {
        $logFiles = Get-ChildItem -Path $LogDir -Filter "setup_and_verify_*.log" -File |
            Sort-Object LastWriteTime -Descending
        $oldLogs = $logFiles | Select-Object -Skip $KeepLatestLogs
        $removed = 0
        foreach ($oldLog in $oldLogs) {
            Remove-Item -Path $oldLog.FullName -Force -ErrorAction SilentlyContinue
            $removed += 1
        }
        if ($removed -gt 0) {
            Write-Host "[LOG] Removed old log files: $removed" -ForegroundColor DarkCyan
        }
    }
}
