import os
import sys
from utils.app_paths import get_application_data_dir

def get_root_dir():
    """Obtiene el directorio raíz del proyecto o del ejecutable."""
    if getattr(sys, 'frozen', False):
        return get_application_data_dir()
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def get_env_file_path():
    """Retorna la ruta absoluta al archivo .env en el directorio raíz."""
    return os.path.join(get_root_dir(), ".env")


_env_loaded = False


def load_env_file(env_path=None):
    """
    Carga variables desde un archivo .env en el diccionario retornado y en os.environ.
    No requiere librerías externas.
    """
    global _env_loaded
    path = env_path or get_env_file_path()
    env_vars = {}
    if not os.path.isfile(path):
        _env_loaded = True
        return env_vars

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Ignorar líneas vacías y comentarios
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("'\"")
                    env_vars[key] = value
                    os.environ[key] = value
    except Exception:
        pass
    _env_loaded = True
    return env_vars


def get_env_var(key, default=""):
    """
    Obtiene el valor de una variable desde os.environ o leyendo el .env una sola vez.
    """
    global _env_loaded
    if key in os.environ:
        return os.environ[key]
    if not _env_loaded:
        load_env_file()
    return os.environ.get(key, default)


def set_env_var(key, value, env_path=None):
    """
    Guarda o actualiza una variable en el archivo .env sin perder las demás líneas.
    """
    path = env_path or get_env_file_path()
    key = str(key).strip()
    value = str(value).strip()

    lines = []
    found = False

    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            lines = []

    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            curr_key = stripped.split("=", 1)[0].strip()
            if curr_key == key:
                new_lines.append(f"{key}={value}\n")
                found = True
                continue
        new_lines.append(line)

    if not found:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines.append("\n")
        new_lines.append(f"{key}={value}\n")

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        os.environ[key] = value
        return True
    except Exception:
        return False
