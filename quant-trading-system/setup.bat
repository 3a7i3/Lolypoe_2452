@echo off
REM Quant Trading System V5 - Setup Script

echo.
echo ========================================
echo Quant Trading System V5 - Setup
echo ========================================
echo.

REM Create virtual environment
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install dependencies
echo.
echo Installing dependencies...
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

REM Create data directories
if not exist "data\market_cache" mkdir data\market_cache
if not exist "logs" mkdir logs

REM Verify installation
echo.
echo Verifying installation...
python -c "import ccxt; import pandas; import numpy; import streamlit; print('✓ All dependencies installed successfully!')"

REM Complete
echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the system:
echo   python main.py --mode live
echo.
echo To start dashboard:
echo   streamlit run dashboard/dashboard.py
echo.
echo To run backtest:
echo   python main.py --mode backtest
echo.
