import os
import shutil
import tempfile
import zipfile

from datetime import datetime, timezone

from bson import json_util
from flask import current_app

from extensions import db


# ============================================================
# EXCEPCIONES
# ============================================================

class BackupServiceError(Exception):
    pass


class InvalidBackupError(BackupServiceError):
    pass


# ============================================================
# COLECCIONES A RESPALDAR
# ============================================================

COLLECTIONS = [
    "users",
    "roles",
    "categories",
    "documents",
    "activity_logs"
]


# ============================================================
# CREAR RESPALDO
# ============================================================

def create_backup():

    backup_folder = os.path.join(
        current_app.root_path,
        "backups"
    )

    os.makedirs(
        backup_folder,
        exist_ok=True
    )

    timestamp = datetime.now(
        timezone.utc
    ).strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_name = (
        f"innovafile_backup_{timestamp}.zip"
    )

    backup_path = os.path.join(
        backup_folder,
        backup_name
    )

    temp_folder = tempfile.mkdtemp()

    try:

        database_folder = os.path.join(
            temp_folder,
            "database"
        )

        os.makedirs(
            database_folder,
            exist_ok=True
        )

        # ====================================================
        # RESPALDAR MONGODB
        # ====================================================

        for collection_name in COLLECTIONS:

            collection = db[
                collection_name
            ]

            records = list(
                collection.find({})
            )

            file_path = os.path.join(
                database_folder,
                f"{collection_name}.json"
            )

            with open(
                file_path,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(
                    json_util.dumps(
                        records,
                        indent=2
                    )
                )

        # ====================================================
        # INFORMACIÓN DEL RESPALDO
        # ====================================================

        manifest = {

            "system": "InnovaFile",

            "created_at": datetime.now(
                timezone.utc
            ),

            "collections": COLLECTIONS
        }

        manifest_path = os.path.join(
            temp_folder,
            "manifest.json"
        )

        with open(
            manifest_path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                json_util.dumps(
                    manifest,
                    indent=2
                )
            )

        # ====================================================
        # RESPALDAR UPLOADS
        # ====================================================

        upload_folder = current_app.config[
            "UPLOAD_FOLDER"
        ]

        temp_uploads = os.path.join(
            temp_folder,
            "uploads"
        )

        if os.path.exists(
            upload_folder
        ):

            shutil.copytree(
                upload_folder,
                temp_uploads,
                dirs_exist_ok=True
            )

        else:

            os.makedirs(
                temp_uploads,
                exist_ok=True
            )

        # ====================================================
        # CREAR ZIP
        # ====================================================

        with zipfile.ZipFile(
            backup_path,
            "w",
            zipfile.ZIP_DEFLATED
        ) as zip_file:

            for root, directories, files in os.walk(
                temp_folder
            ):

                for filename in files:

                    complete_path = os.path.join(
                        root,
                        filename
                    )

                    relative_path = os.path.relpath(
                        complete_path,
                        temp_folder
                    )

                    zip_file.write(
                        complete_path,
                        relative_path
                    )

        current_app.logger.info(
            f"Respaldo creado: {backup_name}"
        )

        return {
            "name": backup_name,
            "path": backup_path
        }

    except Exception as error:

        current_app.logger.exception(
            "Error creando respaldo."
        )

        raise BackupServiceError(
            f"No fue posible crear el respaldo: {error}"
        )

    finally:

        shutil.rmtree(
            temp_folder,
            ignore_errors=True
        )


# ============================================================
# VALIDAR ZIP
# ============================================================

def validate_zip(
    zip_file
):

    for member in zip_file.infolist():

        filename = member.filename

        if (
            filename.startswith("/")
            or filename.startswith("\\")
            or ".." in filename.split("/")
            or ".." in filename.split("\\")
        ):

            raise InvalidBackupError(
                "El respaldo contiene rutas no permitidas."
            )


# ============================================================
# RESTAURAR RESPALDO
# ============================================================

def restore_backup(
    backup_file
):

    if not backup_file:

        raise InvalidBackupError(
            "Debes seleccionar un respaldo."
        )

    filename = (
        backup_file.filename
        or ""
    ).lower()

    if not filename.endswith(
        ".zip"
    ):

        raise InvalidBackupError(
            "El archivo debe ser un respaldo .zip."
        )

    temp_folder = tempfile.mkdtemp()

    try:

        temp_zip = os.path.join(
            temp_folder,
            "backup.zip"
        )

        backup_file.save(
            temp_zip
        )

        extract_folder = os.path.join(
            temp_folder,
            "restore"
        )

        os.makedirs(
            extract_folder,
            exist_ok=True
        )

        # ====================================================
        # EXTRAER
        # ====================================================

        try:

            with zipfile.ZipFile(
                temp_zip,
                "r"
            ) as zip_file:

                validate_zip(
                    zip_file
                )

                zip_file.extractall(
                    extract_folder
                )

        except zipfile.BadZipFile:

            raise InvalidBackupError(
                "El archivo ZIP está dañado o no es válido."
            )

        # ====================================================
        # VALIDAR MANIFEST
        # ====================================================

        manifest_path = os.path.join(
            extract_folder,
            "manifest.json"
        )

        if not os.path.exists(
            manifest_path
        ):

            raise InvalidBackupError(
                "El archivo no corresponde a un respaldo de InnovaFile."
            )

        with open(
            manifest_path,
            "r",
            encoding="utf-8"
        ) as file:

            manifest = json_util.loads(
                file.read()
            )

        if manifest.get(
            "system"
        ) != "InnovaFile":

            raise InvalidBackupError(
                "El respaldo no pertenece a InnovaFile."
            )

        database_folder = os.path.join(
            extract_folder,
            "database"
        )

        if not os.path.isdir(
            database_folder
        ):

            raise InvalidBackupError(
                "El respaldo no contiene la base de datos."
            )

        # ====================================================
        # LEER TODO ANTES DE BORRAR
        # ====================================================

        restored_data = {}

        for collection_name in COLLECTIONS:

            json_path = os.path.join(
                database_folder,
                f"{collection_name}.json"
            )

            if not os.path.exists(
                json_path
            ):

                restored_data[
                    collection_name
                ] = []

                continue

            with open(
                json_path,
                "r",
                encoding="utf-8"
            ) as file:

                restored_data[
                    collection_name
                ] = json_util.loads(
                    file.read()
                )

        # ====================================================
        # RESTAURAR BASE DE DATOS
        # ====================================================

        restored_counts = {}

        for collection_name in COLLECTIONS:

            collection = db[
                collection_name
            ]

            collection.delete_many({})

            records = restored_data[
                collection_name
            ]

            if records:

                result = collection.insert_many(
                    records
                )

                restored_counts[
                    collection_name
                ] = len(
                    result.inserted_ids
                )

            else:

                restored_counts[
                    collection_name
                ] = 0

        # ====================================================
        # RESTAURAR ARCHIVOS
        # ====================================================

        backup_uploads = os.path.join(
            extract_folder,
            "uploads"
        )

        current_uploads = (
            current_app.config[
                "UPLOAD_FOLDER"
            ]
        )

        if os.path.exists(
            current_uploads
        ):

            shutil.rmtree(
                current_uploads
            )

        os.makedirs(
            current_uploads,
            exist_ok=True
        )

        if os.path.exists(
            backup_uploads
        ):

            shutil.copytree(
                backup_uploads,
                current_uploads,
                dirs_exist_ok=True
            )

        current_app.logger.warning(
            "Se realizó una restauración completa del sistema."
        )

        return {
            "collections": restored_counts
        }

    except InvalidBackupError:
        raise

    except Exception as error:

        current_app.logger.exception(
            "Error restaurando respaldo."
        )

        raise BackupServiceError(
            f"No fue posible restaurar el respaldo: {error}"
        )

    finally:

        shutil.rmtree(
            temp_folder,
            ignore_errors=True
        )