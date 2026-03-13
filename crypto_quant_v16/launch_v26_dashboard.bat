@echo off
setlocal

set PYTHON=c:\Users\WINDOWS\crypto_ai_terminal\.venv\Scripts\python.exe
set ROOT=c:\Users\WINDOWS\crypto_ai_terminal\crypto_quant_v16

echo Starting Smart Chart V26 on http://localhost:5026/quant_dashboard_v26 ...
cd /d %ROOT%
%PYTHON% -m panel serve ui\quant_dashboard_v26.py --port 5026 --show --autoreload
