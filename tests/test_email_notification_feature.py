import unittest
import os
import json
import tempfile
from models.shift_manager import ShiftManager
from controllers.main_controller import MainController


class TestEmailNotificationFeature(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, "config.json")
        self.initial_data = {
            "personal": [
                {"id": 1, "nombre": "Persona Uno", "email": "uno@correo.cl"},
                {"id": 2, "nombre": "Persona Dos", "email": "dos@correo.cl"},
                {"id": 3, "nombre": "Persona Tres"} # Sin correo inicialmente
            ],
            "inicio": {},
            "historial": {},
            "pendientes": [],
            "siguiente_id": 1,
            "asignaciones_manuales": {},
            "asignaciones_manuales_motivos": {},
            "notificaciones": {"webhook_url": "https://script.google.com/test", "activo": True}
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.initial_data, f)
        self.controller = MainController(self.temp_dir.name)
        self.manager = self.controller.shift_manager

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_email_sanitization_on_load(self):
        # Persona 3 no tenía 'email' en JSON inicial, debe sanearse a '' en memoria
        p3 = next(p for p in self.manager.personal if p['id'] == 3)
        self.assertEqual(p3['email'], "")

    def test_validate_all_emails_registered(self):
        # Inicialmente Persona 3 no tiene correo
        valido, faltantes = self.manager.validate_all_emails_registered()
        self.assertFalse(valido)
        self.assertIn("Persona Tres", faltantes)

        # Editar Persona 3 y asignarle correo válido
        ok, _ = self.controller.edit_person(3, "Persona Tres", new_email="tres@correo.cl")
        self.assertTrue(ok)

        # Ahora todos deben tener correo
        valido2, faltantes2 = self.manager.validate_all_emails_registered()
        self.assertTrue(valido2)
        self.assertEqual(len(faltantes2), 0)

    def test_add_person_with_valid_and_invalid_email(self):
        # Correo inválido debe ser rechazado por controller
        ok_bad, msg_bad = self.controller.add_person("Persona Cuatro", email="invalido")
        self.assertFalse(ok_bad)
        self.assertIn("no es válido", msg_bad)

        # Correo válido debe aceptarse
        ok_good, msg_good = self.controller.add_person("Persona Cuatro", email="cuatro@correo.cl")
        self.assertTrue(ok_good)
        p4 = next(p for p in self.manager.personal if p['nombre'] == "Persona Cuatro")
        self.assertEqual(p4['email'], "cuatro@correo.cl")

    def test_manual_assignment_stores_motive_and_persists(self):
        week_key = "2026-09-07_2026-09-13"
        period_key = "2026-09"

        self.manager.set_manual_assignment(
            period_key, week_key, "Persona Dos", motivo="Permuta urgente por turno"
        )
        self.assertEqual(self.manager.get_manual_motive(period_key, week_key), "Permuta urgente por turno")

        # Verificar persistencia en archivo
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["asignaciones_manuales_motivos"][period_key][week_key], "Permuta urgente por turno")

        # Remover asignación manual debe limpiar también el motivo
        self.manager.remove_manual_assignment(period_key, week_key)
        self.assertEqual(self.manager.get_manual_motive(period_key, week_key), "")

    def test_notification_settings_crud(self):
        from unittest.mock import patch
        with patch("models.shift_manager.get_env_var", return_value=""), \
             patch("models.shift_manager.set_env_var") as mock_set_env:
            settings = self.controller.get_notification_settings()
            self.assertEqual(settings["webhook_url"], "https://script.google.com/test")

            self.controller.set_notification_settings("https://new.webhook.url")
            new_settings = self.controller.get_notification_settings()
            self.assertEqual(new_settings["webhook_url"], "https://new.webhook.url")
            mock_set_env.assert_any_call("WEBHOOK_URL", "https://new.webhook.url")

        # Verificar persistencia en JSON y que 'notificaciones' sea la primera clave
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["notificaciones"]["webhook_url"], "https://new.webhook.url")
        self.assertEqual(list(data.keys())[0], "notificaciones")
