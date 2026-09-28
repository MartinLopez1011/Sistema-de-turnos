import os
import tempfile
import unittest
from datetime import date, datetime
from unittest.mock import MagicMock, patch

from models.shift_manager import ShiftManager
from controllers.main_controller import MainController
from utils.excel_handler import ExcelHandler
from views.tabs.tab_plan import TabPlan


class CrossMonthExceptionsTests(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json")
        self.temp_file.close()
        self.config_path = self.temp_file.name

        self.initial_data = {
            "personal": [
                {"id": 1, "nombre": "COM PEREZ JUAN", "email": "perez@test.cl"},
                {"id": 2, "nombre": "COM GONZALEZ MARIA", "email": "gonzalez@test.cl"},
                {"id": 3, "nombre": "COM SOTO CARLOS", "email": "soto@test.cl"}
            ],
            "inicio": {},
            "historial": {},
            "siguiente_id": 1,
            "pendientes": [],
            "snapshots": {},
            "excepciones": {},
            "asignaciones_manuales": {},
            "asignaciones_manuales_motivos": {},
            "auditoria": [],
            "notificaciones": {"webhook_url": "", "activo": False}
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            import json
            json.dump(self.initial_data, f)

        self.manager = ShiftManager(self.config_path)

    def tearDown(self):
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

    def test_add_exception_range_across_months(self):
        """Caso de uso principal: agregar del 30 de octubre al 11 de noviembre."""
        start = date(2026, 10, 30)
        end = date(2026, 11, 11)
        stats = self.manager.add_exception_range("COM PEREZ JUAN", start, end, "DA")

        self.assertEqual(stats["total"], 13)
        self.assertEqual(stats["added"], 13)
        self.assertEqual(stats["periods"], ["2026-10", "2026-11"])

        # Verificar persistencia en config.json
        self.assertIn("2026-10", self.manager.excepciones)
        self.assertIn("2026-11", self.manager.excepciones)

        oct_dates = [e["fecha"] for e in self.manager.excepciones["2026-10"]]
        self.assertEqual(oct_dates, ["2026-10-30", "2026-10-31"])

        nov_dates = [e["fecha"] for e in self.manager.excepciones["2026-11"]]
        self.assertEqual(len(nov_dates), 11)
        self.assertEqual(nov_dates[0], "2026-11-01")
        self.assertEqual(nov_dates[-1], "2026-11-11")

        # Recargar desde disco para confirmar persistencia real
        reloaded = ShiftManager(self.config_path)
        self.assertEqual(len(reloaded.excepciones["2026-10"]), 2)
        self.assertEqual(len(reloaded.excepciones["2026-11"]), 11)

    def test_group_exceptions_into_ranges(self):
        """Verifica que fechas continuas entre meses se agrupen en un solo rango en la UI."""
        start = date(2026, 10, 30)
        end = date(2026, 11, 11)
        self.manager.add_exception_range("COM PEREZ JUAN", start, end, "DA")

        # Agregar otra fecha no consecutiva en noviembre
        self.manager.add_exception_date("COM PEREZ JUAN", date(2026, 11, 25), "FL")

        all_exc = self.manager.get_all_exceptions()
        ranges = ShiftManager.group_exceptions_into_ranges(all_exc)

        self.assertEqual(len(ranges), 2)

        # Primer rango: 30/10 al 11/11 (13 días)
        r1 = ranges[0]
        self.assertEqual(r1["persona"], "COM PEREZ JUAN")
        self.assertEqual(r1["start_date"], date(2026, 10, 30))
        self.assertEqual(r1["end_date"], date(2026, 11, 11))
        self.assertEqual(r1["days_count"], 13)
        self.assertEqual(r1["tipo"], "DA")

        # Segundo rango: 25/11 al 25/11 (1 día)
        r2 = ranges[1]
        self.assertEqual(r2["start_date"], date(2026, 11, 25))
        self.assertEqual(r2["end_date"], date(2026, 11, 25))
        self.assertEqual(r2["days_count"], 1)
        self.assertEqual(r2["tipo"], "FL")

    def test_remove_exception_range_across_months(self):
        """Eliminar un rango continuo borra todas las fechas involucradas en los meses respectivos."""
        self.manager.add_exception_range("COM PEREZ JUAN", date(2026, 10, 30), date(2026, 11, 11), "DA")
        removed = self.manager.remove_exception_range("COM PEREZ JUAN", date(2026, 10, 30), date(2026, 11, 11))

        self.assertEqual(removed, 13)
        self.assertEqual(len(self.manager.excepciones["2026-10"]), 0)
        self.assertEqual(len(self.manager.excepciones["2026-11"]), 0)

    def test_get_exceptions_for_period_includes_overlapping_weeks(self):
        """El cálculo de turnos para octubre debe ver el 01/11 si cae en la última semana de octubre."""
        # Semana: 2026-10-26 al 2026-11-01
        self.manager.add_exception_date("COM PEREZ JUAN", date(2026, 11, 1), "DA")
        oct_exc = self.manager.get_exceptions_for_period(2026, 10)

        # Debe incluir 2026-11-01
        self.assertTrue(any(e["fecha"] == date(2026, 11, 1) and e["persona"] == "COM PEREZ JUAN" for e in oct_exc))

    def test_tab_plan_add_range_explicit_dates(self):
        """Verifica que TabPlan interprete Desde y Hasta con fechas DD/MM/AAAA."""
        mock_app = MagicMock()
        mock_app.get_selected_period.return_value = (2026, 10)

        controller = MainController(os.path.dirname(self.config_path))
        controller.shift_manager = self.manager

        tab = TabPlan.__new__(TabPlan)
        tab.app = mock_app
        tab.controller = controller
        tab.person_var = MagicMock()
        tab.person_var.get.return_value = "COM PEREZ JUAN"
        tab.type_var = MagicMock()
        tab.type_var.get.return_value = "DA"
        tab.from_entry = MagicMock()
        tab.from_entry.get.return_value = "30/10/2026"
        tab.to_entry = MagicMock()
        tab.to_entry.get.return_value = "11/11/2026"
        tab.refresh_exceptions = MagicMock()

        tab.add_exception()

        mock_app.add_exception_range.assert_called_once_with(
            "COM PEREZ JUAN", date(2026, 10, 30), date(2026, 11, 11), "DA", ""
        )

    def test_tab_plan_add_range_shortcut_string(self):
        """Verifica que si el usuario escribe '30/10 al 11/11' en 'Desde', se detecte el rango."""
        mock_app = MagicMock()
        mock_app.get_selected_period.return_value = (2026, 10)

        controller = MainController(os.path.dirname(self.config_path))
        controller.shift_manager = self.manager

        tab = TabPlan.__new__(TabPlan)
        tab.app = mock_app
        tab.controller = controller
        tab.person_var = MagicMock()
        tab.person_var.get.return_value = "COM PEREZ JUAN"
        tab.type_var = MagicMock()
        tab.type_var.get.return_value = "FL"
        tab.from_entry = MagicMock()
        tab.from_entry.get.return_value = "30/10 al 11/11"
        tab.to_entry = MagicMock()
        tab.to_entry.get.return_value = ""
        tab.refresh_exceptions = MagicMock()

        tab.add_exception()

        mock_app.add_exception_range.assert_called_once_with(
            "COM PEREZ JUAN", date(2026, 10, 30), date(2026, 11, 11), "FL", ""
        )

    def test_gui_add_and_remove_exception_range(self):
        """Verifica que TurnosApp.add_exception_range y remove_exception_range no fallen (ej: NameError con _short_name)."""
        from views.gui import TurnosApp

        controller = MainController(os.path.dirname(self.config_path))
        controller.shift_manager = self.manager

        app = TurnosApp.__new__(TurnosApp)
        app.controller = controller
        app.get_selected_period = MagicMock(return_value=(2026, 10))
        app.tab_plan = MagicMock()
        app.refresh_plan_views = MagicMock()
        app.set_status = MagicMock()
        app.mark_dirty = MagicMock()

        # Probar agregar rango
        ok, res = TurnosApp.add_exception_range(app, "COM PEREZ JUAN", date(2026, 10, 30), date(2026, 11, 10), "DA")
        self.assertTrue(ok)
        app.set_status.assert_called_with("✓ Excepción DA guardada (30/10/2026 al 10/11/2026): PEREZ JUAN (12 días)", "ok")

        # Probar remover rango
        ok_rem, res_rem = TurnosApp.remove_exception_range(app, "COM PEREZ JUAN", date(2026, 10, 30), date(2026, 11, 10))
        self.assertTrue(ok_rem)
        app.set_status.assert_called_with("Excepción eliminada (30/10/2026 al 10/11/2026): PEREZ JUAN", "warn")


if __name__ == "__main__":
    unittest.main()
