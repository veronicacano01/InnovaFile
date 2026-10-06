import os
import shutil
import uuid

from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from werkzeug.utils import secure_filename

from repositories import document_version_repository


# ============================================================
# EXTENSIONES PERMITIDAS
# ============================================================

ALLOWED_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "ppt",
    "pptx",
    "txt",
    "csv",
    "jpg",
    "jpeg",
    "png"
}


# ============================================================
# EXCEPCIONES
# ============================================================

class DocumentVersionError(Exception):
    pass


class DocumentVersionNotFoundError(
    DocumentVersionError
):
    pass


# ============================================================
# VALIDAR OBJECT ID
# ============================================================

def validate_object_id(value):

    try:

        return ObjectId(
            str(value)
        )

    except (
        InvalidId,
        TypeError,
        ValueError
    ):

        raise DocumentVersionError(
            "Identificador inválido."
        )


# ============================================================
# VALIDAR USUARIO
# ============================================================

def validate_user_id(user_id):

    if not user_id:

        raise DocumentVersionError(
            "No se pudo identificar al usuario."
        )

    return validate_object_id(
        user_id
    )


# ============================================================
# VALIDAR EXTENSIÓN
# ============================================================

def validate_extension(filename):

    if not filename or "." not in filename:

        raise DocumentVersionError(
            "El archivo no tiene una extensión válida."
        )

    extension = (
        filename
        .rsplit(".", 1)[1]
        .lower()
    )

    if extension not in ALLOWED_EXTENSIONS:

        raise DocumentVersionError(
            f"El tipo de archivo .{extension} no está permitido."
        )

    return extension


# ============================================================
# RUTA RELATIVA
# ============================================================

def relative_to_root(
    full_path,
    root_path
):

    return (
        os.path.relpath(
            full_path,
            root_path
        )
        .replace(
            "\\",
            "/"
        )
    )


# ============================================================
# LOCALIZAR ARCHIVO ACTUAL
# ============================================================

def resolve_current_file_path(
    document,
    root_path,
    upload_folder
):

    upload_dir = os.path.join(
        root_path,
        upload_folder
    )

    # --------------------------------------------------------
    # STORED_FILENAME
    # --------------------------------------------------------

    stored_filename = document.get(
        "stored_filename"
    )

    if stored_filename:

        candidate = os.path.join(
            upload_dir,
            os.path.basename(
                stored_filename
            )
        )

        if os.path.isfile(
            candidate
        ):

            return candidate

    # --------------------------------------------------------
    # FILE_PATH
    # --------------------------------------------------------

    file_path = document.get(
        "file_path"
    )

    if file_path:

        candidate = os.path.join(
            upload_dir,
            os.path.basename(
                file_path
            )
        )

        if os.path.isfile(
            candidate
        ):

            return candidate

    # --------------------------------------------------------
    # FILE_PATH RELATIVO AL ROOT
    # --------------------------------------------------------

    if file_path:

        candidate = os.path.join(
            root_path,
            file_path
        )

        if os.path.isfile(
            candidate
        ):

            return candidate

    raise DocumentVersionError(
        "No se encontró el archivo físico de la versión actual."
    )


# ============================================================
# ENRIQUECER VERSIÓN
# ============================================================

def enrich_version(version):

    if not version:
        return None

    data = dict(
        version
    )

    user = None

    user_id = data.get(
        "user_id"
    )

    if user_id:

        try:

            user = (
                document_version_repository
                .get_user(
                    user_id
                )
            )

        except Exception:

            user = None

    data["user"] = (
        user
        or {
            "name": "Desconocido"
        }
    )

    return data


# ============================================================
# OBTENER VERSIONES
# ============================================================

def get_document_versions(
    document_id
):

    document_id = validate_object_id(
        document_id
    )

    versions = (
        document_version_repository
        .get_versions_by_document(
            document_id
        )
    )

    return [
        enrich_version(
            version
        )
        for version in versions
    ]


# ============================================================
# GUARDAR VERSIÓN ANTERIOR
# ============================================================

