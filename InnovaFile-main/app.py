import os

from dotenv import load_dotenv

load_dotenv()

from datetime import timedelta

from flask import (
    Flask,
    redirect,
    url_for
)

from config import Config
from extensions import init_mongo

from helpers.auth import current_user
from helpers.logger import configure_logging
from helpers.error_handlers import register_error_handlers


# ============================================================
# CREAR APLICACIÓN
# ============================================================

def create_app():

    # --------------------------------------------------------
    # INSTANCIA DE FLASK
    # --------------------------------------------------------

    app = Flask(
        __name__
    )

    # --------------------------------------------------------
    # CONFIGURACIÓN
    # --------------------------------------------------------

    app.config.from_object(
        Config
    )

    # --------------------------------------------------------
    # CONFIGURACIÓN DE SESIÓN
    # --------------------------------------------------------

    app.config[
        "SESSION_COOKIE_HTTPONLY"
    ] = True

    app.config[
        "SESSION_COOKIE_SAMESITE"
    ] = "Lax"

    app.config[
        "PERMANENT_SESSION_LIFETIME"
    ] = timedelta(
        hours=8
    )

    # En desarrollo local usamos HTTP.
    # En producción con HTTPS debería ser True.
    app.config[
        "SESSION_COOKIE_SECURE"
    ] = Config.SESSION_COOKIE_SECURE

    # --------------------------------------------------------
    # DIRECTORIOS DEL SISTEMA
    # --------------------------------------------------------

    upload_directory = os.path.join(
        app.root_path,
        app.config[
            "UPLOAD_FOLDER"
        ]
    )

    os.makedirs(
        upload_directory,
        exist_ok=True
    )

    # --------------------------------------------------------
    # CARPETA DE VERSIONES
    # --------------------------------------------------------

    versions_directory = os.path.join(
        upload_directory,
        "versions"
    )

    os.makedirs(
        versions_directory,
        exist_ok=True
    )

    # --------------------------------------------------------
    # CARPETA DE LOGS
    # --------------------------------------------------------

    logs_directory = os.path.join(
        app.root_path,
        "logs"
    )

    os.makedirs(
        logs_directory,
        exist_ok=True
    )

    # --------------------------------------------------------
    # CARPETA DE BACKUPS
    # --------------------------------------------------------

    backups_directory = os.path.join(
        app.root_path,
        "backups"
    )

    os.makedirs(
        backups_directory,
        exist_ok=True
    )

    # --------------------------------------------------------
    # LOGGING
    # --------------------------------------------------------

    configure_logging(
        app
    )

    app.logger.info(
        "Sistema InnovaFile iniciado."
    )

    # --------------------------------------------------------
    # MONGODB
    # --------------------------------------------------------

    try:

        init_mongo(
            app
        )

        app.logger.info(
            "Conexión con MongoDB inicializada."
        )

    except Exception as error:

        app.logger.exception(
            "No fue posible inicializar MongoDB: %s",
            error
        )

        raise

    # ========================================================
    # IMPORTAR BLUEPRINTS
    #
    # Se importan después de inicializar Flask/MongoDB para
    # evitar importaciones circulares.
    # ========================================================

    from routes.auth_routes import (
        auth_bp
    )

    from routes.dashboard_routes import (
        dashboard_bp
    )

    from routes.user_routes import (
        users_bp
    )

    from routes.category_routes import (
        categories_bp
    )

    from routes.document_routes import (
        documents_bp
    )

    from routes.document_version_routes import (
        document_versions_bp
    )

    from routes.history_routes import (
        history_bp
    )

    from routes.backup_routes import (
        backup_bp
    )

    from routes.administration_routes import (
        administration_bp
    )

    # ========================================================
    # REGISTRAR BLUEPRINTS
    # ========================================================

    app.register_blueprint(
        auth_bp
    )

    app.register_blueprint(
        dashboard_bp
    )

    app.register_blueprint(
        users_bp
    )

    app.register_blueprint(
        categories_bp
    )

    app.register_blueprint(
        documents_bp
    )

    app.register_blueprint(
        document_versions_bp
    )

    app.register_blueprint(
        history_bp
    )

    app.register_blueprint(
        backup_bp
    )

    app.register_blueprint(
        administration_bp
    )

    # ========================================================
    # MANEJADORES DE ERROR
    # ========================================================

    register_error_handlers(
        app
    )

    # ========================================================
    # FILTROS DE FECHA (UTC → México)
    # ========================================================

    from helpers.date_utils import (
        format_date,
        format_datetime,
    )

    app.jinja_env.filters[
        "fecha_mx"
    ] = format_date

    app.jinja_env.filters[
        "fecha_hora_mx"
    ] = format_datetime

    # ========================================================
    # CONTEXT PROCESSOR
    #
    # Permite utilizar auth_user en cualquier template.
    # ========================================================

    @app.context_processor
    def inject_user():

        try:

            user = current_user()

        except Exception as error:

            app.logger.warning(
                "No fue posible obtener el usuario actual: %s",
                error
            )

            user = None

        from helpers.permissions import has_permission

        return {
            "auth_user": user,
            "has_permission": has_permission
        }

    # ========================================================
    # RUTA PRINCIPAL
    # ========================================================

    @app.get("/")
    def home():

        try:

            user = current_user()

        except Exception:

            user = None

        if user:

            return redirect(
                url_for(
                    "dashboard.index"
                )
            )

        return redirect(
            url_for(
                "auth.login"
            )
        )

    # ========================================================
    # HEALTH CHECK
    # ========================================================

    @app.get("/health")
    def health():

        return {
            "status":
                "ok",

            "system":
                "InnovaFile",

            "database":
                app.config.get(
                    "MONGO_DB",
                    "innovafile"
                )
        }, 200

    # ========================================================
    # REGISTRO DE RUTAS EN DESARROLLO
    # ========================================================

    app.logger.info(
        "Blueprints de InnovaFile registrados correctamente."
    )

    return app


# ============================================================
# CREAR APP
# ============================================================

app = create_app()


# ============================================================
# EJECUTAR
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "=============================================="
    )

    print(
        "                 INNOVAFILE"
    )

    print(
        "        Sistema de Gestión Documental"
    )

    print(
        "=============================================="
    )

    print()

    print(
        "Servidor:"
    )

    print(
        "http://127.0.0.1:5000"
    )

    print()

    print(
        "Estado:"
    )

    print(
        "http://127.0.0.1:5000/health"
    )

    print()

    # El modo debug puede exponer información sensible; solo activarlo
    # explícitamente durante desarrollo local.
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        debug=debug_mode,
        use_reloader=False
    )