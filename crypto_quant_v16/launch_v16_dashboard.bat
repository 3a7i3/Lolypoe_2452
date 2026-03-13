@echo off
REM ============================================================================
REM Crypto Quant V16 – Dashboard Launcher
REM ============================================================================

setlocal enabledelayedexpansion

cd /d "%~dp0"

REM Check if venv exists
if not exist "..\\.venv\\Scripts\\activate.bat" (
    echo ❌ Virtual environment not found
    echo Please create venv first: python -m venv ..\\.venv
    pause
    exit /b 1
)

REM Activate venv
call "..\\.venv\\Scripts\\activate.bat"

if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

REM Launch dashboard
echo.
echo ============================================================================
echo 🚀 Starting Crypto Quant V16 Dashboard
echo ============================================================================
echo.
echo 📍 Dashboard URL: http://localhost:5011/quant_dashboard
echo 🎛️  Press Ctrl+C to stop
echo.

python -m panel serve ui\quant_dashboard.py --port 5011 --show --autoreload

pause
