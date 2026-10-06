import os
import uuid
import math

from datetime import (
    datetime,
    timezone,
    timedelta
)

from bson import ObjectId
from bson.errors import InvalidId

from werkzeug.utils import secure_filename

from repositories import document_repository


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

class DocumentServiceError(Exception):
    pass


class DocumentNotFoundError(
    DocumentServiceError
):
    pass


class InvalidDocumentIdError(
    DocumentServiceError
):
    pass


class InvalidCategoryError(
    DocumentServiceError
):
    pass


class InvalidFileError(
    DocumentServiceError
):
    pass


# ============================================================
# VALIDAR OBJECT ID
# ============================================================

def validate_object_id(
    value,
    message="Identificador inválido."
):

    try:
        return ObjectId(
            str(value)
        )

    except (
        InvalidId,
        TypeError,
        ValueError
    ):

        raise InvalidDocumentIdError(
            message
        )


# ============================================================
# VALIDAR EXTENSIÓN
# ============================================================

def validate_extension(filename):

    if not filename:
        raise InvalidFileError(
            "Debes seleccionar un archivo."
        )

    if "." not in filename:
        raise InvalidFileError(
            "El archivo no tiene una extensión válida."
        )

    extension = (
        filename.rsplit(
            ".",
            1
        )[1]
        .lower()
        .strip()
    )

    if extension not in ALLOWED_EXTENSIONS:

        raise InvalidFileError(
            (
                f"El tipo de archivo .{extension} "
                "no está permitido."
            )
        )

    return extension


# ============================================================
# ENRIQUECER DOCUMENTO
# ============================================================

def enrich_document(document):

    if not document:
        return None

    data = dict(document)

    # --------------------------------------------------------
    # CATEGORÍA
    # --------------------------------------------------------

    category = None

    category_id = data.get(
        "category_id"
    )

    if category_id:

        try:

            category = (
                document_repository
                .get_category_by_id(
                    category_id
                )
            )

        except Exception:
            category = None

    data["category"] = (
        category or {
            "name": "Sin categoría"
        }
    )

    # --------------------------------------------------------
    # USUARIO
    # --------------------------------------------------------

    user = None

    user_id = data.get(
        "user_id"
    )

    if user_id:

        try:

            user = (
                document_repository
                .get_user_by_id(
                    user_id
                )
            )

        except Exception:
            user = None

    data["user"] = (
        user or {
            "name": "Usuario desconocido"
        }
    )

    return data


# ============================================================
# OBTENER TODOS LOS DOCUMENTOS
# ============================================================

def get_all_documents():

    documents = (
        document_repository
        .get_all()
    )

    return [
        enrich_document(
            document
        )
        for document in documents
    ]


# ============================================================
# OBTENER DOCUMENTO
# ============================================================

def get_document_by_id(
    document_id
):

    document_oid = validate_object_id(
        document_id,
        "El identificador del documento no es válido."
    )

    document = (
        document_repository
        .get_by_id(
            document_oid
        )
    )

    if not document:

        raise DocumentNotFoundError(
            "Documento no encontrado."
        )

    return document


# ============================================================
# OBTENER DOCUMENTO ENRIQUECIDO
# ============================================================

def get_enriched_document(
    document_id
):

    document = get_document_by_id(
        document_id
    )

    return enrich_document(
        document
    )


# ============================================================
# OBTENER CATEGORÍAS
# ============================================================

def get_categories():

    return (
        document_repository
        .get_categories()
    )


# ============================================================
# CREAR DOCUMENTO
# ============================================================

