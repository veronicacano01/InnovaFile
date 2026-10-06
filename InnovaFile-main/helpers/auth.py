from functools import wraps

from flask import (
    session,
    redirect,
    url_for,
    flash
)

from bson import ObjectId
from bson.errors import InvalidId

from extensions import db


# ============================================================
# USUARIO ACTUAL
# ============================================================

def current_user():

    user_id = session.get(
        "user_id"
    )

    if not user_id:
        return None

    try:

        user_oid = ObjectId(
            str(user_id)
        )

    except (
        InvalidId,
        TypeError,
        ValueError
    ):

        # Si la sesión contiene un ID inválido,
        # la limpiamos.
        session.clear()

        return None

    try:

        user = db.users.find_one({
            "_id": user_oid
        })

    except Exception:

        return None

    # Si el usuario fue eliminado mientras
    # tenía una sesión abierta.
    if not user:

        session.clear()

        return None

    # --------------------------------------------------------
    # CARGAR ROL
    # --------------------------------------------------------

    role = None

    role_id = user.get(
        "role_id"
    )

    if role_id:

        try:

            if isinstance(
                role_id,
                str
            ):

                role_id = ObjectId(
                    role_id
                )

            role = db.roles.find_one({
                "_id": role_id
            })

        except Exception:

            role = None

    user[
        "role"
    ] = (
        role
        or {
            "name": "Sin rol"
        }
    )

    return user


# ============================================================
# REQUERIR LOGIN
# ============================================================

def login_required(
    view
):

    @wraps(
        view
    )
    def wrapped(
        *args,
        **kwargs
    ):

        user = current_user()

        if not user:

            flash(
                "Debes iniciar sesión.",
                "warning"
            )

            return redirect(
                url_for(
                    "auth.login"
                )
            )

        return view(
            *args,
            **kwargs
        )

    return wrapped


# ============================================================
# REQUERIR ROL
# ============================================================

def role_required(
    role_name
):

    def decorator(
        view
    ):

        @wraps(
            view
        )
        def wrapped(
            *args,
            **kwargs
        ):

            user = current_user()

            if not user:

                flash(
                    "Debes iniciar sesión.",
                    "warning"
                )

                return redirect(
                    url_for(
                        "auth.login"
                    )
                )

            current_role = (
                user.get(
                    "role",
                    {}
                )
                .get(
                    "name"
                )
            )

            if (
                current_role
                != role_name
            ):

                flash(
                    (
                        "No tienes permisos "
                        "para acceder a esta sección."
                    ),
                    "danger"
                )

                return redirect(
                    url_for(
                        "dashboard.index"
                    )
                )

            return view(
                *args,
                **kwargs
            )

        return wrapped

    return decorator