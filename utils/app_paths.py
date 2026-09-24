import os
import sys


APP_NAME = "Sistema de Turnos"


def get_application_data_dir() -> str:
    """Returns the writable per-user data directory used by the desktop app.
    
    Supports:
    1. Portable mode: If a '.portable' file or an existing 'config.json' is present in the executable's directory.
    2. Per-user standard mode: '%APPDATA%\\Sistema de Turnos' (zero admin permissions required).
    3. Development / test mode: Project root directory.
    """
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        portable_marker = os.path.join(exe_dir, ".portable")
        local_config = os.path.join(exe_dir, "config.json")
        if os.path.exists(portable_marker) or os.path.exists(local_config):
            path = exe_dir
        else:
            base_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
            path = os.path.join(base_dir, APP_NAME)
    else:
        # Development and tests keep their existing project-local behavior.
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.makedirs(path, exist_ok=True)
    return path

