@echo off
setlocal

set "ROOT=%~dp0"
set "PS_CMD=powershell -ExecutionPolicy Bypass -File \"%ROOT%stop_v30_full.ps1\""

%PS_CMD%

endlocal
