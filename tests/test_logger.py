import os
import tempfile
import unittest
from pathlib import Path

from utils.logger import setup_logger, get_logger


class LoggerHierarchyTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = Path(self.temp_dir.name) / "test_turnos.log"

    def tearDown(self):
        # Restaurar logger base
        setup_logger(name="turnos", log_filename="turnos.log", force_reinit=True)
        self.temp_dir.cleanup()

    def test_child_loggers_propagate_to_file(self):
        # Inicializar logger base apuntando al archivo temporal aislado
        base_logger = setup_logger(name="turnos", log_filename=str(self.log_file), force_reinit=True)

        controller_logger = get_logger("controller")
        shift_manager_logger = get_logger("shift_manager")
        gui_logger = get_logger("gui")

        controller_logger.info("Mensaje desde controller")
        shift_manager_logger.info("Mensaje desde shift_manager")
        gui_logger.info("Mensaje desde gui")

        # Forzar flush de handlers
        for h in base_logger.handlers:
            h.flush()

        self.assertTrue(self.log_file.exists())
        content = self.log_file.read_text(encoding="utf-8")

        self.assertIn("turnos.controller: Mensaje desde controller", content)
        self.assertIn("turnos.shift_manager: Mensaje desde shift_manager", content)
        self.assertIn("turnos.gui: Mensaje desde gui", content)


if __name__ == "__main__":
    unittest.main()
