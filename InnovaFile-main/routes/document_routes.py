import os
import tempfile

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    send_from_directory,
    session
)

from helpers.auth import login_required
from helpers.permissions import permission_required
from helpers.activity_helper import log_activity
from helpers.agent_auth import generate_agent_token, save_agent_token, get_agent_user

from services.document_service import (
    get_paginated_documents,
    get_enriched_document,
    get_document_by_id,
    get_categories,
    create_document,
    delete_document,
    search_documents,
    intelligent_search,
    classify_document,
    get_deleted_documents_paginated,
    move_document_to_trash,
    restore_document,
    permanently_delete_document,
    advanced_search_documents,
    get_advanced_search_options,
    DocumentServiceError,
    DocumentNotFoundError,
    InvalidDocumentIdError,
    InvalidCategoryError,
    InvalidFileError
)

from services.auto_import_service import auto_import_file

from services.document_version_service import (
    get_document_versions,
    DocumentVersionError
)


# ============================================================
# BLUEPRINT
# ============================================================

documents_bp = Blueprint(
    "documents",
    __name__,
    url_prefix="/documents"
)


# ============================================================
# LISTAR / BUSCAR DOCUMENTOS
# ============================================================

@documents_bp.get("/")
@login_required
@permission_required("documents.view")
def index():

    page = request.args.get(
        "page",
        1
    )

    per_page = request.args.get(
        "per_page",
        10
    )

    # --------------------------------------------------------
    # FILTROS
    # --------------------------------------------------------

    search_text = request.args.get(
        "search",
        ""
    ).strip()

    category_id = request.args.get(
        "category_id",
        ""
    ).strip()

    user_id = request.args.get(
        "user_id",
        ""
    ).strip()

    file_type = request.args.get(
        "file_type",
        ""
    ).strip()

    date_from = request.args.get(
        "date_from",
        ""
    ).strip()

    date_to = request.args.get(
        "date_to",
        ""
    ).strip()

    filters = {
        "search":
            search_text,

        "category_id":
            category_id,

        "user_id":
            user_id,

        "file_type":
            file_type,

        "date_from":
            date_from,

        "date_to":
            date_to
    }

    try:

        pagination = (
            advanced_search_documents(
                page=page,
                per_page=per_page,
                search_text=search_text,
                category_id=category_id,
                user_id=user_id,
                file_type=file_type,
                date_from=date_from,
                date_to=date_to
            )
        )

        options = (
            get_advanced_search_options()
        )

    except DocumentServiceError as error:

        flash(
            str(error),
            "danger"
        )

        pagination = {
            "documents": [],
            "page": 1,
            "per_page": 10,
            "total": 0,
            "total_pages": 1,
            "has_prev": False,
            "has_next": False,
            "prev_page": 1,
            "next_page": 1
        }

        options = {
            "categories": [],
            "users": [],
            "file_types": []
        }

    except Exception as error:

        current_app.logger.exception(
            "Error al cargar documentos: %s",
            error
        )

        pagination = {
            "documents": [],
            "page": 1,
            "per_page": 10,
            "total": 0,
            "total_pages": 1,
            "has_prev": False,
            "has_next": False,
            "prev_page": 1,
            "next_page": 1
        }

        options = {
            "categories": [],
            "users": [],
            "file_types": []
        }

        flash(
            "No fue posible cargar los documentos.",
            "danger"
        )

    return render_template(
        "documents/index.html",
        documents=pagination[
            "documents"
        ],
        pagination=pagination,
        categories=options[
            "categories"
        ],
        users=options[
            "users"
        ],
        file_types=options[
            "file_types"
        ],
        filters=filters
    )


# ============================================================
# IMPORTACIÓN AUTOMÁTICA DESDE CARPETA AUTORIZADA
# ============================================================
@documents_bp.post("/agent-token")
@login_required
@permission_required("documents.sync")
def create_agent_token():
    token = generate_agent_token()
    save_agent_token(session.get("user_id"), token)
    return {
        "ok": True,
        "token": token,
        "message": "Token creado. Guárdalo en el agente de escritorio; por seguridad no se volverá a mostrar."
    }


