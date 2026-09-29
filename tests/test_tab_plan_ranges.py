import unittest
from datetime import date
from unittest.mock import MagicMock

from views.tabs.tab_plan import TabPlan


class TabPlanRangeParsingTests(unittest.TestCase):
    def test_range_parsing_expands_and_sorts_correctly(self):
        # Simular app y widgets mínimos para probar add_exception
        mock_app = MagicMock()
        mock_app.get_selected_period.return_value = (2026, 9)
        mock_app.exceptions = []

        mock_parent = MagicMock()

        # Instanciar TabPlan con mocks
        tab_plan = TabPlan.__new__(TabPlan)
        tab_plan.app = mock_app
        tab_plan.person_var = MagicMock()
        tab_plan.person_var.get.return_value = "COM PEREZ JUAN"
        tab_plan.type_var = MagicMock()
        tab_plan.type_var.get.return_value = "DA"
        tab_plan.days_entry = MagicMock()
        tab_plan.days_entry.get.return_value = "1-3, 5, 8-10"

        tab_plan.add_exception()

        # Debe haber llamado a app.add_exceptions con días 1, 2, 3, 5, 8, 9, 10
        mock_app.add_exceptions.assert_called_once()
        added = mock_app.add_exceptions.call_args[0][0]
        added_days = [e['fecha'].day for e in added]
        self.assertEqual(added_days, [1, 2, 3, 5, 8, 9, 10])
        for e in added:
            self.assertEqual(e['persona'], "COM PEREZ JUAN")
            self.assertEqual(e['tipo'], "DA")

    def test_range_parsing_tolerant_to_existing_duplicates(self):
        mock_app = MagicMock()
        mock_app.get_selected_period.return_value = (2026, 9)
        # Supongamos que el día 2 ya existía
        mock_app.exceptions = [
            {"persona": "COM PEREZ JUAN", "fecha": date(2026, 9, 2), "tipo": "DA"}
        ]

        tab_plan = TabPlan.__new__(TabPlan)
        tab_plan.app = mock_app
        tab_plan.person_var = MagicMock()
        tab_plan.person_var.get.return_value = "COM PEREZ JUAN"
        tab_plan.type_var = MagicMock()
        tab_plan.type_var.get.return_value = "DA"
        tab_plan.days_entry = MagicMock()
        tab_plan.days_entry.get.return_value = "1-4"

        tab_plan.add_exception()

        # Debe agregar 1, 3, 4 (omitiendo el 2)
        mock_app.add_exceptions.assert_called_once()
        added = mock_app.add_exceptions.call_args[0][0]
        added_days = [e['fecha'].day for e in added]
        self.assertEqual(added_days, [1, 3, 4])


    def test_resolve_initial_picker_date_uses_planned_period(self):
        mock_app = MagicMock()
        mock_app.get_selected_period.return_value = (2026, 11)  # Noviembre 2026

        tab_plan = TabPlan.__new__(TabPlan)
        tab_plan.app = mock_app

        # 1. Si el input está vacío, debe devolver el mes planificado (Noviembre 2026, día 1)
        res_empty = tab_plan._resolve_initial_picker_date("")
        self.assertEqual(res_empty, date(2026, 11, 1))

        # 2. Si el usuario ingresó sólo el día "15", debe resolver a 15/11/2026
        res_day = tab_plan._resolve_initial_picker_date("15")
        self.assertEqual(res_day, date(2026, 11, 15))

        # 3. Si ingresó una fecha explícita, debe respetarla
        res_explicit = tab_plan._resolve_initial_picker_date("20/12/2026")
        self.assertEqual(res_explicit, date(2026, 12, 20))


    def test_multiple_explicit_dates_parsing(self):
        mock_app = MagicMock()
        mock_app.get_selected_period.return_value = (2026, 10)
        mock_app.exceptions = []

        tab_plan = TabPlan.__new__(TabPlan)
        tab_plan.app = mock_app
        tab_plan.person_var = MagicMock()
        tab_plan.person_var.get.return_value = "COM PEREZ JUAN"
        tab_plan.type_var = MagicMock()
        tab_plan.type_var.get.return_value = "FL"
        tab_plan.from_entry = MagicMock()
        tab_plan.from_entry.get.return_value = "04/10/2026, 12/10/2026, 20/10/2026"
        tab_plan.to_entry = MagicMock()
        tab_plan.to_entry.get.return_value = ""

        tab_plan.add_exception()

        mock_app.add_exceptions.assert_called_once()
        added = mock_app.add_exceptions.call_args[0][0]
        self.assertEqual(len(added), 3)
        self.assertEqual(added[0]['fecha'], date(2026, 10, 4))
        self.assertEqual(added[1]['fecha'], date(2026, 10, 12))
        self.assertEqual(added[2]['fecha'], date(2026, 10, 20))
        for e in added:
            self.assertEqual(e['tipo'], "FL")
            self.assertEqual(e['persona'], "COM PEREZ JUAN")


if __name__ == "__main__":
    unittest.main()

