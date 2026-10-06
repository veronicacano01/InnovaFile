"""Helpers for validating automatic document synchronization."""

from pathlib import PurePosixPath

ALLOWED_EXTENSIONS = {
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
    "txt", "csv", "jpg", "jpeg", "png"
}

MAX_FILES_PER_SYNC = 500


def extension(filename):
    name = str(filename or "")
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""


def is_supported(filename):
    return extension(filename) in ALLOWED_EXTENSIONS


def safe_source_path(value):
    """Keep only a relative browser path; never trust a client-provided absolute path."""
    value = str(value or "").replace("\\", "/").strip()
    path = PurePosixPath(value)
    parts = [part for part in path.parts if part not in ("", ".", "..")]
    return "/".join(parts)[:1200]
