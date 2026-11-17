@echo off
cd /d "%~dp0"
set PYTHONUTF8=1
.venv-hardware\Scripts\python.exe -m backend.hardware_check --stream-seconds 5 --report work\hardware-check.json
pause
