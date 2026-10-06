import os

from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId

from repositories import category_repository


# ============================================================
# EXCEPCIONES
# ============================================================

class CategoryServiceError(Exception):
    pass


class CategoryNotFoundError(CategoryServiceError):
    pass


class InvalidCategoryIdError(CategoryServiceError):
    pass


class DuplicateCategoryError(CategoryServiceError):
    pass


# ============================================================
# VALIDAR ID
# ============================================================

def validate_object_id(value):
    try:
        return ObjectId(value)

    except (InvalidId, TypeError):
        raise InvalidCategoryIdError(
            "El identificador de la categoría no es válido."
        )


# ============================================================
# LISTAR CATEGORÍAS
# ============================================================

def get_all_categories():
    return category_repository.get_all()


# ============================================================
# OBTENER CATEGORÍA
# ============================================================

def get_category_by_id(category_id):
    oid = validate_object_id(category_id)

    category = category_repository.get_by_id(
        oid
    )

    if not category:
        raise CategoryNotFoundError(
            "Categoría no encontrada."
        )

    return category


# ============================================================
# CREAR CATEGORÍA
# ============================================================

def create_category(name, description=""):
    name = (name or "").strip()
    description = (description or "").strip()

    if not name:
        raise CategoryServiceError(
            "El nombre es obligatorio."
        )

    if len(name) < 2:
        raise CategoryServiceError(
            "El nombre de la categoría es demasiado corto."
        )

    if len(name) > 100:
        raise CategoryServiceError(
            "El nombre de la categoría es demasiado largo."
        )

    existing = category_repository.get_by_name(
        name
    )

    if existing:
        raise DuplicateCategoryError(
            "Ya existe una categoría con ese nombre."
        )

    now = datetime.now(
        timezone.utc
    )

    data = {
        "name": name,
        "description": description,
        "created_at": now,
        "updated_at": now
    }

    result = category_repository.create(
        data
    )

    data["_id"] = result.inserted_id

    return data


# ============================================================
# ELIMINAR CATEGORÍA
# ============================================================

def delete_category(category_id, root_path):
    category = get_category_by_id(
        category_id
    )

    documents = (
        category_repository
        .get_documents_by_category(
            category["_id"]
        )
    )

    removed_files = 0
    failed_files = []

    # --------------------------------------------------------
    # Eliminar archivos físicos
    # --------------------------------------------------------

    for document in documents:

        relative_path = document.get(
            "file_path",
            ""
        )

        if not relative_path:
            continue

        full_path = os.path.join(
            root_path,
            relative_path
        )

        if os.path.isfile(full_path):

            try:
                os.remove(full_path)
                removed_files += 1

            except OSError:
                failed_files.append(
                    full_path
                )

    # --------------------------------------------------------
    # Si algún archivo no pudo eliminarse, detenemos proceso
    # --------------------------------------------------------

    if failed_files:

        raise CategoryServiceError(
            "No fue posible eliminar uno o más archivos asociados "
            "a esta categoría."
        )

    # --------------------------------------------------------
    # Eliminar documentos de MongoDB
    # --------------------------------------------------------

    document_result = (
        category_repository
        .delete_documents_by_category(
            category["_id"]
        )
    )

    # --------------------------------------------------------
    # Eliminar categoría
    # --------------------------------------------------------

    category_result = (
        category_repository.delete(
            category["_id"]
        )
    )

    if category_result.deleted_count == 0:
        raise CategoryServiceError(
            "No fue posible eliminar la categoría."
        )

    return {
        "category": category,
        "documents_deleted": (
            document_result.deleted_count
        ),
        "files_deleted": removed_files
    }