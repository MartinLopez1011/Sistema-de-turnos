import json
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

from controllers.main_controller import MainController
from models.shift_manager import ShiftManager


class TestCrossMonthContinuity(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root_path = Path(self.temp_dir.name)
        self.config_path = self.root_path / "config.json"

        # Cargar backup 16:12 o plantilla equivalente
        backup_path = Path("backups/config_20260928_161235_respaldo_manual.json")
        if backup_path.exists():
            data = json.loads(backup_path.read_text(encoding="utf-8"))
        else:
            data = {
                "personal": [
                    {"id": 1, "nombre": "P1", "email": ""},
                    {"id": 2, "nombre": "P2", "email": ""},
                ],
                "inicio": {},
                "historial": {},
                "siguiente_id": 1,
                "pendientes": [],
                "snapshots": {},
                "excepciones": {},
                "asignaciones_manuales": {},
            }

        self.config_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        self.controller = MainController(str(self.root_path))
        self.manager = self.controller.shift_manager

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_rosas_pino_transition_between_nov_and_dec(self):
        """
        Verifica que en el escenario del backup 16:12:
        - La semana limítrofe (2026-11-30 a 2026-12-06) queda asignada a PRO ROSAS FERNANDEZ RODRIGO tanto
          en la planificación de Noviembre como en la de Diciembre.
        - En Diciembre, el 1 de diciembre (martes) pertenece a dicho turno y es cubierto por Rosas.
        - PRO PINO ALARCON JOSE MIGUEL (saltado por FL el 30/11) recupera su turno en la siguiente semana
          disponible de Diciembre (2026-12-07 a 2026-12-13).
        """
        nov_exc = self.manager.get_exceptions_for_period(2026, 11)
        nov_shifts = self.controller.preview_shifts(2026, 11, nov_exc)

        dec_exc = self.manager.get_exceptions_for_period(2026, 12)
        dec_shifts = self.controller.preview_shifts(2026, 12, dec_exc)

        # Última semana de Noviembre
        last_nov = nov_shifts[-1]
        self.assertEqual(last_nov["semana"], (date(2026, 11, 30), date(2026, 12, 7)))
        self.assertEqual(last_nov["persona"], "PRO ROSAS FERNANDEZ RODRIGO")

        # Primera semana de Diciembre debe ser exactamente la misma semana limítrofe
        first_dec = dec_shifts[0]
        self.assertEqual(first_dec["semana"], (date(2026, 11, 30), date(2026, 12, 7)))
        self.assertEqual(first_dec["persona"], "PRO ROSAS FERNANDEZ RODRIGO")

        # Segunda semana de Diciembre es donde Pino recupera su guardia
        second_dec = dec_shifts[1]
        self.assertEqual(second_dec["semana"], (date(2026, 12, 7), date(2026, 12, 14)))
        self.assertEqual(second_dec["persona"], "PRO PINO ALARCON JOSE MIGUEL")

    def test_bridging_week_preserved_after_advance_month(self):
        """
        Verifica que al cerrar formalmente Noviembre, la semana 2026-11-30_2026-12-07
        se guarde con Rosas en el historial y la previsualización de Diciembre
        siga mostrando a Rosas en la primera semana y Pino en la segunda.
        """
        nov_exc = self.manager.get_exceptions_for_period(2026, 11)
        ok, msg = self.controller.advance_queue(2026, 11, nov_exc)
        self.assertTrue(ok, f"Error cerrando mes: {msg}")

        # Comprobar historial guardado
        self.assertEqual(
            self.manager.historial.get("2026-11-30_2026-12-07"),
            "PRO ROSAS FERNANDEZ RODRIGO"
        )

        dec_exc = self.manager.get_exceptions_for_period(2026, 12)
        dec_shifts = self.controller.preview_shifts(2026, 12, dec_exc)

        self.assertEqual(dec_shifts[0]["persona"], "PRO ROSAS FERNANDEZ RODRIGO")
        self.assertEqual(dec_shifts[1]["persona"], "PRO PINO ALARCON JOSE MIGUEL")


if __name__ == "__main__":
    unittest.main()
