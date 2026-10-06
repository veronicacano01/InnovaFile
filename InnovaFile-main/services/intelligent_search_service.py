import re
import unicodedata

from datetime import (
    datetime,
    timedelta,
    timezone
)

from repositories import document_repository


# ============================================================
# PALABRAS QUE NO APORTAN VALOR A LA BÚSQUEDA
# ============================================================

STOP_WORDS = {
    "a",
    "al",
    "algo",
    "archivo",
    "archivos",
    "busca",
    "buscar",
    "buscame",
    "con",
    "cual",
    "cuales",
    "de",
    "del",
    "dame",
    "documento",
    "documentos",
    "donde",
    "el",
    "en",
    "encuentra",
    "encontrar",
    "esta",
    "este",
    "estos",
    "la",
    "las",
    "los",
    "me",
    "muestra",
    "muestrame",
    "por",
    "que",
    "quiero",
    "relacionado",
    "relacionados",
    "se",
    "son",
    "un",
    "una",
    "unos",
    "unas",
    "ver"
}


# ============================================================
# MESES
# ============================================================

MONTHS = {

    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12

}


# ============================================================
# TIPOS DE ARCHIVO
# ============================================================

FILE_TYPES = {

    "pdf": ["pdf"],

    "word": [
        "doc",
        "docx"
    ],

    "doc": [
        "doc",
        "docx"
    ],

    "docx": [
        "docx"
    ],

    "excel": [
        "xls",
        "xlsx",
        "csv"
    ],

    "xlsx": [
        "xlsx"
    ],

    "xls": [
        "xls"
    ],

    "csv": [
        "csv"
    ],

    "powerpoint": [
        "ppt",
        "pptx"
    ],

    "presentacion": [
        "ppt",
        "pptx"
    ],

    "ppt": [
        "ppt",
        "pptx"
    ],

    "pptx": [
        "pptx"
    ],

    "texto": [
        "txt"
    ],

    "txt": [
        "txt"
    ],

    "imagen": [
        "jpg",
        "jpeg",
        "png"
    ],

    "imagenes": [
        "jpg",
        "jpeg",
        "png"
    ],

    "jpg": [
        "jpg",
        "jpeg"
    ],

    "jpeg": [
        "jpg",
        "jpeg"
    ],

    "png": [
        "png"
    ]

}


# ============================================================
# NORMALIZAR TEXTO
# ============================================================

