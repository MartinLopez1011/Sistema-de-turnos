import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from utils.app_paths import get_application_data_dir

_logger_initialized = False

def get_root_dir():
    if getattr(sys, 'frozen', False):
        return get_application_data_dir()
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def _init_base_logger(log_filename="turnos.log", level=logging.INFO, force_reinit=False):
    global _logger_initialized
    root_turnos = logging.getLogger("turnos")
    root_turnos.setLevel(level)

    if force_reinit:
        for h in list(root_turnos.handlers):
            try:
                h.close()
            except Exception:
                pass
            root_turnos.removeHandler(h)
        _logger_initialized = False

    if not _logger_initialized and not root_turnos.handlers:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Stream handler for console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        root_turnos.addHandler(console_handler)

        # Rotating file handler
        try:
            if os.path.isabs(log_filename):
                log_path = log_filename
            else:
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
            root_turnos.addHandler(file_handler)
        except Exception as e:
            root_turnos.warning("No se pudo inicializar RotatingFileHandler: %s", e)

        root_turnos.propagate = False
        _logger_initialized = True

    return root_turnos

def setup_logger(name="turnos", log_filename="turnos.log", level=logging.INFO, force_reinit=False):
    _init_base_logger(log_filename=log_filename, level=level, force_reinit=force_reinit)
    
    if name == "turnos" or name.startswith("turnos."):
        logger_name = name
    else:
        logger_name = f"turnos.{name}"

    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    return logger

def get_logger(name="turnos"):
    return setup_logger(name)
