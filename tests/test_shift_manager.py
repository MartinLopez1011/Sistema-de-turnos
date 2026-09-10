import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

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

    def test_previous_december_holiday_person_is_avoided_when_possible(self):
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


if __name__ == "__main__":
    unittest.main()
