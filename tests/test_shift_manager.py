import json
import tempfile
import unittest
import sys
import os
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.shift_manager import ShiftManager


class ShiftManagerHolidayTests(unittest.TestCase):
    def create_manager(self, historial=None):
        personal = [
            {"id": index, "nombre": f"P{index}"}
            for index in range(1, 6)
        ]
        data = {
            "personal": personal,
            "inicio": {},
            "historial": historial or {},
            "siguiente_id": 1,
            "pendientes": [],
            "snapshots": {},
            "excepciones": {},
        }
        temp_dir = tempfile.TemporaryDirectory()
        config_path = Path(temp_dir.name) / "config.json"
        config_path.write_text(json.dumps(data), encoding="utf-8")
        manager = ShiftManager(str(config_path))
        self.addCleanup(temp_dir.cleanup)
        return manager

    def test_previous_holiday_person_is_avoided_when_possible(self):
        manager = self.create_manager({"2025-12-22_2025-12-28": "P4"})

        shifts, _, _ = manager.generate_shifts(2026, 12, [])

        christmas_week = next(
            shift for shift in shifts
            if shift["semana"][0] == date(2026, 12, 21)
        )
        self.assertNotEqual(christmas_week["persona"], "P4")
        self.assertEqual(manager.last_warnings, [])

    def test_without_previous_history_rule_is_not_applied(self):
        manager = self.create_manager()

        shifts, _, _ = manager.generate_shifts(2026, 12, [])

        christmas_week = next(
            shift for shift in shifts
            if shift["semana"][0] == date(2026, 12, 21)
        )
        self.assertEqual(christmas_week["persona"], "P4")
        self.assertEqual(manager.last_warnings, [])

    def test_warning_is_generated_when_all_other_people_are_unavailable(self):
        manager = self.create_manager({"2025-12-22_2025-12-28": "P1"})
        manager.personal = manager.personal[:3]

        shifts, _, _ = manager.generate_shifts(2026, 12, [])

        christmas_week = next(
            shift for shift in shifts
            if shift["semana"][0] == date(2026, 12, 21)
        )
        self.assertEqual(christmas_week["persona"], "P1")
        self.assertTrue(christmas_week["advertencias"])
        self.assertEqual(len(manager.last_warnings), 1)
        self.assertIn("Navidad", manager.last_warnings[0]["feriados"])

    def test_mobile_holiday_viernes_santo(self):
        # Viernes Santo cae el 18 de Abril en 2025 (semana del 14 al 20)
        # y el 3 de Abril en 2026 (semana del 30 de marzo al 5 de abril).
        # Simulamos que P4 trabajó la semana de Viernes Santo en 2025.
        manager = self.create_manager({"2025-04-14_2025-04-20": "P4"})

        # Generamos los turnos para Abril de 2026
        shifts, _, _ = manager.generate_shifts(2026, 4, [])

        viernes_santo_week = next(
            shift for shift in shifts
            if shift["semana"][0] == date(2026, 3, 30)
        )
        # P4 debería ser evitado para esta semana en 2026, a pesar de caer en
        # una semana distinta del mes y en fechas diferentes, porque el sistema
        # detecta que P4 ya trabajó el feriado de "Viernes Santo" el año anterior.
        self.assertNotEqual(viernes_santo_week["persona"], "P4")
        self.assertEqual(manager.last_warnings, [])

if __name__ == "__main__":
    unittest.main()
