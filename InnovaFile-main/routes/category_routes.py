from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app
)

from helpers.auth import login_required
from helpers.permissions import permission_required
from helpers.activity_helper import log_activity

from services.category_service import (
    get_all_categories,
    create_category,
    delete_category,
    CategoryServiceError,
    CategoryNotFoundError,
    InvalidCategoryIdError,
    DuplicateCategoryError
)


# ============================================================
# BLUEPRINT
# ============================================================

categories_bp = Blueprint(
    "categories",
    __name__,
    url_prefix="/categories"
)


# ============================================================
# LISTAR CATEGORÍAS
# ============================================================

@categories_bp.get("/")
@login_required
@permission_required("categories.view")
def index():

    try:

        categories = get_all_categories()

    except Exception as error:

        print(
            f"Error al obtener categorías: {error}"
        )

        categories = []

        flash(
            "No fue posible cargar las categorías.",
            "danger"
        )

    return render_template(
        "categories/index.html",
        categories=categories
    )


# ============================================================
# CREAR CATEGORÍA
# ============================================================

@categories_bp.route(
    "/create",
    methods=["GET", "POST"]
)
@login_required
@permission_required("categories.create")
def create():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        )

        description = request.form.get(
            "description",
            ""
        )

        try:

            category = create_category(
                name=name,
                description=description
            )

            log_activity(
                "Categoría creada",
                (
                    f"Se creó la categoría "
                    f"{category['name']}"
                )
            )

            flash(
                "Categoría creada correctamente.",
                "success"
            )

            return redirect(
                url_for(
                    "categories.index"
                )
            )

        except DuplicateCategoryError as error:

            flash(
                str(error),
                "danger"
            )

        except CategoryServiceError as error:

            flash(
                str(error),
                "danger"
            )

        except Exception as error:

            print(
                f"Error al crear categoría: {error}"
            )

            flash(
                "Ocurrió un error inesperado al crear la categoría.",
                "danger"
            )

    return render_template(
        "categories/create.html"
    )


# ============================================================
# ELIMINAR CATEGORÍA
# ============================================================

@categories_bp.post(
    "/<category_id>/delete"
)
@login_required
@permission_required("categories.delete")
def delete(category_id):

    try:

        result = delete_category(
            category_id,
            current_app.root_path
        )

        category = result[
            "category"
        ]

        log_activity(
            "Categoría eliminada",
            (
                f"Se eliminó la categoría "
                f"{category['name']} "
                f"junto con "
                f"{result['documents_deleted']} "
                f"documento(s)"
            )
        )

        flash(
            "Categoría eliminada correctamente.",
            "success"
        )

    except InvalidCategoryIdError:

        flash(
            "Categoría inválida.",
            "danger"
        )

    except CategoryNotFoundError:

        flash(
            "Categoría no encontrada.",
            "danger"
        )

    except CategoryServiceError as error:

        flash(
            str(error),
            "danger"
        )

    except Exception as error:

        print(
            f"Error al eliminar categoría: {error}"
        )

        flash(
            "Ocurrió un error al eliminar la categoría.",
            "danger"
        )

    return redirect(
        url_for(
            "categories.index"
        )
    )