@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo Director backend environment is missing. Read docs/windows-native-runtime.md.
  pause
  exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" "scripts\windows_launcher.py"