@documents_bp.post("/auto-import")
def auto_import():
    file=request.files.get("file")
    source_path=request.form.get("source_path","").strip()
    if not file or not file.filename:
        return {"ok":False,"message":"No se recibió ningún documento."},400

    # El agente de escritorio usa Bearer Token. El navegador puede seguir
    # usando la sesión normal.
    agent_user = get_agent_user()
    if agent_user:
        user_id = str(agent_user["_id"])
        allowed = True
        try:
            from helpers.permissions import has_permission_for_user
            allowed = has_permission_for_user(agent_user, "documents.sync")
        except ImportError:
            allowed = True
        if not allowed:
            return {"ok":False,"message":"Tu cuenta no tiene permiso para sincronizar documentos."},403
    elif session.get("user_id"):
        user_id = session.get("user_id")
        # Conservamos la protección normal de la sesión.
        from helpers.permissions import has_permission
        if not has_permission("documents.sync"):
            return {"ok":False,"message":"No tienes permiso para sincronizar documentos."},403
    else:
        return {"ok":False,"message":"Sesión o token de sincronización no válido."},401

    upload_dir=os.path.join(current_app.root_path,current_app.config["UPLOAD_FOLDER"])
    try:
        result=auto_import_file(file,source_path or file.filename,user_id,upload_dir)
        if result.get("status") in {"imported","updated"}:
            log_activity("Documento sincronizado",f"{result.get('name')} → {result.get('category')}")
        return {"ok":True,**result}
    except Exception as error:
        current_app.logger.exception("Error importando automáticamente: %s",error)
        return {"ok":False,"message":str(error)[:500]},500


# ============================================================
# CREAR DOCUMENTO
# ============================================================

@documents_bp.route(
    "/create",
    methods=["GET", "POST"]
)
@login_required
@permission_required("documents.create")
def create():

    try:

        categories = get_categories()

    except Exception as error:

        print(
            f"Error al obtener categorías: {error}"
        )

        categories = []

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        )

        description = request.form.get(
            "description",
            ""
        )

        category_id = request.form.get(
            "category_id",
            ""
        )

        file = request.files.get(
            "file"
        )

        upload_dir = os.path.join(
            current_app.root_path,
            current_app.config[
                "UPLOAD_FOLDER"
            ]
        )

        try:

            document = create_document(
                title=title,
                description=description,
                category_id=category_id,
                file=file,
                user_id=session.get(
                    "user_id"
                ),
                upload_dir=upload_dir
            )

            log_activity(
                "Documento subido",
                (
                    f"Se subió el documento "
                    f"{document['title']}"
                )
            )

            flash(
                "Documento subido correctamente.",
                "success"
            )

            return redirect(
                url_for(
                    "documents.index"
                )
            )

        except (
            InvalidFileError,
            InvalidCategoryError,
            DocumentServiceError
        ) as error:

            flash(
                str(error),
                "danger"
            )

        except Exception as error:

            print(
                f"Error al crear documento: {error}"
            )

            flash(
                "Ocurrió un error inesperado al subir el documento.",
                "danger"
            )

    return render_template(
        "documents/create.html",
        categories=categories
    )


# ============================================================
# ELIMINAR DOCUMENTO
# ============================================================

@documents_bp.post(
    "/<document_id>/delete"
)
@login_required
@permission_required(
    "documents.delete"
)
def delete(document_id):

    user_id = session.get(
        "user_id"
    )

    try:

        moved = move_document_to_trash(
            document_id=document_id,
            user_id=user_id
        )

        if moved:

            log_activity(
                "Documento enviado a papelera",
                "Se movió un documento a la papelera.",
                entity_type="document",
                entity_id=document_id
            )

            flash(
                "Documento enviado a la papelera.",
                "success"
            )

        else:

            flash(
                "No fue posible mover el documento.",
                "warning"
            )

    except DocumentServiceError as error:

        flash(
            str(error),
            "danger"
        )

    return redirect(
        url_for(
            "documents.index"
        )
    )


# ============================================================
# VER DOCUMENTO
# ============================================================

