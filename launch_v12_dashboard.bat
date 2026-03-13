@echo off
:: ─────────────────────────────────────────────────────────────────
::  Launcher – Quant AI Control Center V12
::  Ouvrir dans le navigateur : http://localhost:5010/quant_terminal_v12
:: ─────────────────────────────────────────────────────────────────
cd /d "%~dp0"
echo.
echo  ========================================================
echo    Quant AI Control Center V12  -  starting...
echo    URL:  http://localhost:5010/quant_terminal_v12
echo  ========================================================
echo.
call .venv\Scripts\activate.bat
cd quant-hedge-ai
panel serve dashboard\quant_terminal_v12.py --show --port 5010 --autoreload
pause
