@echo off
setlocal
set SCRIPT_DIR=%~dp0

if not exist "%SCRIPT_DIR%setup_and_verify_all.ps1" (
	echo [ERROR] Missing script: "%SCRIPT_DIR%setup_and_verify_all.ps1"
	exit /b 1
)

set PS_EXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe
if not exist "%PS_EXE%" (
	set PS_EXE=powershell
)

"%PS_EXE%" -ExecutionPolicy Bypass -File "%SCRIPT_DIR%setup_and_verify_all.ps1" %*
set EXIT_CODE=%ERRORLEVEL%

if not "%EXIT_CODE%"=="0" (
	echo [ERROR] Setup/verify failed with exit code %EXIT_CODE%.
	exit /b %EXIT_CODE%
)

echo [OK] Setup/verify completed.
endlocal
