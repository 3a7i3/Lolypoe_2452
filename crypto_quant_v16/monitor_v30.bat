@echo off
setlocal

set "ROOT=%~dp0"
set "PYTHON_EXE=%ROOT%..\.venv\Scripts\python.exe"
set "PANEL_PORT=%DASHBOARD_PORT%"
if "%PANEL_PORT%"=="" set "PANEL_PORT=5026"

if not exist "%PYTHON_EXE%" (
  echo [ERROR] Python venv not found at "%PYTHON_EXE%"
  exit /b 1
)

cd /d "%ROOT%"
echo [INFO] Launching monitor only on http://localhost:%PANEL_PORT%/quant_dashboard_v26
"%PYTHON_EXE%" -m panel serve ui\quant_dashboard_v26.py --port %PANEL_PORT% --show

endlocal
