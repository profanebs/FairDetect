@echo off
setlocal
cd /d "%~dp0.."
python server\fairdetect_api.py
pause
