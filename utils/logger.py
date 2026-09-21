import logging
import os
import sys
from logging.handlers import RotatingFileHandler

_logger_initialized = False

def get_root_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def setup_logger(name="turnos", log_filename="turnos.log", level=logging.INFO):
    global _logger_initialized
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not _logger_initialized:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Stream handler for console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)

        # Rotating file handler
        try:
            log_dir = get_root_dir()
            log_path = os.path.join(log_dir, log_filename)
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=2 * 1024 * 1024,  # 2 MB
                backupCount=3,
                encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning("No se pudo inicializar RotatingFileHandler: %s", e)

        _logger_initialized = True

    return logger

def get_logger(name="turnos"):
    return setup_logger(name)
