from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from helpers.auth import login_required
from helpers.permissions import permission_required
from helpers.activity_helper import log_activity

from services.user_service import (
    get_paginated_users,
    get_user_by_id,
    get_available_roles,
    create_user,
    change_user_role,
    InvalidUserIdError,
    UserNotFoundError,
    InvalidRoleError
)


# ============================================================
# BLUEPRINT
# ============================================================

users_bp = Blueprint(
    "users",
    __name__,
    url_prefix="/users"
)


# ============================================================
# LISTAR USUARIOS
# ============================================================

@users_bp.get("/")
@login_required
@permission_required(
    "users.view"
)
def index():

    page = request.args.get(
        "page",
        1
    )

    per_page = request.args.get(
        "per_page",
        10
    )

    try:

        pagination = (
            get_paginated_users(
                page=page,
                per_page=per_page
            )
        )

    except Exception as error:

        print(
            f"Error al obtener usuarios: {error}"
        )

        pagination = {
            "users": [],
            "page": 1,
            "per_page": 10,
            "total": 0,
            "total_pages": 1,
            "has_prev": False,
            "has_next": False,
            "prev_page": 1,
            "next_page": 1
        }

        flash(
            "No fue posible cargar los usuarios.",
            "danger"
        )

    return render_template(
        "users/index.html",
        users=pagination[
            "users"
        ],
        pagination=pagination
    )


# ============================================================
# CREAR USUARIO
# ============================================================
@users_bp.route("/create",methods=["GET","POST"])
@login_required
@permission_required("users.create")
def create():
    roles=get_available_roles()
    if request.method=="POST":
        try:
            user=create_user(request.form.get("name"),request.form.get("last_name"),request.form.get("email"),request.form.get("password"),request.form.get("role_id"))
            log_activity("Usuario creado",f"Se creó el usuario {user.get('email')}")
            flash("Usuario creado correctamente.","success"); return redirect(url_for("users.index"))
        except Exception as error: flash(str(error),"danger")
    return render_template("users/create.html",roles=roles)


# ============================================================
# EDITAR USUARIO
# ============================================================

@users_bp.route(
    "/<user_id>/edit",
    methods=[
        "GET",
        "POST"
    ]
)
@login_required
@permission_required(
    "users.edit"
)
def edit(
    user_id
):

    # --------------------------------------------------------
    # OBTENER USUARIO
    # --------------------------------------------------------

    try:

        user = get_user_by_id(
            user_id
        )

    except InvalidUserIdError:

        flash(
            "Usuario inválido.",
            "danger"
        )

        return redirect(
            url_for(
                "users.index"
            )
        )

    except UserNotFoundError:

        flash(
            "Usuario no encontrado.",
            "danger"
        )

        return redirect(
            url_for(
                "users.index"
            )
        )

    # --------------------------------------------------------
    # ACTUALIZAR ROL
    # --------------------------------------------------------

    if request.method == "POST":

        role_id = request.form.get(
            "role_id",
            ""
        ).strip()

        if not role_id:

            flash(
                "Debes seleccionar un rol.",
                "warning"
            )

            return redirect(
                url_for(
                    "users.edit",
                    user_id=user_id
                )
            )

        try:

            result = change_user_role(
                user_id,
                role_id
            )

            role = result[
                "role"
            ]

            log_activity(
                "Cambio de rol",
                (
                    "Se cambió el rol del usuario "
                    f"{user.get('name', 'Usuario')} "
                    f"a {role.get('name', 'Sin rol')}"
                ),
                entity_type="user",
                entity_id=str(
                    user["_id"]
                )
            )

            if result[
                "modified"
            ]:

                flash(
                    "Rol actualizado correctamente.",
                    "success"
                )

            else:

                flash(
                    "El usuario ya tenía asignado ese rol.",
                    "info"
                )

            return redirect(
                url_for(
                    "users.index"
                )
            )

        except InvalidRoleError as error:

            flash(
                str(error),
                "danger"
            )

        except UserNotFoundError as error:

            flash(
                str(error),
                "danger"
            )

        except Exception as error:

            print(
                f"Error al cambiar rol: {error}"
            )

            flash(
                "Ocurrió un error al actualizar el rol.",
                "danger"
            )

    # --------------------------------------------------------
    # CARGAR ROLES
    # --------------------------------------------------------

    try:

        roles = (
            get_available_roles()
        )

    except Exception as error:

        print(
            f"Error al obtener roles: {error}"
        )

        roles = []

    return render_template(
        "users/edit.html",
        user=user,
        roles=roles
    )