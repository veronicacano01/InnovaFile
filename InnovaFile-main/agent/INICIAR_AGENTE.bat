@echo off
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo No encuentro el entorno .venv del proyecto.
  echo Primero ejecuta la instalacion normal de InnovaFile.
  pause
  exit /b 1
)
start "InnovaFile - Sincronizacion automatica" /min cmd /c ".venv\Scripts\python.exe agent\innovafile_agent.py"
