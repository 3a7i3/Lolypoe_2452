param(
    [string]$PythonExe = "C:/Users/WINDOWS/crypto_ai_terminal/.venv/Scripts/python.exe"
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

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

Invoke-Step -Name "Pip dependency integrity" -Action {
    & $PythonExe -m pip check
}

Invoke-Step -Name "Crypto V30 regression tests" -Action {
    Push-Location (Join-Path $RepoRoot "crypto_quant_v16")
    try {
        $env:V30_OFFLINE_TESTS = "1"
        & $PythonExe test_v30_smart_chart.py
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        & $PythonExe test_v30_profile.py
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        & $PythonExe test_v30_multi_exchange.py
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        & $PythonExe test_v30_profile_persistence.py
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    finally {
        Remove-Item Env:V30_OFFLINE_TESTS -ErrorAction SilentlyContinue
        Pop-Location
    }
}

Invoke-Step -Name "Quant Hedge AI syntax compile" -Action {
    Push-Location (Join-Path $RepoRoot "quant-hedge-ai")
    try {
        & $PythonExe -m py_compile main_v91.py main_system.py
    }
    finally {
        Pop-Location
    }
}

Invoke-Step -Name "Quant AI System syntax compile" -Action {
    Push-Location (Join-Path $RepoRoot "quant-ai-system")
    try {
        & $PythonExe -m py_compile main.py main_v2.py main_v7_multiagent.py main_v7_production.py
    }
    finally {
        Pop-Location
    }
}

Write-Host "All system checks passed." -ForegroundColor Green