def create_document(
    title,
    description,
    category_id,
    file,
    user_id,
    upload_dir
    
):

    # --------------------------------------------------------
    # VALIDAR TÍTULO
    # --------------------------------------------------------

    title = (
        title or ""
    ).strip()

    if not title:

        raise DocumentServiceError(
            "El título del documento es obligatorio."
        )

    if len(title) < 2:

        raise DocumentServiceError(
            "El título debe contener al menos 2 caracteres."
        )

    if len(title) > 200:

        raise DocumentServiceError(
            "El título no puede superar los 200 caracteres."
        )

    # --------------------------------------------------------
    # DESCRIPCIÓN
    # --------------------------------------------------------

    description = (
        description or ""
    ).strip()

    if len(description) > 2000:

        raise DocumentServiceError(
            "La descripción no puede superar los 2000 caracteres."
        )

    # --------------------------------------------------------
    # VALIDAR CATEGORÍA
    # --------------------------------------------------------

    try:

        category_oid = ObjectId(
            str(category_id)
        )

    except Exception:

        raise InvalidCategoryError(
            "La categoría seleccionada no es válida."
        )

    category = (
        document_repository
        .get_category_by_id(
            category_oid
        )
    )

    if not category:

        raise InvalidCategoryError(
            "La categoría seleccionada no existe."
        )

    # --------------------------------------------------------
    # VALIDAR USUARIO
    # --------------------------------------------------------

    try:

        user_oid = ObjectId(
            str(user_id)
        )

    except Exception:

        raise DocumentServiceError(
            "El usuario que intenta subir el documento no es válido."
        )

    user = (
        document_repository
        .get_user_by_id(
            user_oid
        )
    )

    if not user:

        raise DocumentServiceError(
            "El usuario no existe."
        )

    # --------------------------------------------------------
    # VALIDAR ARCHIVO
    # --------------------------------------------------------

    if not file or not file.filename:

        raise InvalidFileError(
            "Debes seleccionar un archivo."
        )

    original_filename = secure_filename(
        file.filename
    )

    if not original_filename:

        raise InvalidFileError(
            "El nombre del archivo no es válido."
        )

    extension = validate_extension(
        original_filename
    )

    # --------------------------------------------------------
    # GENERAR NOMBRE ÚNICO
    # --------------------------------------------------------

    stored_filename = (
        f"{uuid.uuid4().hex}.{extension}"
    )

    os.makedirs(
        upload_dir,
        exist_ok=True
    )

    full_path = os.path.join(
        upload_dir,
        stored_filename
    )

    # --------------------------------------------------------
    # GUARDAR ARCHIVO
    # --------------------------------------------------------

    try:

        file.save(
            full_path
        )

    except Exception as error:

        raise InvalidFileError(
            f"No fue posible guardar el archivo: {error}"
        )

    # --------------------------------------------------------
    # VERIFICAR ARCHIVO
    # --------------------------------------------------------

    if not os.path.isfile(
        full_path
    ):

        raise InvalidFileError(
            "El archivo no pudo guardarse correctamente."
        )

    file_size = os.path.getsize(
        full_path
    )

    if file_size <= 0:

        try:
            os.remove(
                full_path
            )
        except Exception:
            pass

        raise InvalidFileError(
            "El archivo está vacío."
        )

    # --------------------------------------------------------
    # DATOS DEL DOCUMENTO
    # --------------------------------------------------------

    now = datetime.now(
        timezone.utc
    )

    document_data = {

        "title": title,

        "description": description,

        "category_id": category_oid,

        "user_id": user_oid,

        "file_name": original_filename,

        "stored_filename": stored_filename,
        
        "is_deleted": False,
        
        "deleted_at": None,
        
        "deleted_by": None,

        "file_path": os.path.join(
            "uploads",
            stored_filename
        ).replace(
            "\\",
            "/"
        ),

        "file_type": extension,

        "file_size": file_size,

        "created_at": now,

        "updated_at": now
    }

    # --------------------------------------------------------
    # GUARDAR EN MONGODB
    # --------------------------------------------------------

    try:

        result = (
            document_repository
            .create(
                document_data
            )
        )

    except Exception as error:

        # Si MongoDB falla, eliminamos
        # el archivo físico para evitar
        # archivos huérfanos.

        try:

            if os.path.isfile(
                full_path
            ):
                os.remove(
                    full_path
                )

        except Exception:
            pass

        raise DocumentServiceError(
            (
                "No fue posible registrar "
                f"el documento: {error}"
            )
        )

    document_data["_id"] = (
        result.inserted_id
    )

    return document_data


