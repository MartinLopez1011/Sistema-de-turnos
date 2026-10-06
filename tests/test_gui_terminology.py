"""Pruebas unitarias para validar la ausencia de terminología 'guardia'

y la correcta presencia de 'turno / turnos' en los módulos de interfaz gráfica (views).
"""
import os
import unittest


class TestGuiTerminology(unittest.TestCase):
    """Verifica que la interfaz de usuario utilice exclusivamente la terminología de turnos."""

    def setUp(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.views_dir = os.path.join(self.project_root, "views")

    def test_no_guardia_in_views(self):
        """Verifica que ninguna vista contenga la palabra 'guardia'."""
        violations = []
        for root, _, files in os.walk(self.views_dir):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.project_root)
                    with open(full_path, "r", encoding="utf-8") as f:
                        for line_num, line in enumerate(f, 1):
                            if "guardia" in line.lower():
                                violations.append(f"{rel_path}:{line_num}: {line.strip()}")

        self.assertEqual(
            violations,
            [],
            "Se encontraron ocurrencias no deseadas de 'guardia' en las vistas:\n"
            + "\n".join(violations),
        )

    def test_turnos_terminology_present_in_views(self):
        """Verifica que los textos clave de turnos estén presentes en los archivos correspondientes."""
        expected_strings_per_file = {
            os.path.join("views", "components", "dialogs.py"): [
                "Asignar Turno",
                "Semana de turno:",
                "Nuevo funcionario asignado al turno:",
            ],
            os.path.join("views", "tabs", "tab_plan.py"): [
                'title="Cambiar Turno"',
                "● TURNO EN CURSO",
            ],
            os.path.join("views", "tabs", "tab_calendar.py"): [
                "Turno manual:",
                "Turno regular:",
            ],
            os.path.join("views", "gui.py"): [
                "Turno asignado manualmente:",
                "Modificación de Turno",
            ],
        }

        for rel_path, expected_phrases in expected_strings_per_file.items():
            full_path = os.path.join(self.project_root, rel_path)
            self.assertTrue(os.path.exists(full_path), f"El archivo {rel_path} no existe")
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
                for phrase in expected_phrases:
                    self.assertIn(
                        phrase,
                        content,
                        f"La frase esperada '{phrase}' no fue encontrada en {rel_path}",
                    )


if __name__ == "__main__":
    unittest.main()
