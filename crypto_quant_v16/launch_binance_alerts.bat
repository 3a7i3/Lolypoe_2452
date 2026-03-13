@echo off
setlocal

set "ROOT=%~dp0"
set "PYTHON_EXE=%ROOT%..\.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
  echo [ERROR] Python venv not found at "%PYTHON_EXE%"
  exit /b 1
)

if "%TELEGRAM_BOT_TOKEN%"=="" echo [WARN] TELEGRAM_BOT_TOKEN not set
if "%TELEGRAM_CHAT_ID%"=="" echo [WARN] TELEGRAM_CHAT_ID not set

if "%ALERT_SYMBOL%"=="" set "ALERT_SYMBOL=BTC/USDT"
if "%ALERT_TIMEFRAME%"=="" set "ALERT_TIMEFRAME=1h"
if "%ALERT_EXCHANGE%"=="" set "ALERT_EXCHANGE=binance"
if "%ALERT_POLL_SECONDS%"=="" set "ALERT_POLL_SECONDS=45"

echo [INFO] Starting Binance Alert App (%ALERT_SYMBOL% %ALERT_TIMEFRAME% @ %ALERT_EXCHANGE%, poll %ALERT_POLL_SECONDS%s)
cd /d "%ROOT%"
"%PYTHON_EXE%" binance_alert_app.py --symbol "%ALERT_SYMBOL%" --timeframe "%ALERT_TIMEFRAME%" --exchange "%ALERT_EXCHANGE%" --poll %ALERT_POLL_SECONDS%

endlocal
