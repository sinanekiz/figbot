@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" -m figbot_lab.cli doctor
pause
