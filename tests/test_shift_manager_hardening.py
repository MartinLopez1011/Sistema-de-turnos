import json
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

from controllers.main_controller import MainController
from models.shift_manager import ShiftManager


class TestShiftManagerHardening(unittest.TestCase):
    """Pruebas rigurosas de robustez y resiliencia para ShiftManager y MainController."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root_path = Path(self.temp_dir.name)
        self.config_path = self.root_path / "config.json"

        self.personal = [
            {"id": 1, "nombre": "PRO ALVIÑA NEIRA PRISCILA", "email": "p1@example.com"},
            {"id": 2, "nombre": "PRO FLORES ROJAS NATALIA", "email": "p2@example.com"},
            {"id": 3, "nombre": "COM MARFULL VILLANUEVA SCARLETT", "email": "p3@example.com"},
            {"id": 4, "nombre": "PRO ROSAS FERNANDEZ RODRIGO", "email": "p4@example.com"},
            {"id": 5, "nombre": "PRO PINO ALARCON JOSE MIGUEL", "email": "p5@example.com"},
        ]
        self.config_data = {
            "personal": self.personal,
            "inicio": {},
            "historial": {},
            "siguiente_id": 1,
            "pendientes": [],
            "snapshots": {},
            "excepciones": {},
            "asignaciones_manuales": {},
            "asignaciones_manuales_motivos": {},
        }
        self.config_path.write_text(json.dumps(self.config_data), encoding="utf-8")
        self.controller = MainController(str(self.root_path))
        self.manager = self.controller.shift_manager

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_clean_exception_partitioning_no_pollution(self):
        """Verifica que advance_month nunca contamine la clave del mes con excepciones de otros meses."""
        # Agregar excepciones en noviembre y en diciembre (semana limítrofe)
        self.manager.add_exception_date("PRO ROSAS FERNANDEZ RODRIGO", "2026-11-30", "FL")
        self.manager.add_exception_date("PRO PINO ALARCON JOSE MIGUEL", "2026-12-01", "DA")
        self.manager.save_config()

        # Las excepciones deben estar en sus respectivas claves
        self.assertIn("2026-11", self.manager.excepciones)
        self.assertIn("2026-12", self.manager.excepciones)
        self.assertTrue(all(e["fecha"].startswith("2026-11") for e in self.manager.excepciones["2026-11"]))
        self.assertTrue(all(e["fecha"].startswith("2026-12") for e in self.manager.excepciones["2026-12"]))

        # Al consultar para diciembre 2026, get_exceptions_for_period debe incluir ambas
        excs_dec = self.controller.get_exceptions_for_period(2026, 12)
        fechas = [e["fecha"].isoformat() if hasattr(e["fecha"], "isoformat") else str(e["fecha"]) for e in excs_dec]
        self.assertIn("2026-11-30", fechas)
        self.assertIn("2026-12-01", fechas)

        # Cerrar diciembre con la lista de get_exceptions_for_period
        ok, _ = self.controller.advance_queue(2026, 12, excs_dec)
        self.assertTrue(ok)

        # Verificar que la clave 2026-12 NO contiene fechas de 2026-11
        saved_dec = self.manager.excepciones.get("2026-12", [])
        self.assertTrue(all(e["fecha"].startswith("2026-12") for e in saved_dec),
                        "La clave 2026-12 contiene fechas ajenas a diciembre")

    def test_year_boundary_december_to_january(self):
        """Verifica la continuidad de la semana limítrofe entre diciembre y enero de años distintos."""
        # 2026-12 termina con una semana que se extiende a 2027-01: 2026-12-28 a 2027-01-03
        dec_shifts = self.controller.preview_shifts(2026, 12)
        last_shift_dec = dec_shifts[-1]
        self.assertEqual(last_shift_dec["semana"][0], date(2026, 12, 28))
        self.assertEqual(last_shift_dec["semana"][1], date(2027, 1, 3))
        person_bridging = last_shift_dec["persona"]

        # Cerrar diciembre
        ok, _ = self.controller.advance_queue(2026, 12, [])
        self.assertTrue(ok)

        # En enero 2027, la semana 0 debe ser idéntica a la asignada por diciembre
        jan_shifts = self.controller.preview_shifts(2027, 1)
        first_shift_jan = jan_shifts[0]
        self.assertEqual(first_shift_jan["semana"][0], date(2026, 12, 28))
        self.assertEqual(first_shift_jan["semana"][1], date(2027, 1, 3))
        self.assertEqual(first_shift_jan["persona"], person_bridging)

        # La segunda semana de enero no debe repetir a person_bridging inmediatamente
        self.assertNotEqual(jan_shifts[1]["persona"], person_bridging)

    def test_multi_month_future_navigation_consistency(self):
        """Navegar y planificar múltiples meses futuros en orden aleatorio mantiene consistencia perfecta."""
        # Agregar excepción en mes futuro distante (2027-03)
        self.manager.add_exception_date("PRO ROSAS FERNANDEZ RODRIGO", "2027-03-15", "LIC")
        self.manager.save_config()

        # Calcular marzo 2027 primero
        shifts_mar = self.controller.preview_shifts(2027, 3)
        # La persona con LIC no debe ser asignada en la semana del 15 de marzo
        for s in shifts_mar:
            if s["semana"][0] <= date(2027, 3, 15) <= s["semana"][1]:
                self.assertNotEqual(s["persona"], "PRO ROSAS FERNANDEZ RODRIGO")

        # Calcular enero y febrero
        shifts_jan = self.controller.preview_shifts(2027, 1)
        shifts_feb = self.controller.preview_shifts(2027, 2)
        self.assertTrue(len(shifts_jan) > 0)
        self.assertTrue(len(shifts_feb) > 0)

        # Recalcular marzo: debe permanecer idéntico
        shifts_mar_2 = self.controller.preview_shifts(2027, 3)
        self.assertEqual([s["persona"] for s in shifts_mar], [s["persona"] for s in shifts_mar_2])

    def test_remove_exception_range_in_bridging_dates(self):
        """Verifica que eliminar excepciones en fechas limítrofes funcione limpiamente."""
        self.manager.add_exception_date("PRO PINO ALARCON JOSE MIGUEL", "2026-11-30", "FL")
        self.manager.save_config()

        # Verificar presencia
        excs_before = self.controller.get_exceptions_for_period(2026, 12)
        self.assertTrue(any(e["persona"] == "PRO PINO ALARCON JOSE MIGUEL" and "2026-11-30" in str(e["fecha"]) for e in excs_before))

        # Eliminar mediante remove_exception_range
        rem_count = self.manager.remove_exception_range("PRO PINO ALARCON JOSE MIGUEL", date(2026, 11, 30), date(2026, 11, 30))
        self.assertEqual(rem_count, 1)

        excs_after = self.controller.get_exceptions_for_period(2026, 12)
        self.assertFalse(any(e["persona"] == "PRO PINO ALARCON JOSE MIGUEL" and "2026-11-30" in str(e["fecha"]) for e in excs_after))
