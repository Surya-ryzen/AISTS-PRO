@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m backend.scripts.run_week10
) else (
  python -m backend.scripts.run_week10
)
pause
