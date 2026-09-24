@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" -m backend.scripts.show_database
if errorlevel 1 pause
