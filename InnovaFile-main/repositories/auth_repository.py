from bson import ObjectId

from extensions import db


# ============================================================
# USUARIOS
# ============================================================

def get_user_by_email(email):
    return db.users.find_one({
        "email": email
    })


def get_user_by_id(user_id):

    if isinstance(user_id, str):
        user_id = ObjectId(user_id)

    return db.users.find_one({
        "_id": user_id
    })


def create_user(user_data):
    return db.users.insert_one(
        user_data
    )


def update_login_security(
    user_id,
    failed_login_attempts=None,
    locked_until=None,
    last_login_at=None,
    updated_at=None
):

    if isinstance(user_id, str):
        user_id = ObjectId(user_id)

    update_data = {}

    if failed_login_attempts is not None:
        update_data[
            "failed_login_attempts"
        ] = failed_login_attempts

    # locked_until sí puede ser None
    update_data[
        "locked_until"
    ] = locked_until

    if last_login_at is not None:
        update_data[
            "last_login_at"
        ] = last_login_at

    if updated_at is not None:
        update_data[
            "updated_at"
        ] = updated_at

    return db.users.update_one(
        {
            "_id": user_id
        },
        {
            "$set": update_data
        }
    )


# ============================================================
# ROLES
# ============================================================

def get_role_by_name(name):
    return db.roles.find_one({
        "name": name
    })

def get_role_by_id(role_id):
    if not role_id:
        return None
    if isinstance(role_id, str):
        role_id = ObjectId(role_id)
    return db.roles.find_one({"_id": role_id})


def get_all_roles():
    return list(db.roles.find().sort("name", 1))