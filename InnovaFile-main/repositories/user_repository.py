from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

from extensions import db


# ============================================================
# OBTENER TODOS LOS USUARIOS
# ============================================================

def get_all():

    return list(
        db.users.find().sort(
            "created_at",
            DESCENDING
        )
    )


# ============================================================
# OBTENER USUARIOS PAGINADOS
# ============================================================

def get_paginated(page=1, per_page=10):

    page = max(
        int(page),
        1
    )

    per_page = max(
        int(per_page),
        1
    )

    skip = (
        page - 1
    ) * per_page

    users = list(
        db.users.find()
        .sort(
            "created_at",
            DESCENDING
        )
        .skip(skip)
        .limit(per_page)
    )

    total = db.users.count_documents({})

    return {
        "users": users,
        "total": total,
        "page": page,
        "per_page": per_page
    }


# ============================================================
# OBTENER USUARIO POR ID
# ============================================================

def get_by_id(user_id):

    if not user_id:
        return None

    if isinstance(
        user_id,
        str
    ):
        user_id = ObjectId(
            user_id
        )

    return db.users.find_one({
        "_id": user_id
    })


# ============================================================
# OBTENER USUARIO POR CORREO
# ============================================================

def get_by_email(email):

    if not email:
        return None

    return db.users.find_one({
        "email": email.strip().lower()
    })


# ============================================================
# ACTUALIZAR ROL
# ============================================================

def update_role(
    user_id,
    role_id
):

    if isinstance(
        user_id,
        str
    ):
        user_id = ObjectId(
            user_id
        )

    if isinstance(
        role_id,
        str
    ):
        role_id = ObjectId(
            role_id
        )

    return db.users.update_one(
        {
            "_id": user_id
        },
        {
            "$set": {
                "role_id": role_id
            }
        }
    )


# ============================================================
# ROLES
# ============================================================

def get_roles():

    return list(
        db.roles.find().sort(
            "name",
            ASCENDING
        )
    )


# ============================================================
# OBTENER ROL
# ============================================================

def get_role_by_id(role_id):

    if not role_id:
        return None

    if isinstance(
        role_id,
        str
    ):
        role_id = ObjectId(
            role_id
        )

    return db.roles.find_one({
        "_id": role_id
    })

def set_agent_token(user_id, token_hash):
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    return db.users.update_one(
        {"_id": user_id},
        {"$set": {"agent_token_hash": token_hash}}
    )


def get_by_agent_token(token_hash):
    if not token_hash:
        return None
    return db.users.find_one({"agent_token_hash": token_hash})


def revoke_agent_token(user_id):
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    return db.users.update_one(
        {"_id": user_id},
        {"$unset": {"agent_token_hash": ""}}
    )


def create(data):
    return db.users.insert_one(data)
