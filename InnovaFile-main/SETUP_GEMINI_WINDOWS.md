# InnovaFile — instalación completa en Windows

## 1. Requisito de MongoDB

InnovaFile necesita MongoDB local por defecto en `mongodb://127.0.0.1:27017/`. Comprueba que el servicio esté iniciado antes de arrancar Flask.

## 2. Crear el entorno de Python

En PowerShell, dentro de `InnovaFile-main`:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

Si PowerShell bloquea la activación, ejecuta la terminal de VS Code como usuario normal y usa directamente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 3. Crear el archivo `.env`

Copia `.env.example`:

```powershell
Copy-Item .env.example .env
```

Abre `.env` y completa al menos:

```dotenv
SECRET_KEY=una-clave-larga-y-privada
MONGO_URI=mongodb://127.0.0.1:27017/
MONGO_DB=innovafile
GEMINI_API_KEY=PEGA_AQUI_TU_CLAVE_NUEVA
GEMINI_MODEL=gemini-3.8-flash
GEMINI_SEND_DOCUMENT_CONTENT=true
```

**No publiques `.env` ni pongas la API key en HTML, JavaScript, GitHub o el ZIP que compartas con clientes.**

## 4. API de Gemini

Entra a Google AI Studio y crea una API key para el proyecto que usarás con InnovaFile. El modelo predeterminado de esta versión es `gemini-3.8-flash`, que actualmente figura como modelo estable de Gemini API.

La aplicación usa el SDK oficial `google-genai` y lee la clave desde `GEMINI_API_KEY`.

## 5. Crear roles, categorías y administrador de desarrollo

```powershell
.\.venv\Scripts\python.exe seed.py
```

Crea/actualiza:

- Administrador
- Gestor documental
- Supervisor
- Colaborador
- Consulta

Y las categorías predeterminadas:

- Contratos
- Facturas
- Reportes
- Manuales
- Currículums
- Recursos Humanos
- Finanzas
- Clientes
- Proveedores
- Documentación legal
- Administración
- Otros

Usuario inicial de desarrollo:

- correo: `admin@innovafile.com`
- contraseña: `Admin123!`

**Cámbiala antes de usar el sistema con clientes.**

## 6. Iniciar

```powershell
.\.venv\Scripts\python.exe app.py
```

Abre `http://127.0.0.1:5000`.

## 7. Flujo automático de documentos

En Documentos, el usuario autorizado pulsa `Conectar carpeta` la primera vez. El navegador solicita permiso de lectura. InnovaFile no puede ni debe leer todo el disco del equipo sin autorización.

Después de autorizar:

1. Se recorren las carpetas internas.
2. Se detectan archivos compatibles.
3. Se extrae texto cuando es posible.
4. Gemini analiza el documento.
5. Gemini selecciona una categoría predeterminada.
6. InnovaFile guarda resumen, palabras clave, confianza y motivo.
7. Los documentos nuevos se vuelven a revisar cuando se abre Documentos, si el navegador conserva el permiso.

El navegador puede pedir autorización nuevamente según sus políticas de seguridad.

## 8. Roles

### Administrador
Control total: usuarios, roles, documentos, sincronización, IA, categorías, historial y estadísticas.

### Gestor documental
Administra documentos, sincronización, clasificación IA y categorías, pero no administra usuarios.

### Supervisor
Consulta, descarga, sincroniza, revisa IA, historial y estadísticas.

### Colaborador
Consulta, descarga y sincroniza documentos.

### Consulta
Solo consulta/descarga documentos y puede utilizar la asistencia IA disponible.

## 9. Seguridad de la API key

La clave que se usa en el servidor debe mantenerse secreta. Si una clave se comparte públicamente o se pega en un chat/repositorio, revócala y genera otra en Google AI Studio.

## 10. Producción

Antes de usarlo con clientes reales: HTTPS, SECRET_KEY fija y secreta, MongoDB protegido, copias de seguridad, cuentas separadas por empresa y políticas de retención. No expongas el servidor de desarrollo de Flask directamente a Internet.
