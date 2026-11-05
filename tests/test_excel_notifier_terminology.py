"""Pruebas unitarias para validar la ausencia de terminología 'guardia'

y la correcta presencia de 'turno / turnos' en utils/excel_handler.py y utils/email_notifier.py.
"""
import os
import unittest


class TestExcelNotifierTerminology(unittest.TestCase):
    """Verifica que los reportes Excel y las notificaciones utilicen exclusivamente la terminología de turnos."""

    def setUp(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.excel_handler_path = os.path.join(self.project_root, "utils", "excel_handler.py")
        self.email_notifier_path = os.path.join(self.project_root, "utils", "email_notifier.py")

    def test_no_guardia_in_utils(self):
        """Verifica que ni excel_handler.py ni email_notifier.py contengan la palabra 'guardia'."""
        violations = []
        for path in [self.excel_handler_path, self.email_notifier_path]:
            rel_path = os.path.relpath(path, self.project_root)
            with open(path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if "guardia" in line.lower():
                        violations.append(f"{rel_path}:{line_num}: {line.strip()}")

        self.assertEqual(
            violations,
            [],
            "Se encontraron ocurrencias no deseadas de 'guardia':\n"
            + "\n".join(violations),
        )

    def test_turnos_terminology_present_in_excel_and_notifier(self):
        """Verifica que los textos clave de turnos estén presentes en los archivos correspondientes."""
        expected_strings_per_file = {
            self.excel_handler_path: [
                "CAMBIO MANUAL DE TURNO",
                "Turno original:",
                "Cambio de Turno (Manual)",
                "REGISTRO DE CAMBIOS MANUALES DE TURNO (PERMUTAS / REEMPLAZOS)",
                "TURNO ORIGINAL",
            ],
            self.email_notifier_path: [
                "RECORDATORIO DE TURNOS:",
                "AVISO DE CAMBIO DE TURNO",
                "Turno programado original:",
                "Nuevo turno asignado:",
            ],
        }

        for file_path, expected_phrases in expected_strings_per_file.items():
            rel_path = os.path.relpath(file_path, self.project_root)
            self.assertTrue(os.path.exists(file_path), f"El archivo {rel_path} no existe")
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                for phrase in expected_phrases:
                    self.assertIn(
                        phrase,
                        content,
                        f"La frase esperada '{phrase}' no fue encontrada en {rel_path}",
                    )


if __name__ == "__main__":
    unittest.main()
