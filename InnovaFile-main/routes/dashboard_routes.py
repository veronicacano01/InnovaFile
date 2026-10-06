from datetime import datetime, timezone

from flask import Blueprint, render_template

from extensions import db
from helpers.auth import login_required


# ============================================================
# BLUEPRINT
# ============================================================

dashboard_bp = Blueprint(
    "dashboard",
    __name__
)


# ============================================================
# CONSTANTES
# ============================================================

MONTH_NAMES = {
    1: "Ene",
    2: "Feb",
    3: "Mar",
    4: "Abr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Ago",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dic"
}


# ============================================================
# DOCUMENTOS ACTIVOS
# ============================================================

def active_documents_query():

    return {
        "is_deleted": {
            "$ne": True
        }
    }


# ============================================================
# ENRIQUECER DOCUMENTO
# ============================================================

def enriched_document(doc):

    if not doc:
        return None

    data = dict(doc)

    category = None
    user = None

    category_id = data.get(
        "category_id"
    )

    user_id = data.get(
        "user_id"
    )

    if category_id:

        category = db.categories.find_one({
            "_id": category_id
        })

    if user_id:

        user = db.users.find_one({
            "_id": user_id
        })

    data["category"] = (
        category
        or {
            "name": "Sin categoría"
        }
    )

    data["user"] = (
        user
        or {
            "name": "Desconocido"
        }
    )

    return data


# ============================================================
# ENRIQUECER ACTIVIDAD
# ============================================================

def enriched_log(log):

    if not log:
        return None

    data = dict(log)

    user = None

    user_id = data.get(
        "user_id"
    )

    if user_id:

        user = db.users.find_one({
            "_id": user_id
        })

    data["user"] = (
        user
        or {
            "name": "Desconocido"
        }
    )

    return data


# ============================================================
# INICIO DEL MES
# ============================================================

def get_month_start(date):

    return datetime(
        date.year,
        date.month,
        1,
        tzinfo=timezone.utc
    )


# ============================================================
# RESTAR MESES
# ============================================================

def subtract_months(date, months):

    year = date.year
    month = date.month - months

    while month <= 0:

        month += 12
        year -= 1

    return datetime(
        year,
        month,
        1,
        tzinfo=timezone.utc
    )


# ============================================================
# FORMATEAR TAMAÑO
# ============================================================

def format_size(size_bytes):

    try:
        size = float(
            size_bytes or 0
        )

    except (
        TypeError,
        ValueError
    ):
        size = 0

    units = [
        "B",
        "KB",
        "MB",
        "GB",
        "TB"
    ]

    unit_index = 0

    while (
        size >= 1024
        and
        unit_index < len(
            units
        ) - 1
    ):

        size /= 1024
        unit_index += 1

    if unit_index == 0:

        return f"{int(size)} {units[unit_index]}"

    return f"{size:.2f} {units[unit_index]}"


# ============================================================
# DOCUMENTOS POR CATEGORÍA
# ============================================================

def get_documents_by_category():

    pipeline = [
        {
            "$match": active_documents_query()
        },
        {
            "$group": {
                "_id": "$category_id",
                "total": {
                    "$sum": 1
                }
            }
        },
        {
            "$sort": {
                "total": -1
            }
        }
    ]

    counts = {
        item["_id"]: item["total"]
        for item in db.documents.aggregate(
            pipeline
        )
    }

    result = []

    for category in db.categories.find().sort(
        "name",
        1
    ):

        result.append({
            "name": category.get(
                "name",
                "Sin categoría"
            ),
            "total": counts.get(
                category["_id"],
                0
            )
        })

    # Documentos sin categoría válida

    known_category_ids = {
        category["_id"]
        for category in db.categories.find(
            {},
            {
                "_id": 1
            }
        )
    }

    uncategorized = sum(
        total
        for category_id, total in counts.items()
        if category_id not in known_category_ids
    )

    if uncategorized:

        result.append({
            "name": "Sin categoría",
            "total": uncategorized
        })

    return sorted(
        result,
        key=lambda item: item[
            "total"
        ],
        reverse=True
    )


# ============================================================
# DOCUMENTOS POR TIPO
# ============================================================

def get_documents_by_type():

    pipeline = [
        {
            "$match": active_documents_query()
        },
        {
            "$group": {
                "_id": {
                    "$toLower": {
                        "$ifNull": [
                            "$file_type",
                            "otro"
                        ]
                    }
                },
                "total": {
                    "$sum": 1
                }
            }
        },
        {
            "$sort": {
                "total": -1
            }
        }
    ]

    result = []

    for item in db.documents.aggregate(
        pipeline
    ):

        file_type = (
            item.get(
                "_id"
            )
            or
            "otro"
        )

        result.append({
            "name": file_type.upper(),
            "total": item.get(
                "total",
                0
            )
        })

    return result


# ============================================================
# DOCUMENTOS DE LOS ÚLTIMOS 6 MESES
# ============================================================

def get_documents_last_months():

    now = datetime.now(
        timezone.utc
    )

    current_month = get_month_start(
        now
    )

    months = []

    for offset in range(
        5,
        -1,
        -1
    ):

        start = subtract_months(
            current_month,
            offset
        )

        if start.month == 12:

            end = datetime(
                start.year + 1,
                1,
                1,
                tzinfo=timezone.utc
            )

        else:

            end = datetime(
                start.year,
                start.month + 1,
                1,
                tzinfo=timezone.utc
            )

        total = db.documents.count_documents({
            "is_deleted": {
                "$ne": True
            },
            "created_at": {
                "$gte": start,
                "$lt": end
            }
        })

        months.append({
            "label": (
                f"{MONTH_NAMES[start.month]} "
                f"{str(start.year)[2:]}"
            ),
            "total": total
        })

    return months