def normalize_text(value):

    text = str(
        value or ""
    ).strip().lower()

    text = unicodedata.normalize(
        "NFD",
        text
    )

    text = "".join(
        character
        for character in text
        if unicodedata.category(
            character
        ) != "Mn"
    )

    text = re.sub(
        r"[^a-z0-9\s._-]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# CONVERTIR FECHA
# ============================================================

def ensure_datetime(value):

    if not value:
        return None

    if isinstance(
        value,
        datetime
    ):

        if value.tzinfo is None:

            return value.replace(
                tzinfo=timezone.utc
            )

        return value

    try:

        parsed = datetime.fromisoformat(
            str(value).replace(
                "Z",
                "+00:00"
            )
        )

        if parsed.tzinfo is None:

            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed

    except (
        ValueError,
        TypeError
    ):

        return None


# ============================================================
# INICIO DE MES
# ============================================================

def month_start(
    year,
    month
):

    return datetime(
        year,
        month,
        1,
        tzinfo=timezone.utc
    )


# ============================================================
# FIN DE MES
# ============================================================

def next_month_start(
    year,
    month
):

    if month == 12:

        return datetime(
            year + 1,
            1,
            1,
            tzinfo=timezone.utc
        )

    return datetime(
        year,
        month + 1,
        1,
        tzinfo=timezone.utc
    )


# ============================================================
# DETECTAR TIPO DE ARCHIVO
# ============================================================

def detect_file_types(
    normalized_question
):

    detected = []

    words = set(
        normalized_question.split()
    )

    for key, extensions in FILE_TYPES.items():

        if key in words:

            detected.extend(
                extensions
            )

    return list(
        dict.fromkeys(
            detected
        )
    )


# ============================================================
# DETECTAR FECHAS EN LENGUAJE NATURAL
# ============================================================

def detect_date_range(
    normalized_question
):

    now = datetime.now(
        timezone.utc
    )

    today = datetime(
        now.year,
        now.month,
        now.day,
        tzinfo=timezone.utc
    )

    # --------------------------------------------------------
    # HOY
    # --------------------------------------------------------

    if re.search(
        r"\bhoy\b",
        normalized_question
    ):

        return (
            today,
            today + timedelta(
                days=1
            ),
            "de hoy"
        )

    # --------------------------------------------------------
    # AYER
    # --------------------------------------------------------

    if re.search(
        r"\bayer\b",
        normalized_question
    ):

        start = (
            today
            -
            timedelta(
                days=1
            )
        )

        return (
            start,
            today,
            "de ayer"
        )

    # --------------------------------------------------------
    # ESTA SEMANA
    # --------------------------------------------------------

    if "esta semana" in normalized_question:

        start = (
            today
            -
            timedelta(
                days=today.weekday()
            )
        )

        return (
            start,
            start
            +
            timedelta(
                days=7
            ),
            "de esta semana"
        )

    # --------------------------------------------------------
    # ESTE MES
    # --------------------------------------------------------

    if "este mes" in normalized_question:

        start = month_start(
            now.year,
            now.month
        )

        end = next_month_start(
            now.year,
            now.month
        )

        return (
            start,
            end,
            "de este mes"
        )

    # --------------------------------------------------------
    # MES PASADO
    # --------------------------------------------------------

    if (
        "mes pasado"
        in normalized_question
        or
        "ultimo mes"
        in normalized_question
    ):

        current_month = month_start(
            now.year,
            now.month
        )

        previous_day = (
            current_month
            -
            timedelta(
                days=1
            )
        )

        start = month_start(
            previous_day.year,
            previous_day.month
        )

        return (
            start,
            current_month,
            "del mes pasado"
        )

    # --------------------------------------------------------
    # ESTE AÑO
    # --------------------------------------------------------

    if (
        "este ano"
        in normalized_question
        or
        "ano actual"
        in normalized_question
    ):

        start = datetime(
            now.year,
            1,
            1,
            tzinfo=timezone.utc
        )

        end = datetime(
            now.year + 1,
            1,
            1,
            tzinfo=timezone.utc
        )

        return (
            start,
            end,
            f"del año {now.year}"
        )

    # --------------------------------------------------------
    # AÑO PASADO
    # --------------------------------------------------------

    if "ano pasado" in normalized_question:

        start = datetime(
            now.year - 1,
            1,
            1,
            tzinfo=timezone.utc
        )

        end = datetime(
            now.year,
            1,
            1,
            tzinfo=timezone.utc
        )

        return (
            start,
            end,
            f"del año {now.year - 1}"
        )

    # --------------------------------------------------------
    # ÚLTIMOS 7 DÍAS
    # --------------------------------------------------------

    if (
        "ultimos 7 dias"
        in normalized_question
        or
        "ultima semana"
        in normalized_question
    ):

        return (
            now
            -
            timedelta(
                days=7
            ),
            now
            +
            timedelta(
                seconds=1
            ),
            "de los últimos 7 días"
        )

    # --------------------------------------------------------
    # ÚLTIMOS 30 DÍAS
    # --------------------------------------------------------

    if "ultimos 30 dias" in normalized_question:

        return (
            now
            -
            timedelta(
                days=30
            ),
            now
            +
            timedelta(
                seconds=1
            ),
            "de los últimos 30 días"
        )

    # --------------------------------------------------------
    # NOMBRE DE MES
    #
    # Ej:
    # julio
    # julio 2026
    # --------------------------------------------------------

    for month_name, month_number in MONTHS.items():

        pattern = (
            rf"\b{month_name}"
            rf"(?:\s+de)?"
            rf"\s*(\d{{4}})?\b"
        )

        match = re.search(
            pattern,
            normalized_question
        )

        if match:

            year_text = (
                match.group(1)
            )

            year = (
                int(year_text)
                if year_text
                else now.year
            )

            start = month_start(
                year,
                month_number
            )

            end = next_month_start(
                year,
                month_number
            )

            return (
                start,
                end,
                (
                    f"de {month_name} "
                    f"{year}"
                )
            )

    # --------------------------------------------------------
    # AÑO NUMÉRICO
    # --------------------------------------------------------

    match_year = re.search(
        r"\b(20\d{2})\b",
        normalized_question
    )

    if match_year:

        year = int(
            match_year.group(1)
        )

        start = datetime(
            year,
            1,
            1,
            tzinfo=timezone.utc
        )

        end = datetime(
            year + 1,
            1,
            1,
            tzinfo=timezone.utc
        )

        return (
            start,
            end,
            f"del año {year}"
        )

    return (
        None,
        None,
        None
    )


# ============================================================
# DETECTAR BÚSQUEDA POR USUARIO
# ============================================================

def detect_user_phrase(
    normalized_question
):

    patterns = [

        r"subidos por\s+(.+)",
        r"subido por\s+(.+)",
        r"creados por\s+(.+)",
        r"creado por\s+(.+)",
        r"registrados por\s+(.+)",
        r"registrado por\s+(.+)",
        r"documentos de usuario\s+(.+)"

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            normalized_question
        )

        if match:

            value = (
                match.group(1)
                .strip()
            )

            # Quitamos fragmentos de fecha
            value = re.split(
                r"\b("
                r"este mes|"
                r"esta semana|"
                r"este ano|"
                r"ano pasado|"
                r"mes pasado|"
                r"hoy|"
                r"ayer"
                r")\b",
                value
            )[0]

            return value.strip()

    return ""


# ============================================================
# DETECTAR SI SOLICITA RECIENTES
# ============================================================

def wants_recent(
    normalized_question
):

    phrases = [

        "recientes",
        "mas recientes",
        "ultimos documentos",
        "ultimos archivos",
        "nuevos documentos",
        "documentos nuevos"

    ]

    return any(
        phrase
        in normalized_question
        for phrase in phrases
    )


# ============================================================
# OBTENER DOCUMENTOS ACTIVOS
# ============================================================

def get_active_documents():

    documents = (
        document_repository
        .get_all()
    )

    return [
        document
        for document in documents
        if not document.get(
            "is_deleted",
            False
        )
    ]


# ============================================================
# ENRIQUECER DOCUMENTO
# ============================================================

def enrich_document(
    document
):

    data = dict(
        document
    )

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
        category
        or {
            "name":
                "Sin categoría"
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
        user
        or {
            "name":
                "Usuario desconocido"
        }
    )

    return data


# ============================================================
# EXTRAER TÉRMINOS RELEVANTES
# ============================================================

def extract_terms(
    normalized_question
):

    text = normalized_question

    # --------------------------------------------------------
    # QUITAR EXPRESIONES DE FECHA
    # --------------------------------------------------------

    expressions = [

        "este mes",
        "mes pasado",
        "ultimo mes",
        "esta semana",
        "ultima semana",
        "ultimos 7 dias",
        "ultimos 30 dias",
        "este ano",
        "ano actual",
        "ano pasado",
        "hoy",
        "ayer",
        "mas recientes",
        "recientes",
        "ultimos documentos",
        "ultimos archivos"

    ]

    for expression in expressions:

        text = text.replace(
            expression,
            " "
        )

    # --------------------------------------------------------
    # QUITAR NOMBRES DE MESES
    # --------------------------------------------------------

    for month_name in MONTHS:

        text = re.sub(
            rf"\b{month_name}\b",
            " ",
            text
        )

    # --------------------------------------------------------
    # QUITAR AÑOS
    # --------------------------------------------------------

    text = re.sub(
        r"\b20\d{2}\b",
        " ",
        text
    )

    # --------------------------------------------------------
    # QUITAR TIPO DE ARCHIVO
    # --------------------------------------------------------

    for file_type in FILE_TYPES:

        text = re.sub(
            rf"\b{re.escape(file_type)}\b",
            " ",
            text
        )

    # --------------------------------------------------------
    # TOKENIZAR
    # --------------------------------------------------------

    tokens = re.findall(
        r"[a-z0-9_-]+",
        text
    )

    result = []

    for token in tokens:

        if token in STOP_WORDS:
            continue

        if len(token) < 2:
            continue

        if token not in result:

            result.append(
                token
            )

    return result


# ============================================================
# CREAR TEXTO BUSCABLE DE DOCUMENTO
# ============================================================

def document_search_text(
    document
):

    category = (
        document
        .get(
            "category",
            {}
        )
        .get(
            "name",
            ""
        )
    )

    user = (
        document
        .get(
            "user",
            {}
        )
        .get(
            "name",
            ""
        )
    )

    parts = [

        document.get(
            "title",
            ""
        ),

        document.get(
            "description",
            ""
        ),

        document.get(
            "file_name",
            ""
        ),

        document.get(
            "file_type",
            ""
        ),

        category,

        user

    ]

    return normalize_text(
        " ".join(
            str(part or "")
            for part in parts
        )
    )


# ============================================================
# CALCULAR RELEVANCIA
# ============================================================

def calculate_score(
    document,
    terms,
    user_phrase=""
):

    title = normalize_text(
        document.get(
            "title",
            ""
        )
    )

    description = normalize_text(
        document.get(
            "description",
            ""
        )
    )

    filename = normalize_text(
        document.get(
            "file_name",
            ""
        )
    )

    category = normalize_text(
        document
        .get(
            "category",
            {}
        )
        .get(
            "name",
            ""
        )
    )

    user = normalize_text(
        document
        .get(
            "user",
            {}
        )
        .get(
            "name",
            ""
        )
    )

    searchable = (
        document_search_text(
            document
        )
    )

    score = 0

    for term in terms:

        # Título tiene mayor valor
        if term in title:
            score += 8

        # Categoría
        if term in category:
            score += 7

        # Nombre del archivo
        if term in filename:
            score += 6

        # Usuario
        if term in user:
            score += 6

        # Descripción
        if term in description:
            score += 4

        # Campo general
        if term in searchable:
            score += 2

    # --------------------------------------------------------
    # COINCIDENCIA DIRECTA DE USUARIO
    # --------------------------------------------------------

    if user_phrase:

        normalized_user_phrase = (
            normalize_text(
                user_phrase
            )
        )

        if normalized_user_phrase in user:

            score += 20

    return score


# ============================================================
# FILTRAR POR FECHA
# ============================================================

def matches_date(
    document,
    start_date,
    end_date
):

    if not start_date:
        return True

    created_at = ensure_datetime(
        document.get(
            "created_at"
        )
    )

    if not created_at:
        return False

    return (
        created_at >= start_date
        and
        created_at < end_date
    )


# ============================================================
# FILTRAR POR TIPO
# ============================================================

def matches_file_type(
    document,
    extensions
):

    if not extensions:
        return True

    file_type = normalize_text(
        document.get(
            "file_type",
            ""
        )
    )

    return (
        file_type
        in extensions
    )


# ============================================================
# FILTRAR POR USUARIO
# ============================================================

def matches_user(
    document,
    user_phrase
):

    if not user_phrase:
        return True

    user_name = normalize_text(
        document
        .get(
            "user",
            {}
        )
        .get(
            "name",
            ""
        )
    )

    wanted = normalize_text(
        user_phrase
    )

    return (
        wanted in user_name
        or
        all(
            token in user_name
            for token in wanted.split()
        )
    )


# ============================================================
# GENERAR RESPUESTA
# ============================================================

def build_response(
    total,
    extensions,
    date_label,
    user_phrase,
    terms,
    recent
):

    if total == 0:

        parts = []

        if extensions:

            parts.append(
                "del tipo "
                +
                ", ".join(
                    extension.upper()
                    for extension
                    in extensions
                )
            )

        if date_label:

            parts.append(
                date_label
            )

        if user_phrase:

            parts.append(
                f"registrados por {user_phrase.title()}"
            )

        extra = (
            " "
            +
            " ".join(
                parts
            )
            if parts
            else ""
        )

        return (
            "No encontré documentos "
            f"que coincidan con la consulta{extra}. "
            "Intenta usar menos palabras o cambiar alguno de los filtros."
        )

    response = (
        f"Encontré {total} "
        +
        (
            "documento"
            if total == 1
            else "documentos"
        )
    )

    filters = []

    if extensions:

        filters.append(
            "tipo "
            +
            "/".join(
                extension.upper()
                for extension
                in extensions
            )
        )

    if date_label:

        filters.append(
            date_label
        )

    if user_phrase:

        filters.append(
            f"de {user_phrase.title()}"
        )

    if terms:

        filters.append(
            "relacionados con "
            +
            ", ".join(
                terms[:5]
            )
        )

    if recent:

        filters.append(
            "ordenados del más reciente al más antiguo"
        )

    if filters:

        response += (
            " con los filtros: "
            +
            "; ".join(
                filters
            )
            +
            "."
        )

    else:

        response += (
            " relacionados con tu búsqueda."
        )

    return response


# ============================================================
# BÚSQUEDA INTELIGENTE PRINCIPAL
# ============================================================

def intelligent_search(
    question,
    limit=50
):

    question = (
        question or ""
    ).strip()

    if not question:

        return (
            [],
            (
                "Escribe una palabra o pregunta "
                "para realizar la búsqueda."
            )
        )

    normalized_question = normalize_text(
        question
    )

    # --------------------------------------------------------
    # INTERPRETAR LA CONSULTA
    # --------------------------------------------------------

    extensions = detect_file_types(
        normalized_question
    )

    (
        start_date,
        end_date,
        date_label
    ) = detect_date_range(
        normalized_question
    )

    user_phrase = detect_user_phrase(
        normalized_question
    )

    recent = wants_recent(
        normalized_question
    )

    terms = extract_terms(
        normalized_question
    )

    # --------------------------------------------------------
    # CARGAR DOCUMENTOS
    # --------------------------------------------------------

    raw_documents = (
        get_active_documents()
    )

    documents = [
        enrich_document(
            document
        )
        for document
        in raw_documents
    ]

    results = []

    # --------------------------------------------------------
    # FILTRAR
    # --------------------------------------------------------

    for document in documents:

        if not matches_file_type(
            document,
            extensions
        ):
            continue

        if not matches_date(
            document,
            start_date,
            end_date
        ):
            continue

        if not matches_user(
            document,
            user_phrase
        ):
            continue

        score = calculate_score(
            document=document,
            terms=terms,
            user_phrase=user_phrase
        )

        # ----------------------------------------------------
        # SI HAY TÉRMINOS DE CONTENIDO,
        # EXIGIMOS AL MENOS UNA COINCIDENCIA
        # ----------------------------------------------------

        if terms and score <= 0:
            continue

        result = dict(
            document
        )

        result[
            "_ai_score"
        ] = score

        results.append(
            result
        )

    # --------------------------------------------------------
    # ORDENAR
    # --------------------------------------------------------

    if recent:

        results.sort(
            key=lambda item: (
                ensure_datetime(
                    item.get(
                        "created_at"
                    )
                )
                or datetime.min.replace(
                    tzinfo=timezone.utc
                )
            ),
            reverse=True
        )

    else:

        results.sort(
            key=lambda item: (
                item.get(
                    "_ai_score",
                    0
                ),
                (
                    ensure_datetime(
                        item.get(
                            "created_at"
                        )
                    )
                    or datetime.min.replace(
                        tzinfo=timezone.utc
                    )
                )
            ),
            reverse=True
        )

    # --------------------------------------------------------
    # LIMITAR RESULTADOS
    # --------------------------------------------------------

    try:

        limit = int(
            limit
        )

    except (
        TypeError,
        ValueError
    ):

        limit = 50

    limit = max(
        1,
        min(
            limit,
            100
        )
    )

    results = results[
        :limit
    ]

    # --------------------------------------------------------
    # QUITAR INFORMACIÓN INTERNA
    # --------------------------------------------------------

    for result in results:

        result.pop(
            "_ai_score",
            None
        )

    # --------------------------------------------------------
    # RESPUESTA
    # --------------------------------------------------------

    response = build_response(
        total=len(
            results
        ),
        extensions=extensions,
        date_label=date_label,
        user_phrase=user_phrase,
        terms=terms,
        recent=recent
    )

    return (
        results,
        response
    )