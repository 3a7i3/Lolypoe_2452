
@echo off
setlocal

echo ============================================================
echo   AI Quant Platform - Stop All
echo ============================================================
echo.

for %%P in (5010 5011 5013 5026) do (
    for /f "tokens=5" %%I in ('netstat -ano ^| findstr :%%P ^| findstr LISTENING') do (
        echo [STOP] Port %%P -> PID %%I
        taskkill /PID %%I /F >nul 2>&1
    )
)

for /f "tokens=2 delims== " %%I in ('wmic process where "name='python.exe' and commandline like '%%main_v13.py%%'" get ProcessId /value ^| find "ProcessId="') do (
    echo [STOP] V13 autonomous -> PID %%I
)
wmic process where "name='python.exe' and commandline like '%%main_v13.py%%'" call terminate >nul 2>&1

for /f "tokens=2 delims== " %%I in ('wmic process where "name='python.exe' and commandline like '%%binance_alert_app.py%%'" get ProcessId /value ^| find "ProcessId="') do (
    echo [STOP] Binance alert app -> PID %%I
)
wmic process where "name='python.exe' and commandline like '%%binance_alert_app.py%%'" call terminate >nul 2>&1

echo.
echo Stop requests sent for V12, V13, V16, V26, V13 autonomous loop and Binance alert app.
timeout /t 3 /nobreak >nul
