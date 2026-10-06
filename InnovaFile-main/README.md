# InnovaFile Flask + MongoDB

Conversión del proyecto InnovaFile original (Laravel/MySQL) a **Python Flask + MongoDB**, manteniendo los módulos y la interfaz general.

## Estructura

```text
InnovaFile_Flask_MongoDB/
├── app.py
├── config.py
├── extensions.py
├── helpers/
│   ├── auth.py
│   └── activity_helper.py
├── routes/
│   ├── auth_routes.py
│   ├── dashboard_routes.py
│   ├── user_routes.py
│   ├── category_routes.py
│   ├── document_routes.py
│   └── history_routes.py
├── templates/
│   ├── layouts/
│   ├── users/
│   ├── categories/
│   ├── documents/
│   └── history/
├── static/
│   ├── css/app.css
│   └── uploads/documents/
├── data/                  # datos convertidos del innovafile.sql entregado
├── scripts/import_data.py
├── seed.py
├── reset_admin.py
├── requirements.txt
└── .env.example
```

## Funciones conservadas

- Inicio de sesión y registro.
- Roles Administrador, Supervisor y Empleado.
- Dashboard con conteos y últimos movimientos.
- Gestión y cambio de rol de usuarios (Administrador).
- Categorías: listado, alta y eliminación.
- Documentos: listado, alta, búsqueda, detalle, descarga y eliminación.
- Historial de actividad.
- Estadísticas.
- Búsqueda inteligente basada en texto.
- Clasificación por palabras clave: contratos, facturas, reportes, manuales y currículums.

## Instalación en Windows

1. Instala Python 3.11+ y MongoDB Community Server (o usa MongoDB Atlas).
2. Abre la carpeta en VS Code.
3. Crea el entorno virtual:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

4. Instala dependencias:

```powershell
pip install -r requirements.txt
```

5. Copia `.env.example` a `.env`:

```powershell
Copy-Item .env.example .env
```

6. Para importar los datos reales convertidos desde `innovafile.sql`:

```powershell
python scripts/import_data.py --reset
```

7. Si no conoces las contraseñas de los usuarios importados, crea/restablece un administrador conocido:

```powershell
python reset_admin.py
```

Credenciales de desarrollo:

- Correo: `admin@innovafile.com`
- Contraseña: `Admin123!`

8. Ejecuta el proyecto:

```powershell
python app.py
```

9. Abre:

```text
http://127.0.0.1:5000
```

## MongoDB

La base por defecto es `innovafile` y utiliza estas colecciones:

- `roles`
- `users`
- `categories`
- `documents`
- `activity_logs`

Puedes verla con MongoDB Compass conectándote a `mongodb://127.0.0.1:27017/`.


## Mejoras de integración (Gemini y carpeta sincronizada con la nube)

### 1. Preparar la configuración

1. Copia `.env.example` como `.env`.
2. Cambia `SECRET_KEY` por una clave larga y aleatoria. No compartas el `.env` ni lo subas a GitHub.
3. Mantén `MONGO_URI` y `MONGO_DB` según tu instalación de MongoDB.
4. Instala las dependencias con `pip install -r requirements.txt`.

### 2. Configurar Gemini

1. Entra a Google AI Studio: https://aistudio.google.com/api-keys
2. Inicia sesión con tu cuenta de Google y crea una API key. La disponibilidad, los límites y cualquier cobro dependen de las condiciones vigentes de Google.
3. Copia la clave únicamente en `GEMINI_API_KEY` dentro de tu archivo `.env`. No la pongas en plantillas HTML, JavaScript ni en el repositorio.
4. Deja `GEMINI_MODEL=gemini-3.8-flash`. Si Google cambia la disponibilidad de ese modelo para tu cuenta, usa un modelo estable disponible en AI Studio.

Gemini se usa para clasificar automáticamente los documentos sincronizados. Para PDF, DOCX, TXT, CSV y XLSX se extrae texto localmente cuando es posible; para archivos sin texto extraíble, InnovaFile puede enviar el archivo a Gemini si `GEMINI_SEND_DOCUMENT_CONTENT=true`. La aplicación limita el contenido enviado y registra el resultado de clasificación. Las propuestas deben ser revisadas por una persona. La búsqueda inteligente utiliza los resultados/metadatos que ya devolvió la búsqueda local y no debe usarse como autorización de acceso.

### 3. Carpeta compartida en la nube

InnovaFile necesita una ruta de carpeta que la computadora que ejecuta Flask pueda leer y escribir. Para empezar, la opción más sencilla es instalar el cliente de escritorio del proveedor elegido (por ejemplo, Google Drive para escritorio, OneDrive o Dropbox) y crear una carpeta sincronizada llamada `InnovaFile`. Después configura su ruta local en `CLOUD_DOCUMENTS_FOLDER`. Por ejemplo, en Windows (ajusta el usuario y la ruta reales):

```dotenv
CLOUD_DOCUMENTS_FOLDER=C:/Users/TU_USUARIO/Google Drive/InnovaFile
```

Cuando `CLOUD_DOCUMENTS_FOLDER` tiene valor, InnovaFile guarda los documentos en esa carpeta sincronizada. El programa de escritorio del proveedor se encarga de sincronizarlos con la nube. Esto no es todavía una integración directa con la API de Google Drive/OneDrive: la computadora servidor debe permanecer encendida y conectada, y la carpeta debe estar disponible. No configures una carpeta personal de un usuario si el sistema será usado por varias personas; usa una cuenta de servicio/empresa y permisos restringidos.

Si dejas `CLOUD_DOCUMENTS_FOLDER` vacío, InnovaFile continúa usando `UPLOAD_FOLDER` (por defecto `static/uploads/documents`). Antes de cambiar rutas en una instalación que ya contiene archivos, haz un respaldo y mueve los archivos junto con la base de datos de forma coordinada.

### 4. Ejecución y pruebas

En PowerShell, desde la carpeta del proyecto:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env  # solo la primera vez; después edita .env
python app.py
```

Abre `http://127.0.0.1:5000`. Comprueba primero inicio de sesión, carga, descarga y búsqueda de documentos. Luego prueba la búsqueda inteligente y la clasificación con un documento de prueba sin información confidencial. Si Gemini no está configurado o no responde, el sistema conserva la búsqueda/clasificación local.

### 5. Antes de usarlo con documentos reales

- Usa HTTPS real antes de habilitar `SESSION_COOKIE_SECURE=true`.
- No expongas el servidor de desarrollo de Flask directamente a Internet.
- Configura autenticación y permisos del proveedor de nube, respaldo independiente y política de retención.
- Revisa los permisos por rol y los registros de auditoría con cuentas de prueba.
- Evita enviar información confidencial a un proveedor de IA sin autorización y sin revisar sus condiciones de tratamiento de datos.


## Organización automática con Gemini
La pantalla Documentos permite conectar una carpeta del equipo. El navegador solicita permiso de lectura y, después, los documentos compatibles se sincronizan automáticamente, se extrae su contenido y Gemini los clasifica en categorías predeterminadas. La clave se configura en `.env` con `GEMINI_API_KEY`. Nunca publiques `.env`.

Roles: Administrador, Gestor documental, Supervisor, Colaborador y Consulta.
