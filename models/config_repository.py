import json
import os
from collections.abc import Callable
from datetime import datetime
from typing import Any

from utils.config_validator import validate_config
from utils.logger import get_logger


logger = get_logger("config_repository")


class ConfigRepository:
    """Persistence boundary for the JSON operational state."""

    def __init__(self, config_path: str, defaults_factory: Callable[[], dict[str, Any]]):
        self.config_path = config_path
        self.defaults_factory = defaults_factory

    def load(self) -> dict[str, Any] | None:
        if not os.path.exists(self.config_path):
            return None
        with open(self.config_path, "r", encoding="utf-8") as source:
            data = json.load(source)
        if not isinstance(data, dict):
            raise ValueError("El contenido de config.json no es un objeto JSON válido.")
        errors = validate_config(data)
        if errors:
            logger.warning("Configuración con advertencias: %s", "; ".join(errors))
        return data

    def save(self, payload: dict[str, Any]) -> bool:
        errors = validate_config(payload)
        if errors:
            logger.error("Configuración inválida; no se guardará: %s", "; ".join(errors))
            return False
        directory = os.path.dirname(os.path.abspath(self.config_path))
        os.makedirs(directory, exist_ok=True)
        temporary_path = self.config_path + ".tmp"
        try:
            with open(temporary_path, "w", encoding="utf-8") as target:
                json.dump(payload, target, indent=2, ensure_ascii=False)
                target.flush()
                os.fsync(target.fileno())
            os.replace(temporary_path, self.config_path)
            return True
        except OSError as exc:
            logger.error("No se pudo guardar %s: %s", self.config_path, exc)
            return False
        finally:
            if os.path.exists(temporary_path):
                try:
                    os.remove(temporary_path)
                except OSError:
                    logger.warning("No se pudo eliminar temporal %s", temporary_path)

    def backup_corrupt_file(self) -> str | None:
        if not os.path.exists(self.config_path):
            return None
        try:
            backups_dir = os.path.join(os.path.dirname(self.config_path), "backups")
            os.makedirs(backups_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(
                backups_dir,
                f"{os.path.basename(self.config_path)}.corrupted_{timestamp}",
            )
            with open(self.config_path, "rb") as source, open(path, "wb") as target:
                target.write(source.read())
            return path
        except OSError as exc:
            logger.warning("No se pudo respaldar configuración corrupta: %s", exc)
            return None
