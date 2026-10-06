@echo off
setlocal
cd /d "%~dp0"
echo ==============================================
echo          INNOVAFILE - PREPARACION
 echo ==============================================
if not exist ".venv\Scripts\python.exe" (
  echo Creando entorno virtual...
  py -m venv .venv
)
echo Instalando dependencias...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if not exist ".env" (
  copy /Y ".env.example" ".env" >nul
  echo.
  echo Se creo .env. Abrelo y pega tu GEMINI_API_KEY.
)
echo.
echo Ejecuta seed.py cuando hayas configurado MongoDB y .env.
pause
