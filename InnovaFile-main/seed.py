"""Prepara roles, categorías y administrador de InnovaFile.

Este script es idempotente: puede ejecutarse varias veces sin duplicar
roles/categorías y actualiza los permisos de las instalaciones anteriores.
"""
from datetime import datetime, timezone
import bcrypt
from app import create_app
from extensions import db
from helpers.permissions import ROLE_PERMISSIONS

ROLES = [
    ("Administrador", "Acceso completo al sistema"),
    ("Gestor documental", "Administra y organiza documentos"),
    ("Supervisor", "Supervisa documentos y actividad"),
    ("Colaborador", "Consulta y sincroniza documentos"),
    ("Consulta", "Solo lectura"),
]

CATEGORIES = [
    ("Contratos", "Contratos, convenios y acuerdos."),
    ("Facturas", "Facturas, recibos y comprobantes."),
    ("Reportes", "Reportes, informes y estadísticas."),
    ("Manuales", "Manuales, guías y procedimientos."),
    ("Currículums", "Currículums y perfiles profesionales."),
    ("Recursos Humanos", "Expedientes y documentos laborales."),
    ("Finanzas", "Estados financieros y documentos contables."),
    ("Clientes", "Documentos relacionados con clientes."),
    ("Proveedores", "Documentos relacionados con proveedores."),
    ("Documentación legal", "Actas y documentación jurídica."),
    ("Administración", "Oficios y documentación administrativa."),
    ("Otros", "Documentos que no encajan en otra categoría."),
]

app = create_app()

with app.app_context():
    now = datetime.now(timezone.utc)

    # Índice único de correo para evitar usuarios duplicados.
    try:
        db.users.create_index("email", unique=True, name="users_email_unique")
    except Exception:
        pass

    role_ids = {}
    for name, description in ROLES:
        permissions = sorted(ROLE_PERMISSIONS.get(name, set()))
        db.roles.update_one(
            {"name": name},
            {"$set": {
                "name": name,
                "description": description,
                "permissions": permissions,
                "updated_at": now,
            }, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )
        role_ids[name] = db.roles.find_one({"name": name})["_id"]

    # Migración de roles de versiones anteriores.
    legacy_map = {
        "administrador": "Administrador",
        "admin": "Administrador",
        "administrator": "Administrador",
        "supervisor": "Supervisor",
        "empleado": "Colaborador",
        "colaborador": "Colaborador",
        "consulta": "Consulta",
        "gestor documental": "Gestor documental",
    }
    for old_name, new_name in legacy_map.items():
        old_role = db.roles.find_one({"name": old_name})
        if old_role:
            db.users.update_many(
                {"role_id": old_role["_id"]},
                {"$set": {"role_id": role_ids[new_name], "updated_at": now}},
            )

    for name, description in CATEGORIES:
        db.categories.update_one(
            {"name": name},
            {"$set": {"description": description, "updated_at": now},
             "$setOnInsert": {"created_at": now}},
            upsert=True,
        )

    # Administrador inicial. Si ya existe, se conserva su contraseña actual
    # pero se corrige su rol y estado para que pueda administrar usuarios.
    admin_email = "admin@innovafile.com"
    admin = db.users.find_one({"email": admin_email})
    if admin:
        db.users.update_one(
            {"_id": admin["_id"]},
            {"$set": {
                "role_id": role_ids["Administrador"],
                "active": True,
                "updated_at": now,
            }},
        )
        admin_password = "(se conserva la contraseña existente)"
    else:
        admin_password = "Admin123!"
        db.users.insert_one({
            "name": "Administrador",
            "last_name": "InnovaFile",
            "email": admin_email,
            "password": bcrypt.hashpw(admin_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
            "role_id": role_ids["Administrador"],
            "active": True,
            "created_at": now,
            "updated_at": now,
        })

    print("OK: roles y permisos preparados.")
    print("OK: categorías preparadas.")
    print("OK: administrador: ", admin_email)
    print("Contraseña: ", admin_password)