@documents_bp.get(
    "/<document_id>"
)
@login_required
@permission_required("documents.view")
def show(document_id):

    try:

        document = get_enriched_document(
            document_id
        )

        versions = get_document_versions(
            document_id
        )

        if not document.get(
            "version_number"
        ):

            document[
                "version_number"
            ] = 1

    except (
        InvalidDocumentIdError,
        DocumentNotFoundError
    ):

        flash(
            "Documento no encontrado.",
            "danger"
        )

        return redirect(
            url_for(
                "documents.index"
            )
        )

    except DocumentVersionError as error:

        current_app.logger.warning(
            "No fue posible cargar las versiones de %s: %s",
            document_id,
            error
        )

        versions = []

    except Exception as error:

        current_app.logger.exception(
            "Error al mostrar documento %s: %s",
            document_id,
            error
        )

        flash(
            "No fue posible cargar el documento.",
            "danger"
        )

        return redirect(
            url_for(
                "documents.index"
            )
        )

    return render_template(
        "documents/show.html",
        document=document,
        versions=versions
    )


# ============================================================
# DESCARGAR DOCUMENTO
# ============================================================

@documents_bp.get(
    "/<document_id>/download"
)
@login_required
@permission_required("documents.download")
def download(document_id):

    try:

        document = get_document_by_id(
            document_id
        )

    except (
        InvalidDocumentIdError,
        DocumentNotFoundError
    ):

        flash(
            "Documento no encontrado.",
            "danger"
        )

        return redirect(
            url_for(
                "documents.index"
            )
        )

    filename = os.path.basename(
        document.get(
            "file_path",
            ""
        )
    )

    directory = os.path.join(
        current_app.root_path,
        current_app.config[
            "UPLOAD_FOLDER"
        ]
    )

    full_path = os.path.join(
        directory,
        filename
    )

    if not os.path.isfile(
        full_path
    ):

        flash(
            "El archivo físico ya no existe.",
            "danger"
        )

        return redirect(
            url_for(
                "documents.index"
            )
        )

    log_activity(
        "Documento descargado",
        (
            f"Se descargó el documento "
            f"{document.get('title', 'Sin título')}"
        )
    )

    return send_from_directory(
        directory,
        filename,
        as_attachment=True,
        download_name=document.get(
            "file_name",
            filename
        )
    )


# ============================================================
# PANTALLA DE BÚSQUEDA
# ============================================================

@documents_bp.get(
    "/search"
)
@login_required
@permission_required("documents.view")
def search():

    return render_template(
        "documents/search.html"
    )


# ============================================================
# RESULTADOS DE BÚSQUEDA
# ============================================================

@documents_bp.get(
    "/results"
)
@login_required
@permission_required("documents.view")
def results():

    search_text = request.args.get(
        "search",
        ""
    ).strip()

    try:

        documents = search_documents(
            search_text
        )

    except Exception as error:

        print(
            f"Error de búsqueda: {error}"
        )

        documents = []

        flash(
            "No fue posible realizar la búsqueda.",
            "danger"
        )

    return render_template(
        "documents/results.html",
        documents=documents,
        search=search_text
    )


# ============================================================
# BÚSQUEDA INTELIGENTE
# ============================================================

@documents_bp.route(
    "/ai",
    methods=["GET", "POST"]
)
@login_required
@permission_required("documents.view")
def ai():

    if request.method == "POST":

        question = request.form.get(
            "question",
            ""
        ).strip()

        try:
            documents, response = intelligent_search(question)

            # Gemini es opcional: si la API está configurada, mejora la
            # respuesta usando solo documentos que la búsqueda ya devolvió.
            if current_app.config.get("GEMINI_ENABLED"):
                try:
                    from services.gemini_service import ask_gemini
                    response = ask_gemini(question, documents)
                except Exception as gemini_error:
                    current_app.logger.warning(
                        "Gemini no pudo responder; se conserva la búsqueda local: %s",
                        gemini_error,
                    )
                    response = (
                        f"{response}\n\nNota: Gemini no está disponible en este momento; "
                        "se muestran los resultados de la búsqueda local."
                    )

        except Exception as error:
            current_app.logger.exception("Error en búsqueda inteligente: %s", error)
            documents = []
            response = "No fue posible procesar la consulta. Intenta nuevamente."

        return render_template(
            "documents/ai.html",
            documents=documents,
            question=question,
            respuesta=response
        )

    return render_template(
        "documents/ai.html"
    )


# ============================================================
# CLASIFICACIÓN DE DOCUMENTOS
# ============================================================

