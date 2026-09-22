import os
import sys
from models.shift_manager import ShiftManager

def resetear_historial():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    if not os.path.exists(config_path):
        print(f"Error: No se encontró el archivo de configuración en {config_path}")
        return False
        
    manager = ShiftManager(config_path)
    success = manager.reset_historial(preserve_inicio=True)
    if success:
        print("El historial ha sido reseteado exitosamente (con backup automático). El sistema ha vuelto a los datos de inicio.")
    else:
        print("Error al resetear el historial.")
    return success

if __name__ == "__main__":
    resetear_historial()

