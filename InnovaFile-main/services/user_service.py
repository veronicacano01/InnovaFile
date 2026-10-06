import math

from bson import ObjectId
from bson.errors import InvalidId

from repositories import user_repository


# ============================================================
# EXCEPCIONES
# ============================================================

class UserServiceError(Exception):
    pass


class UserNotFoundError(
    UserServiceError
):
    pass


class InvalidUserIdError(
    UserServiceError
):
    pass


class InvalidRoleError(
    UserServiceError
):
    pass


# ============================================================
# VALIDAR OBJECT ID
# ============================================================

def validate_object_id(
    value,
    message="Identificador inválido."
):

    try:

        return ObjectId(
            str(value)
        )

    except (
        InvalidId,
        TypeError,
        ValueError
    ):

        raise InvalidUserIdError(
            message
        )


# ============================================================
# ENRIQUECER USUARIO
# ============================================================

def enrich_user(
    user,
    roles_map=None
):

    if not user:
        return None

    data = dict(
        user
    )

    role_id = data.get(
        "role_id"
    )

    role = None

    # Si ya tenemos el mapa de roles evitamos
    # hacer otra consulta a MongoDB.
    if roles_map is not None:

        role = roles_map.get(
            str(role_id)
        )

    elif role_id:

        try:

            role = (
                user_repository
                .get_role_by_id(
                    role_id
                )
            )

        except Exception:
            role = None

    data["role"] = (
        role or {
            "name": "Sin rol"
        }
    )

    return data


# ============================================================
# CREAR MAPA DE ROLES
# ============================================================

def build_roles_map():

    roles = (
        user_repository
        .get_roles()
    )

    return {
        str(role["_id"]): role
        for role in roles
    }


# ============================================================
# OBTENER TODOS LOS USUARIOS
# ============================================================

def get_all_users():

    users = (
        user_repository
        .get_all()
    )

    roles_map = build_roles_map()

    return [
        enrich_user(
            user,
            roles_map
        )
        for user in users
    ]


# ============================================================
# OBTENER USUARIOS PAGINADOS
# ============================================================

def get_paginated_users(
    page=1,
    per_page=10
):

    try:
        page = int(
            page
        )
    except (
        TypeError,
        ValueError
    ):
        page = 1

    try:
        per_page = int(
            per_page
        )
    except (
        TypeError,
        ValueError
    ):
        per_page = 10

    if page < 1:
        page = 1

    if per_page < 1:
        per_page = 10

    # Evita consultas exageradamente grandes.
    if per_page > 100:
        per_page = 100

    result = (
        user_repository
        .get_paginated(
            page=page,
            per_page=per_page
        )
    )

    roles_map = build_roles_map()

    users = [
        enrich_user(
            user,
            roles_map
        )
        for user in result[
            "users"
        ]
    ]

    total = result[
        "total"
    ]

    total_pages = max(
        math.ceil(
            total / per_page
        ),
        1
    )

    # Si alguien solicita una página demasiado alta,
    # simplemente regresamos la información calculada
    # sin provocar un error del servidor.

    return {
        "users": users,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "prev_page": max(
            page - 1,
            1
        ),
        "next_page": min(
            page + 1,
            total_pages
        )
    }


# ============================================================
# OBTENER USUARIO POR ID
# ============================================================

def get_user_by_id(
    user_id
):

    user_oid = validate_object_id(
        user_id,
        "El identificador del usuario no es válido."
    )

    user = (
        user_repository
        .get_by_id(
            user_oid
        )
    )

    if not user:

        raise UserNotFoundError(
            "Usuario no encontrado."
        )

    return enrich_user(
        user
    )


# ============================================================
# OBTENER ROLES
# ============================================================

def get_available_roles():

    return (
        user_repository
        .get_roles()
    )


# ============================================================
# CAMBIAR ROL
# ============================================================

def change_user_role(
    user_id,
    role_id
):

    user_oid = validate_object_id(
        user_id,
        "El identificador del usuario no es válido."
    )

    try:

        role_oid = ObjectId(
            str(role_id)
        )

    except (
        InvalidId,
        TypeError,
        ValueError
    ):

        raise InvalidRoleError(
            "El rol seleccionado no es válido."
        )

    user = (
        user_repository
        .get_by_id(
            user_oid
        )
    )

    if not user:

        raise UserNotFoundError(
            "Usuario no encontrado."
        )

    role = (
        user_repository
        .get_role_by_id(
            role_oid
        )
    )

    if not role:

        raise InvalidRoleError(
            "El rol seleccionado no existe."
        )

    result = (
        user_repository
        .update_role(
            user_oid,
            role_oid
        )
    )

    return {
        "user": user,
        "role": role,
        "modified": (
            result.modified_count > 0
        )
    }

def create_user(name, last_name, email, password, role_id):
    import re
    import bcrypt
    from datetime import datetime, timezone

    name = (name or "").strip()
    last_name = (last_name or "").strip()
    email = (email or "").strip().lower()
    password = password or ""

    if not name or not email or not password:
        raise UserServiceError("Nombre, correo y contraseña son obligatorios.")
    if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
        raise UserServiceError("El correo electrónico no tiene un formato válido.")
    if len(password) < 8:
        raise UserServiceError("La contraseña debe tener al menos 8 caracteres.")
    if user_repository.get_by_email(email):
        raise UserServiceError("Ya existe un usuario con ese correo.")

    role_oid = validate_object_id(role_id, "El rol seleccionado no es válido.")
    role = user_repository.get_role_by_id(role_oid)
    if not role:
        raise InvalidRoleError("El rol seleccionado no existe. Ejecuta seed.py para preparar los roles.")

    now = datetime.now(timezone.utc)
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    data = {
        "name": name,
        "last_name": last_name,
        "email": email,
        "password": password_hash,
        "role_id": role_oid,
        "active": True,
        "created_at": now,
        "updated_at": now
    }

    try:
        result = user_repository.create(data)
    except Exception as exc:
        raise UserServiceError(f"No fue posible crear el usuario: {exc}") from exc

    data["_id"] = result.inserted_id
    return enrich_user(data)
