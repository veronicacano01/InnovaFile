import re

from bson import ObjectId
from pymongo import DESCENDING

from extensions import db


# ============================================================
# DOCUMENTOS ACTIVOS
# ============================================================

def get_all():

    return list(
        db.documents.find({
            "is_deleted": {
                "$ne": True
            }
        }).sort(
            "created_at",
            DESCENDING
        )
    )


# ============================================================
# DOCUMENTOS PAGINADOS
# ============================================================

def get_paginated(
    page=1,
    per_page=10
):

    page = max(
        int(page),
        1
    )

    per_page = max(
        int(per_page),
        1
    )

    skip = (
        page - 1
    ) * per_page

    query = {
        "is_deleted": {
            "$ne": True
        }
    }

    documents = list(
        db.documents
        .find(query)
        .sort(
            "created_at",
            DESCENDING
        )
        .skip(skip)
        .limit(per_page)
    )

    total = db.documents.count_documents(
        query
    )

    return {
        "documents": documents,
        "total": total,
        "page": page,
        "per_page": per_page
    }


# ============================================================
# PAPELERA
# ============================================================

def get_deleted_documents():

    return list(
        db.documents.find({
            "is_deleted": True
        }).sort(
            "deleted_at",
            DESCENDING
        )
    )


def get_deleted_paginated(
    page=1,
    per_page=10
):

    page = max(
        int(page),
        1
    )

    per_page = max(
        int(per_page),
        1
    )

    skip = (
        page - 1
    ) * per_page

    query = {
        "is_deleted": True
    }

    documents = list(
        db.documents
        .find(query)
        .sort(
            "deleted_at",
            DESCENDING
        )
        .skip(skip)
        .limit(per_page)
    )

    total = db.documents.count_documents(
        query
    )

    return {
        "documents": documents,
        "total": total,
        "page": page,
        "per_page": per_page
    }


# ============================================================
# OBTENER DOCUMENTO
# ============================================================

def get_by_id(
    document_id
):

    if isinstance(
        document_id,
        str
    ):
        document_id = ObjectId(
            document_id
        )

    return db.documents.find_one({
        "_id": document_id
    })


# ============================================================
# CREAR DOCUMENTO
# ============================================================

def create(
    document_data
):

    return db.documents.insert_one(
        document_data
    )


def get_by_source_path(source_path):
    if not source_path:
        return None
    return db.documents.find_one({"source_path": source_path, "is_deleted": {"$ne": True}})

def update_auto_import(document_id, data):
    return db.documents.update_one({"_id": document_id}, {"$set": data})


# ============================================================
# MOVER A PAPELERA
# ============================================================

def soft_delete(
    document_id,
    deleted_at,
    deleted_by
):

    if isinstance(
        document_id,
        str
    ):
        document_id = ObjectId(
            document_id
        )

    if isinstance(
        deleted_by,
        str
    ):
        deleted_by = ObjectId(
            deleted_by
        )

    return db.documents.update_one(
        {
            "_id": document_id
        },
        {
            "$set": {
                "is_deleted": True,
                "deleted_at": deleted_at,
                "deleted_by": deleted_by
            }
        }
    )


# ============================================================
# RESTAURAR
# ============================================================

def restore(
    document_id
):

    if isinstance(
        document_id,
        str
    ):
        document_id = ObjectId(
            document_id
        )

    return db.documents.update_one(
        {
            "_id": document_id
        },
        {
            "$set": {
                "is_deleted": False,
                "deleted_at": None,
                "deleted_by": None
            }
        }
    )


# ============================================================
# ELIMINAR DEFINITIVAMENTE
# ============================================================

def permanent_delete(
    document_id
):

    if isinstance(
        document_id,
        str
    ):
        document_id = ObjectId(
            document_id
        )

    return db.documents.delete_one({
        "_id": document_id
    })


# ============================================================
# BÚSQUEDA DE TEXTO
# ============================================================

def search_text(
    search_value
):

    search_value = (
        search_value or ""
    ).strip()

    if not search_value:
        return get_all()

    query = {
        "$and": [
            {
                "is_deleted": {
                    "$ne": True
                }
            },
            {
                "$text": {
                    "$search": search_value
                }
            }
        ]
    }

    projection = {
        "score": {
            "$meta": "textScore"
        }
    }

    return list(
        db.documents.find(
            query,
            projection
        ).sort([
            (
                "score",
                {
                    "$meta": "textScore"
                }
            ),
            (
                "created_at",
                DESCENDING
            )
        ])
    )


# ============================================================
# BÚSQUEDA PARCIAL
# ============================================================

def search_regex(
    search_value
):

    search_value = (
        search_value or ""
    ).strip()

    if not search_value:
        return get_all()

    safe_text = re.escape(
        search_value
    )

    pattern = {
        "$regex": safe_text,
        "$options": "i"
    }

    query = {
        "is_deleted": {
            "$ne": True
        },
        "$or": [
            {
                "title": pattern
            },
            {
                "description": pattern
            },
            {
                "file_name": pattern
            }
        ]
    }

    return list(
        db.documents.find(
            query
        ).sort(
            "created_at",
            DESCENDING
        )
    )


# ============================================================
# BÚSQUEDA GENERAL
# ============================================================

def search(
    search_value
):

    search_value = (
        search_value or ""
    ).strip()

    if not search_value:
        return get_all()

    try:

        results = search_text(
            search_value
        )

        if results:
            return results

    except Exception as error:

        print(
            f"Error en búsqueda de texto: {error}"
        )

    return search_regex(
        search_value
    )


# ============================================================
# CATEGORÍAS
# ============================================================

def get_categories():

    return list(
        db.categories.find().sort(
            "name",
            1
        )
    )


def get_category_by_id(
    category_id
):

    if not category_id:
        return None

    if isinstance(
        category_id,
        str
    ):
        category_id = ObjectId(
            category_id
        )

    return db.categories.find_one({
        "_id": category_id
    })


# ============================================================
# USUARIOS
# ============================================================

def get_user_by_id(
    user_id
):

    if not user_id:
        return None

    if isinstance(
        user_id,
        str
    ):
        user_id = ObjectId(
            user_id
        )

    return db.users.find_one({
        "_id": user_id
    })
    
# ============================================================
# OPCIONES PARA BÚSQUEDA AVANZADA
# ============================================================

def get_users():

    return list(
        db.users.find().sort(
            "name",
            1
        )
    )


def get_file_types():

    return sorted(
        [
            file_type
            for file_type in db.documents.distinct(
                "file_type",
                {
                    "is_deleted": {
                        "$ne": True
                    }
                }
            )
            if file_type
        ]
    )


# ============================================================
# BÚSQUEDA AVANZADA PAGINADA
# ============================================================

def advanced_search_paginated(
    page=1,
    per_page=10,
    search_text="",
    category_id=None,
    user_id=None,
    file_type="",
    date_from=None,
    date_to=None
):

    page = max(
        int(page),
        1
    )

    per_page = max(
        int(per_page),
        1
    )

    skip = (
        page - 1
    ) * per_page

    conditions = [
        {
            "is_deleted": {
                "$ne": True
            }
        }
    ]

    # --------------------------------------------------------
    # TEXTO
    # --------------------------------------------------------

    search_text = (
        search_text or ""
    ).strip()

    if search_text:

        safe_text = re.escape(
            search_text
        )

        regex = {
            "$regex": safe_text,
            "$options": "i"
        }

        conditions.append({
            "$or": [
                {
                    "title": regex
                },
                {
                    "description": regex
                },
                {
                    "file_name": regex
                }
            ]
        })

    # --------------------------------------------------------
    # CATEGORÍA
    # --------------------------------------------------------

    if category_id:

        conditions.append({
            "category_id": category_id
        })

    # --------------------------------------------------------
    # USUARIO
    # --------------------------------------------------------

    if user_id:

        conditions.append({
            "user_id": user_id
        })

    # --------------------------------------------------------
    # TIPO DE ARCHIVO
    # --------------------------------------------------------

    file_type = (
        file_type or ""
    ).strip().lower()

    if file_type:

        conditions.append({
            "file_type": file_type
        })

    # --------------------------------------------------------
    # FECHAS
    # --------------------------------------------------------

    date_filter = {}

    if date_from:

        date_filter[
            "$gte"
        ] = date_from

    if date_to:

        date_filter[
            "$lt"
        ] = date_to

    if date_filter:

        conditions.append({
            "created_at": date_filter
        })

    # --------------------------------------------------------
    # CONSULTA FINAL
    # --------------------------------------------------------

    if len(
        conditions
    ) == 1:

        query = conditions[
            0
        ]

    else:

        query = {
            "$and": conditions
        }

    documents = list(
        db.documents
        .find(query)
        .sort(
            "created_at",
            DESCENDING
        )
        .skip(skip)
        .limit(per_page)
    )

    total = db.documents.count_documents(
        query
    )

    return {
        "documents": documents,
        "total": total,
        "page": page,
        "per_page": per_page
    }