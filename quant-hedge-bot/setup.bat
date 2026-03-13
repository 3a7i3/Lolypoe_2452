@echo off
REM Quant Hedge Bot - Windows Setup Script
REM =======================================

echo ================================================
echo QUANT HEDGE BOT - Setup Script
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo [1/5] Python found
python --version
echo.

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    pause
    exit /b 1
)

echo [2/5] pip found
echo.

REM Create virtual environment
echo [3/5] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists - skipping
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)
echo.

REM Activate virtual environment
echo [4/5] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo.

REM Install requirements
echo [5/5] Installing dependencies from requirements.txt...
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install requirements
    pause
    exit /b 1
)
echo.

echo ================================================
echo ✓ Setup Complete!
echo ================================================
echo.
echo To run the bot:
echo   python main.py
echo.
echo To view dashboard:
echo   streamlit run dashboard/dashboard.py
echo.
echo To access help:
echo   - Read: README.md
echo   - Read: PROJECT_SUMMARY.md
echo.
echo Happy trading!
pause
