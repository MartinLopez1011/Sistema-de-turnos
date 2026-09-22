import os
import tempfile
import unittest
from utils.env_helper import load_env_file, get_env_var, set_env_var


class TestEnvHelper(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.env_file = os.path.join(self.temp_dir.name, ".env")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_and_get_env_file(self):
        with open(self.env_file, "w", encoding="utf-8") as f:
            f.write("# Comentario\n")
            f.write("WEBHOOK_URL=https://script.google.com/test_env\n")
            f.write("OTRA_VAR='valor con espacios'\n")

        vars_dict = load_env_file(self.env_file)
        self.assertEqual(vars_dict["WEBHOOK_URL"], "https://script.google.com/test_env")
        self.assertEqual(vars_dict["OTRA_VAR"], "valor con espacios")

    def test_set_env_var_creates_and_updates(self):
        # Crear nueva variable
        ok = set_env_var("TEST_KEY", "test_val", self.env_file)
        self.assertTrue(ok)

        vars_dict = load_env_file(self.env_file)
        self.assertEqual(vars_dict.get("TEST_KEY"), "test_val")

        # Actualizar variable existente
        ok2 = set_env_var("TEST_KEY", "nuevo_valor", self.env_file)
        self.assertTrue(ok2)

        vars_dict2 = load_env_file(self.env_file)
        self.assertEqual(vars_dict2.get("TEST_KEY"), "nuevo_valor")
