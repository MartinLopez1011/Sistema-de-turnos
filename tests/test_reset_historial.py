import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reset_historial import resetear_historial


class ResetHistorialScriptTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "config.json"

        data = {
            "personal": [
                {"id": 4, "nombre": "P_CUATRO"},
                {"id": 16, "nombre": "P_DIECISEIS"},
            ],
            "inicio": {
                "2026-08-03_2026-08-09": "P_CUATRO",
                "2026-08-10_2026-08-16": "P_DIECISEIS",
            },
            "historial": {
                "2026-08-17_2026-08-23": "P_CUATRO"
            },
            "siguiente_id": 4,
            "pendientes": [16],
            "snapshots": {"2026-09": {"siguiente_id": 4, "pendientes": [16]}},
            "excepciones": {"2026-09": []},
        }
        self.config_path.write_text(json.dumps(data), encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_resetear_historial_delegates_safely(self):
        with patch("reset_historial.os.path.dirname", return_value=self.temp_dir.name):
            success = resetear_historial()

        self.assertTrue(success)

        with open(self.config_path, "r", encoding="utf-8") as f:
            updated = json.load(f)

        # Historial y snapshots limpiados
        self.assertEqual(updated["historial"], {})
        self.assertEqual(updated["snapshots"], {})
        self.assertEqual(updated["pendientes"], [])

        # Siguiente_id debe ser 4 (la siguiente después de P_DIECISEIS en orden circular de personal [4, 16])
        self.assertEqual(updated["siguiente_id"], 4)

        # Inicio preservado
        self.assertIn("2026-08-03_2026-08-09", updated["inicio"])


if __name__ == "__main__":
    unittest.main()
