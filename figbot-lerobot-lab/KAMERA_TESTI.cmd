@echo off
cd /d "%~dp0"
echo Kamera baglantisi ve model testi. Robot konumu ornek degerdir; motor hareketi yoktur.
".venv\Scripts\python.exe" -m figbot_lab.cli camera --infer %*
pause
