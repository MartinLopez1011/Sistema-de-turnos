import unittest
import os
import json
import tempfile
from datetime import date
from models.shift_manager import ShiftManager
from controllers.main_controller import MainController

class TestManualAssignments(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, "config.json")
        self.initial_data = {
            "personal": [
                {"id": 1, "nombre": "Alice"},
                {"id": 2, "nombre": "Bob"},
                {"id": 3, "nombre": "Charlie"},
                {"id": 4, "nombre": "David"},
                {"id": 5, "nombre": "Eve"},
                {"id": 6, "nombre": "Frank"},
                {"id": 7, "nombre": "Grace"},
                {"id": 8, "nombre": "Heidi"}
            ],
            "historial": {},
            "pendientes": [],
            "siguiente_id": 1,
            "asignaciones_manuales": {}
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.initial_data, f)
        self.controller = MainController(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_manual_assignment_overrides_preview(self):
        # Generar turnos para 2026-10 sin manual
        shifts_auto = self.controller.preview_shifts(2026, 10, [])
        first_week = shifts_auto[0]
        s_date, e_date = first_week['semana']
        week_key = f"{s_date.strftime('%Y-%m-%d')}_{e_date.strftime('%Y-%m-%d')}"
        auto_person = first_week['persona']

        # Asignar manualmente a alguien que no sea auto_person
        override_person = "Alice" if auto_person != "Alice" else "Bob"
        self.assertNotEqual(auto_person, override_person)

        shifts_manual = self.controller.preview_shifts(
            2026, 10, [], manual_assignments={week_key: override_person}
        )
        self.assertEqual(shifts_manual[0]['persona'], override_person)
        self.assertTrue(shifts_manual[0].get('es_manual'))

    def test_clearing_manual_assignment_reverts_to_auto(self):
        shifts_auto = self.controller.preview_shifts(2026, 10, [])
        first_week = shifts_auto[0]
        s_date, e_date = first_week['semana']
        week_key = f"{s_date.strftime('%Y-%m-%d')}_{e_date.strftime('%Y-%m-%d')}"
        auto_person = first_week['persona']
        override_person = "Alice" if auto_person != "Alice" else "Bob"

        # Con manual
        shifts_manual = self.controller.preview_shifts(
            2026, 10, [], manual_assignments={week_key: override_person}
        )
        self.assertEqual(shifts_manual[0]['persona'], override_person)

        # Sin manual (revertido)
        shifts_reverted = self.controller.preview_shifts(
            2026, 10, [], manual_assignments={}
        )
        self.assertEqual(shifts_reverted[0]['persona'], auto_person)
        self.assertFalse(shifts_reverted[0].get('es_manual', False))

    def test_advance_queue_persists_manual_assignments(self):
        shifts_auto = self.controller.preview_shifts(2026, 10, [])
        first_week = shifts_auto[0]
        s_date, e_date = first_week['semana']
        week_key = f"{s_date.strftime('%Y-%m-%d')}_{e_date.strftime('%Y-%m-%d')}"

        manual_dict = {week_key: "Charlie"}
        # Avanzar cola guardando mes con manual_assignments
        self.controller.advance_queue(2026, 10, [], manual_assignments=manual_dict)

        # Verificar que shift_manager tiene la asignación manual guardada
        saved = self.controller.get_saved_manual_assignments()
        self.assertIn("2026-10", saved)
        self.assertEqual(saved["2026-10"].get(week_key), "Charlie")

        # Verificar persistencia en archivo JSON
        with open(self.config_path, "r", encoding="utf-8") as f:
            persisted_data = json.load(f)
        self.assertIn("asignaciones_manuales", persisted_data)
        self.assertEqual(persisted_data["asignaciones_manuales"]["2026-10"][week_key], "Charlie")

    def test_legacy_for_exception_still_works_as_fallback(self):
        # Simular una excepción FOR legacy
        for_exception = [{'persona': 'Eve', 'fecha': date(2026, 10, 6), 'tipo': 'FOR'}]
        shifts = self.controller.preview_shifts(2026, 10, for_exception)
        
        # Debe haber asignado a Eve en esa semana
        matched_shift = next((sh for sh in shifts if sh['persona'] == 'Eve'), None)
        self.assertIsNotNone(matched_shift)
        self.assertTrue(matched_shift.get('es_forzado'))

if __name__ == '__main__':
    unittest.main()
