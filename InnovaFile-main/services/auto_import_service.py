import hashlib
import os
import tempfile
from datetime import datetime, timezone

from flask import current_app
from werkzeug.utils import secure_filename

from services.folder_sync_service import safe_source_path
from repositories import document_repository, category_repository
from services.document_content_service import extract_text_from_file
from services.gemini_service import classify_with_gemini


ALLOWED_EXTENSIONS = {
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
    "txt", "csv", "jpg", "jpeg", "png"
}


def _extension(name):
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""


def _classify_local(filename, extracted_text, categories):
    """Clasificador local por palabras clave cuando Gemini no está disponible."""
    text = f"{filename} {extracted_text}".lower()
    keywords = {
        "Contratos": ["contrato", "acuerdo", "convenio", "cláusula", "arrendamiento"],
        "Facturas": ["factura", "invoice", "recibo", "pago", "total a pagar", "iva"],
        "Reportes": ["reporte", "informe", "report", "análisis", "resultado"],
        "Manuales": ["manual", "guía", "instrucciones", "procedimiento", "tutorial"],
        "Currículums": ["currículum", "cv", "curriculum", "experiencia laboral", "formación académica"],
    }
    best = "Otros"
    best_score = 0
    matched = []
    for cat, words in keywords.items():
        if cat not in categories:
            continue
        score = sum(1 for w in words if w in text)
        if score > best_score:
            best_score = score
            best = cat
            matched = [w for w in words if w in text]
    confidence = min(95, 40 + best_score * 15) if best_score else 0
    return {
        "categoria": best,
        "confianza": confidence,
        "motivo": f"Clasificación local por palabras clave: {', '.join(matched) or 'sin coincidencias'}.",
        "palabras": matched[:8],
        "resumen": "",
        "proveedor": "Reglas locales",
        "requiere_revision": confidence < 75,
    }


def auto_import_file(file_storage, source_path, user_id, upload_dir):
    original = secure_filename(file_storage.filename or "")
    ext = _extension(original)

    if not original or ext not in ALLOWED_EXTENSIONS:
        return {"status": "ignored", "message": f"Tipo .{ext or 'desconocido'} no soportado."}

    os.makedirs(upload_dir, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(suffix=f".{ext}")
    os.close(fd)

    try:
        file_storage.save(temp_path)
        size = os.path.getsize(temp_path)
        if size <= 0:
            return {"status": "ignored", "message": "Archivo vacío."}

        with open(temp_path, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()

        source_path = safe_source_path(source_path) or original
        existing = document_repository.get_by_source_path(source_path)

        if existing and existing.get("source_hash") == digest:
            return {
                "status": "skipped",
                "message": "Ya estaba sincronizado.",
                "id": str(existing["_id"]),
            }

        categories = category_repository.get_all()
        names = [c["name"] for c in categories]
        if "Otros" not in names:
            names.append("Otros")

        extracted = ""
        if ext in {"pdf", "docx", "txt", "csv", "xlsx"}:
            try:
                extracted = extract_text_from_file(temp_path, ext) or ""
            except Exception:
                extracted = ""

        send_content = bool(current_app.config.get("GEMINI_SEND_DOCUMENT_CONTENT", True))

        try:
            ai = classify_with_gemini(
                original,
                "",
                extracted if send_content else "",
                names,
                temp_path if send_content and not extracted else None,
            )
        except Exception as gemini_error:
            current_app.logger.warning(
                "Gemini no disponible, usando clasificación local: %s",
                gemini_error,
            )
            ai = _classify_local(original, extracted, names)

        category = (
            category_repository.get_by_name(ai["categoria"])
            or category_repository.get_by_name("Otros")
        )

        if not category:
            now = datetime.now(timezone.utc)
            result = category_repository.create({
                "name": "Otros",
                "description": "Documentos no clasificados en otra categoría.",
                "created_at": now,
                "updated_at": now,
            })
            category = category_repository.get_by_id(result.inserted_id)

        stored = f"{digest[:24]}_{original}"
        final_path = os.path.join(upload_dir, stored)
        os.replace(temp_path, final_path)

        now = datetime.now(timezone.utc)
        data = {
            "title": os.path.splitext(original)[0][:200],
            "description": f"Clasificado automáticamente por {ai.get('proveedor', 'Gemini')}.",
            "category_id": category["_id"],
            "user_id": user_id,
            "file_name": original,
            "stored_filename": stored,
            "file_path": os.path.join("uploads", stored).replace("\\", "/"),
            "file_type": ext,
            "file_size": size,
            "created_at": now,
            "updated_at": now,
            "is_deleted": False,
            "deleted_at": None,
            "deleted_by": None,
            "source_path": source_path[:1000],
            "source_hash": digest,
            "ai_provider": ai.get("proveedor", "Gemini"),
            "ai_category": ai["categoria"],
            "ai_confidence": ai["confianza"],
            "ai_reason": ai["motivo"],
            "ai_keywords": ai["palabras"],
            "ai_summary": ai["resumen"],
            "extracted_text": extracted[:120000] if send_content else "",
            "ai_index_status": "indexed" if send_content else "metadata-only",
            "ai_indexed_at": now,
        }

        if existing:
            data.pop("created_at", None)
            document_repository.update_auto_import(existing["_id"], data)
            return {
                "status": "updated",
                "id": str(existing["_id"]),
                "category": ai["categoria"],
                "confidence": ai["confianza"],
                "name": original,
            }

        result = document_repository.create(data)
        return {
            "status": "imported",
            "id": str(result.inserted_id),
            "category": ai["categoria"],
            "confidence": ai["confianza"],
            "name": original,
        }

    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass