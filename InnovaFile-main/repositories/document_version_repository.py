from bson import ObjectId

from extensions import db


# ============================================================
# COLECCIÓN
# ============================================================

def collection():
    return db.document_versions


# ============================================================
# OBTENER VERSIONES DE UN DOCUMENTO
# ============================================================

def get_versions_by_document(document_id):

    if isinstance(document_id, str):
        document_id = ObjectId(document_id)

    return list(
        collection()
        .find({
            "document_id": document_id
        })
        .sort(
            "version_number",
            -1
        )
    )


# ============================================================
# OBTENER VERSIÓN POR ID
# ============================================================

def get_version_by_id(version_id):

    if isinstance(version_id, str):
        version_id = ObjectId(version_id)

    return collection().find_one({
        "_id": version_id
    })


# ============================================================
# CREAR VERSIÓN
# ============================================================

def create_version(data):

    result = collection().insert_one(
        data
    )

    return collection().find_one({
        "_id": result.inserted_id
    })


# ============================================================
# OBTENER ÚLTIMO NÚMERO DE VERSIÓN
# ============================================================

def get_last_version_number(document_id):

    if isinstance(document_id, str):
        document_id = ObjectId(document_id)

    version = list(
        collection()
        .find({
            "document_id": document_id
        })
        .sort(
            "version_number",
            -1
        )
        .limit(1)
    )

    if not version:
        return 0

    return version[0].get(
        "version_number",
        0
    )


# ============================================================
# ACTUALIZAR DOCUMENTO PRINCIPAL
# ============================================================

def update_current_document(
    document_id,
    data
):

    if isinstance(document_id, str):
        document_id = ObjectId(document_id)

    return db.documents.update_one(
        {
            "_id": document_id
        },
        {
            "$set": data
        }
    )


# ============================================================
# OBTENER DOCUMENTO
# ============================================================

def get_document(document_id):

    if isinstance(document_id, str):
        document_id = ObjectId(document_id)

    return db.documents.find_one({
        "_id": document_id
    })


# ============================================================
# OBTENER USUARIO
# ============================================================

def get_user(user_id):

    if not user_id:
        return None

    if isinstance(user_id, str):
        user_id = ObjectId(user_id)

    return db.users.find_one({
        "_id": user_id
    })