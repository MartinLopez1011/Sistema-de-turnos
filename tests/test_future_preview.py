import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from controllers.main_controller import MainController


class FuturePreviewChainingTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root_path = Path(self.temp_dir.name)
        self.config_path = self.root_path / "config.json"

        self.personal = [
            {"id": 1, "nombre": "P1"},
            {"id": 2, "nombre": "P2"},
            {"id": 3, "nombre": "P3"},
            {"id": 4, "nombre": "P4"},
        ]
        # Supongamos que estamos en el año 2099 para asegurar que sea siempre futuro
        self.future_year = 2099
        self.config_data = {
            "personal": self.personal,
            "inicio": {},
            "historial": {},
            "siguiente_id": 1,
            "pendientes": [],
            "snapshots": {},
            "excepciones": {
                # P1 tiene excepción en la primera semana de octubre 2099
                f"{self.future_year}-10": [
                    {"persona": "P1", "fecha": f"{self.future_year}-10-01", "tipo": "DA"}
                ]
            }
        }
        self.config_path.write_text(json.dumps(self.config_data), encoding="utf-8")
        self.controller = MainController(str(self.root_path))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_preview_loads_saved_intermediate_exceptions(self):
        # Al proyectar noviembre 2099, el cálculo pasa por octubre 2099.
        # Las excepciones guardadas de octubre deben ser consideradas.
        shifts_nov = self.controller.preview_shifts(self.future_year, 11, [])
        self.assertTrue(len(shifts_nov) > 0)

        # Si octubre consideró la excepción de P1, P1 quedó en pendientes o fue saltado,
        # lo que altera la cola respecto a si octubre no hubiera tenido excepciones.
        saved_oct_exc = self.controller.shift_manager.get_exceptions(f"{self.future_year}-10")
        self.assertEqual(len(saved_oct_exc), 1)
        self.assertEqual(saved_oct_exc[0]["persona"], "P1")


if __name__ == "__main__":
    unittest.main()