def save_previous_version(
    document,
    user_id,
    root_path,
    upload_folder
):

    user_id = validate_user_id(
        user_id
    )

    document_id = document.get(
        "_id"
    )

    if not document_id:

        raise DocumentVersionError(
            "El documento no tiene identificador."
        )

    current_version = int(
        document.get(
            "version_number",
            1
        )
        or 1
    )

    # --------------------------------------------------------
    # LOCALIZAR ARCHIVO
    # --------------------------------------------------------

    source_path = resolve_current_file_path(
        document=document,
        root_path=root_path,
        upload_folder=upload_folder
    )

    # --------------------------------------------------------
    # DIRECTORIO DE VERSIONES
    # --------------------------------------------------------

    upload_dir = os.path.join(
        root_path,
        upload_folder
    )

    versions_dir = os.path.join(
        upload_dir,
        "versions"
    )

    os.makedirs(
        versions_dir,
        exist_ok=True
    )

    # --------------------------------------------------------
    # EXTENSIÓN
    # --------------------------------------------------------

    extension = (
        document.get(
            "file_type"
        )
        or ""
    ).lower().strip(".")

    if not extension:

        current_name = (
            document.get(
                "file_name"
            )
            or
            os.path.basename(
                source_path
            )
        )

        if "." in current_name:

            extension = (
                current_name
                .rsplit(
                    ".",
                    1
                )[1]
                .lower()
            )

    if not extension:

        raise DocumentVersionError(
            "No fue posible determinar el tipo del archivo actual."
        )

    # --------------------------------------------------------
    # NOMBRE ÚNICO
    # --------------------------------------------------------

    version_filename = (
        f"{uuid.uuid4().hex}.{extension}"
    )

    version_full_path = os.path.join(
        versions_dir,
        version_filename
    )

    # --------------------------------------------------------
    # COPIAR ARCHIVO ACTUAL
    # --------------------------------------------------------

    try:

        shutil.copy2(
            source_path,
            version_full_path
        )

    except OSError as error:

        raise DocumentVersionError(
            f"No fue posible conservar la versión anterior: {error}"
        )

    version_relative_path = relative_to_root(
        version_full_path,
        root_path
    )

    # --------------------------------------------------------
    # INFORMACIÓN DE VERSIÓN
    # --------------------------------------------------------

    version_data = {

        "document_id":
            document_id,

        "version_number":
            current_version,

        "file_name":
            document.get(
                "file_name"
            ),

        "stored_filename":
            version_filename,

        "file_path":
            version_relative_path,

        "file_type":
            extension,

        "file_size":
            document.get(
                "file_size",
                0
            ),

        "user_id":
            user_id,

        "created_at":
            datetime.now(
                timezone.utc
            )
    }

    try:

        return (
            document_version_repository
            .create_version(
                version_data
            )
        )

    except Exception:

        if os.path.isfile(
            version_full_path
        ):

            try:

                os.remove(
                    version_full_path
                )

            except OSError:
                pass

        raise


# ============================================================
# SUBIR NUEVA VERSIÓN
# ============================================================

