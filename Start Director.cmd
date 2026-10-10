@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo Director setup is missing. Open Setup Director.exe from the release ZIP first.
  pause
  exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" "scripts\windows_launcher.py"