# ============================================================
# ELIMINAR DOCUMENTO
# ============================================================

def delete_document(
    document_id,
    root_path
):

    document = get_document_by_id(
        document_id
    )

    file_path = document.get(
        "file_path"
    )

    # --------------------------------------------------------
    # ELIMINAR ARCHIVO FÍSICO
    # --------------------------------------------------------

    if file_path:

        full_path = os.path.join(
            root_path,
            file_path
        )

        if os.path.isfile(
            full_path
        ):

            try:

                os.remove(
                    full_path
                )

            except Exception as error:

                raise DocumentServiceError(
                    (
                        "No fue posible eliminar "
                        f"el archivo físico: {error}"
                    )
                )

    # --------------------------------------------------------
    # ELIMINAR REGISTRO
    # --------------------------------------------------------

    result = (
        document_repository
        .delete(
            document["_id"]
        )
    )

    if result.deleted_count == 0:

        raise DocumentServiceError(
            "No fue posible eliminar el documento."
        )

    return document


# ============================================================
# BUSCAR DOCUMENTOS
# ============================================================

def search_documents(
    search_text
):

    search_text = (
        search_text or ""
    ).strip()

    if not search_text:

        return get_all_documents()

    documents = (
        document_repository
        .search(
            search_text
        )
    )

    return [
        enrich_document(
            document
        )
        for document in documents
    ]


# ============================================================
# BÚSQUEDA INTELIGENTE
# ============================================================

def intelligent_search(
    question
):

    question = (
        question or ""
    ).strip()

    if not question:

        return (
            [],
            "Escribe una palabra o pregunta para realizar la búsqueda."
        )

    documents = search_documents(
        question
    )

    if documents:

        total = len(
            documents
        )

        response = (
            f"Encontré {total} documento"
        )

        if total != 1:
            response += "s"

        response += (
            " relacionado"
        )

        if total != 1:
            response += "s"

        response += (
            " con tu búsqueda."
        )

    else:

        response = (
            "No encontré documentos relacionados con tu búsqueda."
        )

    return (
        documents,
        response
    )

# ============================================================
# OBTENER DOCUMENTOS PAGINADOS
# ============================================================

def get_paginated_documents(
    page=1,
    per_page=10
):

    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1

    try:
        per_page = int(per_page)
    except (TypeError, ValueError):
        per_page = 10

    if page < 1:
        page = 1

    if per_page < 1:
        per_page = 10

    if per_page > 100:
        per_page = 100

    result = (
        document_repository
        .get_paginated(
            page=page,
            per_page=per_page
        )
    )

    documents = [
        enrich_document(
            document
        )
        for document in result[
            "documents"
        ]
    ]

    total = result[
        "total"
    ]

    total_pages = max(
        math.ceil(
            total / per_page
        ),
        1
    )

    return {
        "documents": documents,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "prev_page": page - 1,
        "next_page": page + 1
    }

# ============================================================
# CLASIFICACIÓN AUTOMÁTICA
# ============================================================

def classify_document(
    filename,
    description=""
):

    filename = (
        filename or ""
    ).lower()

    description = (
        description or ""
    ).lower()

    text = (
        f"{filename} {description}"
    )

    rules = [
        {
            "keywords": [
                "contrato"
            ],
            "category": "Contratos",
            "confidence": 98
        },
        {
            "keywords": [
                "factura"
            ],
            "category": "Facturas",
            "confidence": 97
        },
        {
            "keywords": [
                "reporte"
            ],
            "category": "Reportes",
            "confidence": 95
        },
        {
            "keywords": [
                "manual"
            ],
            "category": "Manuales",
            "confidence": 94
        },
        {
            "keywords": [
                "cv",
                "curriculum",
                "currículum"
            ],
            "category": "Currículums",
            "confidence": 96
        }
    ]

    for rule in rules:

        detected_words = [
            word
            for word in rule[
                "keywords"
            ]
            if word in text
        ]

        if detected_words:

            return {
                "categoria": (
                    rule[
                        "category"
                    ]
                ),
                "confianza": (
                    rule[
                        "confidence"
                    ]
                ),
                "motivo": (
                    "Se detectaron palabras "
                    "relacionadas con esta categoría."
                ),
                "palabras": detected_words
            }

    return {
        "categoria": (
            "Sin clasificación"
        ),
        "confianza": 50,
        "motivo": (
            "No se encontraron palabras "
            "suficientes para determinar "
            "una categoría automáticamente."
        ),
        "palabras": []
    }
    
