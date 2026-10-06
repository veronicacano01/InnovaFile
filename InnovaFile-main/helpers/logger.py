import logging
import os

from logging.handlers import RotatingFileHandler


# ============================================================
# CONFIGURAR LOGGING
# ============================================================

def configure_logging(app):

    log_folder = os.path.join(
        app.root_path,
        "logs"
    )

    os.makedirs(
        log_folder,
        exist_ok=True
    )

    log_file = os.path.join(
        log_folder,
        "innovafile.log"
    )

    # Evitar agregar handlers duplicados
    # cuando Flask se recarga en desarrollo.
    if not any(
        isinstance(
            handler,
            RotatingFileHandler
        )
        for handler in app.logger.handlers
    ):

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=2 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )

        file_handler.setLevel(
            logging.INFO
        )

        formatter = logging.Formatter(
            (
                "%(asctime)s | "
                "%(levelname)s | "
                "%(module)s | "
                "%(message)s"
            )
        )

        file_handler.setFormatter(
            formatter
        )

        app.logger.addHandler(
            file_handler
        )

    app.logger.setLevel(
        logging.INFO
    )

    app.logger.info(
        "Sistema InnovaFile iniciado."
    )