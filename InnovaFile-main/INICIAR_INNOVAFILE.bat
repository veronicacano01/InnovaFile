@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo No existe el entorno virtual. Ejecuta INSTALAR_Y_PREPARAR.bat primero.
  pause
  exit /b 1
)
.venv\Scripts\python.exe app.py
pause
