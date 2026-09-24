import os
import sys
import tempfile
import unittest
from unittest.mock import patch

from utils.app_paths import get_application_data_dir, APP_NAME
from models.shift_manager import ShiftManager


class TestAppPaths(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dev_mode_returns_repo_root(self):
        with patch.object(sys, "frozen", False, create=True):
            path = get_application_data_dir()
            self.assertTrue(os.path.isabs(path))
            self.assertTrue(os.path.exists(os.path.join(path, "main.py")))

    def test_frozen_mode_defaults_to_appdata(self):
        mock_appdata = os.path.join(self.temp_dir.name, "AppData", "Roaming")
        with patch.object(sys, "frozen", True, create=True), \
             patch.object(sys, "executable", os.path.join(self.temp_dir.name, "bin", "Sistema de Turnos.exe")), \
             patch.dict(os.environ, {"APPDATA": mock_appdata}):
            path = get_application_data_dir()
            expected = os.path.join(mock_appdata, APP_NAME)
            self.assertEqual(path, expected)
            self.assertTrue(os.path.exists(expected))

    def test_frozen_mode_detects_portable_config(self):
        exe_dir = os.path.join(self.temp_dir.name, "PortableTurnos")
        os.makedirs(exe_dir, exist_ok=True)
        local_config = os.path.join(exe_dir, "config.json")
        with open(local_config, "w", encoding="utf-8") as f:
            f.write("{}")

        with patch.object(sys, "frozen", True, create=True), \
             patch.object(sys, "executable", os.path.join(exe_dir, "Sistema de Turnos.exe")):
            path = get_application_data_dir()
            self.assertEqual(path, exe_dir)

    def test_frozen_mode_detects_portable_marker(self):
        exe_dir = os.path.join(self.temp_dir.name, "UsbDrive")
        os.makedirs(exe_dir, exist_ok=True)
        marker = os.path.join(exe_dir, ".portable")
        with open(marker, "w", encoding="utf-8") as f:
            f.write("")

        with patch.object(sys, "frozen", True, create=True), \
             patch.object(sys, "executable", os.path.join(exe_dir, "Sistema de Turnos.exe")):
            path = get_application_data_dir()
            self.assertEqual(path, exe_dir)

    def test_shift_manager_loads_bundled_template_when_frozen(self):
        bundle_dir = os.path.join(self.temp_dir.name, "meipass_mock")
        os.makedirs(bundle_dir, exist_ok=True)
        bundled_config_file = os.path.join(bundle_dir, "config.json")
        with open(bundled_config_file, "w", encoding="utf-8") as f:
            f.write('{"personal": [{"id": 1, "nombre": "TEST FUNCIONARIO"}]}')

        target_config = os.path.join(self.temp_dir.name, "fresh_user_data", "config.json")

        with patch.object(sys, "frozen", True, create=True), \
             patch.object(sys, "_MEIPASS", bundle_dir, create=True):
            sm = ShiftManager(target_config)
            self.assertEqual(len(sm.personal), 1)
            self.assertEqual(sm.personal[0]["nombre"], "TEST FUNCIONARIO")
            self.assertTrue(os.path.exists(target_config))
