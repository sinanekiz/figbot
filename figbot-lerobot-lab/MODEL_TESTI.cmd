@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" -m figbot_lab.cli reference-test --model base
if errorlevel 1 goto end
".venv\Scripts\python.exe" -m figbot_lab.cli reference-test --model pickplace
:end
pause
