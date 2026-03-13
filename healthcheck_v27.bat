@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0healthcheck_v27.ps1"
