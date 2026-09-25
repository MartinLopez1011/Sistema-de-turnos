import unittest
from unittest.mock import patch, MagicMock
import urllib.error
from utils.email_notifier import (
    is_valid_email,
    check_internet_connection,
    format_plain_text_message,
    send_notification_webhook
)


class TestEmailNotifier(unittest.TestCase):
    def test_is_valid_email(self):
        # Correos válidos
        self.assertTrue(is_valid_email("usuario@dominio.cl"))
        self.assertTrue(is_valid_email("juan.perez@institucion.gob.cl"))
        self.assertTrue(is_valid_email("test_123+tag@gmail.com"))
        self.assertTrue(is_valid_email("  persona@correo.com  "))

        # Correos inválidos
        self.assertFalse(is_valid_email(""))
        self.assertFalse(is_valid_email("   "))
        self.assertFalse(is_valid_email("sincorreo"))
        self.assertFalse(is_valid_email("usuario@"))
        self.assertFalse(is_valid_email("@dominio.cl"))
        self.assertFalse(is_valid_email("usuario@dominio"))
        self.assertFalse(is_valid_email(None))
        self.assertFalse(is_valid_email(12345))

    def test_format_plain_text_message(self):
        cambios = [
            {
                "semana_texto": "07/09/2026 al 13/09/2026",
                "anterior": "JUAN PEREZ",
                "nuevo": "MARIA GONZALEZ",
                "motivo": "Permuta acordada",
                "fecha_registro": "22/09/2026 16:30"
            }
        ]
        msg = format_plain_text_message("Septiembre", 2026, cambios)
        self.assertIn("SISTEMA DE GESTIÓN DE TURNOS", msg)
        self.assertIn("Septiembre 2026", msg)
        self.assertIn("07/09/2026 al 13/09/2026", msg)
        self.assertIn("JUAN PEREZ", msg)
        self.assertIn("MARIA GONZALEZ", msg)
        self.assertIn("Permuta acordada", msg)
        self.assertIn("• CAMBIO #1", msg)

    @patch("socket.create_connection")
    def test_check_internet_connection(self, mock_socket):
        # Simular conexión exitosa
        mock_socket.return_value = MagicMock()
        self.assertTrue(check_internet_connection())
        # Verificar que se utiliza el puerto 443 HTTPS
        call_args = mock_socket.call_args[0][0]
        self.assertEqual(call_args[1], 443)

        # Simular falla de conexión
        mock_socket.side_effect = OSError("Sin red")
        self.assertFalse(check_internet_connection())

    def test_send_notification_webhook_empty_url(self):
        ok, msg = send_notification_webhook("", ["a@b.cl"], "Asunto", "Cuerpo")
        self.assertFalse(ok)
        self.assertIn("no está configurada", msg)

    def test_send_notification_webhook_no_valid_recipients(self):
        ok, msg = send_notification_webhook("https://fake.url", ["invalido", ""], "Asunto", "Cuerpo")
        self.assertFalse(ok)
        self.assertIn("No hay destinatarios válidos", msg)

    @patch("urllib.request.build_opener")
    def test_send_notification_webhook_success(self, mock_build_opener):
        mock_opener = MagicMock()
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.read.return_value = b'{"status": "ok"}'
        mock_resp.__enter__.return_value = mock_resp
        mock_opener.open.return_value = mock_resp
        mock_build_opener.return_value = mock_opener

        ok, msg = send_notification_webhook(
            "https://script.google.com/macros/s/xyz/exec",
            ["test@correo.cl"],
            "Asunto",
            "Cuerpo"
        )
        self.assertTrue(ok)
        self.assertIn("correctamente", msg)

    @patch("urllib.request.build_opener")
    def test_send_notification_webhook_remote_error(self, mock_build_opener):
        mock_opener = MagicMock()
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.read.return_value = b'{"status": "error", "message": "Cuota diaria excedida"}'
        mock_resp.__enter__.return_value = mock_resp
        mock_opener.open.return_value = mock_resp
        mock_build_opener.return_value = mock_opener

        ok, msg = send_notification_webhook(
            "https://script.google.com/macros/s/xyz/exec",
            ["test@correo.cl"],
            "Asunto",
            "Cuerpo"
        )
        self.assertFalse(ok)
        self.assertIn("Cuota diaria excedida", msg)

    @patch("urllib.request.build_opener")
    def test_send_notification_webhook_timeout(self, mock_build_opener):
        mock_opener = MagicMock()
        mock_opener.open.side_effect = TimeoutError("Timeout")
        mock_build_opener.return_value = mock_opener

        ok, msg = send_notification_webhook(
            "https://script.google.com/macros/s/xyz/exec",
            ["test@correo.cl"],
            "Asunto",
            "Cuerpo"
        )
        self.assertFalse(ok)
        self.assertIn("Tiempo de espera agotado", msg)
