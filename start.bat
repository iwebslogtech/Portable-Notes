@echo off
cd /d "%~dp0"
py app.py || python app.py
pause
