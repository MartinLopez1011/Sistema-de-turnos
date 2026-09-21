import os
import sys

# Agregar la raíz del proyecto al sys.path para pruebas
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
