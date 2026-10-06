from functools import wraps

from flask import (
    session,
    flash,
    redirect,
    url_for
)

from bson import ObjectId

from extensions import db


# ============================================================
# PERMISOS DISPONIBLES POR ROL
# ============================================================

ROLE_PERMISSIONS = {
    "Administrador": {"dashboard.view","documents.view","documents.create","documents.download","documents.delete","documents.sync","documents.ai","categories.view","categories.create","categories.delete","users.view","users.create","users.edit","history.view","statistics.view"},
    "Gestor documental": {"dashboard.view","documents.view","documents.create","documents.download","documents.delete","documents.sync","documents.ai","categories.view","categories.create","history.view","statistics.view"},
    "Supervisor": {"dashboard.view","documents.view","documents.download","documents.sync","documents.ai","categories.view","history.view","statistics.view"},
    "Colaborador": {"dashboard.view","documents.view","documents.download","documents.sync","categories.view"},
    "Consulta": {"dashboard.view","documents.view","documents.download","documents.ai","categories.view"}
}


# ============================================================
# OBTENER USUARIO ACTUAL
# ============================================================

def get_current_user():

    user_id = session.get("user_id")

    if not user_id:
        return None

    try:
        user_oid = ObjectId(user_id)
    except Exception:
        return None

    return db.users.find_one({
        "_id": user_oid
    })


# ============================================================
# OBTENER ROL ACTUAL
# ============================================================

def get_current_role():

    user = get_current_user()

    if not user:
        return None

    role_id = user.get("role_id")

    if not role_id:
        return None

    try:

        if isinstance(role_id, str):
            role_id = ObjectId(role_id)

    except Exception:
        return None

    role = db.roles.find_one({
        "_id": role_id
    })

    if not role:
        return None

    return role.get("name")


# ============================================================
# COMPROBAR PERMISO
# ============================================================

def has_permission(permission):

    role = get_current_role()

    if not role:
        return False

    # Primero usamos los permisos almacenados en MongoDB.
    # Esto permite que los roles administrados desde la base de datos
    # sean la fuente real de autorización.
    role_doc = db.roles.find_one({"name": role}) or {}
    stored_permissions = role_doc.get("permissions") or []

    if stored_permissions:
        return permission in set(stored_permissions)

    # Compatibilidad con instalaciones anteriores.
    permissions = ROLE_PERMISSIONS.get(role, set())
    return permission in permissions


# ============================================================
# DECORADOR DE PERMISOS
# ============================================================

def permission_required(permission):

    def decorator(function):

        @wraps(function)
        def wrapper(*args, **kwargs):

            if not has_permission(permission):

                flash(
                    "No tienes permisos para realizar esta acción.",
                    "danger"
                )

                return redirect(
                    url_for("dashboard.index")
                )

            return function(
                *args,
                **kwargs
            )

        return wrapper

    return decorator

def has_permission_for_user(user, permission):
    """Comprueba un permiso para un usuario ya autenticado (usado por el agente)."""
    if not user:
        return False
    role_id = user.get("role_id")
    try:
        role = db.roles.find_one({"_id": role_id}) if role_id else None
    except Exception:
        role = None
    if role and permission in set(role.get("permissions", [])):
        return True
    role_name = role.get("name") if role else None
    return permission in ROLE_PERMISSIONS.get(role_name, set())
