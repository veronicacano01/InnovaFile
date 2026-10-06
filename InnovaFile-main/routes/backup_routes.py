from flask import (
    Blueprint,
    request,
    redirect,
    url_for,
    flash,
    send_file
)

from helpers.auth import (
    login_required,
    role_required
)

from helpers.activity_helper import (
    log_activity
)

from services.backup_service import (
    create_backup,
    restore_backup,
    BackupServiceError,
    InvalidBackupError
)


# ============================================================
# BLUEPRINT
# ============================================================

backup_bp = Blueprint(
    "backups",
    __name__,
    url_prefix="/backups"
)


# ============================================================
# CREAR RESPALDO
# ============================================================

@backup_bp.post(
    "/create"
)
@login_required
@role_required(
    "Administrador"
)
def create():

    try:

        backup = create_backup()

        log_activity(
            "Respaldo del sistema",
            (
                "El administrador creó "
                "un respaldo completo de InnovaFile."
            ),
            entity_type="backup",
            entity_id=backup[
                "name"
            ]
        )

        return send_file(
            backup[
                "path"
            ],
            as_attachment=True,
            download_name=backup[
                "name"
            ]
        )

    except BackupServiceError as error:

        flash(
            str(error),
            "danger"
        )

        return redirect(
            url_for(
                "dashboard.index"
            )
        )


# ============================================================
# RESTAURAR RESPALDO
# ============================================================

@backup_bp.post(
    "/restore"
)
@login_required
@role_required(
    "Administrador"
)
def restore():

    backup_file = request.files.get(
        "backup_file"
    )

    try:

        result = restore_backup(
            backup_file
        )

        log_activity(
            "Restauración del sistema",
            (
                "El administrador restauró "
                "un respaldo completo de InnovaFile."
            ),
            entity_type="backup"
        )

        flash(
            "Respaldo restaurado correctamente.",
            "success"
        )

    except InvalidBackupError as error:

        flash(
            str(error),
            "danger"
        )

    except BackupServiceError as error:

        flash(
            str(error),
            "danger"
        )

    return redirect(
        url_for(
            "dashboard.index"
        )
    )