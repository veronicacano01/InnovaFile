from datetime import datetime, timezone

from flask import (
    session,
    request
)

from bson import ObjectId

from repositories import activity_repository


# ============================================================
# REGISTRAR ACTIVIDAD
# ============================================================

def log_activity(
    action,
    description="",
    entity_type=None,
    entity_id=None
):

    # --------------------------------------------------------
    # USUARIO
    # --------------------------------------------------------

    user_id = session.get(
        "user_id"
    )

    user_oid = None

    if user_id:
        try:
            user_oid = ObjectId(
                user_id
            )
        except Exception:
            user_oid = None

    # --------------------------------------------------------
    # IP
    # --------------------------------------------------------

    forwarded_for = request.headers.get(
        "X-Forwarded-For"
    )

    if forwarded_for:
        ip_address = (
            forwarded_for.split(",")[0]
            .strip()
        )
    else:
        ip_address = request.remote_addr

    # --------------------------------------------------------
    # DATOS DE AUDITORÍA
    # --------------------------------------------------------

    activity_data = {

        "user_id": user_oid,

        "action": (
            action or "Actividad"
        ).strip(),

        "description": (
            description or ""
        ).strip(),

        "entity_type": entity_type,

        "entity_id": entity_id,

        "ip_address": ip_address,

        "http_method": request.method,

        "route": request.path,

        "user_agent": request.headers.get(
            "User-Agent",
            ""
        ),

        "created_at": datetime.now(
            timezone.utc
        )
    }

    try:

        activity_repository.create(
            activity_data
        )

    except Exception as error:

        print(
            f"Error al registrar actividad: {error}"
        )