import os

from dotenv import load_dotenv

load_dotenv()  # Carga las variables del archivo .env


class Config:

    SECRET_KEY = os.getenv("SECRET_KEY") or os.urandom(32)

    MONGO_URI = os.getenv(
        "MONGO_URI",
        "mongodb://127.0.0.1:27017/"
    )

    MONGO_DB = os.getenv(
        "MONGO_DB",
        "innovafile"
    )

    CLOUD_DOCUMENTS_FOLDER = os.getenv("CLOUD_DOCUMENTS_FOLDER", "").strip()
    UPLOAD_FOLDER = CLOUD_DOCUMENTS_FOLDER or os.getenv(
        "UPLOAD_FOLDER", os.path.join("static", "uploads", "documents")
    )

    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(50 * 1024 * 1024)))
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    GEMINI_ENABLED = bool(GEMINI_API_KEY)
    GEMINI_SEND_DOCUMENT_CONTENT = os.getenv("GEMINI_SEND_DOCUMENT_CONTENT", "true").lower() == "true"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    PREFERRED_URL_SCHEME = "https" if SESSION_COOKIE_SECURE else "http"