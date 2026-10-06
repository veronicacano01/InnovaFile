from pymongo import ASCENDING, DESCENDING, TEXT
from pymongo.errors import OperationFailure

from app import create_app
from extensions import db


# ============================================================
# CREAR ÍNDICE DE FORMA SEGURA
# ============================================================

def safe_create_index(collection, keys, **kwargs):
    """
    Intenta crear un índice.
    Si ya existe uno equivalente con otro nombre,
    no detiene la ejecución.
    """

    try:
        index_name = collection.create_index(
            keys,
            **kwargs
        )

        print(
            f"  ✓ {collection.name}: {index_name}"
        )

    except OperationFailure as error:

        # Código 85 = IndexOptionsConflict
        if error.code == 85:

            print(
                f"  ↳ {collection.name}: "
                "ya existe un índice equivalente."
            )

        else:
            raise


# ============================================================
# CREAR ÍNDICES
# ============================================================

def create_indexes():

    app = create_app()

    with app.app_context():

        print("\n====================================")
        print(" CREACIÓN DE ÍNDICES - INNOVAFILE")
        print("====================================\n")

        # ====================================================
        # USUARIOS
        # ====================================================

        print("Usuarios:")

        safe_create_index(
            db.users,
            [("email", ASCENDING)],
            unique=True,
            name="idx_users_email_unique"
        )

        safe_create_index(
            db.users,
            [("name", ASCENDING)],
            name="idx_users_name"
        )

        safe_create_index(
            db.users,
            [("role_id", ASCENDING)],
            name="idx_users_role"
        )

        safe_create_index(
            db.users,
            [("created_at", DESCENDING)],
            name="idx_users_created_at"
        )

        # ====================================================
        # ROLES
        # ====================================================

        print("\nRoles:")

        safe_create_index(
            db.roles,
            [("name", ASCENDING)],
            unique=True,
            name="idx_roles_name_unique"
        )

        # ====================================================
        # CATEGORÍAS
        # ====================================================

        print("\nCategorías:")

        safe_create_index(
            db.categories,
            [("name", ASCENDING)],
            unique=True,
            name="idx_categories_name_unique"
        )

        safe_create_index(
            db.categories,
            [("created_at", DESCENDING)],
            name="idx_categories_created_at"
        )

        # ====================================================
        # DOCUMENTOS
        # ====================================================

        print("\nDocumentos:")

        safe_create_index(
            db.documents,
            [("category_id", ASCENDING)],
            name="idx_documents_category"
        )

        safe_create_index(
            db.documents,
            [("user_id", ASCENDING)],
            name="idx_documents_user"
        )

        safe_create_index(
            db.documents,
            [("created_at", DESCENDING)],
            name="idx_documents_created_at"
        )

        safe_create_index(
            db.documents,
            [("file_type", ASCENDING)],
            name="idx_documents_file_type"
        )

        safe_create_index(
            db.documents,
            [
                ("category_id", ASCENDING),
                ("created_at", DESCENDING)
            ],
            name="idx_documents_category_date"
        )

        safe_create_index(
            db.documents,
            [
                ("user_id", ASCENDING),
                ("created_at", DESCENDING)
            ],
            name="idx_documents_user_date"
        )

        safe_create_index(
            db.documents,
            [
                ("title", TEXT),
                ("description", TEXT),
                ("file_name", TEXT)
            ],
            name="idx_documents_text_search"
        )

        # ====================================================
        # ACTIVIDAD
        # ====================================================

        print("\nActividad:")

        safe_create_index(
            db.activity_logs,
            [("user_id", ASCENDING)],
            name="idx_activity_user"
        )

        safe_create_index(
            db.activity_logs,
            [("created_at", DESCENDING)],
            name="idx_activity_created_at"
        )

        safe_create_index(
            db.activity_logs,
            [
                ("user_id", ASCENDING),
                ("created_at", DESCENDING)
            ],
            name="idx_activity_user_date"
        )

        safe_create_index(
            db.activity_logs,
            [("action", ASCENDING)],
            name="idx_activity_action"
        )

        print("\n====================================")
        print(" ÍNDICES VERIFICADOS CORRECTAMENTE")
        print("====================================\n")


# ============================================================
# EJECUTAR
# ============================================================

if __name__ == "__main__":
    create_indexes()