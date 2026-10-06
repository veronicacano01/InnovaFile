from bson import ObjectId
from pymongo import DESCENDING

from extensions import db


# ============================================================
# CREAR ACTIVIDAD
# ============================================================

def create(
    activity_data
):

    return (
        db.activity_logs
        .insert_one(
            activity_data
        )
    )


# ============================================================
# OBTENER TODAS
# ============================================================

def get_all():

    return list(
        db.activity_logs
        .find()
        .sort(
            "created_at",
            DESCENDING
        )
    )


# ============================================================
# OBTENER ACTIVIDAD PAGINADA
# ============================================================

def get_paginated(
    page=1,
    per_page=15
):

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

    activities = list(
        db.activity_logs
        .find()
        .sort(
            "created_at",
            DESCENDING
        )
        .skip(skip)
        .limit(per_page)
    )

    total = (
        db.activity_logs
        .count_documents({})
    )

    return {
        "activities": activities,
        "total": total,
        "page": page,
        "per_page": per_page
    }


# ============================================================
# ACTIVIDADES RECIENTES
# ============================================================

def get_recent(
    limit=10
):

    return list(
        db.activity_logs
        .find()
        .sort(
            "created_at",
            DESCENDING
        )
        .limit(limit)
    )


# ============================================================
# ACTIVIDAD POR USUARIO
# ============================================================

def get_by_user(
    user_id
):

    if isinstance(
        user_id,
        str
    ):

        user_id = ObjectId(
            user_id
        )

    return list(
        db.activity_logs
        .find({
            "user_id": user_id
        })
        .sort(
            "created_at",
            DESCENDING
        )
    )