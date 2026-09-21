import json
import os
import tempfile
import unittest
from pathlib import Path

from models.shift_manager import ShiftManager


class ShiftManagerBackupAndResetTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "config.json"

        self.personal = [
            {"id": 1, "nombre": "PERSONA UNO"},
            {"id": 2, "nombre": "PERSONA DOS"},
            {"id": 3, "nombre": "PERSONA TRES"},
        ]
        self.inicio = {
            "2026-08-03_2026-08-09": "PERSONA UNO",
            "2026-08-10_2026-08-16": "PERSONA DOS",
        }
        self.historial = {
            "2026-08-17_2026-08-23": "PERSONA TRES",
            "2026-08-24_2026-08-30": "PERSONA UNO",
        }
        self.data = {
            "personal": self.personal,
            "inicio": self.inicio,
            "historial": self.historial,
            "siguiente_id": 2,
            "pendientes": [1],
            "snapshots": {"2026-09": {"siguiente_id": 2, "pendientes": [1]}},
            "excepciones": {"2026-09": [{"persona": "PERSONA UNO", "fecha": "2026-09-07", "tipo": "DA"}]},
        }
        self.config_path.write_text(json.dumps(self.data), encoding="utf-8")
        self.manager = ShiftManager(str(self.config_path))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_backup_creates_file_in_backups_dir(self):
        backup_path = self.manager.create_backup("test_tag")
        self.assertIsNotNone(backup_path)
        self.assertTrue(os.path.exists(backup_path))
        self.assertIn("backups", backup_path)
        self.assertIn("test_tag", backup_path)

        with open(backup_path, "r", encoding="utf-8") as f:
            backup_data = json.load(f)
        self.assertEqual(backup_data["personal"], self.personal)
        self.assertEqual(backup_data["inicio"], self.inicio)

    def test_reset_historial_preserves_inicio_by_default(self):
        result = self.manager.reset_historial()
        self.assertTrue(result)

        # inicio debe preservarse
        self.assertEqual(self.manager.inicio, self.inicio)
        # historial, snapshots, pendientes, excepciones deben limpiarse
        self.assertEqual(self.manager.historial, {})
        self.assertEqual(self.manager.snapshots, {})
        self.assertEqual(self.manager.pendientes, [])
        self.assertEqual(self.manager.excepciones, {})

        # siguiente_id debe continuar después de la última persona en 'inicio' (PERSONA DOS -> id 2 -> siguiente es id 3)
        self.assertEqual(self.manager.siguiente_id, 3)

        # Se debe haber generado un backup
        backups_dir = Path(self.temp_dir.name) / "backups"
        self.assertTrue(backups_dir.exists())
        backups = list(backups_dir.glob("config_*pre_reset.json"))
        self.assertGreaterEqual(len(backups), 1)

    def test_reset_historial_can_wipe_inicio_when_explicitly_requested(self):
        result = self.manager.reset_historial(preserve_inicio=False)
        self.assertTrue(result)
        self.assertEqual(self.manager.inicio, {})
        self.assertEqual(self.manager.historial, {})
        # Al no haber inicio, empieza por el primer funcionario
        self.assertEqual(self.manager.siguiente_id, 1)


if __name__ == "__main__":
    unittest.main()