@documents_bp.route(
    "/classification",
    methods=["GET", "POST"]
)
@login_required
@permission_required("documents.create")
def classification():

    if request.method == "POST":

        file = request.files.get(
            "file"
        )

        description = request.form.get(
            "description",
            ""
        )

        if not file or not file.filename:

            flash(
                "Selecciona un archivo.",
                "danger"
            )

            return render_template(
                "documents/classification.html"
            )

        try:
            result = classify_document(file.filename, description)
            # Si Gemini está configurado, se usa para proponer una categoría.
            # La pantalla deja claro que la sugerencia debe ser revisada.
            if current_app.config.get("GEMINI_ENABLED"):
                try:
                    from services.gemini_service import classify_with_gemini
                    extracted_text = ""
                    if current_app.config.get("GEMINI_SEND_DOCUMENT_CONTENT"):
                        # Solo extrae texto cuando el administrador lo autoriza en .env.
                        extension = os.path.splitext(file.filename)[1].lower()
                        if extension in {".pdf", ".docx", ".txt", ".csv", ".xlsx"}:
                            temp_path = None
                            try:
                                with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temp_file:
                                    temp_path = temp_file.name
                                file.save(temp_path)
                                from services.document_content_service import extract_text_from_file
                                extracted_text = extract_text_from_file(temp_path, extension.lstrip("."))[:12000]
                            finally:
                                if temp_path and os.path.exists(temp_path):
                                    os.remove(temp_path)
                                try:
                                    file.stream.seek(0)
                                except (AttributeError, OSError):
                                    pass
                    result = classify_with_gemini(file.filename, description, extracted_text)
                except Exception as gemini_error:
                    current_app.logger.warning(
                        "No se pudo usar Gemini para clasificar: %s", gemini_error
                    )
                    result["proveedor"] = "Reglas locales"
                    result["requiere_revision"] = True

        except Exception as error:

            print(
                f"Error al clasificar: {error}"
            )

            flash(
                "No fue posible clasificar el documento.",
                "danger"
            )

            return render_template(
                "documents/classification.html"
            )

        return render_template(
            "documents/classification.html",
            categoria=result[
                "categoria"
            ],
            confianza=result[
                "confianza"
            ],
            motivo=result[
                "motivo"
            ],
            palabras=result[
                "palabras"
            ]
        )

    return render_template(
        "documents/classification.html"
    )


# ============================================================
# PAPELERA
# ============================================================

@documents_bp.get(
    "/trash"
)
@login_required
@permission_required(
    "documents.delete"
)
def trash():

    page = request.args.get(
        "page",
        1
    )

    per_page = request.args.get(
        "per_page",
        10
    )

    pagination = (
        get_deleted_documents_paginated(
            page=page,
            per_page=per_page
        )
    )

    return render_template(
        "documents/trash.html",
        documents=pagination[
            "documents"
        ],
        pagination=pagination
    )


# ============================================================
# RESTAURAR
# ============================================================

@documents_bp.post(
    "/<document_id>/restore"
)
@login_required
@permission_required(
    "documents.delete"
)
def restore(document_id):

    try:

        restored = restore_document(
            document_id
        )

        if restored:

            log_activity(
                "Documento restaurado",
                "Se restauró un documento desde la papelera.",
                entity_type="document",
                entity_id=document_id
            )

            flash(
                "Documento restaurado correctamente.",
                "success"
            )

    except DocumentServiceError as error:

        flash(
            str(error),
            "danger"
        )

    return redirect(
        url_for(
            "documents.trash"
        )
    )


# ============================================================
# ELIMINAR DEFINITIVAMENTE
# ============================================================

@documents_bp.post(
    "/<document_id>/permanent-delete"
)
@login_required
@permission_required(
    "documents.delete"
)
def permanent_delete(document_id):

    try:

        deleted = (
            permanently_delete_document(
                document_id=document_id,
                root_path=current_app.root_path
            )
        )

        if deleted:

            log_activity(
                "Documento eliminado definitivamente",
                "Se eliminó permanentemente un documento.",
                entity_type="document",
                entity_id=document_id
            )

            flash(
                "Documento eliminado definitivamente.",
                "success"
            )

    except DocumentServiceError as error:

        flash(
            str(error),
            "danger"
        )

    return redirect(
        url_for(
            "documents.trash"
        )
    )