@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" -m figbot_lab.virtual_server
if errorlevel 1 pause
