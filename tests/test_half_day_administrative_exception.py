import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
import openpyxl

from utils.config_validator import validate_config, VALID_EXCEPTION_TYPES
from utils.excel_handler import ExcelHandler
from models.shift_manager import ShiftManager
from views.theme import EXC_COLORS, EXC_ICONS, P


class HalfDayAdministrativeExceptionTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = self.temp_dir.name
        self.output_path = Path(self.temp_dir.name) / "test_turnos_mda.xlsx"
        self.personal = [
            {"id": 1, "nombre": "COM ALARCON JOSE"},
            {"id": 2, "nombre": "PRO BRAVO PATRICIO"},
        ]

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_config_validator_accepts_1_2da(self):
        self.assertIn("1/2DA", VALID_EXCEPTION_TYPES)
        config_data = {
            "personal": [{"id": 1, "nombre": "TEST PERSON"}],
            "siguiente_id": 1,
            "pendientes": [],
            "excepciones": {
                "2026-10": [
                    {"persona": "TEST PERSON", "fecha": "2026-10-15", "tipo": "1/2DA"}
                ]
            }
        }
        errors = validate_config(config_data)
        self.assertEqual(errors, [])

    def test_theme_contains_1_2da_color_and_icon(self):
        self.assertIn("1/2DA", EXC_COLORS)
        self.assertIn("1/2DA", EXC_ICONS)
        self.assertEqual(EXC_COLORS["1/2DA"], P["mda"])
        self.assertEqual(EXC_ICONS["1/2DA"], "🌗")

    def test_excel_cell_fill_and_totals_calculation_for_1_2da(self):
        handler = ExcelHandler(str(self.output_path), self.personal)
        handler.load_template()

        shifts = [
            {
                "semana": (date(2026, 9, 7), date(2026, 9, 13)),
                "persona": "COM ALARCON JOSE",
                "saltados": [],
            }
        ]
        exceptions = [
            # ALARCON has 1 DA and 1 1/2DA -> should sum to 1.5 in col 34
            {"persona": "COM ALARCON JOSE", "fecha": date(2026, 9, 1), "tipo": "DA"},
            {"persona": "COM ALARCON JOSE", "fecha": date(2026, 9, 2), "tipo": "1/2DA"},
            # BRAVO has 2 1/2DA -> should sum to 1.0 (rendered as int 1) in col 34
            {"persona": "PRO BRAVO PATRICIO", "fecha": date(2026, 9, 15), "tipo": "1/2DA"},
            {"persona": "PRO BRAVO PATRICIO", "fecha": date(2026, 9, 16), "tipo": "1/2DA"},
        ]

        handler.write_shifts(shifts, exceptions, year=2026, month=9)
        handler.save_report()
        handler.close()

        self.assertTrue(self.output_path.exists())
        wb = openpyxl.load_workbook(self.output_path)
        sheet = wb["Turnos"]

        # Day 2 for ALARCON (row 4, col 3) has value '1/2DA'
        cell_mda = sheet.cell(row=4, column=3)
        self.assertEqual(cell_mda.value, "1/2DA")

        # Totals col 34 (AH):
        # Row 4 (ALARCON): 1 DA + 1 1/2DA = 1.5
        tot_alarcon = sheet.cell(row=4, column=34).value
        self.assertEqual(tot_alarcon, 1.5)

        # Row 5 (BRAVO): 2 1/2DA = 1
        tot_bravo = sheet.cell(row=5, column=34).value
        self.assertEqual(tot_bravo, 1)

        # Verify legend includes 1/2DA
        legend_found = False
        for row in range(5, sheet.max_row + 1):
            val = sheet.cell(row=row, column=3).value
            if val and "1/2DA" in str(val):
                legend_found = True
                break
        self.assertTrue(legend_found, "Legend entry for 1/2DA was not found in Excel")
        wb.close()

    def test_shift_manager_skips_person_with_1_2da_in_shift_week(self):
        config_path = str(Path(self.data_dir) / "config.json")
        manager = ShiftManager(config_path)
        manager.personal = [
            {"id": 1, "nombre": "PERSONA UNO"},
            {"id": 2, "nombre": "PERSONA DOS"},
        ]
        manager.siguiente_id = 1
        manager.pendientes = []
        manager.inicio = {}
        manager.historial = {}
        manager.excepciones = {
            "2026-10": [
                {"persona": "PERSONA UNO", "fecha": "2026-10-06", "tipo": "1/2DA"}
            ]
        }
        manager.save_config()

        # Preview October 2026 shifts
        # First week of October 2026 includes 2026-10-01.
        # PERSONA UNO has 1/2DA on 2026-10-01, so PERSONA UNO must be skipped in week 1 and PERSONA DOS assigned.
        exceptions = [{"persona": "PERSONA UNO", "fecha": date(2026, 10, 1), "tipo": "1/2DA"}]
        shifts, final_id, new_pendientes = manager.generate_shifts(2026, 10, exceptions)
        self.assertTrue(len(shifts) > 0)
        first_shift = shifts[0]
        self.assertEqual(first_shift["persona"], "PERSONA DOS")
        self.assertTrue(any(s["persona"] == "PERSONA UNO" and s["tipo"] == "1/2DA" for s in first_shift["saltados"]))
        # In a subsequent week, PERSONA UNO recovers the turn from pendientes
        self.assertTrue(any(sh["persona"] == "PERSONA UNO" for sh in shifts[1:]))


if __name__ == "__main__":
    unittest.main()
