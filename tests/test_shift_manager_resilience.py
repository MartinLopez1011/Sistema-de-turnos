import json
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

from models.shift_manager import ShiftManager
from controllers.main_controller import MainController


class ShiftManagerResilienceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root_path = Path(self.temp_dir.name)
        self.config_path = self.root_path / "config.json"

        self.personal = [
            {"id": 1, "nombre": "SGT (F) PEREZ JUAN"},
            {"id": 2, "nombre": "CBO (M) GOMEZ ANA"},
            {"id": 3, "nombre": "CBO (F) DIAZ LUIS"},
            {"id": 4, "nombre": "SBC (M) SILVA MARIA"},
        ]
        self.data = {
            "personal": self.personal,
            "inicio": {},
            "historial": {},
            "siguiente_id": 1,
            "pendientes": [],
            "snapshots": {},
            "excepciones": {},
        }
        self.config_path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
        self.manager = ShiftManager(str(self.config_path))
        self.controller = MainController(str(self.root_path))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_config_creates_clean_file_when_missing(self):
        missing_config = self.root_path / "subdir" / "new_config.json"
        self.assertFalse(missing_config.exists())

        mgr = ShiftManager(str(missing_config))
        self.assertTrue(missing_config.exists())
        self.assertEqual(mgr.personal, [])
        self.assertEqual(mgr.siguiente_id, 1)
        self.assertEqual(mgr.pendientes, [])

    def test_load_config_backs_up_and_recovers_from_corrupted_json(self):
        corrupt_config = self.root_path / "corrupt_config.json"
        corrupt_config.write_text("{ this is completely invalid json [[]] ", encoding="utf-8")

        mgr = ShiftManager(str(corrupt_config))
        # Manager starts up cleanly without crashing
        self.assertEqual(mgr.personal, [])
        self.assertEqual(mgr.siguiente_id, 1)

        # A backup of the corrupted file must exist in backups directory
        backups_dir = self.root_path / "backups"
        self.assertTrue(backups_dir.exists())
        corrupt_backups = list(backups_dir.glob("corrupt_config.json.corrupted_*"))
        self.assertGreaterEqual(len(corrupt_backups), 1)

        with open(corrupt_backups[0], "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("completely invalid json", content)

    def test_advance_past_month_preserves_current_operational_queue(self):
        # 1. Avanzar Abril 2024
        self.manager.advance_month(2024, 4, [])
        # 2. Avanzar Mayo 2024
        self.manager.advance_month(2024, 5, [])

        present_siguiente_id = self.manager.siguiente_id
        present_pendientes = self.manager.pendientes.copy()

        # 3. Guardar retroactivamente Marzo 2024 (un mes previo al frente)
        exc_marzo = [{"persona": "CBO (M) GOMEZ ANA", "fecha": date(2024, 3, 15), "tipo": "DA"}]
        self.manager.advance_month(2024, 3, exc_marzo)

        # El puntero del presente NO debe alterarse
        self.assertEqual(self.manager.siguiente_id, present_siguiente_id)
        self.assertEqual(self.manager.pendientes, present_pendientes)

        # El historial y la excepción de Marzo deben haberse registrado
        self.assertIn("2024-03", self.manager.excepciones)
        self.assertEqual(len(self.manager.excepciones["2024-03"]), 1)
        self.assertIn("2024-04", self.manager.snapshots)

    def test_model_edit_person_validations(self):
        # Rechazar tipos inválidos o nombres vacíos / solo espacios
        self.assertFalse(self.manager.edit_person(1, ""))
        self.assertFalse(self.manager.edit_person(1, "   "))
        self.assertFalse(self.manager.edit_person(1, None))
        self.assertFalse(self.manager.edit_person(1, 12345))

        # Rechazar duplicado con otra persona existente (ignorando mayúsculas y espacios extra)
        self.assertFalse(self.manager.edit_person(1, "cbo (m) gomez ana"))
        self.assertFalse(self.manager.edit_person(1, "  CBO (M)   GOMEZ ANA  "))

        # Permitir modificar a la misma persona (mismo ID)
        self.assertTrue(self.manager.edit_person(1, "SGT (F) PEREZ JUAN"))
        self.assertTrue(self.manager.edit_person(1, "  sgt (f) perez juan  "))

        # Permitir renombrar a un nombre válido nuevo
        self.assertTrue(self.manager.edit_person(1, "SGT (F) PEREZ GONZALEZ JUAN"))
        self.assertEqual(self.manager.get_person_by_id(1), "SGT (F) PEREZ GONZALEZ JUAN")

    def test_controller_edit_and_add_person_feedback(self):
        # Validación de nombre vacío en controlador
        ok_edit, msg_edit = self.controller.edit_person(1, "   ")
        self.assertFalse(ok_edit)
        self.assertEqual(msg_edit, "El nombre no puede estar vacío")

        # Validación de duplicado en controlador al editar
        ok_edit, msg_edit = self.controller.edit_person(1, "CBO (M) GOMEZ ANA")
        self.assertFalse(ok_edit)
        self.assertIn("Ya existe un funcionario", msg_edit)

        # Edición exitosa
        ok_edit, msg_edit = self.controller.edit_person(1, "SGT (F) PEREZ ACTUALIZADO")
        self.assertTrue(ok_edit)
        self.assertIn("Funcionario editado", msg_edit)

        # Validación de nombre vacío en controlador al agregar
        ok_add, msg_add = self.controller.add_person("   ")
        self.assertFalse(ok_add)
        self.assertEqual(msg_add, "El nombre no puede estar vacío")

        # Validación de duplicado en controlador al agregar
        ok_add, msg_add = self.controller.add_person("cbo (m) gomez ana")
        self.assertFalse(ok_add)
        self.assertIn("Ya existe un funcionario", msg_add)
