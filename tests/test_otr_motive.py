import unittest
import tempfile
import os
import json
from datetime import date
from unittest.mock import MagicMock, patch

from utils.config_validator import validate_config
from models.shift_manager import ShiftManager
from utils.excel_handler import ExcelHandler
from views.tabs.tab_plan import TabPlan
from views.components.dialogs import AddExceptionDialog, PromptOTRMotiveDialog


class OTRMotiveUnitTests(unittest.TestCase):
    def test_config_validator_allows_valid_motivo(self):
        data = {
            "personal": [{"id": 1, "nombre": "PERSONA UNO"}],
            "inicio": {"2026-08-31_2026-09-06": "PERSONA UNO"},
            "siguiente_id": 1,
            "pendientes": [],
            "excepciones": {
                "2026-09": [
                    {"persona": "PERSONA UNO", "fecha": "2026-09-05", "tipo": "OTR", "motivo": "Comisión de servicio"}
                ]
            }
        }
        errors = validate_config(data)
        self.assertEqual(errors, [])

    def test_config_validator_rejects_non_string_motivo(self):
        data = {
            "personal": [{"id": 1, "nombre": "PERSONA UNO"}],
            "inicio": {"2026-08-31_2026-09-06": "PERSONA UNO"},
            "siguiente_id": 1,
            "pendientes": [],
            "excepciones": {
                "2026-09": [
                    {"persona": "PERSONA UNO", "fecha": "2026-09-05", "tipo": "OTR", "motivo": 12345}
                ]
            }
        }
        errors = validate_config(data)
        self.assertTrue(any("Motivo de excepción inválido" in e for e in errors))

    def test_shift_manager_preserves_motivo_in_get_and_normalize(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as f:
            cfg = {
                "personal": [{"id": 1, "nombre": "PERSONA UNO"}],
                "inicio": {"2026-08-31_2026-09-06": "PERSONA UNO"},
                "siguiente_id": 1,
                "pendientes": [],
                "excepciones": {
                    "2026-09": [
                        {"persona": "PERSONA UNO", "fecha": "2026-09-05", "tipo": "OTR", "motivo": "Capacitación"}
                    ]
                }
            }
            json.dump(cfg, f)
            cfg_path = f.name

        try:
            sm = ShiftManager(cfg_path)
            excs = sm.get_exceptions("2026-09")
            self.assertEqual(len(excs), 1)
            self.assertEqual(excs[0]["motivo"], "Capacitación")

            normalized = sm._normalize_exceptions(excs)
            self.assertEqual(normalized[0]["motivo"], "Capacitación")
        finally:
            if os.path.exists(cfg_path):
                os.remove(cfg_path)

    def test_shift_manager_advance_month_saves_motivo(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as f:
            cfg = {
                "personal": [{"id": 1, "nombre": "PERSONA UNO"}],
                "inicio": {"2026-08-31_2026-09-06": "PERSONA UNO"},
                "siguiente_id": 1,
                "pendientes": [],
                "excepciones": {}
            }
            json.dump(cfg, f)
            cfg_path = f.name

        try:
            sm = ShiftManager(cfg_path)
            excs = [
                {"persona": "PERSONA UNO", "fecha": date(2026, 9, 10), "tipo": "OTR", "motivo": "Duelo institucional"}
            ]
            sm.advance_month(2026, 9, excs)
            saved = sm.excepciones["2026-09"]
            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0]["tipo"], "OTR")
            self.assertEqual(saved[0]["motivo"], "Duelo institucional")
        finally:
            if os.path.exists(cfg_path):
                os.remove(cfg_path)

    def test_excel_handler_writes_comment_for_otr_with_motivo(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".xlsx") as f:
            xlsx_path = f.name

        try:
            personal = [{"id": 1, "nombre": "COM PEREZ JUAN"}]
            handler = ExcelHandler(xlsx_path, personal)
            handler.load_template()

            exceptions = [
                {"persona": "COM PEREZ JUAN", "fecha": date(2026, 9, 15), "tipo": "OTR", "motivo": "Comisión de servicio"},
                {"persona": "COM PEREZ JUAN", "fecha": date(2026, 9, 16), "tipo": "DA"}
            ]
            shifts = []
            handler.write_shifts(shifts, exceptions, 2026, 9)

            # En la fila de COM PEREZ JUAN (fila 4): día 15 (col 16) debe tener comentario, día 16 (col 17) no
            day_15_cell = handler.sheet.cell(row=4, column=16)
            day_16_cell = handler.sheet.cell(row=4, column=17)

            self.assertEqual(day_15_cell.value, "OTR")
            self.assertIsNotNone(day_15_cell.comment)
            self.assertIn("Comisión de servicio", day_15_cell.comment.text)

            self.assertEqual(day_16_cell.value, "DA")
            self.assertIsNone(day_16_cell.comment)
        finally:
            if os.path.exists(xlsx_path):
                os.remove(xlsx_path)

    def test_excel_handler_writes_otr_detail_table(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".xlsx") as f:
            xlsx_path = f.name

        try:
            personal = [{"id": 1, "nombre": "COM PEREZ JUAN"}]
            handler = ExcelHandler(xlsx_path, personal)
            handler.load_template()

            exceptions = [
                {"persona": "COM PEREZ JUAN", "fecha": date(2026, 9, 1), "tipo": "OTR", "motivo": "Comisión de servicio"},
                {"persona": "COM PEREZ JUAN", "fecha": date(2026, 9, 2), "tipo": "OTR", "motivo": "Comisión de servicio"},
                {"persona": "COM PEREZ JUAN", "fecha": date(2026, 9, 3), "tipo": "OTR", "motivo": "Comisión de servicio"},
                {"persona": "COM PEREZ JUAN", "fecha": date(2026, 9, 15), "tipo": "OTR", "motivo": "Duelo institucional"},
            ]
            shifts = []
            handler.write_shifts(shifts, exceptions, 2026, 9)

            all_values = [
                str(cell.value)
                for row in handler.sheet.iter_rows()
                for cell in row
                if cell.value is not None
            ]

            self.assertTrue(any("DETALLE DE PERMISOS Y EXCEPCIONES ESPECIALES (OTR)" in v for v in all_values))
            self.assertTrue(any("01/09 al 03/09" in v for v in all_values))
            self.assertTrue(any("15/09" in v for v in all_values))
            self.assertTrue(any("Comisión de servicio" in v for v in all_values))
            self.assertTrue(any("Duelo institucional" in v for v in all_values))
        finally:
            if os.path.exists(xlsx_path):
                os.remove(xlsx_path)

    def test_tab_plan_rejects_otr_without_motivo(self):
        mock_app = MagicMock()
        mock_app.get_selected_period.return_value = (2026, 9)
        mock_app.exceptions = []

        tab = TabPlan.__new__(TabPlan)
        tab.app = mock_app
        tab.person_var = MagicMock()
        tab.person_var.get.return_value = "COM PEREZ JUAN"
        tab.type_var = MagicMock()
        tab.type_var.get.return_value = "OTR"
        tab.days_entry = MagicMock()
        tab.days_entry.get.return_value = "5"
        tab.reason_frame = MagicMock()
        tab.reason_entry = MagicMock()
        tab.reason_entry.get.return_value = "  "  # Vacío / espacios

        tab.add_exception()

        # No debe haber llamado a add_exceptions
        mock_app.add_exceptions.assert_not_called()
        mock_app.set_status.assert_called_with(
            "Para la excepción 'OTR', debes ingresar un motivo válido (mínimo 3 caracteres).",
            "error"
        )

    def test_tab_plan_rejects_otr_with_short_motivo(self):
        mock_app = MagicMock()
        mock_app.get_selected_period.return_value = (2026, 9)
        mock_app.exceptions = []

        tab = TabPlan.__new__(TabPlan)
        tab.app = mock_app
        tab.person_var = MagicMock()
        tab.person_var.get.return_value = "COM PEREZ JUAN"
        tab.type_var = MagicMock()
        tab.type_var.get.return_value = "OTR"
        tab.days_entry = MagicMock()
        tab.days_entry.get.return_value = "5"
        tab.reason_frame = MagicMock()
        tab.reason_entry = MagicMock()
        tab.reason_entry.get.return_value = "ab"  # solo 2 caracteres

        tab.add_exception()

        mock_app.add_exceptions.assert_not_called()
        mock_app.set_status.assert_called_with(
            "Para la excepción 'OTR', debes ingresar un motivo válido (mínimo 3 caracteres).",
            "error"
        )

    def test_tab_plan_accepts_otr_with_valid_motivo_and_applies_to_range(self):
        mock_app = MagicMock()
        mock_app.get_selected_period.return_value = (2026, 9)
        mock_app.exceptions = []

        tab = TabPlan.__new__(TabPlan)
        tab.app = mock_app
        tab.person_var = MagicMock()
        tab.person_var.get.return_value = "COM PEREZ JUAN"
        tab.type_var = MagicMock()
        tab.type_var.get.return_value = "OTR"
        tab.days_entry = MagicMock()
        tab.days_entry.get.return_value = "1-3"
        tab.reason_frame = MagicMock()
        tab.reason_entry = MagicMock()
        tab.reason_entry.get.return_value = "Comisión de servicio"

        tab.add_exception()

        mock_app.add_exceptions.assert_called_once()
        added = mock_app.add_exceptions.call_args[0][0]
        self.assertEqual(len(added), 3)
        for item in added:
            self.assertEqual(item["tipo"], "OTR")
            self.assertEqual(item["motivo"], "Comisión de servicio")
            self.assertEqual(item["persona"], "COM PEREZ JUAN")

    def test_tab_plan_type_changed_toggles_reason_frame(self):
        tab = TabPlan.__new__(TabPlan)
        tab.type_var = MagicMock()
        tab.reason_frame = MagicMock()
        tab.reason_entry = MagicMock()

        # Cuando es OTR -> grid
        tab._on_type_changed("OTR")
        tab.reason_frame.grid.assert_called_with(row=3, column=0, sticky="ew")

        # Cuando es DA -> grid_forget
        tab._on_type_changed("DA")
        tab.reason_frame.grid_forget.assert_called_once()

    def test_add_exception_dialog_prompts_motivo_on_otr(self):
        callback = MagicMock()
        parent = MagicMock()

        with patch.object(PromptOTRMotiveDialog, "show", return_value="Permiso especial"):
            def dummy_callback(tipo, motivo=""):
                callback(tipo, motivo)

            motivo = PromptOTRMotiveDialog.show(parent, "COM PEREZ JUAN", 10)
            dummy_callback("OTR", motivo)

            callback.assert_called_once_with("OTR", "Permiso especial")


if __name__ == "__main__":
    unittest.main()