def upload_new_version(
    document_id,
    file,
    user_id,
    root_path,
    upload_folder,
    comment=""
):

    document_id = validate_object_id(
        document_id
    )

    user_id = validate_user_id(
        user_id
    )

    # --------------------------------------------------------
    # VALIDAR ARCHIVO
    # --------------------------------------------------------

    if not file:

        raise DocumentVersionError(
            "Debes seleccionar un archivo."
        )

    original_filename = secure_filename(
        file.filename or ""
    )

    if not original_filename:

        raise DocumentVersionError(
            "Debes seleccionar un archivo válido."
        )

    extension = validate_extension(
        original_filename
    )

    # --------------------------------------------------------
    # OBTENER DOCUMENTO
    # --------------------------------------------------------

    document = (
        document_version_repository
        .get_document(
            document_id
        )
    )

    if not document:

        raise DocumentVersionError(
            "El documento no existe."
        )

    if document.get(
        "is_deleted"
    ) is True:

        raise DocumentVersionError(
            "No puedes subir una nueva versión de un documento que está en la papelera."
        )

    # --------------------------------------------------------
    # ARCHIVO ANTERIOR
    # --------------------------------------------------------

    old_file_path = resolve_current_file_path(
        document=document,
        root_path=root_path,
        upload_folder=upload_folder
    )

    # --------------------------------------------------------
    # GUARDAR VERSIÓN ANTERIOR
    # --------------------------------------------------------

    saved_previous_version = (
        save_previous_version(
            document=document,
            user_id=user_id,
            root_path=root_path,
            upload_folder=upload_folder
        )
    )

    # --------------------------------------------------------
    # PREPARAR NUEVO ARCHIVO
    # --------------------------------------------------------

    upload_dir = os.path.join(
        root_path,
        upload_folder
    )

    os.makedirs(
        upload_dir,
        exist_ok=True
    )

    stored_filename = (
        f"{uuid.uuid4().hex}.{extension}"
    )

    new_file_full_path = os.path.join(
        upload_dir,
        stored_filename
    )

    # --------------------------------------------------------
    # GUARDAR ARCHIVO
    # --------------------------------------------------------

    try:

        file.save(
            new_file_full_path
        )

    except Exception as error:

        raise DocumentVersionError(
            f"No fue posible guardar el nuevo archivo: {error}"
        )

    # --------------------------------------------------------
    # TAMAÑO
    # --------------------------------------------------------

    try:

        file_size = os.path.getsize(
            new_file_full_path
        )

    except OSError:

        if os.path.isfile(
            new_file_full_path
        ):

            try:
                os.remove(
                    new_file_full_path
                )
            except OSError:
                pass

        raise DocumentVersionError(
            "No fue posible obtener el tamaño del archivo."
        )

    # --------------------------------------------------------
    # NÚMERO DE VERSIÓN
    # --------------------------------------------------------

    current_version = int(
        document.get(
            "version_number",
            1
        )
        or 1
    )

    new_version_number = (
        current_version + 1
    )

    new_relative_path = relative_to_root(
        new_file_full_path,
        root_path
    )

    now = datetime.now(
        timezone.utc
    )

    # --------------------------------------------------------
    # ACTUALIZAR MONGODB
    # --------------------------------------------------------

    update_data = {

        "file_name":
            original_filename,

        "stored_filename":
            stored_filename,

        "file_path":
            new_relative_path,

        "file_type":
            extension,

        "file_size":
            file_size,

        "version_number":
            new_version_number,

        "version_comment":
            (
                comment.strip()
                if comment
                else ""
            ),

        "version_updated_by":
            user_id,

        "updated_at":
            now
    }

    try:

        result = (
            document_version_repository
            .update_current_document(
                document_id,
                update_data
            )
        )

        if result.modified_count == 0:

            raise DocumentVersionError(
                "No fue posible actualizar la información del documento."
            )

    except Exception:

        if os.path.isfile(
            new_file_full_path
        ):

            try:

                os.remove(
                    new_file_full_path
                )

            except OSError:
                pass

        raise

    # --------------------------------------------------------
    # ELIMINAR ARCHIVO ACTUAL VIEJO
    # --------------------------------------------------------

    if (
        old_file_path
        and
        os.path.isfile(
            old_file_path
        )
        and
        os.path.abspath(
            old_file_path
        )
        !=
        os.path.abspath(
            new_file_full_path
        )
    ):

        try:

            os.remove(
                old_file_path
            )

        except OSError:
            pass

    # --------------------------------------------------------
    # AGREGAR COMENTARIO A LA VERSIÓN ANTERIOR
    # --------------------------------------------------------

    if saved_previous_version and comment:

        try:

            document_version_repository.collection().update_one(
                {
                    "_id":
                        saved_previous_version[
                            "_id"
                        ]
                },
                {
                    "$set": {
                        "replacement_comment":
                            comment.strip()
                    }
                }
            )

        except Exception:
            pass

    # --------------------------------------------------------
    # REGRESAR DOCUMENTO ACTUAL
    # --------------------------------------------------------

    return (
        document_version_repository
        .get_document(
            document_id
        )
    )


# ============================================================
# DESCARGAR VERSIÓN
# ============================================================

def get_version_for_download(
    version_id
):

    version_id = validate_object_id(
        version_id
    )

    version = (
        document_version_repository
        .get_version_by_id(
            version_id
        )
    )

    if not version:

        raise DocumentVersionNotFoundError(
            "La versión solicitada no existe."
        )

    return version