import math

from datetime import (
    datetime,
    timezone
)

# ============================================================
# OPCIONES DE BÚSQUEDA AVANZADA
# ============================================================

def get_advanced_search_options():

    categories = (
        document_repository
        .get_categories()
    )

    users = (
        document_repository
        .get_users()
    )

    file_types = (
        document_repository
        .get_file_types()
    )

    return {
        "categories": categories,
        "users": users,
        "file_types": file_types
    }


# ============================================================
# BÚSQUEDA AVANZADA
# ============================================================

def advanced_search_documents(
    page=1,
    per_page=10,
    search_text="",
    category_id="",
    user_id="",
    file_type="",
    date_from="",
    date_to=""
):

    # --------------------------------------------------------
    # PAGINACIÓN
    # --------------------------------------------------------

    try:

        page = int(
            page
        )

    except (
        TypeError,
        ValueError
    ):

        page = 1

    try:

        per_page = int(
            per_page
        )

    except (
        TypeError,
        ValueError
    ):

        per_page = 10

    if page < 1:
        page = 1

    if per_page < 1:
        per_page = 10

    if per_page > 100:
        per_page = 100

    # --------------------------------------------------------
    # TEXTO
    # --------------------------------------------------------

    search_text = (
        search_text or ""
    ).strip()

    # --------------------------------------------------------
    # CATEGORÍA
    # --------------------------------------------------------

    category_oid = None

    category_id = (
        category_id or ""
    ).strip()

    if category_id:

        try:

            category_oid = ObjectId(
                category_id
            )

        except Exception:

            raise DocumentServiceError(
                "La categoría seleccionada no es válida."
            )

    # --------------------------------------------------------
    # USUARIO
    # --------------------------------------------------------

    user_oid = None

    user_id = (
        user_id or ""
    ).strip()

    if user_id:

        try:

            user_oid = ObjectId(
                user_id
            )

        except Exception:

            raise DocumentServiceError(
                "El usuario seleccionado no es válido."
            )

    # --------------------------------------------------------
    # TIPO
    # --------------------------------------------------------

    file_type = (
        file_type or ""
    ).strip().lower()

    # --------------------------------------------------------
    # FECHA DESDE
    # --------------------------------------------------------

    start_date = None

    date_from = (
        date_from or ""
    ).strip()

    if date_from:

        try:

            start_date = datetime.strptime(
                date_from,
                "%Y-%m-%d"
            ).replace(
                tzinfo=timezone.utc
            )

        except ValueError:

            raise DocumentServiceError(
                "La fecha inicial no es válida."
            )

    # --------------------------------------------------------
    # FECHA HASTA
    # --------------------------------------------------------

    end_date = None

    date_to = (
        date_to or ""
    ).strip()

    if date_to:

        try:

            end_date = (
                datetime.strptime(
                    date_to,
                    "%Y-%m-%d"
                ).replace(
                    tzinfo=timezone.utc
                )
                +
                timedelta(
                    days=1
                )
            )

        except ValueError:

            raise DocumentServiceError(
                "La fecha final no es válida."
            )

    # --------------------------------------------------------
    # VALIDAR RANGO
    # --------------------------------------------------------

    if (
        start_date
        and
        end_date
        and
        start_date >= end_date
    ):

        raise DocumentServiceError(
            "La fecha inicial no puede ser mayor que la fecha final."
        )

    # --------------------------------------------------------
    # REPOSITORY
    # --------------------------------------------------------

    result = (
        document_repository
        .advanced_search_paginated(
            page=page,
            per_page=per_page,
            search_text=search_text,
            category_id=category_oid,
            user_id=user_oid,
            file_type=file_type,
            date_from=start_date,
            date_to=end_date
        )
    )

    documents = [
        enrich_document(
            document
        )
        for document in result[
            "documents"
        ]
    ]

    total = result[
        "total"
    ]

    total_pages = max(
        math.ceil(
            total / per_page
        ),
        1
    )

    return {

        "documents":
            documents,

        "page":
            page,

        "per_page":
            per_page,

        "total":
            total,

        "total_pages":
            total_pages,

        "has_prev":
            page > 1,

        "has_next":
            page < total_pages,

        "prev_page":
            max(
                page - 1,
                1
            ),

        "next_page":
            min(
                page + 1,
                total_pages
            )
    }


