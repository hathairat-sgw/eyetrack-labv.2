@echo off
cd /d "%~dp0"
node scripts\run.mjs
if errorlevel 1 pause
