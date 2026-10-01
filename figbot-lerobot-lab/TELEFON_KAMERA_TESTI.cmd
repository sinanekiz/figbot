@echo off
cd /d "%~dp0"
echo Telefon USB ile bagli, kilidi acik ve USB hata ayiklama izni verilmis olmali.
".venv\Scripts\python.exe" -m figbot_lab.cli phone-camera --infer %*
pause
