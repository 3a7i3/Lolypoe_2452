@echo off
setlocal EnableExtensions EnableDelayedExpansion
set "ROOT_DIR=%~dp0"
set "LAUNCHER=%ROOT_DIR%scripts\run_setup_verify.bat"
set "LOG_DIR=%ROOT_DIR%logs\setup"
set "SHOW_LOG_ON_SUCCESS=0"
set "OPEN_LOG=0"

:parse_args
if "%~1"=="" goto :start

if /I "%~1"=="--show-log" (
	set "SHOW_LOG_ON_SUCCESS=1"
	shift
	goto :parse_args
)

if /I "%~1"=="--open-log" (
	set "OPEN_LOG=1"
	shift
	goto :parse_args
)

if /I "%~1"=="--help" goto :usage

echo [WARN] Unknown option: "%~1"
shift
goto :parse_args

:usage
echo Usage:
echo   ONE_CLICK_SETUP_VERIFY.bat [--show-log] [--open-log]
echo.
echo Options:
echo   --show-log    Show last 10 lines of latest setup log even on success.
echo   --open-log    Open the latest setup log file after run.
echo.
echo Examples:
echo   ONE_CLICK_SETUP_VERIFY.bat
echo   ONE_CLICK_SETUP_VERIFY.bat --show-log
echo   ONE_CLICK_SETUP_VERIFY.bat --show-log --open-log
exit /b 0

:start

if not exist "%LAUNCHER%" (
	echo [ERROR] Missing launcher: "%LAUNCHER%"
	pause
	exit /b 1
)

echo [INFO] Starting one-click setup and verification...
call "%LAUNCHER%" %*
set "EXIT_CODE=%ERRORLEVEL%"

set "LATEST_LOG="
if exist "%LOG_DIR%" (
	for /f "delims=" %%F in ('dir /b /a:-d /o:-d "%LOG_DIR%\setup_and_verify_*.log" 2^>nul') do (
		set "LATEST_LOG=%LOG_DIR%\%%F"
		goto :log_done
	)
)
:log_done

if defined LATEST_LOG (
	echo [INFO] Latest log: "!LATEST_LOG!"
) else (
	echo [WARN] No setup log found in "%LOG_DIR%".
)

if not "!EXIT_CODE!"=="0" (
	echo [ERROR] One-click setup failed with exit code !EXIT_CODE!.
	if defined LATEST_LOG if exist "!LATEST_LOG!" (
		echo [INFO] Last 30 log lines from "!LATEST_LOG!":
		powershell -NoProfile -Command "Get-Content -Path \"!LATEST_LOG!\" -Tail 30"
		if "!OPEN_LOG!"=="1" (
			echo [INFO] Opening latest log...
			start "" "!LATEST_LOG!"
		)
	) else (
		echo [WARN] Could not read latest setup log.
	)
	echo [HINT] Share the error section above if you want automatic troubleshooting.
	pause
	exit /b !EXIT_CODE!
)

echo [OK] One-click setup completed successfully.
if "!SHOW_LOG_ON_SUCCESS!"=="1" (
	if defined LATEST_LOG if exist "!LATEST_LOG!" (
		echo [INFO] Last 10 log lines from "!LATEST_LOG!":
		powershell -NoProfile -Command "Get-Content -Path \"!LATEST_LOG!\" -Tail 10"
	)
)
if "!OPEN_LOG!"=="1" (
	if defined LATEST_LOG if exist "!LATEST_LOG!" (
		echo [INFO] Opening latest log...
		start "" "!LATEST_LOG!"
	)
)
endlocal
