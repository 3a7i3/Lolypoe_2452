param(
    [string]$PythonExe = "C:/Users/WINDOWS/crypto_ai_terminal/.venv/Scripts/python.exe"
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

$reqs = @(
    (Join-Path $RepoRoot "quant-ai-system/requirements-py314.txt"),
    (Join-Path $RepoRoot "quant-ai-system/requirements-prod-py314.txt"),
    (Join-Path $RepoRoot "quant-hedge-bot/requirements-py314.txt"),
    (Join-Path $RepoRoot "quant-trading-system/requirements-py314.txt")
)

foreach ($req in $reqs) {
    Write-Host "Installing from $req" -ForegroundColor Cyan
    & $PythonExe -m pip install -r $req
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed on $req" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

Write-Host "All Python 3.14 compatible legacy requirements installed." -ForegroundColor Green
