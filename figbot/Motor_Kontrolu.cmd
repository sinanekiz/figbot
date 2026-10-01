@echo off
setlocal
cd /d "%~dp0"
start "FIGBOT Motor Kontrolu" "%~dp0.codex_artifacts\servo-ui-venv\Scripts\pythonw.exe" "%~dp0software\servo_panel\pca_app.py"
