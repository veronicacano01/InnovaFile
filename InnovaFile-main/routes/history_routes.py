from flask import (
    Blueprint,
    render_template,
    request,
    flash
)

from helpers.auth import (
    login_required
)

from helpers.permissions import (
    permission_required
)

from services.activity_service import (
    get_paginated_activities
)


# ============================================================
# BLUEPRINT
# ============================================================

history_bp = Blueprint(
    "history",
    __name__,
    url_prefix="/history"
)


# ============================================================
# HISTORIAL
# ============================================================

@history_bp.get("/")
@login_required
@permission_required(
    "history.view"
)
def index():

    page = request.args.get(
        "page",
        1
    )

    per_page = request.args.get(
        "per_page",
        15
    )

    try:

        pagination = (
            get_paginated_activities(
                page=page,
                per_page=per_page
            )
        )

    except Exception as error:

        print(
            f"Error al cargar auditoría: {error}"
        )

        pagination = {
            "activities": [],
            "page": 1,
            "per_page": 15,
            "total": 0,
            "total_pages": 1,
            "has_prev": False,
            "has_next": False,
            "prev_page": 1,
            "next_page": 1
        }

        flash(
            "No fue posible cargar el historial de actividad.",
            "danger"
        )

    return render_template(
        "history/index.html",
        activities=pagination[
            "activities"
        ],
        pagination=pagination
    )