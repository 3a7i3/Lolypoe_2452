@echo off
setlocal

set "ROOT=%~dp0"
set "PYTHON_EXE=%ROOT%..\.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
  echo [ERROR] Python venv not found at "%PYTHON_EXE%"
  exit /b 1
)

echo [INFO] Launching V30 Suite from %ROOT%
cd /d "%ROOT%"
echo [INFO] Starting via launch_v30_full.py (loads .env automatically)
start "V30 Suite" "%PYTHON_EXE%" launch_v30_full.py --detached

echo [OK] V30 suite started.
endlocal
