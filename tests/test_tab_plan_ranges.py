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


if __name__ == "__main__":
    unittest.main()
