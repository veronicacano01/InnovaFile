from datetime import timezone, timedelta

try:
    from zoneinfo import ZoneInfo
    MEXICO_TZ = ZoneInfo("America/Mexico_City")
except Exception:
    # Fallback si zoneinfo no está disponible
    MEXICO_TZ = timezone(timedelta(hours=-6))


def to_mexico(dt):
    """Convierte un datetime UTC a la zona horaria de México."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(MEXICO_TZ)


def format_date(dt, fmt="%d/%m/%Y"):
    """Formatea una fecha UTC a la zona horaria de México."""
    local = to_mexico(dt)
    if local is None:
        return "-"
    return local.strftime(fmt)


def format_datetime(dt, fmt="%d/%m/%Y %H:%M"):
    """Formatea fecha y hora UTC a la zona horaria de México."""
    local = to_mexico(dt)
    if local is None:
        return "-"
    return local.strftime(fmt)