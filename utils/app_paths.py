import os
import sys


APP_NAME = "Sistema de Turnos"


def get_application_data_dir() -> str:
    """Returns the writable per-user data directory used by the desktop app."""
    if getattr(sys, "frozen", False):
        base_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
        path = os.path.join(base_dir, APP_NAME)
    else:
        # Development and tests keep their existing project-local behavior.
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.makedirs(path, exist_ok=True)
    return path
