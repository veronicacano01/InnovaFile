from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from helpers.activity_helper import (
    log_activity
)

from services.auth_service import (
    authenticate_user,
    register_user,
    InvalidCredentialsError,
    AccountLockedError,
    InvalidRegistrationError,
    DuplicateUserError,
    MAX_FAILED_ATTEMPTS
)


# ============================================================
# BLUEPRINT
# ============================================================

auth_bp = Blueprint(
    "auth",
    __name__
)


# ============================================================
# LOGIN
# ============================================================

@auth_bp.route(
    "/login",
    methods=[
        "GET",
        "POST"
    ]
)
def login():

    # --------------------------------------------------------
    # SESIÓN YA INICIADA
    # --------------------------------------------------------

    if (
        request.method == "GET"
        and session.get(
            "user_id"
        )
    ):

        return redirect(
            url_for(
                "dashboard.index"
            )
        )

    # --------------------------------------------------------
    # LOGIN
    # --------------------------------------------------------

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        )

        password = request.form.get(
            "password",
            ""
        )

        try:

            user = authenticate_user(
                email=email,
                password=password
            )

            # Limpiamos cualquier
            # información de sesión anterior.
            session.clear()

            session[
                "user_id"
            ] = str(
                user[
                    "_id"
                ]
            )

            session.permanent = True

            log_activity(
                "Inicio de sesión",
                "El usuario inició sesión correctamente.",
                entity_type="user",
                entity_id=str(
                    user[
                        "_id"
                    ]
                )
            )

            flash(
                "Bienvenido a InnovaFile.",
                "success"
            )

            return redirect(
                url_for(
                    "dashboard.index"
                )
            )

        # ----------------------------------------------------
        # CUENTA BLOQUEADA
        # ----------------------------------------------------

        except AccountLockedError as error:

            log_activity(
                "Acceso bloqueado",
                (
                    "Se intentó iniciar sesión "
                    "durante un bloqueo temporal."
                )
            )

            flash(
                str(error),
                "danger"
            )

            return render_template(
                "login.html",
                lock_seconds=(
                    error.remaining_seconds
                )
            )

        # ----------------------------------------------------
        # CREDENCIALES INCORRECTAS
        # ----------------------------------------------------

        except InvalidCredentialsError as error:

            user = getattr(
                error,
                "user",
                None
            )

            attempts = getattr(
                error,
                "attempts",
                None
            )

            if user:

                log_activity(
                    "Inicio de sesión fallido",
                    (
                        "Se ingresó una contraseña "
                        "incorrecta. "
                        f"Intento "
                        f"{attempts or 1} "
                        f"de "
                        f"{MAX_FAILED_ATTEMPTS}."
                    ),
                    entity_type="user",
                    entity_id=str(
                        user[
                            "_id"
                        ]
                    )
                )

            else:

                log_activity(
                    "Inicio de sesión fallido",
                    (
                        "Se intentó iniciar sesión "
                        "con credenciales incorrectas."
                    )
                )

            flash(
                str(error),
                "danger"
            )

        except Exception as error:

            print(
                f"Error inesperado en login: {error}"
            )

            flash(
                "No fue posible iniciar sesión.",
                "danger"
            )

    return render_template(
        "login.html"
    )


# ============================================================
# REGISTRO
# ============================================================

@auth_bp.route(
    "/register",
    methods=[
        "GET",
        "POST"
    ]
)
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        )

        last_name = request.form.get(
            "last_name",
            ""
        )

        email = request.form.get(
            "email",
            ""
        )

        password = request.form.get(
            "password",
            ""
        )

        try:

            user = register_user(
                name=name,
                last_name=last_name,
                email=email,
                password=password
            )

            log_activity(
                "Registro de usuario",
                (
                    "Se registró una nueva "
                    "cuenta de usuario."
                ),
                entity_type="user",
                entity_id=str(
                    user[
                        "_id"
                    ]
                )
            )

            flash(
                (
                    "Usuario registrado correctamente. "
                    "Ya puedes iniciar sesión."
                ),
                "success"
            )

            return redirect(
                url_for(
                    "auth.login"
                )
            )

        except DuplicateUserError as error:

            flash(
                str(error),
                "danger"
            )

        except InvalidRegistrationError as error:

            flash(
                str(error),
                "danger"
            )

        except Exception as error:

            print(
                f"Error inesperado al registrar usuario: {error}"
            )

            flash(
                (
                    "No fue posible registrar "
                    "el usuario."
                ),
                "danger"
            )

    return render_template(
        "register.html"
    )


# ============================================================
# CERRAR SESIÓN
# ============================================================

@auth_bp.post(
    "/logout"
)
def logout():

    user_id = session.get(
        "user_id"
    )

    if user_id:

        log_activity(
            "Cerrar sesión",
            "El usuario cerró sesión.",
            entity_type="user",
            entity_id=user_id
        )

    session.clear()

    flash(
        "Sesión cerrada correctamente.",
        "success"
    )

    return redirect(
        url_for(
            "auth.login"
        )
    )