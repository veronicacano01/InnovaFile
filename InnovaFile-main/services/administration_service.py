import os

from datetime import datetime

from flask import current_app

from repositories import (
    administration_repository
)


# ============================================================
# FORMATEAR TAMAÑO
# ============================================================

def format_size(
    size_bytes
):

    if size_bytes < 1024:

        return (
            f"{size_bytes} B"
        )

    if size_bytes < (
        1024 * 1024
    ):

        return (
            f"{size_bytes / 1024:.2f} KB"
        )

    if size_bytes < (
        1024 * 1024 * 1024
    ):

        return (
            f"{size_bytes / (1024 * 1024):.2f} MB"
        )

    return (
        f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    )


# ============================================================
# CALCULAR ESPACIO DE UPLOADS
# ============================================================

def get_uploads_size():

    upload_folder = current_app.config[
        "UPLOAD_FOLDER"
    ]

    total_size = 0

    if not os.path.exists(
        upload_folder
    ):

        return {
            "bytes": 0,
            "formatted": "0 B"
        }

    for root, directories, files in os.walk(
        upload_folder
    ):

        for file_name in files:

            file_path = os.path.join(
                root,
                file_name
            )

            try:

                total_size += (
                    os.path.getsize(
                        file_path
                    )
                )

            except OSError:

                continue

    return {
        "bytes": total_size,
        "formatted": format_size(
            total_size
        )
    }


# ============================================================
# ÚLTIMO RESPALDO
# ============================================================

def get_last_backup():

    backup_folder = os.path.join(
        current_app.root_path,
        "backups"
    )

    if not os.path.exists(
        backup_folder
    ):

        return None

    backup_files = []

    for file_name in os.listdir(
        backup_folder
    ):

        if not file_name.lower().endswith(
            ".zip"
        ):

            continue

        file_path = os.path.join(
            backup_folder,
            file_name
        )

        try:

            modified_at = os.path.getmtime(
                file_path
            )

            backup_files.append({
                "name": file_name,
                "path": file_path,
                "modified_at": modified_at
            })

        except OSError:

            continue

    if not backup_files:

        return None

    latest = max(
        backup_files,
        key=lambda item: item[
            "modified_at"
        ]
    )

    latest[
        "date"
    ] = datetime.fromtimestamp(
        latest[
            "modified_at"
        ]
    ).strftime(
        "%d/%m/%Y %H:%M"
    )

    try:

        latest[
            "size"
        ] = format_size(
            os.path.getsize(
                latest[
                    "path"
                ]
            )
        )

    except OSError:

        latest[
            "size"
        ] = "Desconocido"

    return latest


# ============================================================
# INFORMACIÓN GENERAL
# ============================================================

def get_system_information():

    database_online = (
        administration_repository
        .ping_database()
    )

    uploads = get_uploads_size()

    last_backup = get_last_backup()

    return {

        "database_online":
            database_online,

        "database_name":
            current_app.config.get(
                "MONGO_DB",
                "innovafile"
            ),

        "users":
            administration_repository
            .count_users(),

        "documents":
            administration_repository
            .count_documents(),

        "categories":
            administration_repository
            .count_categories(),

        "activities":
            administration_repository
            .count_activities(),

        "uploads_size":
            uploads,

        "last_backup":
            last_backup
    }