# ============================================================
# TOP USUARIOS
# ============================================================

def get_top_users(limit=5):

    pipeline = [
        {
            "$match": active_documents_query()
        },
        {
            "$group": {
                "_id": "$user_id",
                "total": {
                    "$sum": 1
                }
            }
        },
        {
            "$sort": {
                "total": -1
            }
        },
        {
            "$limit": limit
        }
    ]

    result = []

    for item in db.documents.aggregate(
        pipeline
    ):

        user = None

        user_id = item.get(
            "_id"
        )

        if user_id:

            user = db.users.find_one({
                "_id": user_id
            })

        result.append({
            "name": (
                user.get(
                    "name"
                )
                if user
                else "Usuario desconocido"
            ),
            "total": item.get(
                "total",
                0
            )
        })

    return result


# ============================================================
# TOTAL ALMACENAMIENTO
# ============================================================

def get_storage_information():

    pipeline = [
        {
            "$match": active_documents_query()
        },
        {
            "$group": {
                "_id": None,
                "total": {
                    "$sum": {
                        "$ifNull": [
                            "$file_size",
                            0
                        ]
                    }
                }
            }
        }
    ]

    result = list(
        db.documents.aggregate(
            pipeline
        )
    )

    total_bytes = (
        result[0].get(
            "total",
            0
        )
        if result
        else 0
    )

    return {
        "bytes": total_bytes,
        "formatted": format_size(
            total_bytes
        )
    }


# ============================================================
# DASHBOARD
# ============================================================

@dashboard_bp.get(
    "/dashboard"
)
@login_required
def index():

    now = datetime.now(
        timezone.utc
    )

    month_start = get_month_start(
        now
    )

    # --------------------------------------------------------
    # MÉTRICAS PRINCIPALES
    # --------------------------------------------------------

    usuarios = db.users.count_documents(
        {}
    )

    documentos = db.documents.count_documents(
        active_documents_query()
    )

    documentos_papelera = (
        db.documents.count_documents({
            "is_deleted": True
        })
    )

    categorias = db.categories.count_documents(
        {}
    )

    documentos_mes = (
        db.documents.count_documents({
            "is_deleted": {
                "$ne": True
            },
            "created_at": {
                "$gte": month_start
            }
        })
    )

    actividades = (
        db.activity_logs.count_documents(
            {}
        )
    )

    # --------------------------------------------------------
    # ALMACENAMIENTO
    # --------------------------------------------------------

    almacenamiento = (
        get_storage_information()
    )

    # --------------------------------------------------------
    # DOCUMENTOS RECIENTES
    # --------------------------------------------------------

    ultimos_documentos = [
        enriched_document(
            document
        )
        for document in (
            db.documents
            .find(
                active_documents_query()
            )
            .sort(
                "created_at",
                -1
            )
            .limit(5)
        )
    ]

    # --------------------------------------------------------
    # ACTIVIDAD RECIENTE
    # --------------------------------------------------------

    historial = [
        enriched_log(
            activity
        )
        for activity in (
            db.activity_logs
            .find()
            .sort(
                "created_at",
                -1
            )
            .limit(6)
        )
    ]

    # --------------------------------------------------------
    # ANALÍTICA
    # --------------------------------------------------------

    documentos_categoria = (
        get_documents_by_category()
    )

    documentos_tipo = (
        get_documents_by_type()
    )

    documentos_meses = (
        get_documents_last_months()
    )

    top_usuarios = (
        get_top_users(
            limit=5
        )
    )

    # --------------------------------------------------------
    # PORCENTAJE DEL MES
    # --------------------------------------------------------

    porcentaje_mes = 0

    if documentos > 0:

        porcentaje_mes = round(
            (
                documentos_mes
                /
                documentos
            )
            *
            100,
            1
        )

    return render_template(
        "dashboard.html",

        usuarios=usuarios,

        documentos=documentos,

        documentos_mes=documentos_mes,

        documentos_papelera=documentos_papelera,

        categorias=categorias,

        actividades=actividades,

        almacenamiento=almacenamiento,

        porcentaje_mes=porcentaje_mes,

        ultimos_documentos=ultimos_documentos,

        historial=historial,

        documentos_categoria=documentos_categoria,

        documentos_tipo=documentos_tipo,

        documentos_meses=documentos_meses,

        top_usuarios=top_usuarios
    )


# ============================================================
# ESTADÍSTICAS
# ============================================================

@dashboard_bp.get(
    "/estadisticas"
)
@login_required
def statistics():

    usuarios = db.users.count_documents(
        {}
    )

    documentos = db.documents.count_documents(
        active_documents_query()
    )

    categorias = db.categories.count_documents(
        {}
    )

    actividades = (
        db.activity_logs.count_documents(
            {}
        )
    )

    ultimos_documentos = list(
        db.documents
        .find(
            active_documents_query()
        )
        .sort(
            "created_at",
            -1
        )
        .limit(5)
    )

    ultimas_actividades = list(
        db.activity_logs
        .find()
        .sort(
            "created_at",
            -1
        )
        .limit(5)
    )

    documentos_categoria = (
        get_documents_by_category()
    )

    return render_template(
        "statistics.html",

        usuarios=usuarios,

        documentos=documentos,

        categorias=categorias,

        actividades=actividades,

        ultimos_documentos=ultimos_documentos,

        ultimas_actividades=ultimas_actividades,

        documentos_categoria=documentos_categoria
    )