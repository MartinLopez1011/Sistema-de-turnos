import os
import sys
import traceback
from tkinter import messagebox
from controllers.main_controller import MainController
from views.gui import TurnosApp
from utils.logger import get_logger
from utils.env_helper import load_env_file
from utils.app_paths import get_application_data_dir

logger = get_logger("main")

def setup_global_exception_handler():
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.critical("Excepción no controlada capturada:\n%s", err_msg)
        try:
            messagebox.showerror(
                "Error inesperado en Sistema de Turnos",
                f"Ocurrió un error inesperado:\n\n{exc_value}\n\nLos detalles han sido registrados en turnos.log."
            )
        except Exception:
            pass

    sys.excepthook = handle_exception

def main():
    setup_global_exception_handler()
    root_path = get_application_data_dir()
        
    load_env_file(os.path.join(root_path, ".env"))
    controller = MainController(root_path)
    app = TurnosApp(controller)

    def tk_exception_handler(exc_type, exc_value, exc_tb):
        err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        logger.error("Error en callback de interfaz gráfica:\n%s", err_msg)
        try:
            messagebox.showerror(
                "Error de operación",
                f"Ocurrió un problema al procesar la acción:\n\n{exc_value}\n\nRevisa turnos.log para más información.",
                parent=app
            )
        except Exception:
            pass

    app.report_callback_exception = tk_exception_handler
    app.mainloop()

if __name__ == "__main__":
    main()
