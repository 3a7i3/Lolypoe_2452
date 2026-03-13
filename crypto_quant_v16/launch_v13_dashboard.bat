@echo off
cd /d "%~dp0"
call "..\.venv\Scripts\activate.bat"
echo Starting Crypto Quant V13 Dashboard on http://localhost:5013/quant_dashboard_v13 ...
python -m panel serve ui\quant_dashboard_v13.py --port 5013 --show --autoreload