# ============================================================
# PAPELERA PAGINADA
# ============================================================

def get_deleted_documents_paginated(
    page=1,
    per_page=10
):

    try:
        page = int(page)
    except (
        TypeError,
        ValueError
    ):
        page = 1

    try:
        per_page = int(
            per_page
        )
    except (
        TypeError,
        ValueError
    ):
        per_page = 10

    if page < 1:
        page = 1

    if per_page < 1:
        per_page = 10

    if per_page > 100:
        per_page = 100

    result = (
        document_repository
        .get_deleted_paginated(
            page=page,
            per_page=per_page
        )
    )

    documents = [
        enrich_document(
            document
        )
        for document in result[
            "documents"
        ]
    ]

    total = result[
        "total"
    ]

    total_pages = max(
        math.ceil(
            total / per_page
        ),
        1
    )

    return {
        "documents": documents,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "prev_page": max(
            page - 1,
            1
        ),
        "next_page": min(
            page + 1,
            total_pages
        )
    }


# ============================================================
# MOVER DOCUMENTO A PAPELERA
# ============================================================

def move_document_to_trash(
    document_id,
    user_id
):

    document = get_document_by_id(
        document_id
    )

    if not document:

        raise DocumentNotFoundError(
            "Documento no encontrado."
        )

    if document.get(
        "is_deleted"
    ):

        raise DocumentServiceError(
            "El documento ya se encuentra en la papelera."
        )

    result = (
        document_repository
        .soft_delete(
            document_id=document[
                "_id"
            ],
            deleted_at=datetime.now(
                timezone.utc
            ),
            deleted_by=user_id
        )
    )

    return (
        result.modified_count > 0
    )


# ============================================================
# RESTAURAR DOCUMENTO
# ============================================================

def restore_document(
    document_id
):

    document = get_document_by_id(
        document_id
    )

    if not document:

        raise DocumentNotFoundError(
            "Documento no encontrado."
        )

    if not document.get(
        "is_deleted"
    ):

        raise DocumentServiceError(
            "El documento no está en la papelera."
        )

    result = (
        document_repository
        .restore(
            document["_id"]
        )
    )

    return (
        result.modified_count > 0
    )


# ============================================================
# ELIMINAR DOCUMENTO DEFINITIVAMENTE
# ============================================================

def permanently_delete_document(
    document_id,
    root_path
):

    document = get_document_by_id(
        document_id
    )

    if not document:

        raise DocumentNotFoundError(
            "Documento no encontrado."
        )

    if not document.get(
        "is_deleted"
    ):

        raise DocumentServiceError(
            "Primero debes enviar el documento a la papelera."
        )

    file_path = document.get(
        "file_path"
    )

    if file_path:

        absolute_path = os.path.join(
            root_path,
            file_path
        )

        if os.path.exists(
            absolute_path
        ):

            try:

                os.remove(
                    absolute_path
                )

            except OSError as error:

                raise DocumentServiceError(
                    f"No fue posible eliminar el archivo físico: {error}"
                )

    result = (
        document_repository
        .permanent_delete(
            document["_id"]
        )
    )

    return (
        result.deleted_count > 0
    )
    
# ============================================================
# MOTOR DE BÚSQUEDA INTELIGENTE
# ============================================================

from services.intelligent_search_service import (
    intelligent_search
)