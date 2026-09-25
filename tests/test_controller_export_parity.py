import json
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import openpyxl

from controllers.main_controller import MainController
from utils.excel_handler import ExcelHandler


class ControllerExportParityTests(unittest.TestCase):
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
        self.future_year = 2099
        self.config_data = {
            "personal": self.personal,
            "inicio": {},
            "historial": {},
            "siguiente_id": 1,
            "pendientes": [],
            "snapshots": {},
            "excepciones": {
                f"{self.future_year}-10": [
                    {"persona": "P1", "fecha": f"{self.future_year}-10-01", "tipo": "DA"}
                ]
            }
        }
        self.config_path.write_text(json.dumps(self.config_data), encoding="utf-8")
        self.controller = MainController(str(self.root_path))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_process_generation_matches_preview_shifts_for_future_month(self):
        # Para el mes futuro 2099-11:
        # preview_shifts encadena el cálculo desde hoy pasando por 2099-10
        expected_shifts = self.controller.preview_shifts(self.future_year, 11, [])
        self.assertTrue(len(expected_shifts) > 0)

        output_file = self.root_path / "parity_test.xlsx"
        written_shifts_holder = []

        def spy_write_shifts(shifts, exceptions, year, month, *args, **kwargs):
            written_shifts_holder.extend(shifts)

        with patch.object(ExcelHandler, "write_shifts", side_effect=spy_write_shifts):
            ok, msg = self.controller.process_generation(
                self.future_year, 11, [], target_path=str(output_file)
            )

        self.assertTrue(ok, f"Export failed: {msg}")
        self.assertEqual(len(written_shifts_holder), len(expected_shifts))

        for written, expected in zip(written_shifts_holder, expected_shifts):
            self.assertEqual(written["semana"], expected["semana"])
            self.assertEqual(written["persona"], expected["persona"])


if __name__ == "__main__":
    unittest.main()
