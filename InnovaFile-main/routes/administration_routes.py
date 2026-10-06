from flask import (
    Blueprint,
    render_template
)

from helpers.auth import (
    login_required,
    role_required
)

from services.administration_service import (
    get_system_information
)


# ============================================================
# BLUEPRINT
# ============================================================

administration_bp = Blueprint(
    "administration",
    __name__,
    url_prefix="/administration"
)


# ============================================================
# PANEL DE ADMINISTRACIÓN
# ============================================================

@administration_bp.get(
    "/"
)
@login_required
@role_required(
    "Administrador"
)
def index():

    system_info = (
        get_system_information()
    )

    return render_template(
        "administration/index.html",
        system_info=system_info
    )