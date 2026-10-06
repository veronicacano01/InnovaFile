from bson import ObjectId
from extensions import db


# ============================================================
# CATEGORÍAS
# ============================================================

def get_all():
    return list(
        db.categories.find().sort("name", 1)
    )


def get_by_id(category_id):
    if isinstance(category_id, str):
        category_id = ObjectId(category_id)

    return db.categories.find_one({
        "_id": category_id
    })


def get_by_name(name):
    return db.categories.find_one({
        "name": {
            "$regex": f"^{name}$",
            "$options": "i"
        }
    })


def create(category_data):
    return db.categories.insert_one(
        category_data
    )


def delete(category_id):
    if isinstance(category_id, str):
        category_id = ObjectId(category_id)

    return db.categories.delete_one({
        "_id": category_id
    })


# ============================================================
# DOCUMENTOS DE LA CATEGORÍA
# ============================================================

def get_documents_by_category(category_id):
    if isinstance(category_id, str):
        category_id = ObjectId(category_id)

    return list(
        db.documents.find({
            "category_id": category_id
        })
    )


def delete_documents_by_category(category_id):
    if isinstance(category_id, str):
        category_id = ObjectId(category_id)

    return db.documents.delete_many({
        "category_id": category_id
    })