@echo off
setlocal

set "ROOT=%~dp0"
set "PYTHON_EXE=%ROOT%..\.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
  echo [ERROR] Python venv not found at "%PYTHON_EXE%"
  exit /b 1
)

cd /d "%ROOT%"
"%PYTHON_EXE%" healthcheck_v30.py

endlocal
