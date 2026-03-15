@echo off
REM Lance le test Alpha Discovery Engine depuis la racine du projet
REM Utilise l'environnement virtuel Python local

cd /d %~dp0
.venv\Scripts\python.exe -m AI_HEDGE_FUND_SYSTEM.alpha_discovery.test_alpha_lab
pause
