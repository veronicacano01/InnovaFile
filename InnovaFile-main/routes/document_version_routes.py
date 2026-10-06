import os

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    request,
    send_file,
    session,
    url_for
)

from helpers.auth import login_required
from helpers.permissions import permission_required
from helpers.activity_helper import log_activity

from services.document_version_service import (
    upload_new_version,
    get_version_for_download,
    DocumentVersionError
)


# ============================================================
# BLUEPRINT
# ============================================================

document_versions_bp = Blueprint(
    "document_versions",
    __name__,
    url_prefix="/document-versions"
)


# ============================================================
# SUBIR NUEVA VERSIÓN
# ============================================================

@document_versions_bp.post(
    "/<document_id>/upload"
)
@login_required
@permission_required(
    "documents.create"
)
def upload(document_id):

    file = request.files.get(
        "file"
    )

    comment = (
        request.form.get(
            "comment",
            ""
        )
        .strip()
    )

    user_id = session.get(
        "user_id"
    )

    try:

        document = upload_new_version(
            document_id=document_id,
            file=file,
            user_id=user_id,
            root_path=current_app.root_path,
            upload_folder=current_app.config[
                "UPLOAD_FOLDER"
            ],
            comment=comment
        )

        log_activity(
            "Nueva versión de documento",
            (
                f"Se subió la versión "
                f"{document.get('version_number', '')} "
                f"del documento "
                f"{document.get('title', 'Sin título')}."
            ),
            entity_type="document",
            entity_id=document_id
        )

        flash(
            (
                f"Versión "
                f"{document.get('version_number', '')} "
                f"subida correctamente."
            ),
            "success"
        )

    except DocumentVersionError as error:

        flash(
            str(error),
            "danger"
        )

    except Exception as error:

        current_app.logger.exception(
            "Error al subir nueva versión del documento %s: %s",
            document_id,
            error
        )

        flash(
            "Ocurrió un error al subir la nueva versión.",
            "danger"
        )

    return redirect(
        url_for(
            "documents.show",
            document_id=document_id
        )
    )


# ============================================================
# DESCARGAR VERSIÓN ANTERIOR
# ============================================================

@document_versions_bp.get(
    "/version/<version_id>/download"
)
@login_required
@permission_required(
    "documents.download"
)
def download(version_id):

    try:

        version = get_version_for_download(
            version_id
        )

        file_path = version.get(
            "file_path"
        )

        if not file_path:

            raise DocumentVersionError(
                "Esta versión no tiene un archivo asociado."
            )

        full_path = os.path.join(
            current_app.root_path,
            file_path
        )

        if not os.path.isfile(
            full_path
        ):

            flash(
                "El archivo físico de esta versión ya no existe.",
                "danger"
            )

            return redirect(
                url_for(
                    "documents.index"
                )
            )

        log_activity(
            "Versión descargada",
            (
                f"Se descargó la versión "
                f"{version.get('version_number', '')} "
                f"de un documento."
            ),
            entity_type="document",
            entity_id=str(
                version.get(
                    "document_id",
                    ""
                )
            )
        )

        return send_file(
            full_path,
            as_attachment=True,
            download_name=version.get(
                "file_name",
                "documento"
            )
        )

    except DocumentVersionError as error:

        flash(
            str(error),
            "danger"
        )

        return redirect(
            url_for(
                "documents.index"
            )
        )

    except Exception as error:

        current_app.logger.exception(
            "Error al descargar la versión %s: %s",
            version_id,
            error
        )

        flash(
            "No fue posible descargar esta versión.",
            "danger"
        )

        return redirect(
            url_for(
                "documents.index"
            )
        )