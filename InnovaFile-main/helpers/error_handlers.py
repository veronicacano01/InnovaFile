from flask import (
    render_template,
    request,
    current_app
)

from werkzeug.exceptions import (
    HTTPException
)


# ============================================================
# ERROR 403
# ============================================================

def forbidden_error(error):

    current_app.logger.warning(
        (
            "403 | Acceso prohibido | "
            f"Ruta: {request.path} | "
            f"IP: {request.remote_addr}"
        )
    )

    return render_template(
        "errors/403.html"
    ), 403


# ============================================================
# ERROR 404
# ============================================================

def not_found_error(error):

    current_app.logger.warning(
        (
            "404 | Página no encontrada | "
            f"Ruta: {request.path} | "
            f"IP: {request.remote_addr}"
        )
    )

    return render_template(
        "errors/404.html"
    ), 404


# ============================================================
# ERROR 413
# ============================================================

def file_too_large_error(error):

    current_app.logger.warning(
        (
            "413 | Archivo demasiado grande | "
            f"Ruta: {request.path} | "
            f"IP: {request.remote_addr}"
        )
    )

    return render_template(
        "errors/413.html"
    ), 413


# ============================================================
# ERROR 500
# ============================================================

def internal_server_error(error):

    current_app.logger.error(
        (
            "500 | Error interno | "
            f"Ruta: {request.path} | "
            f"Método: {request.method} | "
            f"IP: {request.remote_addr}"
        ),
        exc_info=True
    )

    return render_template(
        "errors/500.html"
    ), 500


# ============================================================
# ERROR HTTP GENERAL
# ============================================================

def http_error(error):

    current_app.logger.warning(
        (
            f"{error.code} | "
            f"{error.name} | "
            f"Ruta: {request.path}"
        )
    )

    return render_template(
        "errors/generic.html",
        error_code=error.code,
        error_name=error.name,
        error_description=error.description
    ), error.code


# ============================================================
# REGISTRAR MANEJADORES
# ============================================================

def register_error_handlers(app):

    app.register_error_handler(
        403,
        forbidden_error
    )

    app.register_error_handler(
        404,
        not_found_error
    )

    app.register_error_handler(
        413,
        file_too_large_error
    )

    app.register_error_handler(
        500,
        internal_server_error
    )

    # Para otros errores HTTP:
    # 400, 405, 429, etc.
    app.register_error_handler(
        HTTPException,
        http_error
    )