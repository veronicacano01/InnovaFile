# InnovaFile - versión final Gemini + sincronización automática

## Características
- Gemini API mediante `google-genai`.
- Clasificación automática de documentos.
- Categorías predeterminadas.
- Conexión de carpeta autorizada desde el navegador.
- Detección de archivos nuevos al volver a entrar cuando el navegador conserva el permiso.
- Roles: Administrador, Gestor documental, Supervisor, Colaborador y Consulta.
- Administración de usuarios basada en permisos almacenados en MongoDB.
- Migración de roles de instalaciones anteriores.

## Inicio rápido en Windows PowerShell

```powershell
cd "C:\Users\verit\OneDrive\Documentos\GEMINI\InnovaFile-Gemini-Automatico-FINAL\InnovaFile-main"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
python seed.py
python app.py
```

En `.env` coloca tu clave en `GEMINI_API_KEY`.

Abre: http://127.0.0.1:5000

Administrador inicial si la base estaba vacía:
- correo: admin@innovafile.com
- contraseña: Admin123!

Si ya existía ese administrador, `seed.py` conserva su contraseña y corrige su rol a Administrador.

## Sincronización automática con una carpeta de Windows

Para que InnovaFile continúe detectando documentos aunque el navegador esté cerrado, el proyecto incluye `agent/innovafile_agent.py`.

1. En **Documentos**, una cuenta con permiso `documents.sync` pulsa **Sincronización automática** y genera un token.
2. Copia el token que aparece.
3. Ejecuta `agent\CONFIGURAR_AGENTE.bat` en la computadora que contiene la carpeta.
4. Escribe la URL de InnovaFile, pega el token y selecciona la carpeta.
5. El agente hace una revisión inicial y después vigila la carpeta y sus subcarpetas.
6. Los archivos nuevos o modificados se envían automáticamente a `/documents/auto-import` y Gemini los clasifica.

> Nota: por seguridad de Windows, un sitio web no puede entregar a un proceso Python permiso permanente para leer cualquier carpeta del disco. El agente de escritorio es el componente que mantiene esa vigilancia después de cerrar el navegador.
