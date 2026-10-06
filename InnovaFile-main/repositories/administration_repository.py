from extensions import db


# ============================================================
# CONTADORES
# ============================================================

def count_users():
    return db.users.count_documents({})


def count_documents():
    return db.documents.count_documents({})


def count_categories():
    return db.categories.count_documents({})


def count_activities():
    return db.activity_logs.count_documents({})


# ============================================================
# ESTADO DE MONGODB
# ============================================================

def ping_database():

    try:

        db.command(
            "ping"
        )

        return True

    except Exception:

        return False