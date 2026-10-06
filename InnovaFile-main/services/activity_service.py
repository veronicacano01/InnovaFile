import math

from repositories import (
    activity_repository,
    user_repository
)


# ============================================================
# ENRIQUECER ACTIVIDAD
# ============================================================

def enrich_activity(
    activity,
    users_map=None
):

    data = dict(
        activity
    )

    user_id = data.get(
        "user_id"
    )

    user = None

    if user_id:

        if users_map is not None:

            user = users_map.get(
                str(user_id)
            )

        else:

            try:

                user = (
                    user_repository
                    .get_by_id(
                        user_id
                    )
                )

            except Exception:
                user = None

    data["user"] = (
        user or {
            "name": "Sistema",
            "email": ""
        }
    )

    return data


# ============================================================
# CREAR MAPA DE USUARIOS
# ============================================================

def build_users_map():

    users = (
        user_repository
        .get_all()
    )

    return {
        str(user["_id"]): user
        for user in users
    }


# ============================================================
# ACTIVIDAD PAGINADA
# ============================================================

def get_paginated_activities(
    page=1,
    per_page=15
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

        per_page = 15

    if page < 1:
        page = 1

    if per_page < 1:
        per_page = 15

    if per_page > 100:
        per_page = 100

    result = (
        activity_repository
        .get_paginated(
            page=page,
            per_page=per_page
        )
    )

    users_map = (
        build_users_map()
    )

    activities = [
        enrich_activity(
            activity,
            users_map
        )
        for activity in result[
            "activities"
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

    return {
        "activities": activities,
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