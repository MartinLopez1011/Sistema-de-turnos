import os
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import openpyxl

from models.shift_manager import ShiftManager
from controllers.main_controller import MainController
from utils.excel_handler import ExcelHandler
from views.components.widgets import _make_row_hover
from main import setup_global_exception_handler


class ImprovementsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root_path = Path(self.temp_dir.name)
        self.config_path = self.root_path / "config.json"
        self.output_excel = self.root_path / "test_excel_improvements.xlsx"

        self.personal = [
            {"id": 1, "nombre": "COM PEREZ JUAN"},
            {"id": 2, "nombre": "SGT GOMEZ ANA"},
        ]
        self.data = {
            "personal": self.personal,
            "inicio": {},
            "historial": {},
            "siguiente_id": 1,
            "pendientes": [],
            "snapshots": {},
            "excepciones": {},
            "asignaciones_manuales": {}
        }
        self.config_path.write_text(json.dumps(self.data), encoding="utf-8")
        self.manager = ShiftManager(str(self.config_path))
        self.controller = MainController(str(self.root_path))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_excel_weekdays_and_page_setup(self):
        handler = ExcelHandler(str(self.output_excel), self.personal)
        handler.load_template()

        # Verificar orientación apaisada y fit-to-page
        self.assertEqual(handler.sheet.page_setup.orientation, "landscape")
        self.assertEqual(handler.sheet.page_setup.fitToWidth, 1)
        self.assertEqual(handler.sheet.page_setup.fitToHeight, 0)
        self.assertTrue(handler.sheet.sheet_properties.pageSetUpPr.fitToPage)

        # Escribir turnos para Septiembre 2026 (1 de Septiembre de 2026 fue Martes -> "M")
        handler.write_shifts([], [], year=2026, month=9)
        handler.save_report()

        wb = openpyxl.load_workbook(str(self.output_excel))
        sheet = wb["Turnos"]

        # Fila 3, Columna 2 es el día 1 de Septiembre 2026 (Martes -> "M")
        day_1_letter = sheet.cell(row=3, column=2).value
        self.assertEqual(day_1_letter, "M")

        # Fila 3, Columna 3 es el día 2 de Septiembre 2026 (Miércoles -> "X")
        day_2_letter = sheet.cell(row=3, column=3).value
        self.assertEqual(day_2_letter, "X")

        # Fila 3, Columna 32 es el día 31 de Septiembre 2026 (no existe -> "-")
        day_31_letter = sheet.cell(row=3, column=32).value
        self.assertEqual(day_31_letter, "-")

    def test_excel_excludes_funcionario_header_from_person_rows(self):
        handler = ExcelHandler(str(self.output_excel), self.personal)
        handler.load_template()
        handler.write_shifts([], [], year=2026, month=9)

        # Verificar que A3 conserva 'FUNCIONARIO'
        self.assertEqual(handler.sheet.cell(row=3, column=1).value, "FUNCIONARIO")

    def test_exception_date_string_normalization(self):
        # Pasar excepciones con fecha como string ("2026-09-01") en vez de date
        exceptions = [
            {"persona": "COM PEREZ JUAN", "fecha": "2026-09-01", "tipo": "DA"}
        ]
        # No debe lanzar TypeError y debe procesar la excepción
        shifts, final_id, pendientes = self.manager.generate_shifts(2026, 9, exceptions)
        self.assertTrue(len(shifts) > 0)
        # La semana 1 (31 ago - 6 sep) le tocaba a Perez Juan, pero se salta por tener excepción el día 1
        week_1 = shifts[0]
        self.assertNotEqual(week_1['persona'], "COM PEREZ JUAN")
        self.assertEqual(week_1['persona'], "SGT GOMEZ ANA")
        self.assertTrue(any(s['persona'] == "COM PEREZ JUAN" for s in week_1['saltados']))

    def test_was_forced_recently_checks_manual_assignments(self):
        # Registrar una asignación manual en agosto 2026
        self.manager.asignaciones_manuales = {
            "2026-08": {
                "2026-08-10_2026-08-16": "COM PEREZ JUAN"
            }
        }
        # Evaluar si fue forzado/manual recientemente respecto al 24 de agosto de 2026 (dentro de 4 semanas)
        was_forced = self.manager._was_forced_recently("COM PEREZ JUAN", date(2026, 8, 24), [])
        self.assertTrue(was_forced)

        # Para otra persona debe dar False
        self.assertFalse(self.manager._was_forced_recently("SGT GOMEZ ANA", date(2026, 8, 24), []))

    def test_make_row_hover_supports_fg_color(self):
        # Simular widget CTkFrame (soporta fg_color) y tk.Frame (soporta bg)
        ctk_mock = MagicMock()
        ctk_mock.winfo_children.return_value = []
        ctk_mock.configure.side_effect = lambda **kwargs: None

        ref_mock = MagicMock()
        _make_row_hover(ref_mock, [(ctk_mock, "#1C2228")])
        # Verificar que se asociaron los eventos <Enter> y <Leave>
        self.assertTrue(ctk_mock.bind.called)

    def test_global_exception_handler_captures_exceptions(self):
        setup_global_exception_handler()
        import sys
        with patch("main.logger.critical") as mock_log, patch("main.messagebox.showerror") as mock_box:
            try:
                raise ValueError("Prueba de error no controlado")
            except ValueError as e:
                sys.excepthook(type(e), e, e.__traceback__)
                mock_log.assert_called_once()
                mock_box.assert_called_once()


if __name__ == "__main__":
    unittest.main()
